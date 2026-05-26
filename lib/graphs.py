"""Registry of named graph definitions.

A graph is a callable that takes an iterable of packet dicts plus options and
returns a matplotlib Figure. Register new graphs with @register("name").
"""

from collections import defaultdict


_REGISTRY = {}


def register(name, description=""):
    def decorator(fn):
        _REGISTRY[name] = (fn, description)
        return fn
    return decorator


def get(name):
    if name not in _REGISTRY:
        raise KeyError(f"Unknown graph '{name}'. Available: {', '.join(sorted(_REGISTRY))}")
    return _REGISTRY[name][0]


def available():
    return [(name, desc) for name, (_, desc) in sorted(_REGISTRY.items())]


# --- Unit conversions ---

WATTS_PER_HP = 745.6998715822702
NM_PER_LBFT = 1.3558179483314004


def watts_to_hp(w):
    return w / WATTS_PER_HP


def nm_to_lbft(nm):
    return nm / NM_PER_LBFT


# --- Graph implementations ---

def _moving_average(values, window):
    if window <= 1 or len(values) < 2:
        return list(values)
    half = window // 2
    out = []
    for i in range(len(values)):
        lo = max(0, i - half)
        hi = min(len(values), i + half + 1)
        out.append(sum(values[lo:hi]) / (hi - lo))
    return out


@register("dyno", "RPM vs torque & horsepower (envelope per RPM bin)")
def dyno(packets, bins=80, in_race_only=True, smooth=0):
    import matplotlib.pyplot as plt

    # bucket by RPM; keep max torque and max power per bucket so the curve
    # reflects the engine's output envelope rather than partial-throttle noise.
    rpm_max = 0.0
    rpm_idle = 0.0
    max_torque_per_bin = defaultdict(lambda: float("-inf"))
    max_power_per_bin = defaultdict(lambda: float("-inf"))
    sample_count = 0

    for p in packets:
        if in_race_only and not p.get("IsRaceOn"):
            continue
        rpm = p.get("CurrentEngineRpm", 0.0)
        if rpm <= 0:
            continue
        rpm_max = max(rpm_max, p.get("EngineMaxRpm", 0.0))
        rpm_idle = rpm_idle or p.get("EngineIdleRpm", 0.0)
        sample_count += 1
        torque = p.get("Torque", 0.0)
        power = p.get("Power", 0.0)
        # bin index keyed by rpm; finalize ranges once we know rpm_max
        max_torque_per_bin[rpm] = max(max_torque_per_bin[rpm], torque)
        max_power_per_bin[rpm] = max(max_power_per_bin[rpm], power)

    if sample_count == 0:
        raise ValueError("No usable samples (try --all to include non-race samples)")

    rpm_lo = rpm_idle if rpm_idle > 0 else 0.0
    rpm_hi = rpm_max if rpm_max > rpm_lo else max(max_torque_per_bin)
    edges = [rpm_lo + (rpm_hi - rpm_lo) * i / bins for i in range(bins + 1)]

    binned_rpm = []
    binned_torque = []
    binned_power = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        torques = [t for r, t in max_torque_per_bin.items() if lo <= r < hi]
        powers = [p for r, p in max_power_per_bin.items() if lo <= r < hi]
        if not torques:
            continue
        binned_rpm.append((lo + hi) / 2)
        binned_torque.append(nm_to_lbft(max(torques)))
        binned_power.append(watts_to_hp(max(powers)))

    binned_torque = _moving_average(binned_torque, smooth)
    binned_power = _moving_average(binned_power, smooth)

    fig, ax_t = plt.subplots(figsize=(10, 6))
    ax_p = ax_t.twinx()

    (line_t,) = ax_t.plot(binned_rpm, binned_torque, color="tab:red", label="Torque (lb-ft)")
    (line_p,) = ax_p.plot(binned_rpm, binned_power, color="tab:blue", label="Power (HP)")

    if binned_torque:
        peak_t_i = max(range(len(binned_torque)), key=lambda i: binned_torque[i])
        peak_p_i = max(range(len(binned_power)), key=lambda i: binned_power[i])
        ax_t.axvline(binned_rpm[peak_t_i], color="tab:red", alpha=0.2, linestyle="--")
        ax_p.axvline(binned_rpm[peak_p_i], color="tab:blue", alpha=0.2, linestyle="--")
        ax_t.annotate(
            f"{binned_torque[peak_t_i]:.0f} lb-ft @ {binned_rpm[peak_t_i]:.0f}",
            xy=(binned_rpm[peak_t_i], binned_torque[peak_t_i]),
            xytext=(6, -14), textcoords="offset points", color="tab:red", fontsize=9,
        )
        ax_p.annotate(
            f"{binned_power[peak_p_i]:.0f} HP @ {binned_rpm[peak_p_i]:.0f}",
            xy=(binned_rpm[peak_p_i], binned_power[peak_p_i]),
            xytext=(6, 6), textcoords="offset points", color="tab:blue", fontsize=9,
        )

    ax_t.set_xlabel("Engine RPM")
    ax_t.set_ylabel("Torque (lb-ft)", color="tab:red")
    ax_p.set_ylabel("Power (HP)", color="tab:blue")
    ax_t.tick_params(axis="y", labelcolor="tab:red")
    ax_p.tick_params(axis="y", labelcolor="tab:blue")
    ax_t.grid(True, alpha=0.3)
    ax_t.legend(handles=[line_t, line_p], loc="lower right")
    fig.tight_layout()
    return fig


@register("timeseries", "Plot one or more fields over CurrentRaceTime")
def timeseries(packets, fields=("CurrentEngineRpm",), in_race_only=True, smooth=0):
    import matplotlib.pyplot as plt

    times = []
    series = {f: [] for f in fields}
    for p in packets:
        if in_race_only and not p.get("IsRaceOn"):
            continue
        times.append(p.get("CurrentRaceTime", 0.0))
        for f in fields:
            series[f].append(p.get(f, 0.0))

    if not times:
        raise ValueError("No usable samples (try --all to include non-race samples)")

    fig, ax = plt.subplots(figsize=(10, 6))
    for f, ys in series.items():
        ax.plot(times, _moving_average(ys, smooth), label=f, linewidth=1)
    ax.set_xlabel("Race time (s)")
    ax.set_ylabel("Value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    return fig
