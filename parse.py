import argparse
from pathlib import Path

from lib.recording import EXPORTERS, count_packets


def _infer_format(path):
    ext = path.suffix.lower().lstrip(".")
    if ext == "json":
        ext = "jsonl"
    return ext if ext in EXPORTERS else None


def cmd_info(args):
    n = count_packets(args.input)
    print(f"{args.input}: {n} packets")


def cmd_export(args):
    fmt = args.format or _infer_format(args.output)
    if fmt not in EXPORTERS:
        raise SystemExit(
            f"Unknown format. Supported: {', '.join(EXPORTERS)}. "
            "Use -f or give the output a matching extension."
        )
    EXPORTERS[fmt](args.input, args.output)
    print(f"Exported {args.input} -> {args.output} ({fmt})")


def main():
    p = argparse.ArgumentParser(description="Inspect and convert FH6 recordings.")
    sub = p.add_subparsers(dest="cmd", required=True)

    info = sub.add_parser("info", help="Show recording info")
    info.add_argument("input", type=Path)
    info.set_defaults(func=cmd_info)

    exp = sub.add_parser("export", help="Convert a recording to JSONL or CSV")
    exp.add_argument("input", type=Path)
    exp.add_argument("output", type=Path)
    exp.add_argument(
        "-f", "--format",
        choices=sorted(EXPORTERS),
        help="Output format (defaults to inferring from the output extension).",
    )
    exp.set_defaults(func=cmd_export)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
