#!/usr/bin/env python3
"""Copy the current MO2 potion predictions into the matching fixture."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Iterable

from config import MO2_PROFILE


SCRIPT_ROOT = Path(__file__).resolve().parent
SOURCE_CSV_ZST = SCRIPT_ROOT / "links" / "alchemist.potion-predictions.csv.zst"
SOURCE_CSV_PLAIN = SCRIPT_ROOT / "links" / "alchemist.potion-predictions.csv"
SOURCE_CSV = SOURCE_CSV_ZST if SOURCE_CSV_ZST.is_file() else (SOURCE_CSV_PLAIN if SOURCE_CSV_PLAIN.is_file() else SOURCE_CSV_ZST)

DESTINATION_BY_STATE = {
	(False, False): SCRIPT_ROOT / "potions-predicted-vanilla.csv.zst",
	(True, False): SCRIPT_ROOT / "potions-predicted-caco.csv.zst",
	(False, True): SCRIPT_ROOT / "potions-predicted-ap.csv.zst",
	(True, True): SCRIPT_ROOT / "potions-predicted-caco-ap.csv.zst",
}
CACO_NAMES = frozenset({"caco", "completealchemycookingoverhaul"})
ALCHEMY_PLUS_NAMES = frozenset({"alchemyplus"})


class ProfileResolutionError(RuntimeError):
	"""Raised when the configured MO2 path does not identify one profile."""


def normalize_mod_name(name: str) -> str:
	"""Normalize an MO2 mod name for exact, punctuation-insensitive matching."""
	return "".join(character for character in name.casefold() if character.isalnum())


def resolve_modlist(mo2_path: Path) -> Path:
	"""Resolve a direct profile path or an MO2 instance containing one profile."""
	direct_modlist = mo2_path / "modlist.txt"
	if direct_modlist.is_file():
		return direct_modlist

	profiles_path = mo2_path / "profiles"
	if not profiles_path.is_dir():
		raise ProfileResolutionError(
			f"Could not find {direct_modlist} or a profiles directory under {mo2_path}"
		)

	profile_modlists = sorted(
		path
		for path in profiles_path.glob("*/modlist.txt")
		if path.is_file()
	)
	if len(profile_modlists) == 1:
		return profile_modlists[0]
	if not profile_modlists:
		raise ProfileResolutionError(f"No MO2 profile modlist.txt found under {profiles_path}")

	profiles = ", ".join(str(path.parent.name) for path in profile_modlists)
	raise ProfileResolutionError(
		f"Multiple MO2 profiles found under {profiles_path}; refusing to guess: {profiles}"
	)


def enabled_mod_names(modlist_path: Path) -> tuple[str, ...]:
	"""Return names from enabled (+-prefixed) entries in an MO2 modlist."""
	enabled_names: list[str] = []
	for line in modlist_path.read_text(encoding="utf-8-sig").splitlines():
		entry = line.strip()
		if entry.startswith("+") and entry[1:].strip():
			enabled_names.append(entry[1:].strip())
	return tuple(enabled_names)


def detect_integrations(mod_names: Iterable[str]) -> tuple[bool, bool]:
	"""Return (caco_enabled, alchemy_plus_enabled) for enabled mod names."""
	normalized_names = {normalize_mod_name(name) for name in mod_names}
	return (
		bool(normalized_names & CACO_NAMES),
		bool(normalized_names & ALCHEMY_PLUS_NAMES),
	)


def destination_for(caco_enabled: bool, alchemy_plus_enabled: bool) -> Path:
	"""Return the fixture path for the detected integration combination."""
	return DESTINATION_BY_STATE[(caco_enabled, alchemy_plus_enabled)]


def synchronize(
	mo2_path: Path = MO2_PROFILE,
	source_csv: Path = SOURCE_CSV,
) -> tuple[Path, Path, bool, bool]:
	"""Copy the generated prediction export into the matching fixture."""
	modlist_path = resolve_modlist(mo2_path)
	caco_enabled, alchemy_plus_enabled = detect_integrations(
		enabled_mod_names(modlist_path)
	)
	destination_csv = destination_for(caco_enabled, alchemy_plus_enabled)

	if not source_csv.is_file():
		raise FileNotFoundError(f"Prediction source does not exist: {source_csv}")

	shutil.copyfile(source_csv, destination_csv)
	return modlist_path, destination_csv, caco_enabled, alchemy_plus_enabled


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description=(
			"Detect enabled CACO and Alchemy Plus mods in MO2 and copy "
			"the generated potion predictions into the matching fixture."
		)
	)
	parser.add_argument(
		"--mo2-path",
		type=Path,
		default=MO2_PROFILE,
		help=(
			"MO2 profile directory or instance directory; defaults to "
			"MO2_PROFILE from config.py"
		),
	)
	return parser


def main() -> int:
	args = build_parser().parse_args()
	try:
		modlist_path, destination_csv, caco_enabled, alchemy_plus_enabled = synchronize(
			args.mo2_path
		)
	except (OSError, ProfileResolutionError) as error:
		print(f"Error: {error}", file=sys.stderr)
		return 1

	print(f"MO2 modlist: {modlist_path}")
	print(f"CACO enabled: {'yes' if caco_enabled else 'no'}")
	print(f"Alchemy Plus enabled: {'yes' if alchemy_plus_enabled else 'no'}")
	print(f"Copied {SOURCE_CSV} to {destination_csv}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
