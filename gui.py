import datetime as dt
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from lib.fh6 import TELEMETRY_FIELDS, listen_raw, parse_packet
from lib.recording import EXTENSION, Recorder


COLUMNS = 2
REFRESH_MS = 50
DEFAULT_DIR = Path("recordings")
DEFAULT_NAME = "recording"
DEFAULT_RATE_HZ = 60.0


def format_value(v):
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def timestamped_path(name):
    DEFAULT_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    return DEFAULT_DIR / f"{name}-{stamp}{EXTENSION}"


def main():
    latest = {}
    state = {
        "recorder": None,
        "min_interval": 1.0 / DEFAULT_RATE_HZ,
        "last_write": 0.0,
    }
    lock = threading.Lock()

    def reader():
        for tele_ms, raw in listen_raw():
            packet = parse_packet(raw)
            with lock:
                latest.update(packet)
                rec = state["recorder"]
                if rec is not None:
                    now = time.monotonic()
                    if state["min_interval"] <= 0 or now - state["last_write"] >= state["min_interval"]:
                        state["last_write"] = now
                        rec.write(tele_ms, raw)

    threading.Thread(target=reader, daemon=True).start()

    root = tk.Tk()
    root.title("FH6 Telemetry")

    paned = ttk.PanedWindow(root, orient="horizontal")
    paned.pack(fill="both", expand=True)

    # Left panel: recording controls
    left = ttk.Frame(paned, padding=8)
    paned.add(left, weight=0)

    ttk.Label(left, text="Recording", font=("TkDefaultFont", 11, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
    )

    ttk.Label(left, text="Name prefix").grid(row=1, column=0, sticky="w", padx=(0, 4))
    name_var = tk.StringVar(value=DEFAULT_NAME)
    name_entry = ttk.Entry(left, textvariable=name_var, width=20)
    name_entry.grid(row=1, column=1, sticky="ew", pady=2)

    ttk.Label(left, text="Rate (Hz)").grid(row=2, column=0, sticky="w", padx=(0, 4))
    rate_var = tk.StringVar(value=str(DEFAULT_RATE_HZ))
    rate_entry = ttk.Entry(left, textvariable=rate_var, width=20)
    rate_entry.grid(row=2, column=1, sticky="ew", pady=2)

    button_var = tk.StringVar(value="Start recording")
    status_var = tk.StringVar(value="Idle")
    path_var = tk.StringVar(value="")

    def set_inputs_enabled(enabled):
        state_str = "normal" if enabled else "disabled"
        name_entry.configure(state=state_str)
        rate_entry.configure(state=state_str)

    def toggle_recording():
        with lock:
            currently_recording = state["recorder"] is not None

        if currently_recording:
            with lock:
                rec = state["recorder"]
                state["recorder"] = None
            rec.__exit__(None, None, None)
            status_var.set(f"Saved {rec.count} packets")
            button_var.set("Start recording")
            set_inputs_enabled(True)
            return

        try:
            rate = float(rate_var.get())
        except ValueError:
            status_var.set("Invalid rate")
            return
        name = name_var.get().strip() or DEFAULT_NAME
        path = timestamped_path(name)
        rec = Recorder(path)
        rec.__enter__()
        with lock:
            state["recorder"] = rec
            state["min_interval"] = 1.0 / rate if rate > 0 else 0.0
            state["last_write"] = 0.0
        path_var.set(str(path))
        status_var.set("Recording…")
        button_var.set("Stop recording")
        set_inputs_enabled(False)

    record_btn = ttk.Button(left, textvariable=button_var, command=toggle_recording)
    record_btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 4))

    ttk.Label(left, textvariable=status_var).grid(
        row=4, column=0, columnspan=2, sticky="w", pady=(8, 0)
    )
    count_var = tk.StringVar(value="")
    ttk.Label(left, textvariable=count_var).grid(
        row=5, column=0, columnspan=2, sticky="w"
    )
    ttk.Label(left, textvariable=path_var, wraplength=200, foreground="#666").grid(
        row=6, column=0, columnspan=2, sticky="w", pady=(4, 0)
    )

    left.columnconfigure(1, weight=1)

    # Right panel: telemetry display
    right = ttk.Frame(paned, padding=8)
    paned.add(right, weight=1)

    value_vars = {}
    per_col = (len(TELEMETRY_FIELDS) + COLUMNS - 1) // COLUMNS
    for i, name in enumerate(TELEMETRY_FIELDS):
        col = i // per_col
        row = i % per_col
        ttk.Label(right, text=name, anchor="w").grid(
            row=row, column=col * 2, sticky="w", padx=(8, 4)
        )
        var = tk.StringVar(value="-")
        ttk.Label(right, textvariable=var, anchor="e", width=14).grid(
            row=row, column=col * 2 + 1, sticky="e", padx=(0, 16)
        )
        value_vars[name] = var

    def refresh():
        with lock:
            snapshot = dict(latest)
            rec = state["recorder"]
            count = rec.count if rec is not None else None
        for name, var in value_vars.items():
            if name in snapshot:
                var.set(format_value(snapshot[name]))
        if count is not None:
            count_var.set(f"Packets: {count}")
        root.after(REFRESH_MS, refresh)

    def on_close():
        with lock:
            rec = state["recorder"]
            state["recorder"] = None
        if rec is not None:
            rec.__exit__(None, None, None)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.after(REFRESH_MS, refresh)
    root.mainloop()


if __name__ == "__main__":
    main()
