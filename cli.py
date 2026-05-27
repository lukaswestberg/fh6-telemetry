import argparse
import datetime as dt
import time
from pathlib import Path

from lib.calculations import summarize
from lib.fh6 import listen_raw
from lib.recording import EXTENSION, Recorder, read_packets


DEFAULT_DIR = Path("recordings")
DEFAULT_RATE_HZ = 60.0
DEFAULT_NAME = "recording"


def parse_args():
    p = argparse.ArgumentParser(
        description="Record FH6 telemetry packets to a binary recording file."
    )
    p.add_argument(
        "-o", "--output",
        type=Path,
        help=f"Output file path. Overrides --name. Defaults to recordings/<name>-<timestamp>{EXTENSION}",
    )
    p.add_argument(
        "-n", "--name",
        default=DEFAULT_NAME,
        help="Name prefix for the recording file (default: %(default)s).",
    )
    p.add_argument(
        "-r", "--rate",
        type=float,
        default=DEFAULT_RATE_HZ,
        help="Max packets recorded per second. Use 0 for unlimited (default: %(default)s).",
    )
    return p.parse_args()


def default_output_path(name):
    DEFAULT_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    return DEFAULT_DIR / f"{name}-{stamp}{EXTENSION}"


def main():
    args = parse_args()
    path = args.output or default_output_path(args.name)

    min_interval = 1.0 / args.rate if args.rate > 0 else 0.0
    last_write = 0.0

    print(f"Recording to {path}")
    print(f"Rate cap: {args.rate} Hz" if args.rate > 0 else "Rate cap: unlimited")
    print("Press Ctrl+C to stop.\n")

    rec = Recorder(path)
    try:
        with rec:
            for tele_ms, raw in listen_raw():
                now = time.monotonic()
                if now - last_write < min_interval:
                    continue
                last_write = now
                rec.write(tele_ms, raw)
                print(f"\rPackets recorded: {rec.count}", end="", flush=True)
    except KeyboardInterrupt:
        pass
    print(f"\nSaved {rec.count} packets to {path}")

    if rec.count > 0:
        stats = summarize(read_packets(path))
        if stats["peak_power_rpm"] is not None:
            print(f"Peak power: {stats['peak_power_hp']:.0f} HP @ {stats['peak_power_rpm']:.0f} RPM")
        if stats["redline_rpm"] is not None:
            print(f"Redline:    {stats['redline_rpm']:.0f} RPM")


if __name__ == "__main__":
    main()
