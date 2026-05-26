import argparse
import datetime as dt
import json
import time
from pathlib import Path

from lib.fh6 import listen


DEFAULT_DIR = Path("recordings")
DEFAULT_RATE_HZ = 60.0


def parse_args():
    p = argparse.ArgumentParser(
        description="Record FH6 telemetry packets to a JSONL file."
    )
    p.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file path. Defaults to recordings/recording-<timestamp>.jsonl",
    )
    p.add_argument(
        "-r", "--rate",
        type=float,
        default=DEFAULT_RATE_HZ,
        help="Max packets recorded per second. Use 0 for unlimited (default: %(default)s).",
    )
    return p.parse_args()


def default_output_path():
    DEFAULT_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    return DEFAULT_DIR / f"recording-{stamp}.jsonl"


def main():
    args = parse_args()
    path = args.output or default_output_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    min_interval = 1.0 / args.rate if args.rate > 0 else 0.0
    last_write = 0.0

    print(f"Recording to {path}")
    print(f"Rate cap: {args.rate} Hz" if args.rate > 0 else "Rate cap: unlimited")
    print("Press Ctrl+C to stop.\n")

    count = 0
    try:
        with path.open("w") as f:
            for packet in listen():
                now = time.monotonic()
                if now - last_write < min_interval:
                    continue
                last_write = now
                f.write(json.dumps(packet) + "\n")
                f.flush()
                count += 1
                print(f"\rPackets recorded: {count}", end="", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        print(f"\nSaved {count} packets to {path}")


if __name__ == "__main__":
    main()
