#!/usr/bin/env python3
"""Rename/store synced default potion prediction files to .default.settings.csv.zst."""

from pathlib import Path
import shutil

SCRIPT_ROOT = Path(__file__).resolve().parent

FILES = [
    ("potions-predicted-vanilla", "potions-predicted-vanilla.default.settings"),
    ("potions-predicted-ap", "potions-predicted-ap.default.settings"),
    ("potions-predicted-caco-ap", "potions-predicted-caco-ap.default.settings"),
    ("potions-predicted-caco", "potions-predicted-caco.default.settings"),
]

def main() -> None:
    copied = 0
    for src_base, dst_base in FILES:
        for ext in (".csv.zst", ".csv"):
            src = SCRIPT_ROOT / f"{src_base}{ext}"
            dst = SCRIPT_ROOT / f"{dst_base}{ext}"
            if src.is_file():
                shutil.copyfile(src, dst)
                print(f"Copied {src.name} -> {dst.name}")
                copied += 1
    if copied == 0:
        print("Warning: No predicted CSV files were found to save.")

if __name__ == "__main__":
    main()
