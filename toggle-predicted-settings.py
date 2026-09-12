#!/usr/bin/env python3
"""Toggle active predicted potion CSV files between default and changed settings fixtures.

This script overwrites the un-suffixed active files (`potions-predicted-*.csv.zst`
and `.csv`) with either the `.default.settings` or `.changed.settings` variants,
preserving the original archived fixtures intact.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent

MODES = [
    "potions-predicted-vanilla",
    "potions-predicted-ap",
    "potions-predicted-caco-ap",
    "potions-predicted-caco",
]

EXTENSIONS = [".csv.zst", ".csv"]


def detect_current_state() -> str:
    """Detect whether current active files match default settings, changed settings, or unknown.

    Returns:
        'default' if active files match default fixtures,
        'changed' if active files match changed fixtures,
        'unknown' otherwise.
    """
    matches_default = 0
    matches_changed = 0
    total_checked = 0

    for mode in MODES:
        for ext in EXTENSIONS:
            active = SCRIPT_ROOT / f"{mode}{ext}"
            default_fixture = SCRIPT_ROOT / f"{mode}.default.settings{ext}"
            changed_fixture = SCRIPT_ROOT / f"{mode}.changed.settings{ext}"

            if not active.is_file():
                continue

            total_checked += 1
            if default_fixture.is_file() and filecmp.cmp(active, default_fixture, shallow=False):
                matches_default += 1
            elif changed_fixture.is_file() and filecmp.cmp(active, changed_fixture, shallow=False):
                matches_changed += 1

    if total_checked > 0 and matches_default == total_checked:
        return "default"
    elif total_checked > 0 and matches_changed == total_checked:
        return "changed"
    return "unknown"


def switch_predicted_settings(target: str) -> int:
    """Copy target settings fixtures to active un-suffixed prediction files.

    Args:
        target: 'default' or 'changed'

    Returns:
        Number of files copied.
    """
    copied_count = 0
    target_suffix = "default.settings" if target == "default" else "changed.settings"

    for mode in MODES:
        for ext in EXTENSIONS:
            src = SCRIPT_ROOT / f"{mode}.{target_suffix}{ext}"
            dst = SCRIPT_ROOT / f"{mode}{ext}"

            if src.is_file():
                shutil.copyfile(src, dst)
                print(f"Copied {src.name} -> {dst.name}")
                copied_count += 1

    return copied_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Toggle active predicted potion CSV files between default and changed settings fixtures."
    )
    parser.add_argument(
        "target",
        nargs="?",
        choices=[
            "default",
            "changed",
            "default-settings",
            "changed-settings",
            "default_settings",
            "changed_settings",
            "toggle",
        ],
        default="toggle",
        help="Target setting set to switch to ('default', 'changed', or 'toggle' to alternate automatically).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_target = args.target.lower()

    current_state = detect_current_state()

    if raw_target in ("default", "default-settings", "default_settings"):
        target = "default"
    elif raw_target in ("changed", "changed-settings", "changed_settings"):
        target = "changed"
    else:
        # Automatic toggle
        if current_state == "default":
            target = "changed"
        else:
            target = "default"

    print(f"Current prediction state: {current_state}")
    print(f"Switching active predicted files to '{target}' settings...")

    copied = switch_predicted_settings(target)
    if copied == 0:
        print("Warning: No predicted fixture files were found to copy.", file=sys.stderr)
        return 1

    new_state = detect_current_state()
    print(f"Successfully updated {copied} predicted file(s). Active state: {new_state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
