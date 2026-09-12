"""Clear the configured MO2 saves directory and launch the SKSE shortcut."""

from __future__ import annotations

import subprocess
from pathlib import Path


import config


def remove_files(directory: Path) -> int:
	"""Remove files directly inside directory and return the number removed."""
	if directory.is_symlink() or not directory.is_dir():
		raise NotADirectoryError(f"Configured saves directory is not a directory: {directory}")

	removed = 0
	for entry in directory.iterdir():
		if entry.is_file() or entry.is_symlink():
			entry.unlink()
			removed += 1
	return removed


def launch_mo2(executable: Path, shortcut: str) -> None:
	"""Launch Mod Organizer 2 with the configured shortcut."""
	if not executable.is_file():
		raise FileNotFoundError(f"Configured Mod Organizer executable was not found: {executable}")

	subprocess.Popen([str(executable), shortcut], cwd=executable.parent)


def main() -> None:
	removed = remove_files(config.MO2_SAVES_DIR)
	print(f"Removed {removed} file(s) from {config.MO2_SAVES_DIR}")

	launch_mo2(config.MO2_EXECUTABLE, config.MO2_SKSE_SHORTCUT)
	print(f"Launched {config.MO2_EXECUTABLE} with {config.MO2_SKSE_SHORTCUT}")


if __name__ == "__main__":
	main()
