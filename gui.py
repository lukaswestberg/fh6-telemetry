import threading
import tkinter as tk
from tkinter import ttk

from lib.fh6 import TELEMETRY_FIELDS, listen


COLUMNS = 2
REFRESH_MS = 50


def format_value(v):
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def main():
    latest = {}
    lock = threading.Lock()

    def reader():
        for packet in listen():
            with lock:
                latest.update(packet)

    threading.Thread(target=reader, daemon=True).start()

    root = tk.Tk()
    root.title("FH6 Telemetry")

    frame = ttk.Frame(root, padding=8)
    frame.pack(fill="both", expand=True)

    value_vars = {}
    per_col = (len(TELEMETRY_FIELDS) + COLUMNS - 1) // COLUMNS
    for i, name in enumerate(TELEMETRY_FIELDS):
        col = i // per_col
        row = i % per_col
        ttk.Label(frame, text=name, anchor="w").grid(
            row=row, column=col * 2, sticky="w", padx=(8, 4)
        )
        var = tk.StringVar(value="-")
        ttk.Label(frame, textvariable=var, anchor="e", width=14).grid(
            row=row, column=col * 2 + 1, sticky="e", padx=(0, 16)
        )
        value_vars[name] = var

    def refresh():
        with lock:
            snapshot = dict(latest)
        for name, var in value_vars.items():
            if name in snapshot:
                var.set(format_value(snapshot[name]))
        root.after(REFRESH_MS, refresh)

    root.after(REFRESH_MS, refresh)
    root.mainloop()


if __name__ == "__main__":
    main()
