import datetime as dt
import json
from pathlib import Path

from lib.fh6 import listen


RECORDINGS_DIR = Path("recordings")


def main():
    RECORDINGS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    path = RECORDINGS_DIR / f"recording-{stamp}.jsonl"

    print(f"Recording to {path}")
    print("Press Ctrl+C to stop.\n")

    count = 0
    try:
        with path.open("w") as f:
            for packet in listen():
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
