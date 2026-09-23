#!/usr/bin/env python3
"""
tail_predicted.py - Print the last N rows of potions-predicted-*.csv.zst files.

Usage:
    python tail_predicted.py [FILE_OR_GLOB ...] [-n N]

Examples:
    python tail_predicted.py                                        # all *.csv.zst in cwd, last 10 rows
    python tail_predicted.py potions-predicted-vanilla.default.settings.csv.zst -n 5
    python tail_predicted.py potions-predicted-*.csv.zst -n 20
    python tail_predicted.py potions-predicted-requiem*.csv.zst potions-predicted-vanilla*.csv.zst
"""

import argparse
import csv
import glob
import io
import sys
from pathlib import Path


def _zst_rows(path: Path) -> list[list[str]]:
    """Return all rows (including header) from a .csv.zst file."""
    try:
        import zstandard  # type: ignore
    except ImportError:
        sys.exit("zstandard package is required: pip install zstandard")

    with open(path, "rb") as fh:
        dctx = zstandard.ZstdDecompressor()
        reader = io.TextIOWrapper(dctx.stream_reader(fh), encoding="utf-8", newline="")
        rows = list(csv.reader(reader))
    return rows


def tail_file(path: Path, n: int, *, show_header: bool = True) -> None:
    """Print the last *n* data rows of *path*, optionally preceded by the header."""
    rows = _zst_rows(path)
    if not rows:
        print(f"  (empty)")
        return

    header = rows[0]
    data = rows[1:]  # everything after the header row

    tail = data[-n:] if n > 0 else data

    if show_header:
        print(",".join(header))

    for row in tail:
        print(",".join(row))


def resolve_paths(patterns: list[str]) -> list[Path]:
    """Expand glob patterns and return sorted unique Paths."""
    paths: list[Path] = []
    for pattern in patterns:
        matched = glob.glob(pattern, recursive=False)
        if matched:
            paths.extend(Path(m) for m in matched)
        else:
            # Treat as a literal path even if no glob match
            p = Path(pattern)
            if p.exists():
                paths.append(p)
            else:
                print(f"Warning: no file matched: {pattern}", file=sys.stderr)
    # Stable unique ordering
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print the last N rows of potions-predicted-*.csv.zst files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.strip(),
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files or glob patterns to read (default: all potions-predicted-*.csv.zst in cwd).",
    )
    parser.add_argument(
        "-n",
        "--rows",
        type=int,
        default=10,
        metavar="N",
        help="Number of tail rows to print per file (default: 10).",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Suppress the CSV header line.",
    )
    args = parser.parse_args()

    patterns = args.files if args.files else ["potions-predicted-*.csv.zst"]
    paths = resolve_paths(patterns)

    if not paths:
        sys.exit("No matching .csv.zst files found.")

    for i, path in enumerate(paths):
        if i > 0:
            print()  # blank line between files
        print(f"==> {path} (last {args.rows} rows) <==")
        try:
            tail_file(path, args.rows, show_header=not args.no_header)
        except Exception as exc:
            print(f"  Error reading {path}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
