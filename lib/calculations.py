"""Derived metrics from telemetry packets.

Each calculation is a small streaming accumulator: feed packets via update()
and read the result from a property. Build new metrics by following the same
pattern.
"""

from .graphs import watts_to_hp  # convenience re-use; small dep


class PeakPower:
    """Tracks the RPM at which the highest engine Power was observed."""

    def __init__(self, in_race_only=True):
        self.in_race_only = in_race_only
        self._max_power = float("-inf")
        self._rpm_at_max = None

    def update(self, packet):
        if self.in_race_only and not packet.get("IsRaceOn"):
            return
        power = packet.get("Power", 0.0)
        if power > self._max_power:
            self._max_power = power
            self._rpm_at_max = packet.get("CurrentEngineRpm")

    @property
    def rpm(self):
        return self._rpm_at_max

    @property
    def power_watts(self):
        return self._max_power if self._rpm_at_max is not None else None

    @property
    def power_hp(self):
        w = self.power_watts
        return watts_to_hp(w) if w is not None else None


class Redline:
    """Engine rev limit as reported by the game (EngineMaxRpm)."""

    def __init__(self, in_race_only=True):
        self.in_race_only = in_race_only
        self._max = 0.0

    def update(self, packet):
        if self.in_race_only and not packet.get("IsRaceOn"):
            return
        rpm = packet.get("EngineMaxRpm", 0.0)
        if rpm > self._max:
            self._max = rpm

    @property
    def rpm(self):
        return self._max if self._max > 0 else None


def summarize(packets, in_race_only=True):
    """Run all stock calculations in one pass. Returns a dict of results."""
    peak = PeakPower(in_race_only=in_race_only)
    redline = Redline(in_race_only=in_race_only)
    for p in packets:
        peak.update(p)
        redline.update(p)
    return {
        "peak_power_rpm": peak.rpm,
        "peak_power_hp": peak.power_hp,
        "redline_rpm": redline.rpm,
    }
