import argparse
from pathlib import Path

from lib.graphs import available, get
from lib.recording import read_packets


DEFAULT_OUTPUT_DIR = Path("output")


def parse_args():
    p = argparse.ArgumentParser(
        description="Plot graphs from FH6 recordings.",
    )
    p.add_argument("input", type=Path, nargs="?", help="Recording file (.fh6r)")
    p.add_argument(
        "graph",
        nargs="?",
        default="dyno",
        help="Graph name (default: dyno). Use --list to see options.",
    )
    p.add_argument(
        "-o", "--output",
        type=Path,
        help=f"Save figure to file instead of showing. Defaults to {DEFAULT_OUTPUT_DIR}/<input-stem>-<graph>.png with --save.",
    )
    p.add_argument(
        "--save",
        action="store_true",
        help=f"Save to default path under {DEFAULT_OUTPUT_DIR}/ (no display).",
    )
    p.add_argument(
        "--all",
        action="store_true",
        help="Include samples where IsRaceOn is false.",
    )
    p.add_argument(
        "--fields",
        help="Comma-separated field list (for graphs that accept it, e.g. timeseries).",
    )
    p.add_argument(
        "--bins",
        type=int,
        default=80,
        help="RPM bin count for the dyno graph (default: 80).",
    )
    p.add_argument(
        "--smooth",
        type=int,
        default=0,
        help="Centered moving-average window size (0 = off, default).",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="List available graphs and exit.",
    )
    return p.parse_args()


def main():
    args = parse_args()

    if args.list:
        for name, desc in available():
            print(f"  {name:<12} {desc}")
        return

    if args.input is None:
        raise SystemExit("error: input recording is required (use --list to see graphs)")

    fn = get(args.graph)

    kwargs = {"in_race_only": not args.all, "smooth": args.smooth}
    if args.graph == "dyno":
        kwargs["bins"] = args.bins
    if args.graph == "timeseries" and args.fields:
        kwargs["fields"] = tuple(f.strip() for f in args.fields.split(",") if f.strip())

    fig = fn(read_packets(args.input), **kwargs)
    fig.suptitle(f"{args.input.name} — {args.graph}", fontsize=10, y=0.995)

    if args.save and args.output is None:
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        args.output = DEFAULT_OUTPUT_DIR / f"{args.input.stem}-{args.graph}.png"

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output, dpi=120)
        print(f"Saved {args.output}")
    else:
        import matplotlib.pyplot as plt
        plt.show()


if __name__ == "__main__":
    main()
