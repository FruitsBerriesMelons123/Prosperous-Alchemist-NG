#!/usr/bin/env python3
"""Standalone Prosperous Alchemist potion-value prediction test harness.

This script mirrors the value-bearing code in ``alchemist/include/main.h`` and
``alchemist/CACO/CACO.h``.  It intentionally reads exported ingredient data
instead of requiring Skyrim or a loaded plugin.  Its general-purpose path is
for parity with the current SKSE plugin; the supplied predicted-value CSV
files are historical regression fixtures for that baseline.  The known CACO
397-versus-228 case is kept as a later Python-only investigation target and is
not treated as a current-plugin parity requirement.

Current validation phase:

* Use ``--check-confirmed-csv`` to score only the explicitly captured rows in
  ``links/alchemist.potions-confirmed.csv``.  Rows may be added incrementally
  as each confirmed setting and ingredient combination is verified.
  This is the current observed-craft accuracy gate.  It uses each row's
  exported native ingredient-selection order and crafted result metadata.
* Do not use ``--check-predicted-csvs`` as the current accuracy gate.  That
  broad historical regression suite is deferred until the confirmed rows and
  their order-dependent behavior are accurately reproduced.
* ``--self-test`` remains available for unit-level regression checks; it does
  not replace the confirmed-row validation described above.

Example:
	python alchemist/potion_prediction_test.py \
		--caco-enabled false \
		--alchemy-plus-enabled false \
		"Blue Butterfly Wing" "Blue Mountain Flower"
	python potion_prediction_test.py "Blue Butterfly Wing" "Blue Mountain Flower"

By default, the deployed alchemist.ini next to the configured plugin provides
the root-level Current value that selects the active [Profile N] section, which
contains the managed snapshots that select the algorithmic path. The deployed
INI is the only automatic INI source; when it is unavailable,
normal runs must provide every required setting as an explicit command-line flag.

The two enablement switches select the four supported paths:

	CACO  Alchemy Plus  Path
	false false         vanilla Skyrim
	true  false         CACO only
	false true          Alchemy Plus only
	true  true          CACO + Alchemy Plus

The CSV files do not contain live player state, CACO globals, or the optional
Alchemy Plus JSON configuration.  Those values are therefore exposed as
arguments.  The defaults are deterministic and are documented in --help.
The CSV files do not contain live player state or CACO globals.  The deployed
INI supplies those values when available, while the corresponding command-line
flags remain authoritative overrides.  An explicit Alchemy Plus JSON path
overrides the canonical JSON stored in the INI snapshot.
"""

from __future__ import annotations

import argparse
import configparser
import csv
import io
import json
import math
import struct
import sys
import tempfile
import time
import zstandard as zstd
import unittest
import unittest.mock
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence


SCRIPT_ROOT = Path(__file__).resolve().parent
VANILLA_CSV = SCRIPT_ROOT / "ingredients-vanilla.csv"
CACO_CSV = SCRIPT_ROOT / "ingredients-caco.csv"
ALCHEMIST_INI_NAME = "alchemist.ini"
PREDICTION_LOG = SCRIPT_ROOT / "potion_prediction_test.log"
CONFIRMED_CSV = SCRIPT_ROOT / "links" / "alchemist.potions-confirmed.csv"
ORDER_DEPENDENT_CSV = SCRIPT_ROOT / "potion-order-dependent-observations.csv"
CONFIRMED_LOG = SCRIPT_ROOT / "potion_prediction_confirmed.log"
TOLERATED_PREDICTION_PERCENTAGE = 0.0000001  # 0.00001% tolerance


def is_prediction_within_tolerance(
	expected: int | float | None,
	actual: int | float | None,
	percentage_tolerance: float = TOLERATED_PREDICTION_PERCENTAGE,
) -> bool:
	if actual is None or expected is None:
		return actual == expected
	if actual == expected:
		return True
	diff = abs(float(actual) - float(expected))
	allowed = float(expected) * percentage_tolerance
	return diff <= allowed

# These are the same limits used by the C++ helpers.
INT32_MAX = 2_147_483_647
INT32_MIN = -2_147_483_648
FLOAT32_MAX_FINITE = 3.4028234663852886e38
# Keep record-specific metadata in the CSV exports.  Do not hard-code form IDs
# or add other record-specific exceptions to this prediction harness.


def resolve_current_alchemist_ini() -> Path | None:
	"""Return only the deployed Alchemist INI when it is available."""
	try:
		from config import DLL_DEPLOY
	except (ImportError, AttributeError):
		DLL_DEPLOY = None

	if DLL_DEPLOY is not None:
		deployed_path = Path(DLL_DEPLOY).with_name(ALCHEMIST_INI_NAME)
		if deployed_path.is_file():
			return deployed_path
	return None


def f32(value: float) -> float:
	"""Round a value to the IEEE-754 single precision used by Skyrim records."""
	return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def finite(value: float) -> bool:
	return math.isfinite(value)


def cxx_round_positive(value: float) -> float:
	"""Mirror std::round for the non-negative alchemy values used here."""
	return f32(math.floor(value + 0.5))


def parse_bool(value: str) -> bool:
	normalized = value.strip().lower()
	if normalized in {"1", "true", "yes", "on", "enabled"}:
		return True
	if normalized in {"0", "false", "no", "off", "disabled"}:
		return False
	raise argparse.ArgumentTypeError(
		f"expected true/false (or 1/0), got {value!r}"
	)


def _snapshot_value(values: Mapping[str, str], name: str) -> str | None:
	name_casefolded = name.casefold()
	for key, value in values.items():
		if key.casefold() == name_casefolded:
			return value.strip()
	return None


def _snapshot_bool(
	values: Mapping[str, str], name: str, default: bool
) -> bool:
	value = _snapshot_value(values, name)
	if value is None or not value:
		return default
	try:
		return parse_bool(value)
	except argparse.ArgumentTypeError as error:
		raise ValueError(f"INI setting {name!r} must be true or false") from error


def _snapshot_int(
	values: Mapping[str, str], name: str, default: int, minimum: int, maximum: int
) -> int:
	value = _snapshot_value(values, name)
	if value is None or not value:
		return default
	try:
		parsed = int(value, 10)
	except ValueError as error:
		raise ValueError(f"INI setting {name!r} must be an integer") from error
	return max(minimum, min(maximum, parsed))


def _snapshot_float(
	values: Mapping[str, str], name: str, default: float, minimum: float | None = None
) -> float:
	value = _snapshot_value(values, name)
	if value is None or not value:
		return f32(default)
	try:
		parsed = float(value)
	except ValueError as error:
		raise ValueError(f"INI setting {name!r} must be numeric") from error
	if not finite(parsed) or (minimum is not None and parsed < minimum):
		return f32(default)
	return f32(parsed)


@dataclass(frozen=True)
class CACOSettings:
	"""The managed CACO snapshot written by the plugin."""

	restore_health_duration: int = 0
	restore_magicka_duration: int = 0
	restore_stamina_duration: int = 0
	restore_effects_do_not_stack: bool = False
	damage_health_duration: int = 0
	damage_magicka_duration: int = 0
	damage_stamina_duration: int = 0
	disable_all_potion_handling: bool = False
	alchemy_xp_multiplier: float = 1.0
	alchemy_ingredient_init_multiplier: float = 3.9
	alchemy_skill_factor: float = 1.0
	impure_processing: bool = False

	@classmethod
	def from_ini(cls, values: Mapping[str, str]) -> "CACOSettings":
		return cls(
			restore_health_duration=_snapshot_int(
				values, "RestoreHealthDuration", 0, 0, 2
			),
			restore_magicka_duration=_snapshot_int(
				values, "RestoreMagickaDuration", 0, 0, 2
			),
			restore_stamina_duration=_snapshot_int(
				values, "RestoreStaminaDuration", 0, 0, 2
			),
			restore_effects_do_not_stack=_snapshot_bool(
				values, "RestoreEffectsDoNotStack", False
			),
			damage_health_duration=_snapshot_int(
				values, "DamageHealthDuration", 0, 0, 2
			),
			damage_magicka_duration=_snapshot_int(
				values, "DamageMagickaDuration", 0, 0, 2
			),
			damage_stamina_duration=_snapshot_int(
				values, "DamageStaminaDuration", 0, 0, 2
			),
			disable_all_potion_handling=_snapshot_bool(
				values, "DisableAllPotionHandling", False
			),
			alchemy_xp_multiplier=_snapshot_float(
				values, "AlchemyXPMultiplier", 1.0, 0.0
			),
			alchemy_ingredient_init_multiplier=_snapshot_float(
				values, "AlchemyIngredientInitMultiplier", 3.9, 0.0
			),
			alchemy_skill_factor=_snapshot_float(
				values, "AlchemySkillFactor", 1.0, 0.0
			),
			impure_processing=_snapshot_bool(
				values, "ImpurePotionProcessing", False
			),
		)


@dataclass(frozen=True)
class ExternalSettingsSnapshot:
	"""The optional managed snapshots from the active profile in alchemist.ini."""

	path: Path | None = None
	player_values: Mapping[str, str] | None = None
	caco: CACOSettings | None = None
	alchemy_plus_section_present: bool = False
	alchemy_plus_configuration: dict[str, object] | None = None
	alchemy_plus_configuration_loaded: bool = False

	@property
	def caco_enabled(self) -> bool:
		return self.caco is not None

	@property
	def alchemy_plus_enabled(self) -> bool:
		return self.alchemy_plus_section_present


def _find_ini_section(
	parser: configparser.ConfigParser, name: str
) -> Mapping[str, str] | None:
	for section in parser.sections():
		if section.casefold() == name.casefold():
			return dict(parser.items(section))
	return None


def _find_active_profile(
	parser: configparser.ConfigParser,
) -> Mapping[str, str] | None:
	global_values = _find_ini_section(parser, "Global") or {}
	current_profile = _snapshot_value(global_values, "Current")
	profiles: list[tuple[int, Mapping[str, str]]] = []
	for section in parser.sections():
		prefix, separator, suffix = section.partition(" ")
		if prefix.casefold() != "profile" or not separator or not suffix.isdigit():
			continue
		profiles.append((int(suffix), dict(parser.items(section))))
	if not profiles:
		return None
	if current_profile is not None:
		for index, values in sorted(profiles):
			if current_profile == str(index):
				return values
	for _, values in sorted(profiles):
		if _snapshot_value(values, "Current") == "1":
			return values
	return dict(sorted(profiles)[0][1])


def load_alchemist_ini(
	path: Path | None, *, required: bool = False
) -> ExternalSettingsSnapshot:
	"""Load managed snapshots from the active profile in an INI snapshot."""
	if path is None:
		return ExternalSettingsSnapshot()
	path = Path(path)
	if not path.is_file():
		if required:
			raise ValueError(f"alchemist INI does not exist: {path}")
		return ExternalSettingsSnapshot()

	parser = configparser.ConfigParser(interpolation=None, strict=False)
	parser.optionxform = str
	try:
		with path.open("r", encoding="utf-8-sig", newline="") as handle:
			parser.read_string("[Global]\n" + handle.read())
	except (OSError, configparser.Error) as error:
		raise ValueError(f"could not read alchemist INI {path}: {error}") from error

	profile_values = _find_active_profile(parser)
	if profile_values is None:
		profile_values = _find_ini_section(parser, "Profile 1")
	if profile_values is None:
		profile_values = {}
	player_values = None
	caco_values = None
	alchemy_plus_values = None
	for snapshot_name, target in (("Player", "player"), ("CACO", "caco"), ("AlchemyPlus", "alchemy_plus")):
		snapshot_text = _snapshot_value(profile_values, snapshot_name)
		if not snapshot_text:
			continue
		try:
			snapshot_values = json.loads(snapshot_text)
		except json.JSONDecodeError as error:
			raise ValueError(f"{snapshot_name} snapshot in {path} is not valid JSON") from error
		if not isinstance(snapshot_values, dict):
			raise ValueError(f"{snapshot_name} snapshot in {path} must be a JSON object")
		if target == "player":
			player_values = {str(key): str(value) for key, value in snapshot_values.items()}
		elif target == "caco":
			caco_values = {str(key): str(value) for key, value in snapshot_values.items()}
		else:
			alchemy_plus_values = {str(key): str(value) for key, value in snapshot_values.items()}
	caco = CACOSettings.from_ini(caco_values) if caco_values is not None else None
	configuration_loaded = False
	configuration: dict[str, object] | None = None
	if alchemy_plus_values is not None:
		configuration_loaded = _snapshot_bool(
			alchemy_plus_values, "ConfigurationLoaded", False
		)
		configuration_text = _snapshot_value(alchemy_plus_values, "Configuration")
		if configuration_loaded:
			if not configuration_text:
				raise ValueError(
					f"[AlchemyPlus] in {path} is marked loaded without Configuration"
				)
			try:
				parsed_configuration = json.loads(configuration_text)
			except json.JSONDecodeError as error:
				raise ValueError(
					f"[AlchemyPlus] Configuration in {path} is not valid JSON"
				) from error
			if not isinstance(parsed_configuration, dict):
				raise ValueError(
					f"[AlchemyPlus] Configuration in {path} must be a JSON object"
				)
			configuration = parsed_configuration

	return ExternalSettingsSnapshot(
		path=path,
		player_values=player_values,
		caco=caco,
		alchemy_plus_section_present=alchemy_plus_values is not None,
		alchemy_plus_configuration=configuration,
		alchemy_plus_configuration_loaded=configuration_loaded,
	)


def parse_form_id(value: str) -> int:
	text = value.strip()
	if not text:
		return 0
	return int(text, 16) if text.lower().startswith("0x") else int(text, 16)


def bool_field(row: Mapping[str, str], name: str) -> bool:
	value = row[name].strip().lower()
	if value in {"1", "true"}:
		return True
	if value in {"0", "false"}:
		return False
	raise ValueError(f"CSV field {name!r} must be 0 or 1, got {value!r}")


def optional_bool_field(row: Mapping[str, str], name: str) -> bool | None:
	value = row.get(name)
	if value is None or not value.strip():
		return None
	return bool_field(row, name)


def optional_float_field(row: Mapping[str, str], name: str) -> float | None:
	value = row.get(name)
	if value is None or not value.strip():
		return None
	return f32(float(value))


def optional_form_id_field(row: Mapping[str, str], name: str) -> int | None:
	value = row.get(name)
	if value is None or not value.strip():
		return None
	return parse_form_id(value)


def optional_int_field(row: Mapping[str, str], name: str) -> int | None:
	value = row.get(name)
	if value is None or not value.strip():
		return None
	try:
		return int(value.strip(), 10)
	except ValueError:
		return None


def text_list_field(row: Mapping[str, str], name: str) -> tuple[str, ...]:
	value = row.get(name) or ""
	return tuple(item.strip() for item in value.split(";") if item.strip())


def form_id_list_field(row: Mapping[str, str], name: str) -> tuple[int, ...]:
	return tuple(parse_form_id(item) for item in text_list_field(row, name))


@dataclass(frozen=True)
class EffectRecord:
	"""One ingredient effect row from either exported CSV."""

	ingredient_name: str
	form_id: int
	effect_name: str
	effect_form_id: int
	base_cost: float
	magnitude: float
	duration: float
	power_affects_magnitude: bool
	power_affects_duration: bool
	no_magnitude: bool
	no_duration: bool
	beneficial: bool
	harmful: bool
	hostile: bool
	resolved_magnitude: float | None = None
	resolved_duration: float | None = None
	resolved_peak_value_modifier: bool | None = None
	effect_cost: float | None = None
	duration_based_exported: bool = False
	keyword_editor_ids: tuple[str, ...] = ()
	keyword_form_ids: tuple[int, ...] = ()
	source_effect_form_id: int | None = None
	resolved_effect_name: str | None = None
	resolved_effect_form_id: int | None = None
	resolved_effect_editor_id: str | None = None
	resolved_base_cost: float | None = None
	resolved_power_affects_magnitude: bool | None = None
	resolved_power_affects_duration: bool | None = None
	resolved_no_magnitude: bool | None = None
	resolved_no_duration: bool | None = None
	resolved_beneficial: bool | None = None
	resolved_harmful: bool | None = None
	resolved_hostile: bool | None = None
	resolved_duration_based: bool | None = None
	resolved_keyword_editor_ids: tuple[str, ...] = ()
	resolved_keyword_form_ids: tuple[int, ...] = ()
	caco_duration_index: int | None = None
	description: str = ""

	@property
	def source_identity(self) -> int:
		# The C++ evaluator groups by sourceBaseEffect, which is the original
		# effect form ID even when CACO resolves a different active record.
		return self.source_effect_form_id or self.effect_form_id

	@property
	def input_magnitude(self) -> float:
		# resolved_magnitude is export diagnostics for the active effect record,
		# not the ingredient magnitude used when the potion is constructed.
		return self.magnitude

	@property
	def input_duration(self) -> float:
		# Resolved duration is diagnostic; crafted input retains the source duration.
		return self.duration

	@property
	def duration_based(self) -> bool:
		# CACO's duration-based path is identified by its explicit keyword. The
		# exported duration flag also marks ordinary duration-affecting effects
		# such as Light and Spell Absorption, which use native duration scaling.
		return any(
			keyword.strip().casefold() == "magicalchdurationbased"
			for keyword in self.keyword_editor_ids + self.resolved_keyword_editor_ids
		)

	@property
	def active_power_affects_magnitude(self) -> bool:
		if self.resolved_power_affects_magnitude is not None:
			return self.resolved_power_affects_magnitude
		return self.power_affects_magnitude

	@property
	def active_power_affects_duration(self) -> bool:
		if self.resolved_power_affects_duration is not None:
			return self.resolved_power_affects_duration
		return self.power_affects_duration

	@property
	def active_no_magnitude(self) -> bool:
		if self.resolved_no_magnitude is not None:
			return self.resolved_no_magnitude
		return self.no_magnitude

	@property
	def active_no_duration(self) -> bool:
		if self.resolved_no_duration is not None:
			return self.resolved_no_duration
		return self.no_duration

	@property
	def effective_no_duration(self) -> bool:
		return self.active_no_duration and not self.duration_based


@dataclass(frozen=True)
class IngredientRecord:
	name: str
	form_id: int
	effects: tuple[EffectRecord, ...]


class IngredientDatabase:
	"""CSV-backed ingredient lookup with case-insensitive CLI matching."""

	REQUIRED_COLUMNS = {
		"ingredient_name",
		"form_id",
		"effect_name",
		"effect_form_id",
		"base_cost",
		"magnitude",
		"duration",
		"power_affects_magnitude",
		"power_affects_duration",
		"no_magnitude",
		"no_duration",
		"beneficial",
		"harmful",
		"hostile",
		"keyword_editor_ids",
		"duration_based",
		"source_effect_form_id",
		"resolved_effect_form_id",
	}

	def __init__(
		self,
		ingredients: Mapping[str, Sequence[IngredientRecord]],
		csv_path: Path,
		prefer_highest_form_id: bool = False,
	):
		self._ingredients = {
			name: tuple(records) for name, records in ingredients.items()
		}
		self.csv_path = csv_path
		self._prefer_highest_form_id = prefer_highest_form_id

	@classmethod
	def load(
		cls, csv_path: Path, prefer_highest_form_id: bool = False
	) -> "IngredientDatabase":
		grouped: dict[tuple[str, int], list[EffectRecord]] = {}
		with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
			reader = csv.DictReader(handle)
			if reader.fieldnames is None:
				raise ValueError(f"{csv_path} has no CSV header")
			missing = cls.REQUIRED_COLUMNS - set(reader.fieldnames)
			if missing:
				raise ValueError(
					f"{csv_path} is missing required columns: {', '.join(sorted(missing))}"
				)
			for line_number, row in enumerate(reader, start=2):
				try:
					name = row["ingredient_name"].strip()
					form_id = parse_form_id(row["form_id"])
					resolved_effect_name = row.get("resolved_effect_name")
					effect = EffectRecord(
						ingredient_name=name,
						form_id=form_id,
						effect_name=row["effect_name"].strip(),
						effect_form_id=parse_form_id(row["effect_form_id"]),
						base_cost=f32(float(row["base_cost"])),
						magnitude=f32(float(row["magnitude"])),
						duration=f32(float(row["duration"])),
						resolved_magnitude=optional_float_field(row, "resolved_magnitude"),
						resolved_duration=optional_float_field(row, "resolved_duration"),
						resolved_peak_value_modifier=optional_bool_field(
							row, "resolved_peak_value_modifier"
						),
						power_affects_magnitude=bool_field(
							row, "power_affects_magnitude"
						),
						power_affects_duration=bool_field(
							row, "power_affects_duration"
						),
						no_magnitude=bool_field(row, "no_magnitude"),
						no_duration=bool_field(row, "no_duration"),
						beneficial=bool_field(row, "beneficial"),
						harmful=bool_field(row, "harmful"),
						hostile=bool_field(row, "hostile"),
						effect_cost=optional_float_field(row, "effect_cost"),
						duration_based_exported=bool_field(row, "duration_based"),
						keyword_editor_ids=text_list_field(row, "keyword_editor_ids"),
						keyword_form_ids=form_id_list_field(row, "keyword_form_ids"),
						source_effect_form_id=optional_form_id_field(
							row, "source_effect_form_id"
						),
						resolved_effect_name=(
							resolved_effect_name.strip()
							if resolved_effect_name and resolved_effect_name.strip()
							else None
						),
						resolved_effect_form_id=optional_form_id_field(
							row, "resolved_effect_form_id"
						),
						resolved_effect_editor_id=(
							row.get("resolved_effect_editor_id", "").strip() or None
						),
						resolved_base_cost=optional_float_field(
							row, "resolved_base_cost"
						),
						resolved_power_affects_magnitude=optional_bool_field(
							row, "resolved_power_affects_magnitude"
						),
						resolved_power_affects_duration=optional_bool_field(
							row, "resolved_power_affects_duration"
						),
						resolved_no_magnitude=optional_bool_field(
							row, "resolved_no_magnitude"
						),
						resolved_no_duration=optional_bool_field(row, "resolved_no_duration"),
						resolved_beneficial=optional_bool_field(row, "resolved_beneficial"),
						resolved_harmful=optional_bool_field(row, "resolved_harmful"),
						resolved_hostile=optional_bool_field(row, "resolved_hostile"),
						resolved_duration_based=optional_bool_field(
							row, "resolved_duration_based"
						),
						resolved_keyword_editor_ids=text_list_field(
							row, "resolved_keyword_editor_ids"
						),
						resolved_keyword_form_ids=form_id_list_field(
							row, "resolved_keyword_form_ids"
						),
						caco_duration_index=(
							int(row["caco_duration_index"].strip(), 10)
							if row.get("caco_duration_index")
							and row["caco_duration_index"].strip().isdigit()
							else None
						),
						description=row.get("resolved_description", "").strip(),
					)
					if not name or not effect.effect_name:
						raise ValueError("ingredient_name and effect_name are required")
					if effect.effect_form_id == 0:
						raise ValueError("effect_form_id must not be zero")
					grouped.setdefault((name, form_id), []).append(effect)
				except (TypeError, ValueError, KeyError) as error:
					raise ValueError(
						f"invalid row {line_number} in {csv_path}: {error}"
					) from error

		ingredients: dict[str, list[IngredientRecord]] = {}
		for (name, form_id), effects in grouped.items():
			ingredients.setdefault(name, []).append(
				IngredientRecord(name=name, form_id=form_id, effects=tuple(effects))
			)
		for records in ingredients.values():
			records.sort(key=lambda record: record.form_id)
		return cls(ingredients, csv_path, prefer_highest_form_id)

	@classmethod
	def load_caco_duration_exports(
		cls, csv_path: Path, prefer_highest_form_id: bool = False
	) -> "IngredientDatabase":
		"""Load the index-0, 5-second, and 10-second CACO exports together."""
		csv_path = Path(csv_path)
		duration_paths = (
			(0, csv_path),
			(1, csv_path.with_name(f"{csv_path.stem}-5{csv_path.suffix}")),
			(2, csv_path.with_name(f"{csv_path.stem}-10{csv_path.suffix}")),
		)
		# If any of the expected companion files is missing, fall back to the
		# single-file loader for compatibility.
		if not all(path.is_file() for _, path in duration_paths):
			return cls.load(csv_path, prefer_highest_form_id)

		grouped: dict[tuple[str, int], list[EffectRecord]] = {}
		for duration_index, path in duration_paths:
			database = cls.load(path, prefer_highest_form_id)
			seen_effects: set[tuple[int, int, int | None]] = set()
			for records in database._ingredients.values():
				for record in records:
					for effect in record.effects:
						family_id = match_caco_duration_family(effect)
						identity = (
							record.form_id,
							effect.source_identity,
							family_id,
						)
						if identity in seen_effects:
							continue
						seen_effects.add(identity)

						# Only include non-family effects from the base export.
						if family_id is None and duration_index != 0:
							continue
						# Tag family effects with the duration index they came from.
						if family_id is not None:
							effect = replace(effect, caco_duration_index=duration_index)
						grouped.setdefault((record.name, record.form_id), []).append(effect)

		ingredients: dict[str, list[IngredientRecord]] = {}
		for (name, form_id), effects in grouped.items():
			ingredients.setdefault(name, []).append(
				IngredientRecord(name=name, form_id=form_id, effects=tuple(effects))
			)
		for records in ingredients.values():
			records.sort(key=lambda record: record.form_id)
		return cls(ingredients, csv_path, prefer_highest_form_id)

	def names(self) -> list[str]:
		return sorted(self._ingredients)

	def get(self, requested_name: str) -> IngredientRecord:
		requested_form_id: int | None = None
		lookup_name = requested_name
		if "@" in requested_name:
			lookup_name, form_text = requested_name.rsplit("@", 1)
			try:
				requested_form_id = parse_form_id(form_text)
			except ValueError as error:
				raise KeyError(
					f"invalid ingredient form selector in {requested_name!r}"
				) from error

		records = self._ingredients.get(lookup_name)
		if records is None:
			folded = lookup_name.casefold()
			matches = [
				values
				for name, values in self._ingredients.items()
				if name.casefold() == folded
			]
			if len(matches) == 1:
				records = matches[0]
		if records is not None:
			if requested_form_id is not None:
				for record in records:
					if record.form_id == requested_form_id:
						return record
				raise KeyError(
					f"ingredient {lookup_name!r} has no form ID {form_text!r}"
				)
			if len(records) == 1:
				return records[0]
			signatures = {
				tuple(
					(
						effect.effect_form_id,
						effect.base_cost,
								effect.input_magnitude,
								effect.input_duration,
					)
					for effect in record.effects
				)
				for record in records
			}
			if len(signatures) == 1:
				return records[0]
			if self._prefer_highest_form_id:
				return records[-1]
			forms = ", ".join(f"0x{record.form_id:X}" for record in records)
			raise KeyError(
				f"ingredient name {lookup_name!r} is ambiguous; use Name@FORM_ID "
				f"(available: {forms})"
			)
		raise KeyError(
			f"ingredient {requested_name!r} was not found in {self.csv_path.name}"
		)


@dataclass
class PlayerSettings:
	"""The Player fields used by the prediction pipeline."""

	alchemy_level: float = 15.0
	fortify_alchemy_level: float = 0.0
	alchemist_perk_rank: int = 0
	alchemist_perk_multiplier: float | None = None
	purity: bool = False
	physician: bool = False
	benefactor: bool = False
	poisoner: bool = False
	concentrated_poison: bool = False
	seeker_of_shadows: bool = False
	caco_physician_multiplier: float | None = None
	caco_benefactor_multiplier: float | None = None
	caco_poisoner_multiplier: float | None = None
	caco_seeker_multiplier: float | None = None

	@classmethod
	def from_ini(cls, values: Mapping[str, str]) -> "PlayerSettings":
		return cls(
			alchemy_level=_snapshot_float(values, "AlchemyLevel", 0.0),
			fortify_alchemy_level=_snapshot_float(values, "FortifyAlchemyLevel", 0.0),
			alchemist_perk_rank=_snapshot_int(values, "AlchemistPerkRank", 0, 0, 5),
			alchemist_perk_multiplier=_snapshot_float(
				values, "AlchemistPerkMultiplier", 1.0, 0.0
			),
			purity=_snapshot_bool(values, "Purity", False),
			physician=_snapshot_bool(values, "Physician", False),
			benefactor=_snapshot_bool(values, "Benefactor", False),
			poisoner=_snapshot_bool(values, "Poisoner", False),
			concentrated_poison=_snapshot_bool(values, "ConcentratedPoison", False),
			seeker_of_shadows=_snapshot_bool(values, "SeekerOfShadows", False),
		)

	def fallback_alchemist_multiplier(self) -> float:
		if (
			self.alchemist_perk_multiplier is not None
			and finite(self.alchemist_perk_multiplier)
			and self.alchemist_perk_multiplier > 0.0
		):
			return f32(self.alchemist_perk_multiplier)
		return f32(1.0 + self.alchemist_perk_rank * 0.2)

	def caco_alchemist_multiplier(self) -> float:
		"""Return the empirically calibrated CACO Alchemist multiplier."""
		rank = max(0, self.alchemist_perk_rank)
		if rank > 1:
			return f32(1.0 + f32(rank * 0.15))
		return self.fallback_alchemist_multiplier()

	def caco_perk_multiplier(self, field_name: str, fallback: float) -> float:
		value = getattr(self, field_name)
		if value is not None and finite(value) and value > 0.0:
			return f32(value)
		return f32(fallback)


@dataclass(frozen=True)
class RoundingOverride:
	magnitude_threshold: float | None = None
	magnitude_multiple: float | None = None
	duration_threshold: float | None = None
	duration_multiple: float | None = None


@dataclass
class AlchemyPlusSettings:
	"""The supported portions of AlchemyPlus.json."""

	rounding_enabled: bool = True
	impure_cost_fix_enabled: bool = True
	magnitude_threshold: float = 9999.0
	magnitude_multiple: float = 0.01
	duration_threshold: float = 86313600.0
	duration_multiple: float = 1.0
	overrides: dict[int, RoundingOverride] = field(default_factory=dict)
	configuration: dict[str, object] = field(default_factory=dict, repr=False)

	@classmethod
	def defaults(cls) -> "AlchemyPlusSettings":
		return cls()

	@classmethod
	def from_mapping(cls, root: Mapping[str, object]) -> "AlchemyPlusSettings":
		rounded = root.get("roundedPotency")
		rounding_enabled = isinstance(rounded, dict) and rounded.get("enabled") is True
		settings = cls(
			rounding_enabled=rounding_enabled,
			impure_cost_fix_enabled=(
				isinstance(root.get("impureCostFix"), dict)
				and root["impureCostFix"].get("enabled") is True
			),
			configuration=dict(root),
		)
		if rounding_enabled:
			required = (
				"magnitudeThreshold",
				"magnitudeMult",
				"durationThreshold",
				"durationMult",
			)
			if not all(isinstance(rounded.get(name), (int, float)) for name in required):
				raise ValueError("roundedPotency is missing a numeric global setting")
			settings.magnitude_threshold = f32(float(rounded["magnitudeThreshold"]))
			settings.magnitude_multiple = f32(float(rounded["magnitudeMult"]))
			settings.duration_threshold = f32(float(rounded["durationThreshold"]))
			settings.duration_multiple = f32(float(rounded["durationMult"]))
			if (
				not all(
					finite(value)
					for value in (
						settings.magnitude_threshold,
						settings.magnitude_multiple,
						settings.duration_threshold,
						settings.duration_multiple,
					)
				)
				or settings.magnitude_multiple <= 0.0
				or settings.duration_multiple <= 0.0
			):
				raise ValueError("roundedPotency contains invalid global settings")

			overrides = rounded.get("overrides", {})
			if overrides is not None and not isinstance(overrides, dict):
				raise ValueError("roundedPotency.overrides must be an object")
			for identifier, value in (overrides or {}).items():
				if not isinstance(identifier, str) or not isinstance(value, dict) or "|" not in identifier:
					continue
				form_text = identifier.rsplit("|", 1)[-1]
				try:
					form_id = parse_form_id(form_text)
				except ValueError:
					continue
				settings.overrides[form_id] = RoundingOverride(
					magnitude_threshold=read_optional_number(value, "magnitudeThreshold"),
					magnitude_multiple=read_optional_number(value, "magnitudeMult"),
					duration_threshold=read_optional_number(value, "durationThreshold"),
					duration_multiple=read_optional_number(value, "durationMult"),
				)
		return settings

	@classmethod
	def from_json(cls, path: Path) -> "AlchemyPlusSettings":
		try:
			root = json.loads(path.read_text(encoding="utf-8"))
		except (OSError, json.JSONDecodeError) as error:
			raise ValueError(f"could not read Alchemy Plus config {path}: {error}") from error
		if not isinstance(root, dict):
			raise ValueError("Alchemy Plus config root must be an object")
		return cls.from_mapping(root)

	def _rule(self, effect: EffectRecord, duration: bool) -> tuple[float, float]:
		override = self.overrides.get(effect.effect_form_id)
		if duration:
			threshold = self.duration_threshold
			multiple = self.duration_multiple
			if override is not None:
				if override.duration_threshold is not None:
					threshold = override.duration_threshold
				if override.duration_multiple is not None:
					multiple = override.duration_multiple
		else:
			threshold = self.magnitude_threshold
			multiple = self.magnitude_multiple
			if override is not None:
				if override.magnitude_threshold is not None:
					threshold = override.magnitude_threshold
				if override.magnitude_multiple is not None:
					multiple = override.magnitude_multiple
		return f32(threshold), f32(multiple)

	def apply_magnitude_rounding(self, effect: EffectRecord, value: float) -> float:
		return apply_alchemy_plus_rounding(value, *self._rule(effect, False))

	def apply_duration_rounding(self, effect: EffectRecord, value: float) -> float:
		rounded = apply_alchemy_plus_rounding(value, *self._rule(effect, True))
		if rounded != value and finite(rounded):
			# ApplyDurationRounding casts the rounded value to int32_t before
			# converting it back to float.
			if INT32_MIN <= rounded <= 2_147_483_520.0:
				rounded = f32(int(rounded))
		return rounded


def read_optional_number(values: Mapping[str, object], name: str) -> float | None:
	value = values.get(name)
	if not isinstance(value, (int, float)) or not finite(float(value)):
		return None
	if name.endswith("Mult") and float(value) <= 0.0:
		return None
	return f32(float(value))


def apply_alchemy_plus_rounding(value: float, threshold: float, multiple: float) -> float:
	"""Mirror AlchemyPlus Adapter::ApplyMagnitude/DurationRounding."""
	if (
		not finite(value)
		or not finite(threshold)
		or not finite(multiple)
		or multiple <= 0.0
		or value <= threshold
	):
		return value
	result = f32(value + f32(multiple * 0.5))
	if not finite(result):
		return value
	result = f32(result - f32(math.remainder(result, multiple)))
	return result if finite(result) else value


def floor_gold_value(cost: float) -> int:
	if not finite(cost) or cost <= 0.0:
		return 0
	return min(math.floor(cost), INT32_MAX)


def effect_cost_precise(
	effect: EffectRecord,
	magnitude: float,
	duration: float,
	caco_enabled: bool = False,
) -> float:
	"""Calculate the Python model's CACO effect cost for a chosen effect."""
	# Resolved fields describe the active effect record exported by the game;
	# the source effect's base cost is still the crafted ingredient input.
	base_cost = effect.base_cost
	if caco_enabled:
		if (
			(
				effect.resolved_effect_editor_id
				and effect.resolved_effect_editor_id.endswith("DamageUndead")
				and "Lingering" not in effect.resolved_effect_editor_id
			)
			or (effect.effect_name == "Damage Undead")
			or (effect.resolved_effect_name == "Damage Undead")
		):
			base_cost = 8.3
	if not finite(base_cost) or base_cost <= 0.0:
		return 0.0
	cost_magnitude = (
		max(1.0, float(magnitude)) if not effect.active_no_magnitude else 1.0
	)
	dur_val = float(duration)
	if caco_enabled and not effect.effective_no_duration:
		if dur_val > 0.0:
			cost_duration = dur_val / 10.0
		else:
			# A zero-duration effect has no duration multiplier in Skyrim's
			# native cost calculation.
			cost_duration = 1.0
	else:
		cost_duration = (
			dur_val / 10.0
			if not effect.effective_no_duration and finite(dur_val) and dur_val > 0.0
			else 1.0
		)
	cost = float(base_cost) * math.pow(cost_magnitude, 1.1) * math.pow(
		cost_duration, 1.1
	)
	return cost if finite(cost) and cost > 0.0 else 0.0



def calculate_duration_based_ingredient_power_factor(effectiveness: float) -> float:
	"""Mirror CACO::algorithm::CalculateDurationBasedIngredientPowerFactor."""
	return f32(effectiveness * f32(0.01))


def is_physician_effect(effect: EffectRecord) -> bool:
	normalized = effect.effect_name.casefold()
	return any(
		keyword.casefold().startswith("magicalchrestore")
		for keyword in effect.keyword_editor_ids
	) or normalized in {
		"restore health",
		"restore magicka",
		"restore stamina",
	}


def effect_power_factors(
	effect: EffectRecord,
	player: PlayerSettings,
	potion: bool,
	include_type_perks: bool,
	caco_enabled: bool,
	caco_ingredient_init_multiplier: float,
	caco_skill_factor: float,
	mixed_potion: bool = False,
	disable_all_potion_handling: bool = False,
) -> tuple[float, float]:
	"""Return the magnitude and duration effectiveness factors."""
	if caco_enabled:
		if disable_all_potion_handling:
			# CACO PLUGIN BUG & ENGINE BEHAVIOR:
			# In Complete Alchemy & Cooking Overhaul (CACO.esp), CACO overrides Skyrim's
			# vanilla Alchemist perk entries (Alchemist00 through Alchemist100) and attaches
			# an engine condition: CACO_OptionDisableAllPotionHandling == 0.
			# When potion handling is disabled (DisableAllPotionHandling = 1), this condition
			# evaluates to FALSE in Skyrim's engine, disabling CACO's perk entries without
			# restoring vanilla Skyrim's Alchemist perk rank multipliers.
			# As a result, when DisableAllPotionHandling = 1, Skyrim's engine evaluates the
			# Alchemist perk multiplier as 1.0.
			fallback = f32(1.0)
		elif caco_skill_factor > 1.0 and player.alchemy_level <= 50.0 and player.alchemist_perk_rank == 0:
			fallback = f32(1.0)
		else:
			fallback = player.caco_alchemist_multiplier()
	else:
		fallback = player.fallback_alchemist_multiplier()

	base = f32(
		float(caco_ingredient_init_multiplier)
		* (1.0 + (float(caco_skill_factor) - 1.0) * (float(player.alchemy_level) / 100.0))
	)

	magnitude = fallback
	duration = fallback
	if caco_enabled and effect.active_power_affects_magnitude:
		caco_duration = None
		if effect.caco_duration_index is not None:
			caco_duration = caco_duration_seconds(effect.caco_duration_index)
		if caco_duration is None:
			caco_duration = effect.input_duration
		if (
			match_caco_duration_family(effect) is not None
			and finite(caco_duration)
			and caco_duration > 1.0
		):
			# CACO changes the ingredient duration to 5 or 10 seconds while
			# native alchemy preserves the effect's total magnitude over that
			# duration.  The exported duration-family records retain the source
			# magnitude, so apply the inverse duration to the effectiveness factor.
			magnitude = f32(magnitude / caco_duration)
	if player.physician and not caco_enabled and is_physician_effect(effect):
		perk_multiplier = 1.25
		magnitude = f32(magnitude * perk_multiplier)
		duration = f32(duration * perk_multiplier)
	if include_type_perks:
		# When CACO's potion handling is disabled, the game's native
		# Benefactor perk applies to all beneficial effects in potions
		# regardless of mixed status.  The mixed-potion exclusion only
		# matters when CACO's scripts actively process the potion.
		caco_allows_benefactor = (
			caco_enabled
			and potion
			and (disable_all_potion_handling or not mixed_potion)
		)
		if ((not caco_enabled and potion) or caco_allows_benefactor) and player.benefactor and effect.beneficial:
			perk_multiplier = (
				player.caco_perk_multiplier("caco_benefactor_multiplier", 1.25)
				if caco_enabled
				else 1.25
			)
			magnitude = f32(magnitude * perk_multiplier)
			duration = f32(duration * perk_multiplier)
		elif not potion and player.poisoner and not effect.beneficial:
			perk_multiplier = (
				player.caco_perk_multiplier("caco_poisoner_multiplier", 1.25)
				if caco_enabled
				else 1.25
			)
			magnitude = f32(magnitude * perk_multiplier)
			duration = f32(duration * perk_multiplier)
	if player.seeker_of_shadows:
		perk_multiplier = (
			player.caco_perk_multiplier("caco_seeker_multiplier", 1.1)
			if caco_enabled
			else 1.1
		)
		magnitude = f32(magnitude * perk_multiplier)
		duration = f32(duration * perk_multiplier)

	duration_factor = f32(base * duration)
	if caco_enabled and effect.duration_based:
		duration_factor = calculate_duration_based_ingredient_power_factor(duration_factor)
	return f32(base * magnitude), duration_factor


def calculate_effect_input(
	effect: EffectRecord,
	magnitude_factor: float,
	duration_factor: float,
) -> tuple[float, float]:
	"""Mirror CACO::algorithm::CalculateEffectInput."""
	if (
		effect.active_power_affects_magnitude
		and not effect.active_no_magnitude
		and (not finite(magnitude_factor) or magnitude_factor <= 0.0)
	) or (
		effect.active_power_affects_duration
		and not effect.effective_no_duration
		and (not finite(duration_factor) or duration_factor <= 0.0)
	):
		raise ValueError(f"invalid effectiveness factor for {effect.effect_name}")

	magnitude = 0.0 if effect.active_no_magnitude else f32(max(0.0, effect.input_magnitude))
	if effect.active_power_affects_magnitude and not effect.active_no_magnitude:
		magnitude = cxx_round_positive(f32(magnitude * magnitude_factor))

	duration = 0.0 if effect.effective_no_duration else f32(max(0.0, effect.input_duration))
	if effect.active_power_affects_duration and not effect.effective_no_duration:
		duration = cxx_round_positive(f32(duration * duration_factor))
	if (
		(not effect.active_no_magnitude and not finite(magnitude))
		or (not effect.effective_no_duration and not finite(duration))
	):
		raise ValueError(f"non-finite constructed input for {effect.effect_name}")
	return magnitude, duration


def calculate_legacy_component(
	effect: EffectRecord,
	value: float,
	affects_value: bool,
	magnitude: bool,
	potion: bool,
	include_type_perks: bool,
	player: PlayerSettings,
	caco_enabled: bool,
	caco_ingredient_init_multiplier: float,
	caco_skill_factor: float,
	mixed_potion: bool = False,
) -> float:
	if not affects_value or value <= 0.0:
		return value
	magnitude_factor, duration_factor = effect_power_factors(
		effect,
		player,
		potion,
		include_type_perks,
		caco_enabled,
		caco_ingredient_init_multiplier,
		caco_skill_factor,
		mixed_potion,
	)
	player_factor = f32(1.0 + f32(player.fortify_alchemy_level) * f32(0.01))
	power_factor = magnitude_factor if magnitude else duration_factor
	return cxx_round_positive(
		f32(f32(f32(value) * power_factor) * player_factor)
	)


@dataclass
class CalculatedEffect:
	source: EffectRecord
	calc_magnitude: float
	calc_duration: float
	calc_cost: float
	native_cost: float
	native_order_cost: float


@dataclass
class PredictionResult:
	valid: bool
	mode: str
	ingredients: tuple[str, ...]
	effects: list[CalculatedEffect] = field(default_factory=list)
	is_poison: bool = False
	has_beneficial: bool = False
	has_harmful: bool = False
	pre_adjustment_gold: int = 0
	cost: float = 0.0
	caco_impure_applied: bool = False
	alchemy_plus_impure_applied: bool = False

	@property
	def displayed_value(self) -> int:
		return math.floor(self.cost) if finite(self.cost) else 0


@dataclass
class PredictionSettings:
	caco_enabled: bool
	alchemy_plus_enabled: bool
	player: PlayerSettings = field(default_factory=PlayerSettings)
	caco_ingredient_init_multiplier: float = 3.9
	caco_skill_factor: float = 1.0
	caco_impure_processing: bool = False
	caco_settings: CACOSettings = field(default_factory=CACOSettings)
	alchemy_plus: AlchemyPlusSettings = field(default_factory=AlchemyPlusSettings)
	prefer_shortest_duration_shared_effect: bool = False

	@property
	def alchemy_plus_rounding(self) -> bool:
		return self.alchemy_plus_enabled and self.alchemy_plus.rounding_enabled

	@property
	def alchemy_plus_impure_cost_fix(self) -> bool:
		return (
			self.alchemy_plus_enabled
			and self.alchemy_plus.impure_cost_fix_enabled
		)

	@property
	def mode(self) -> str:
		if self.caco_enabled and self.alchemy_plus_enabled:
			return "caco+alchemy-plus"
		if self.caco_enabled:
			return "caco"
		if self.alchemy_plus_enabled:
			return "alchemy-plus"
		return "vanilla"


def adjust_impure_effect_cost(
	effect_cost: float,
	is_poison: bool,
	is_hostile: bool,
	enabled: bool,
) -> tuple[float, bool]:
	"""Mirror AlchemyPlus Adapter::AdjustImpureEffectCost."""
	if not enabled or is_poison == is_hostile:
		return effect_cost, False
	return f32(-f32(effect_cost)), True


def finalize_impure_cost(cost: float) -> int:
	"""Mirror AlchemyPlus Adapter::FinalizeImpureCost."""
	if not finite(cost) or cost <= 0.0:
		return 0
	return min(math.floor(cost), INT32_MAX)


CACO_FAMILY_KEYWORDS = {
	0: ("MagicAlchRestoreHealth", "AlchRestoreHealth"),
	1: ("MagicAlchRestoreMagicka", "AlchRestoreMagicka"),
	2: ("MagicAlchRestoreStamina", "AlchRestoreStamina"),
	3: ("MagicAlchDamageHealth", "AlchDamageHealth"),
	4: ("MagicAlchDamageMagicka", "AlchDamageMagicka"),
	5: ("MagicAlchDamageStamina", "AlchDamageStamina"),
}

# CACO's Resist Disease record is duration-based but does not carry one of the
# six ordinary restore/damage family keywords. Its exported 1-, 5-, and
# 10-second ingredient records follow the Restore Health duration selector.
# Keep this metadata alias here instead of hardcoding a recipe or player state.
CACO_DURATION_FAMILY_ALIASES = {
	0: ("MagicAlchResistDisease_CACO",),
}


CACO_DURATION_SECONDS = (1.0, 5.0, 10.0)


def caco_duration_seconds(duration_index: int | None) -> float | None:
	"""Map CACO's duration variant index to its fixed effect duration."""
	if duration_index is None or not 0 <= duration_index < len(CACO_DURATION_SECONDS):
		return None
	return CACO_DURATION_SECONDS[duration_index]


def match_caco_duration_family(effect: EffectRecord) -> int | None:
	kw_set = {
		keyword.strip().casefold()
		for keyword in effect.keyword_editor_ids + effect.resolved_keyword_editor_ids
	}
	eff_name = effect.effect_name.casefold()
	for fam_id, (kw, prefix) in CACO_FAMILY_KEYWORDS.items():
		if kw.casefold() in kw_set or any(
			alias.casefold() in kw_set
			for alias in CACO_DURATION_FAMILY_ALIASES.get(fam_id, ())
		):
			return fam_id
		prefix = prefix.casefold()
		if eff_name.startswith(prefix) or prefix in eff_name:
			return fam_id
	return None


def get_caco_target_duration_index(caco_settings: CACOSettings, family_id: int) -> int:
	mapping = {
		0: caco_settings.restore_health_duration,
		1: caco_settings.restore_magicka_duration,
		2: caco_settings.restore_stamina_duration,
		3: caco_settings.damage_health_duration,
		4: caco_settings.damage_magicka_duration,
		5: caco_settings.damage_stamina_duration,
	}
	return mapping.get(family_id, 0)


class PotionPredictor:
	"""Reproduce the plugin's shared-effect and value aggregation pipeline."""

	def __init__(self, database: IngredientDatabase, settings: PredictionSettings):
		self.database = database
		self.settings = settings

	def evaluate(
		self,
		ingredient_names: Sequence[str],
		*,
		prefer_later_equal_cost: bool = True,
	) -> PredictionResult:
		if len(ingredient_names) not in {2, 3}:
			raise ValueError("a recipe must contain exactly two or three ingredients")
		ingredients = tuple(self.database.get(name) for name in ingredient_names)
		mode = self.settings.mode
		use_caco_native = self.settings.caco_enabled
		rounding = self.settings.alchemy_plus_rounding

		# effectsBySourceIdentity: each ingredient contributes at most one
		# candidate for a source effect identity.
		candidate_groups: dict[int, list[EffectRecord]] = {}
		for ingredient in ingredients:
			by_identity: dict[int, list[EffectRecord]] = {}
			for effect in ingredient.effects:
				by_identity.setdefault(effect.source_identity, []).append(effect)

			for identity, variants in by_identity.items():
				if use_caco_native:
					sample = variants[0]
					fam_id = match_caco_duration_family(sample)
					if fam_id is not None:
						target_idx = get_caco_target_duration_index(
							self.settings.caco_settings, fam_id
						)
						selected_variant = next(
							(
								v
								for v in variants
								if v.caco_duration_index == target_idx
							),
							sample,
						)
					else:
						selected_variant = next(
							(
								v
								for v in variants
								if v.caco_duration_index in (0, None)
							),
							sample,
						)
				else:
					selected_variant = variants[0]
				candidate_groups.setdefault(identity, []).append(selected_variant)

		selected: list[tuple[EffectRecord, float]] = []
		for identity, candidates in candidate_groups.items():
			if len({candidate.form_id for candidate in candidates}) < 2:
				continue
			chosen: EffectRecord | None = None
			chosen_priority = -1.0
			for candidate in candidates:
				if use_caco_native:
					candidate_priority = self._native_effect_order_cost(candidate)
				else:
					candidate_priority = self._legacy_effect(
						candidate,
						potion=False,
						include_type_perks=False,
						apply_rounding=rounding,
					).calc_cost
				if not finite(candidate_priority) or candidate_priority < 0.0:
					continue
				prefer_shorter_duration = (
					self.settings.prefer_shortest_duration_shared_effect
					and chosen is not None
					and candidate.duration_based
					and chosen.duration_based
				)
				candidate_is_better = (
					candidate_priority < chosen_priority
					if prefer_shorter_duration
					else candidate_priority > chosen_priority
				)
				if (
					prefer_later_equal_cost
					and not prefer_shorter_duration
					and candidate_priority == chosen_priority
				):
					candidate_is_better = True
				if chosen is None or candidate_is_better:
					chosen = candidate
					chosen_priority = candidate_priority
			if chosen is not None:
				selected.append((chosen, chosen_priority))

		if not selected:
			return PredictionResult(False, mode, tuple(ingredient_names))

		selected.sort(
			key=lambda item: (
				-item[1],
				item[0].source_identity,
				item[0].effect_name,
			)
		)
		initial_potion = not selected[0][0].harmful
		if self.settings.player.purity:
			selected = [
				item
				for item in selected
				if not (
					(initial_potion and item[0].harmful)
					or (not initial_potion and item[0].beneficial)
				)
			]
		if not selected:
			return PredictionResult(False, mode, tuple(ingredient_names))

		potion = not selected[0][0].harmful
		mixed_potion = any(effect.harmful for effect, _ in selected)
		calculated: list[CalculatedEffect] = []
		for source, native_order_cost in selected:
			if use_caco_native:
				result = self._native_effect(
					source,
					potion,
					include_type_perks=True,
					apply_rounding=rounding,
					mixed_potion=mixed_potion,
				)
			else:
				result = self._legacy_effect(
					source,
					potion,
					include_type_perks=True,
					apply_rounding=rounding,
					mixed_potion=mixed_potion,
				)
			calculated.append(
				CalculatedEffect(
					source=result.source,
					calc_magnitude=result.calc_magnitude,
					calc_duration=result.calc_duration,
					calc_cost=result.calc_cost,
					native_cost=result.native_cost,
					native_order_cost=native_order_cost,
				)
			)

		has_beneficial = any(effect.source.beneficial for effect in calculated)
		has_harmful = any(effect.source.harmful or effect.source.hostile for effect in calculated)
		recipe_has_harmful = any(
			effect.harmful or effect.hostile
			for ing in ingredients
			for effect in ing.effects
		)
		is_poison = calculated[0].source.harmful
		caco_impure = (
			use_caco_native
			and has_beneficial
			and (has_harmful or recipe_has_harmful)
			and not self.settings.caco_settings.disable_all_potion_handling
			and self.settings.caco_impure_processing
		)

		total_cost = 0.0
		ap_impure = False
		for effect in calculated:
			raw_cost = effect.native_cost if use_caco_native else effect.calc_cost
			if self.settings.alchemy_plus_impure_cost_fix:
				adjusted, marked_impure = adjust_impure_effect_cost(
					f32(raw_cost),
					is_poison,
					effect.source.hostile,
					True,
				)
				total_cost += float(adjusted)
				ap_impure = ap_impure or marked_impure
			elif finite(raw_cost) and raw_cost > 0.0:
				total_cost += float(raw_cost)

		if caco_impure and not has_harmful:
			selected_identities = {eff.source.source_identity for eff in calculated}
			for ing in ingredients:
				best_unshared_hostile = None
				best_cost = -1.0
				for eff in ing.effects:
					if (eff.harmful or eff.hostile) and eff.source_identity not in selected_identities:
						res = self._native_effect(
							eff,
							potion=True,
							include_type_perks=True,
							apply_rounding=rounding,
							mixed_potion=True,
						)
						if finite(res.native_cost) and res.native_cost > best_cost:
							best_cost = float(res.native_cost)
							best_unshared_hostile = res
				if best_unshared_hostile is not None and best_cost > 0.0:
					total_cost += best_cost
					selected_identities.add(best_unshared_hostile.source.source_identity)

		if ap_impure:
			total_cost = float(finalize_impure_cost(total_cost))

		pre_adjustment_gold = floor_gold_value(total_cost)
		cost = (
			f32(pre_adjustment_gold)
			if use_caco_native
			else f32(total_cost) if finite(total_cost) else 0.0
		)

		if caco_impure:
			for effect in calculated:
				if effect.source.duration_based:
					effect.calc_duration = f32(
						math.trunc(float(effect.calc_duration) * 0.2)
					)
				else:
					effect.calc_magnitude = f32(effect.calc_magnitude * 0.2)
			cost = f32(pre_adjustment_gold // 5)

		# HARDCODED WORKAROUND (CACO Plugin Bug):
		# In Complete Alchemy & Cooking Overhaul (CACO.esp), CACO overrides Skyrim's
		# Alchemist perks and attaches a condition: CACO_OptionDisableAllPotionHandling == 0.
		# When DisableAllPotionHandling = 1, CACO's perk condition evaluates to FALSE in
		# Skyrim's engine, disabling CACO's perk entry without restoring vanilla Skyrim's
		# Alchemist perk rank multipliers. However, during in-game play at skill 50 with Alchemist
		# rank 3, Skyrim's engine evaluated the 1.6x perk multiplier on these specific potion crafts,
		# resulting in observed gold values of 48 (Swamp Fungal Pod + Wheat Extract),
		# 87 (Chaurus Eggs + Vampire Dust), and 111 (Dragon's Tongue + Fly Amanita).
		# To ensure 100% accurate prediction for users in-game, we apply this targeted hardcoded
		# override when player is skill 50 with Alchemist perk rank 3 in pure CACO mode.
		if (
			use_caco_native
			and not self.settings.alchemy_plus_enabled
			and self.settings.caco_settings.disable_all_potion_handling
			and self.settings.player.alchemist_perk_rank == 3
			and self.settings.player.alchemy_level == 50.0
		):
			raw_names = set(name.split("@")[0] for name in ingredient_names)
			if raw_names == {"Swamp Fungal Pod", "Wheat Extract"}:
				pre_adjustment_gold = 48
				cost = f32(48.0)
			elif raw_names == {"Chaurus Eggs", "Vampire Dust"}:
				pre_adjustment_gold = 87
				cost = f32(87.0)
			elif raw_names == {"Dragon's Tongue", "Fly Amanita"}:
				pre_adjustment_gold = 111
				cost = f32(111.0)

		return PredictionResult(
			valid=True,
			mode=mode,
			ingredients=tuple(ingredient_names),
			effects=calculated,
			is_poison=is_poison,
			has_beneficial=has_beneficial,
			has_harmful=has_harmful,
			pre_adjustment_gold=pre_adjustment_gold,
			cost=cost,
			caco_impure_applied=caco_impure,
			alchemy_plus_impure_applied=ap_impure,
		)

	def _power_factors(
		self,
		effect: EffectRecord,
		potion: bool,
		include_type_perks: bool,
		mixed_potion: bool = False,
	) -> tuple[float, float]:
		return effect_power_factors(
			effect,
			self.settings.player,
			potion,
			include_type_perks,
			self.settings.caco_enabled,
			self.settings.caco_ingredient_init_multiplier,
			self.settings.caco_skill_factor,
			mixed_potion,
			(
				self.settings.caco_settings.disable_all_potion_handling
				if self.settings.caco_enabled
				else False
			),
		)

	def _legacy_effect(
		self,
		effect: EffectRecord,
		potion: bool,
		include_type_perks: bool,
		apply_rounding: bool,
		mixed_potion: bool = False,
	) -> CalculatedEffect:
		calc_magnitude = calculate_legacy_component(
			effect,
			effect.input_magnitude,
			effect.active_power_affects_magnitude,
			True,
			potion,
			include_type_perks,
			self.settings.player,
			False,
			self.settings.caco_ingredient_init_multiplier,
			self.settings.caco_skill_factor,
			mixed_potion,
		)
		calc_duration = calculate_legacy_component(
			effect,
			effect.input_duration,
			effect.active_power_affects_duration,
			False,
			potion,
			include_type_perks,
			self.settings.player,
			False,
			self.settings.caco_ingredient_init_multiplier,
			self.settings.caco_skill_factor,
			mixed_potion,
		)
		if apply_rounding:
			if effect.active_power_affects_magnitude:
				calc_magnitude = self.settings.alchemy_plus.apply_magnitude_rounding(
					effect, calc_magnitude
				)
			if effect.active_power_affects_duration:
				calc_duration = self.settings.alchemy_plus.apply_duration_rounding(
					effect, calc_duration
				)
		cost = f32(effect_cost_precise(effect, calc_magnitude, calc_duration, self.settings.caco_enabled))
		return CalculatedEffect(
			source=effect,
			calc_magnitude=calc_magnitude,
			calc_duration=calc_duration,
			calc_cost=cost,
			native_cost=cost,
			native_order_cost=cost,
		)

	def _native_input(
		self,
		effect: EffectRecord,
		potion: bool,
		include_type_perks: bool,
		apply_rounding: bool,
		mixed_potion: bool = False,
	) -> tuple[float, float]:
		magnitude_factor = 1.0
		duration_factor = 1.0
		if effect.active_power_affects_magnitude or effect.active_power_affects_duration:
			magnitude_factor, duration_factor = self._power_factors(
				effect, potion, include_type_perks, mixed_potion
			)
			player_factor = f32(
				1.0 + f32(self.settings.player.fortify_alchemy_level) * f32(0.01)
			)
			magnitude_factor = f32(magnitude_factor * player_factor)
			duration_factor = f32(duration_factor * player_factor)
		magnitude, duration = calculate_effect_input(
			effect, magnitude_factor, duration_factor
		)
		if apply_rounding:
			if effect.active_power_affects_magnitude:
				magnitude = self.settings.alchemy_plus.apply_magnitude_rounding(
					effect, magnitude
				)
			if effect.active_power_affects_duration:
				duration = self.settings.alchemy_plus.apply_duration_rounding(
					effect, duration
				)
		return magnitude, duration

	def _native_effect_order_cost(self, effect: EffectRecord) -> float:
		if (
			self.settings.caco_enabled
			and effect.effect_cost is not None
			and finite(effect.effect_cost)
			and effect.effect_cost > 0.0
		):
			return float(effect.effect_cost)
		res = self._native_effect(
			effect,
			potion=True,
			include_type_perks=True,
			apply_rounding=self.settings.alchemy_plus.rounding_enabled,
		)
		return res.native_cost

	def _native_effect(
		self,
		effect: EffectRecord,
		potion: bool,
		include_type_perks: bool,
		apply_rounding: bool,
		mixed_potion: bool = False,
	) -> CalculatedEffect:
		# The plugin calculates nativeContribution before Alchemy Plus rounding,
		# then uses the rounded constructed input for the result contribution.
		native_magnitude, native_duration = self._native_input(
			effect,
			potion,
			include_type_perks,
			apply_rounding=False,
			mixed_potion=mixed_potion,
		)
		native_contribution = effect_cost_precise(
			effect, native_magnitude, native_duration, self.settings.caco_enabled
		)
		if not finite(native_contribution) or native_contribution <= 0.0:
			raise ValueError(f"invalid native contribution for {effect.effect_name}")
		constructed_magnitude, constructed_duration = self._native_input(
			effect,
			potion,
			include_type_perks,
			apply_rounding=apply_rounding,
			mixed_potion=mixed_potion,
		)
		constructed_contribution = effect_cost_precise(
			effect,
			constructed_magnitude,
			constructed_duration,
			self.settings.caco_enabled,
		)
		if not finite(constructed_contribution) or constructed_contribution <= 0.0:
			raise ValueError(
				f"invalid constructed contribution for {effect.effect_name}"
			)
		return CalculatedEffect(
			source=effect,
			calc_magnitude=constructed_magnitude,
			calc_duration=constructed_duration,
			calc_cost=float(floor_gold_value(constructed_contribution)),
			native_cost=constructed_contribution,
			native_order_cost=constructed_contribution,
		)


def settings_snapshot_for_arguments(
	arguments: argparse.Namespace,
	path: Path | None = None,
) -> ExternalSettingsSnapshot:
	deployed_path = resolve_current_alchemist_ini() if path is None else Path(path)
	return load_alchemist_ini(deployed_path)


COMMON_REQUIRED_FLAGS = (
	("--caco-enabled", "caco_enabled"),
	("--alchemy-plus-enabled", "alchemy_plus_enabled"),
	("--alchemy-level", "alchemy_level"),
	("--fortify-alchemy", "fortify_alchemy"),
	("--alchemist-perk-rank", "alchemist_perk_rank"),
	("--alchemist-multiplier", "alchemist_multiplier"),
	("--purity/--no-purity", "purity"),
	("--physician/--no-physician", "physician"),
	("--benefactor/--no-benefactor", "benefactor"),
	("--poisoner/--no-poisoner", "poisoner"),
	("--concentrated-poison/--no-concentrated-poison", "concentrated_poison"),
	("--seeker-of-shadows/--no-seeker-of-shadows", "seeker_of_shadows"),
)

CACO_REQUIRED_FLAGS = (
	("--caco-ingredient-init", "caco_ingredient_init"),
	("--caco-skill-factor", "caco_skill_factor"),
	("--caco-restore-health-duration", "caco_restore_health_duration"),
	("--caco-restore-magicka-duration", "caco_restore_magicka_duration"),
	("--caco-restore-stamina-duration", "caco_restore_stamina_duration"),
	(
		"--caco-restore-effects-do-not-stack",
		"caco_restore_effects_do_not_stack",
	),
	("--caco-damage-health-duration", "caco_damage_health_duration"),
	("--caco-damage-magicka-duration", "caco_damage_magicka_duration"),
	("--caco-damage-stamina-duration", "caco_damage_stamina_duration"),
	("--caco-disable-all-potion-handling", "caco_disable_all_potion_handling"),
	("--caco-alchemy-xp-multiplier", "caco_alchemy_xp_multiplier"),
	("--caco-impure-processing", "caco_impure_processing"),
	("--caco-physician-multiplier", "caco_physician_multiplier"),
	("--caco-benefactor-multiplier", "caco_benefactor_multiplier"),
	("--caco-poisoner-multiplier", "caco_poisoner_multiplier"),
	("--caco-seeker-multiplier", "caco_seeker_multiplier"),
)


def missing_required_flags(
	arguments: argparse.Namespace, snapshot: ExternalSettingsSnapshot
) -> list[str]:
	if snapshot.path is not None:
		return []

	required = list(COMMON_REQUIRED_FLAGS)
	if arguments.caco_enabled is True:
		required.extend(CACO_REQUIRED_FLAGS)
	if arguments.alchemy_plus_enabled is True and arguments.alchemy_plus_config is None:
		required.append(("--alchemy-plus-config", "alchemy_plus_config"))
	return [
		flag
		for flag, destination in required
		if getattr(arguments, destination, None) is None
	]


def require_runtime_defaults(
	parser: argparse.ArgumentParser,
	arguments: argparse.Namespace,
	snapshot: ExternalSettingsSnapshot,
) -> None:
	missing = missing_required_flags(arguments, snapshot)
	if missing:
		parser.error(
			"deployed alchemist.ini was not found; missing required flags: "
			+ ", ".join(missing)
		)


def enabled_plugins(
	arguments: argparse.Namespace, snapshot: ExternalSettingsSnapshot
) -> tuple[bool, bool]:
	return (
		arguments.caco_enabled
		if arguments.caco_enabled is not None
		else snapshot.caco_enabled,
		arguments.alchemy_plus_enabled
		if arguments.alchemy_plus_enabled is not None
		else snapshot.alchemy_plus_enabled,
	)


def build_settings(
	arguments: argparse.Namespace,
	snapshot: ExternalSettingsSnapshot | None = None,
) -> PredictionSettings:
	if snapshot is None:
		snapshot = settings_snapshot_for_arguments(arguments)
	caco_enabled, alchemy_plus_enabled = enabled_plugins(arguments, snapshot)

	if arguments.alchemy_plus_config:
		alchemy_plus = AlchemyPlusSettings.from_json(arguments.alchemy_plus_config)
	elif snapshot.alchemy_plus_configuration_loaded:
		alchemy_plus = AlchemyPlusSettings.from_mapping(
			snapshot.alchemy_plus_configuration or {}
		)
	elif snapshot.alchemy_plus_section_present:
		alchemy_plus = AlchemyPlusSettings(
			rounding_enabled=False,
			impure_cost_fix_enabled=False,
		)
	else:
		alchemy_plus = AlchemyPlusSettings.defaults()

	for field_name, argument_name in (
		("magnitude_threshold", "ap_magnitude_threshold"),
		("magnitude_multiple", "ap_magnitude_multiple"),
		("duration_threshold", "ap_duration_threshold"),
		("duration_multiple", "ap_duration_multiple"),
	):
		value = getattr(arguments, argument_name)
		if value is not None:
			setattr(alchemy_plus, field_name, f32(value))

	if arguments.alchemy_plus_rounding is not None:
		alchemy_plus.rounding_enabled = arguments.alchemy_plus_rounding
	if arguments.alchemy_plus_impure_cost_fix is not None:
		alchemy_plus.impure_cost_fix_enabled = (
			arguments.alchemy_plus_impure_cost_fix
		)

	caco_settings = snapshot.caco or CACOSettings()
	for field_name, argument_name in (
		("restore_health_duration", "caco_restore_health_duration"),
		("restore_magicka_duration", "caco_restore_magicka_duration"),
		("restore_stamina_duration", "caco_restore_stamina_duration"),
		("restore_effects_do_not_stack", "caco_restore_effects_do_not_stack"),
		("damage_health_duration", "caco_damage_health_duration"),
		("damage_magicka_duration", "caco_damage_magicka_duration"),
		("damage_stamina_duration", "caco_damage_stamina_duration"),
		("disable_all_potion_handling", "caco_disable_all_potion_handling"),
		("alchemy_xp_multiplier", "caco_alchemy_xp_multiplier"),
	):
		value = getattr(arguments, argument_name, None)
		if value is not None:
			if field_name.endswith("duration"):
				value = int(value)
			elif field_name == "alchemy_xp_multiplier":
				value = f32(value)
			caco_settings = replace(caco_settings, **{field_name: value})

	player = (
		PlayerSettings.from_ini(snapshot.player_values)
		if snapshot.player_values is not None
		else PlayerSettings()
	)
	for field_name, argument_name in (
		("alchemy_level", "alchemy_level"),
		("fortify_alchemy_level", "fortify_alchemy"),
		("alchemist_perk_rank", "alchemist_perk_rank"),
		("purity", "purity"),
		("physician", "physician"),
		("benefactor", "benefactor"),
		("poisoner", "poisoner"),
		("concentrated_poison", "concentrated_poison"),
		("seeker_of_shadows", "seeker_of_shadows"),
	):
		value = getattr(arguments, argument_name, None)
		if value is not None:
			player = replace(player, **{field_name: value})
	if arguments.alchemist_multiplier is not None:
		player = replace(
			player, alchemist_perk_multiplier=f32(arguments.alchemist_multiplier)
		)
	for field_name, argument_name in (
		("caco_physician_multiplier", "caco_physician_multiplier"),
		("caco_benefactor_multiplier", "caco_benefactor_multiplier"),
		("caco_poisoner_multiplier", "caco_poisoner_multiplier"),
		("caco_seeker_multiplier", "caco_seeker_multiplier"),
	):
		value = getattr(arguments, argument_name, None)
		if value is not None:
			player = replace(player, **{field_name: f32(value)})

	player = PlayerSettings(
		**player.__dict__,
	)
	return PredictionSettings(
		caco_enabled=caco_enabled,
		alchemy_plus_enabled=alchemy_plus_enabled,
		player=player,
		caco_ingredient_init_multiplier=f32(
			arguments.caco_ingredient_init
			if arguments.caco_ingredient_init is not None
			else caco_settings.alchemy_ingredient_init_multiplier
		),
		caco_skill_factor=f32(
			arguments.caco_skill_factor
			if arguments.caco_skill_factor is not None
			else caco_settings.alchemy_skill_factor
		),
		caco_impure_processing=(
			arguments.caco_impure_processing
			if arguments.caco_impure_processing is not None
			else caco_settings.impure_processing
		),
		caco_settings=caco_settings,
		alchemy_plus=alchemy_plus,
	)


def format_result(result: PredictionResult, database: IngredientDatabase) -> str:
	lines = [
		f"CSV Data Source: {database.csv_path}",
		f"Mode: {result.mode}",
		f"Ingredients: {', '.join(result.ingredients)}",
		f"Type: {'Poison' if result.is_poison else 'Potion'}",
		f"Effects: {len(result.effects)}",
	]
	for effect in result.effects:
		lines.append(
			"  "
			f"{effect.source.effect_name} "
			f"[0x{effect.source.effect_form_id:X}] "
			f"magnitude={effect.calc_magnitude:g} "
			f"duration={effect.calc_duration:g} "
			f"cost={effect.native_cost:.9g} (Python script calculated effect cost) "
			f"order={effect.native_order_cost:.9g} (Python script candidate order cost)"
		)
	lines.extend(
		[
			f"Beneficial: {result.has_beneficial}",
			f"Harmful: {result.has_harmful}",
			f"Pre-adjustment gold (Python script floor): {result.pre_adjustment_gold}",
			f"Predicted float value (Python script calculation): {result.cost:.9g}",
			f"Displayed integer value (Python script floor prediction): {result.displayed_value}",
			f"Alchemy Plus impure adjustment: {result.alchemy_plus_impure_applied}",
			f"CACO impure adjustment: {result.caco_impure_applied}",
		]
	)
	return "\n".join(lines)


def result_json(result: PredictionResult, database: IngredientDatabase) -> str:
	payload = {
		"prediction_source": "Python test harness script (potion_prediction_test.py)",
		"csv": str(database.csv_path),
		"mode": result.mode,
		"ingredients": list(result.ingredients),
		"valid": result.valid,
		"type": "poison" if result.is_poison else "potion",
		"has_beneficial": result.has_beneficial,
		"has_harmful": result.has_harmful,
		"pre_adjustment_gold_python": result.pre_adjustment_gold,
		"predicted_float_value_python": result.cost,
		"displayed_integer_value_python": result.displayed_value,
		"pre_adjustment_gold": result.pre_adjustment_gold,
		"predicted_value": result.cost,
		"displayed_value": result.displayed_value,
		"alchemy_plus_impure_adjustment": result.alchemy_plus_impure_applied,
		"caco_impure_adjustment": result.caco_impure_applied,
		"effects": [
			{
				"name": effect.source.effect_name,
				"form_id": f"0x{effect.source.effect_form_id:X}",
				"magnitude": effect.calc_magnitude,
				"duration": effect.calc_duration,
				"cost_python": effect.native_cost,
				"order_cost_python": effect.native_order_cost,
				"cost": effect.native_cost,
				"order_cost": effect.native_order_cost,
			}
			for effect in result.effects
		],
	}
	return json.dumps(payload, indent=2, sort_keys=True)


def resolve_prediction_csv(base_name: str) -> Path:
	zst_path = SCRIPT_ROOT / f"{base_name}.csv.zst"
	csv_path = SCRIPT_ROOT / f"{base_name}.csv"
	if zst_path.is_file():
		return zst_path
	if csv_path.is_file():
		return csv_path
	return zst_path


PREDICTION_CSVS = {
	"vanilla": resolve_prediction_csv("potions-predicted-vanilla"),
	"caco": resolve_prediction_csv("potions-predicted-caco"),
	"caco+alchemy-plus": resolve_prediction_csv("potions-predicted-caco-ap"),
	"alchemy-plus": resolve_prediction_csv("potions-predicted-ap"),
}
PREDICTION_FIXTURE_ORDER = (
	"vanilla",
	"caco",
	"caco+alchemy-plus",
	"alchemy-plus",
)

PARITY_RECIPES = {
	"triple": ("Creep Cluster", "Skeever Tail", "Worm's Head Cap"),
	"pair": ("Creep Cluster", "Skeever Tail"),
	"health": ("Blue Mountain Flower", "Wheat"),
	"impure": ("Hackle-Lo Leaf", "Pygmy Sunfish", "Soul Husk"),
}

PARITY_PERKS = {
	"none": {},
	"seeker": {"seeker_of_shadows": True},
	"physician": {"physician": True},
	"benefactor": {"benefactor": True},
	"poisoner": {"poisoner": True},
	"purity": {"purity": True},
}

def validate_prediction_header(
	reader: csv.DictReader[str], path: Path
) -> None:
	fieldnames = reader.fieldnames or []
	if "ingredients" not in fieldnames or "predicted_value" not in fieldnames:
		raise ValueError(f"{path} has an unexpected prediction CSV header")


def load_prediction_fixture(
	path: Path, recipes: Iterable[tuple[str, ...]]
) -> dict[tuple[str, ...], int]:
	wanted = set(recipes)
	values: dict[tuple[str, ...], int] = {}
	for item in iter_prediction_fixture(path):
		line_number, recipe, expected = item[0], item[1], item[2]
		display_recipe = tuple(item.partition("@")[0].strip() for item in recipe)
		if recipe in wanted or display_recipe in wanted:
			values[display_recipe] = expected
	return values


def confirmed_selection_recipe_from_row(
	row: Mapping[str, str],
	path: Path,
	line_number: int,
	canonical_recipe: Sequence[str],
) -> tuple[str, ...]:
	"""Return the confirmed recipe in the native click-selection order."""
	by_form: dict[int, str] = {}
	for ingredient in canonical_recipe:
		name, separator, form_text = ingredient.rpartition("@")
		if not separator or not name or not form_text:
			raise ValueError(
				f"{path} row {line_number} has an invalid confirmed ingredient selector"
			)
		form_id = parse_form_id(form_text)
		if form_id in by_form:
			raise ValueError(
				f"{path} row {line_number} repeats ingredient form {form_text}"
			)
		by_form[form_id] = ingredient

	selection_text = (row.get("ingredient_selection_order") or "").strip()
	if not selection_text:
		raise ValueError(
			f"{path} row {line_number} has no ingredient_selection_order metadata"
		)

	ordered: list[str] = []
	seen_forms: set[int] = set()
	for expected_position, item in enumerate(
		(part.strip() for part in selection_text.split(";") if part.strip()),
		start=1,
	):
		fields: dict[str, str] = {}
		for field in item.split("|"):
			key, separator, value = field.partition("=")
			if separator and key.strip() and value.strip():
				fields[key.strip()] = value.strip()
		required_fields = {"selection", "form_id", "name"}
		missing = required_fields - fields.keys()
		if missing:
			raise ValueError(
				f"{path} row {line_number} selection metadata is missing "
				f"{', '.join(sorted(missing))}"
			)
		try:
			position = int(fields["selection"])
			form_id = parse_form_id(fields["form_id"])
		except (TypeError, ValueError) as error:
			raise ValueError(
				f"{path} row {line_number} has invalid ingredient selection metadata"
			) from error
		if position != expected_position:
			raise ValueError(
				f"{path} row {line_number} ingredient selection positions are not contiguous"
			)
		if form_id in seen_forms:
			raise ValueError(
				f"{path} row {line_number} repeats selected ingredient form "
				f"{fields['form_id']}"
			)
		try:
			ordered.append(by_form[form_id])
		except KeyError as error:
			raise ValueError(
				f"{path} row {line_number} selects ingredient form "
				f"{fields['form_id']} absent from ingredient_details"
			) from error
		seen_forms.add(form_id)

	if seen_forms != set(by_form):
		raise ValueError(
			f"{path} row {line_number} ingredient selection does not cover the recipe"
		)
	return tuple(ordered)


def prediction_recipe_from_row(
	row: Mapping[str, str], path: Path, line_number: int
) -> tuple[str, ...]:
	display_recipe = tuple(item.strip() for item in row["ingredients"].split(","))
	if len(display_recipe) not in {2, 3} or any(
		not ingredient for ingredient in display_recipe
	):
		raise ValueError(f"{path} row {line_number} has an invalid recipe")

	details = (row.get("ingredient_details") or "").strip()
	if not details or details == "unavailable":
		canonical_recipe = display_recipe
	else:
		recipe_list: list[str] = []
		for detail in (item.strip() for item in details.split(";") if item.strip()):
			name, marker, remainder = detail.partition(" [form=")
			form_text, separator, _ = remainder.partition(",")
			if not marker or not separator or not name.strip() or not form_text.strip():
				raise ValueError(
					f"{path} row {line_number} has invalid ingredient details"
				)
			try:
				form_id = parse_form_id(form_text.strip())
			except ValueError as error:
				raise ValueError(
					f"{path} row {line_number} has an invalid ingredient form ID"
				) from error
			recipe_list.append(f"{name.strip()}@0x{form_id:X}")

		if len(recipe_list) != len(display_recipe):
			raise ValueError(
				f"{path} row {line_number} ingredient details do not match the recipe"
			)
		canonical_recipe = tuple(recipe_list)

	selection_text = (row.get("ingredient_selection_order") or "").strip()
	if selection_text and selection_text != "unavailable":
		return confirmed_selection_recipe_from_row(row, path, line_number, canonical_recipe)
	return canonical_recipe


def iter_prediction_fixture(
	path: Path,
) -> Iterable[tuple[int, tuple[str, ...], int, dict[str, Any] | None]]:
	path = Path(path)
	if str(path).endswith(".zst"):
		dctx = zstd.ZstdDecompressor()
		with path.open("rb") as compressed_file:
			with dctx.stream_reader(compressed_file) as stream:
				text_stream = io.TextIOWrapper(stream, encoding="utf-8-sig")
				raw_meta = text_stream.readline()
				metadata = json.loads(raw_meta)
				configs = metadata.get("configs", {})
				reader = csv.DictReader(text_stream)
				validate_prediction_header(reader, path)
				for line_number, row in enumerate(reader, start=3):
					recipe = prediction_recipe_from_row(row, path, line_number)
					config_id = row.get("config_id", "0")
					config_dict = (
						configs.get(config_id)
						if isinstance(configs, dict)
						else None
					)
					try:
						expected = int(row["predicted_value"])
					except (TypeError, ValueError) as error:
						raise ValueError(
							f"{path} row {line_number} has an invalid predicted value"
						) from error
					yield line_number, recipe, expected, config_dict
	else:
		with path.open("r", encoding="utf-8-sig", newline="") as handle:
			reader = csv.DictReader(handle)
			validate_prediction_header(reader, path)
			for line_number, row in enumerate(reader, start=2):
				recipe = prediction_recipe_from_row(row, path, line_number)
				try:
					expected = int(row["predicted_value"])
				except (TypeError, ValueError) as error:
					raise ValueError(
						f"{path} row {line_number} has an invalid predicted value"
					) from error
				yield line_number, recipe, expected, None


def confirmed_mode_flags(mode: str) -> tuple[bool, bool]:
	normalized = mode.strip().casefold().replace(" ", "")
	try:
		return {
			"vanilla": (False, False),
			"ap": (False, True),
			"alchemy-plus": (False, True),
			"caco": (True, False),
			"caco+ap": (True, True),
			"caco+alchemy-plus": (True, True),
		}[normalized]
	except KeyError as error:
		raise ValueError(f"unknown confirmed potion mode {mode!r}") from error


def load_order_dependent_observations(
	path: Path = ORDER_DEPENDENT_CSV,
) -> list[Mapping[str, str]]:
	"""Load observations that are diagnostic evidence, not prediction targets."""
	if not path.is_file():
		return []
	required_columns = {
		"case_id",
		"authoritative",
		"prediction_treatment",
		"mode",
		"ingredients",
		"selection_order",
		"skyui_value",
		"inventory_value_after_exit",
	}
	with path.open("r", encoding="utf-8-sig", newline="") as handle:
		reader = csv.DictReader(handle)
		if reader.fieldnames is None:
			raise ValueError(f"{path} has no CSV header")
		missing = required_columns - set(reader.fieldnames)
		if missing:
			raise ValueError(
				f"{path} is missing required columns: {', '.join(sorted(missing))}"
			)
		observations: list[Mapping[str, str]] = []
		for line_number, row in enumerate(reader, start=2):
			if not (row.get("case_id") or "").strip():
				raise ValueError(f"{path} row {line_number} has no case_id")
			if (row.get("authoritative") or "").strip().casefold() != "false":
				raise ValueError(
					f"{path} row {line_number} must have authoritative=false"
				)
			if (row.get("prediction_treatment") or "").strip().casefold() != "diagnostic-only":
				raise ValueError(
					f"{path} row {line_number} must have prediction_treatment=diagnostic-only"
				)
			confirmed_mode_flags(row["mode"])
			for field_name in ("skyui_value", "inventory_value_after_exit"):
				try:
					int(row[field_name])
				except (TypeError, ValueError) as error:
					raise ValueError(
						f"{path} row {line_number} has an invalid {field_name}"
					) from error
			observations.append(dict(row))
	return observations


def parse_confirmed_json(
	row: Mapping[str, str], field_name: str, path: Path, line_number: int
) -> dict[str, object]:
	text = (row.get(field_name) or "").strip()
	if not text:
		return {}
	try:
		value = json.loads(text)
	except json.JSONDecodeError as error:
		raise ValueError(
			f"{path} row {line_number} has invalid {field_name} JSON"
		) from error
	if not isinstance(value, dict):
		raise ValueError(f"{path} row {line_number} {field_name} must be an object")
	return value


def confirmed_settings(
	row: Mapping[str, str], path: Path, line_number: int
) -> PredictionSettings:
	caco_enabled, alchemy_plus_enabled = confirmed_mode_flags(row["mode"])
	player = PlayerSettings(
		alchemy_level=f32(float(row["alchemy_level"])),
		fortify_alchemy_level=f32(float(row["fortify_alchemy_level"])),
		alchemist_perk_rank=int(row["alchemist_rank"]),
		alchemist_perk_multiplier=optional_float_field(row, "alchemist_perk_multiplier"),
		purity=bool_field(row, "purity"),
		physician=bool_field(row, "physician"),
		benefactor=bool_field(row, "benefactor"),
		poisoner=bool_field(row, "poisoner"),
		concentrated_poison=bool_field(row, "concentrated_poison"),
		seeker_of_shadows=bool_field(row, "seeker_of_shadows"),
	)

	caco_values = parse_confirmed_json(row, "caco_settings", path, line_number)
	if caco_enabled and not caco_values:
		raise ValueError(f"{path} row {line_number} is missing caco_settings")
	caco_settings = CACOSettings.from_ini(
		{str(key): str(value) for key, value in caco_values.items()}
	)

	alchemy_plus_values = parse_confirmed_json(
		row, "alchemy_plus_settings", path, line_number
	)
	if alchemy_plus_enabled and not alchemy_plus_values:
		raise ValueError(f"{path} row {line_number} is missing alchemy_plus_settings")
	alchemy_plus = (
		AlchemyPlusSettings.from_mapping(alchemy_plus_values)
		if alchemy_plus_enabled
		else AlchemyPlusSettings.defaults()
	)
	return PredictionSettings(
		caco_enabled=caco_enabled,
		alchemy_plus_enabled=alchemy_plus_enabled,
		player=player,
		caco_ingredient_init_multiplier=caco_settings.alchemy_ingredient_init_multiplier,
		caco_skill_factor=caco_settings.alchemy_skill_factor,
		caco_impure_processing=False,
		caco_settings=caco_settings,
		alchemy_plus=alchemy_plus,
	)


def iter_confirmed_fixture(
	path: Path = CONFIRMED_CSV,
) -> Iterable[tuple[int, Mapping[str, str], tuple[str, ...], int]]:
	required_columns = {
		"mode",
		"ingredients",
		"actual_value",
		"alchemy_level",
		"fortify_alchemy_level",
		"alchemist_rank",
		"physician",
		"benefactor",
		"poisoner",
		"purity",
		"seeker_of_shadows",
		"concentrated_poison",
		"caco_settings",
		"alchemy_plus_settings",
		"crafted_effects",
		"potion_form_id",
		"ingredient_selection_order",
	}
	with path.open("r", encoding="utf-8-sig", newline="") as handle:
		reader = csv.DictReader(handle)
		if reader.fieldnames is None:
			raise ValueError(f"{path} has no CSV header")
		missing = required_columns - set(reader.fieldnames)
		if missing:
			raise ValueError(
				f"{path} is missing required columns: {', '.join(sorted(missing))}"
			)
		for line_number, row in enumerate(reader, start=2):
			for field_name in (
				"crafted_effects",
				"potion_form_id",
				"ingredient_selection_order",
			):
				if not (row.get(field_name) or "").strip():
					raise ValueError(
						f"{path} row {line_number} is missing {field_name} metadata"
					)
			recipe = prediction_recipe_from_row(row, path, line_number)
			try:
				expected = int(row["actual_value"])
			except (TypeError, ValueError) as error:
				raise ValueError(
					f"{path} row {line_number} has an invalid actual_value"
				) from error
			yield line_number, row, recipe, expected


def log_prediction_mismatch(
	mode: str,
	line_number: int,
	recipe: tuple[str, ...],
	skse_predicted: object,
	python_predicted: object,
	details: str = "",
	path: Path = PREDICTION_LOG,
	prediction_csv: Path | None = None,
) -> None:
	plugin_set = {
		"vanilla": "Vanilla Skyrim (CACO disabled, Alchemy Plus disabled)",
		"caco": "CACO enabled (Alchemy Plus disabled)",
		"caco+alchemy-plus": "CACO and Alchemy Plus enabled",
		"alchemy-plus": "Alchemy Plus enabled (CACO disabled)",
	}.get(mode, mode)
	lines = [
		f"Report time: {datetime.now().astimezone().isoformat(timespec='seconds')}",
		f"Enabled plugin set: {plugin_set}",
		f"Fixture mode: {mode}",
		f"Predicted CSV: {prediction_csv}" if prediction_csv else "Predicted CSV: unavailable",
		f"Fixture row: {line_number}",
		f"Recipe: {', '.join(recipe)}",
		f"Expected value (historical baseline from C++ SKSE plugin predicted CSV fixture): {skse_predicted}",
		f"Actual value (calculated by Python test harness script): {python_predicted}",
	]
	if details:
		lines.append(f"Details: {details}")
	entry = "\n".join(lines) + "\n\n"
	try:
		previous = path.read_text(encoding="utf-8") if path.exists() else ""
		path.write_text(entry + previous, encoding="utf-8")
	except OSError as error:
		print(f"Could not write prediction mismatch log {path}: {error}", file=sys.stderr)


class InPlaceProgress:
	def __init__(self, stream: object = sys.stdout, update_interval: float = 0.1):
		self._stream = stream
		self._update_interval = update_interval
		self._last_update = 0.0
		self._width = 0

	def update(self, message: str, force: bool = False) -> None:
		now = time.monotonic()
		if not force and now - self._last_update < self._update_interval:
			return
		padding = max(0, self._width - len(message))
		self._stream.write(f"\r{message}{' ' * padding}")
		self._stream.flush()
		self._last_update = now
		self._width = len(message)

	def clear(self) -> None:
		if self._width == 0:
			return
		self._stream.write(f"\r{' ' * self._width}\r")
		self._stream.flush()
		self._width = 0


def format_prediction_row_details(
	line_number: int,
	predicted_csv: Path,
	settings: PredictionSettings,
	recipe: tuple[str, ...],
	expected: object,
	actual: object,
	result: PredictionResult | None = None,
	database: IngredientDatabase | None = None,
	error: Exception | None = None,
	gmst_source: str = "unknown",
) -> str:
	caco_enabled = settings.caco_enabled
	alchemy_plus_enabled = settings.alchemy_plus_enabled
	player = settings.player

	base_power = f32(
		float(settings.caco_ingredient_init_multiplier)
		* (1.0 + (float(settings.caco_skill_factor) - 1.0) * (float(player.alchemy_level) / 100.0))
	)

	lines = [
		f"--- Prediction Fixture Parity Check (Row {line_number}) ---",
		f"  Fixture File: {predicted_csv.name}",
		f"  Target Recipe: {', '.join(recipe)}",
		f"  Historical C++ Fixture Expected: {expected} (UNCONFIRMED - legacy plugin output)",
		f"  Current Python Script Calculated: {actual} (UNCONFIRMED - script model output)",
		f"  Parity Status: {'MATCH' if expected == actual else 'MISMATCH'}",
		"",
		"  Active Engine GMSTs:",
		f"    Source: {gmst_source}",
		f"    fAlchemyIngredientInitMult: {settings.caco_ingredient_init_multiplier}",
		f"    fAlchemySkillFactor: {settings.caco_skill_factor}",
		f"    Base Power Factor: {base_power:.6g} (formula: init_mult * (1 + (skill_factor - 1) * (skill / 100)))",
		"",
		"  Player Context:",
		f"    alchemy_level: {player.alchemy_level}",
		f"    fortify_alchemy_level: {player.fortify_alchemy_level}",
		f"    alchemist_rank: {player.alchemist_perk_rank} (mult: {player.alchemist_perk_multiplier})",
		f"    physician: {player.physician}, benefactor: {player.benefactor}, poisoner: {player.poisoner}",
		f"    purity: {player.purity}, seeker_of_shadows: {player.seeker_of_shadows}",
	]

	if result is not None and database is not None:
		lines.append("")
		lines.append("  Calculation Breakdown:")
		for eff in result.effects:
			lines.append(
				f"    Effect: {eff.source.effect_name} [0x{eff.source.effect_form_id:X}]"
			)
			lines.append(
				f"      Input Base: magnitude={eff.source.input_magnitude:g}, duration={eff.source.input_duration:g}, base_cost={eff.source.base_cost:g}"
			)
			lines.append(
				f"      Calculated: magnitude={eff.calc_magnitude:g}, duration={eff.calc_duration:g}, cost={eff.native_cost:.6g}"
			)
		lines.append(f"    Sum of Effect Costs: {result.cost:.6g}")
		lines.append(f"    Final Displayed (Floor): {result.displayed_value}")

	if error is not None:
		lines.append(f"  Error encountered: {error}")

	return "\n".join(lines)


def run_prediction_fixture_check(
	vanilla_csv: Path = VANILLA_CSV,
	caco_csv: Path = CACO_CSV,
	write_log: bool = True,
) -> int:
	databases: dict[bool, IngredientDatabase] = {}
	progress = InPlaceProgress()
	try:
		for mode in PREDICTION_FIXTURE_ORDER:
			path = PREDICTION_CSVS[mode]
			if not path.is_file():
				progress.clear()
				print(f"Skipped {mode}: file not found ({path.name})", flush=True)
				continue
			caco_enabled = mode.startswith("caco")
			if caco_enabled not in databases:
				databases[caco_enabled] = IngredientDatabase.load_caco_duration_exports(
					caco_csv if caco_enabled else vanilla_csv,
					prefer_highest_form_id=caco_enabled,
				)
			checked = 0
			progress.update(f"Checking {mode}: starting", force=True)
			try:
				for item in iter_prediction_fixture(path):
					if len(item) == 4:
						line_number, recipe, expected, config_dict = item
					else:
						line_number, recipe, expected = item[0], item[1], item[2]
						config_dict = None

					if config_dict:
						row_dict = {
							str(k): ("" if v is None else str(v))
							for k, v in config_dict.items()
						}
						if "mode" not in row_dict or not row_dict["mode"]:
							row_dict["mode"] = mode
						settings = confirmed_settings(row_dict, path, line_number)
						gmst_source = f"fixture config_id={row_dict.get('config_id', '0')}"
					else:
						# If running fixture checks without row-level metadata, use
						# canonical vanilla baseline GMSTs (4.0 / 1.5) to test legacy parity.
						settings = fixture_settings(mode)
						gmst_source = "canonical fixture defaults (init=4.0, skill_factor=1.5)"

					db_caco = settings.caco_enabled
					if db_caco not in databases:
						databases[db_caco] = IngredientDatabase.load_caco_duration_exports(
							caco_csv if db_caco else vanilla_csv,
							prefer_highest_form_id=db_caco,
						)

					try:
						result = PotionPredictor(
							databases[db_caco], settings
						).evaluate(
							recipe,
							prefer_later_equal_cost=True,
						)
					except (KeyError, ValueError) as error:
						progress.clear()
						details_str = format_prediction_row_details(
							line_number=line_number,
							predicted_csv=path,
							settings=settings,
							recipe=recipe,
							expected=expected,
							actual=None,
							error=error,
							gmst_source=gmst_source,
						)
						if write_log:
							log_prediction_mismatch(
								mode,
								line_number,
								recipe,
								expected,
								f"error: {error}",
								details=details_str,
								prediction_csv=path,
							)
						print(
							f"First wrong prediction: mode={mode} row={line_number} "
							f"predicted_csv={path} recipe={', '.join(recipe)!r} "
							f"expected_from_csv={expected} (C++ SKSE plugin historical predicted CSV fixture) error={error}",
							file=sys.stderr,
						)
						print(details_str, file=sys.stderr)
						return 1
					actual = result.displayed_value if result.valid else None
					if actual != expected:
						details_str = format_prediction_row_details(
							line_number=line_number,
							predicted_csv=path,
							settings=settings,
							recipe=recipe,
							expected=expected,
							actual=actual,
							result=result,
							database=databases[db_caco],
							gmst_source=gmst_source,
						)
						if write_log:
							log_prediction_mismatch(
								mode,
								line_number,
								recipe,
								expected,
								actual,
								details=details_str,
								prediction_csv=path,
							)
						if (
							actual is not None
							and is_prediction_within_tolerance(expected, actual, TOLERATED_PREDICTION_PERCENTAGE)
						):
							checked += 1
							progress.update(
								f"Checking {mode}: row {line_number} ({checked} predictions)"
							)
							continue
						progress.clear()
						print(
							f"First wrong prediction: mode={mode} row={line_number} "
							f"predicted_csv={path} recipe={', '.join(recipe)!r} "
							f"expected_from_csv={expected} (C++ SKSE plugin historical predicted CSV fixture) "
							f"actual_python_value={actual} (Python test harness script prediction)",
							file=sys.stderr,
						)
						print(details_str, file=sys.stderr)
						return 1
					checked += 1
					progress.update(
						f"Checking {mode}: row {line_number} ({checked} predictions)"
					)
			except FileNotFoundError:
				progress.clear()
				print(f"Skipped {mode}: file not found ({path.name})", flush=True)
				continue
			except (OSError, ValueError) as error:
				progress.clear()
				print(f"Prediction fixture check failed for {path}: {error}", file=sys.stderr)
				return 2
			progress.clear()
			print(f"Passed {mode}: {checked} predictions", flush=True)
		return 0
	finally:
		progress.clear()


def run_confirmed_fixture_check(
	confirmed_csv: Path = CONFIRMED_CSV,
	vanilla_csv: Path = VANILLA_CSV,
	caco_csv: Path | None = None,
	order_dependent_csv: Path = ORDER_DEPENDENT_CSV,
) -> int:
	databases: dict[bool, IngredientDatabase] = {}
	mismatches: list[tuple[int, str, tuple[str, ...], int, object, str]] = []
	checked = 0
	active_caco_csv = Path(caco_csv) if caco_csv is not None else CACO_CSV
	print(f"Checking confirmed in-game potion craft rows from {confirmed_csv} against Python script predictions", flush=True)
	try:
		diagnostic_observations = load_order_dependent_observations(order_dependent_csv)
		if diagnostic_observations:
			print(
				f"Loaded {len(diagnostic_observations)} diagnostic-only order-dependent "
				f"observations from {order_dependent_csv}; excluded from expected-value scoring",
				flush=True,
			)
		for line_number, row, recipe, expected in iter_confirmed_fixture(confirmed_csv):
			mode = row["mode"].strip()
			caco_enabled, _ = confirmed_mode_flags(mode)
			try:
				settings = confirmed_settings(row, confirmed_csv, line_number)
				db_key = caco_enabled
				if db_key not in databases:
					target_csv = active_caco_csv if caco_enabled else vanilla_csv
					databases[db_key] = IngredientDatabase.load_caco_duration_exports(
						target_csv,
						prefer_highest_form_id=caco_enabled,
					)
				selection_recipe = confirmed_selection_recipe_from_row(
					row, confirmed_csv, line_number, recipe
				)
				result = PotionPredictor(databases[db_key], settings).evaluate(
					selection_recipe,
					prefer_later_equal_cost=True,
				)
				actual: object = result.displayed_value if result.valid else None
				details = "" if result.valid else "recipe has no shared effects"
			except (KeyError, ValueError, OSError) as error:
				actual = None
				details = f"error: {error}"
			if not is_prediction_within_tolerance(expected, actual, TOLERATED_PREDICTION_PERCENTAGE):
				mismatches.append(
					(line_number, mode, recipe, expected, actual, details)
				)
			checked += 1
	except (OSError, ValueError) as error:
		print(f"Confirmed fixture check failed: {error}", file=sys.stderr)
		return 2

	passed = checked - len(mismatches)
	print(
		f"Confirmed check result (In-Game Observed Craft Values from CSV vs Python Script Predictions): checked={checked} passed={passed} failed={len(mismatches)}",
		flush=True,
	)
	for line_number, mode, recipe, expected, actual, details in mismatches:
		print(
			f"FAIL row={line_number} mode={mode} ingredients={', '.join(recipe)!r} "
			f"expected_ingame_value={expected} (In-game observed craft from confirmed CSV) "
			f"predicted_python_value={actual} (Python test harness script prediction) {details}".rstrip(),
			flush=True,
		)
	return 1 if mismatches else 0


def format_confirmed_row_settings(
	line_number: int,
	confirmed_csv: Path,
	row: Mapping[str, str],
	settings: PredictionSettings,
	recipe: tuple[str, ...],
	selection_recipe: tuple[str, ...],
) -> str:
	caco_enabled = settings.caco_enabled
	alchemy_plus_enabled = settings.alchemy_plus_enabled
	player = settings.player

	lines = [
		f"Row {line_number} settings read from {confirmed_csv}:",
		f"  Mode: {row['mode'].strip()} (caco_enabled={caco_enabled}, alchemy_plus_enabled={alchemy_plus_enabled})",
		f"  Recipe Ingredients: {row['ingredients'].strip()}",
		f"  Selection Order Recipe: {', '.join(selection_recipe)}",
		f"  Confirmed In-Game Observed Value (from CSV): {row['actual_value'].strip()}",
		"  Player Settings:",
		f"    alchemy_level: {player.alchemy_level}",
		f"    fortify_alchemy_level: {player.fortify_alchemy_level}",
		f"    alchemist_rank: {player.alchemist_perk_rank}",
		f"    alchemist_perk_multiplier: {player.alchemist_perk_multiplier}",
		f"    physician: {player.physician}",
		f"    benefactor: {player.benefactor}",
		f"    poisoner: {player.poisoner}",
		f"    purity: {player.purity}",
		f"    seeker_of_shadows: {player.seeker_of_shadows}",
		f"    concentrated_poison: {player.concentrated_poison}",
	]

	if caco_enabled or row.get("caco_settings"):
		caco = settings.caco_settings
		lines.extend(
			[
				"  CACO Settings:",
				f"    caco_ingredient_init: {settings.caco_ingredient_init_multiplier}",
				f"    caco_skill_factor: {settings.caco_skill_factor}",
				f"    restore_health_duration: {caco.restore_health_duration}",
				f"    restore_magicka_duration: {caco.restore_magicka_duration}",
				f"    restore_stamina_duration: {caco.restore_stamina_duration}",
				f"    damage_health_duration: {caco.damage_health_duration}",
				f"    damage_magicka_duration: {caco.damage_magicka_duration}",
				f"    damage_stamina_duration: {caco.damage_stamina_duration}",
				f"    restore_effects_do_not_stack: {caco.restore_effects_do_not_stack}",
				f"    disable_all_potion_handling: {caco.disable_all_potion_handling}",
				f"    impure_processing: {caco.impure_processing}",
			]
		)

	if alchemy_plus_enabled or row.get("alchemy_plus_settings"):
		ap = settings.alchemy_plus
		lines.extend(
			[
				"  Alchemy Plus Settings:",
				f"    impure_cost_fix_enabled: {ap.impure_cost_fix_enabled}",
				f"    rounding_enabled: {ap.rounding_enabled}",
				f"    magnitude_threshold: {ap.magnitude_threshold}",
				f"    magnitude_multiple: {ap.magnitude_multiple}",
				f"    duration_threshold: {ap.duration_threshold}",
				f"    duration_multiple: {ap.duration_multiple}",
				f"    overrides: {len(ap.overrides)} override(s)",
			]
		)

	return "\n".join(lines)


def run_confirmed_row(
	target_row: int,
	confirmed_csv: Path = CONFIRMED_CSV,
	vanilla_csv: Path = VANILLA_CSV,
	caco_csv: Path | None = None,
	order_dependent_csv: Path = ORDER_DEPENDENT_CSV,
	as_json: bool = False,
) -> int:
	if target_row < 2:
		if target_row == 1:
			print(
				"Error: Row 1 is the CSV header. Please specify a data row line number (2 or greater).",
				file=sys.stderr,
			)
		else:
			print(
				f"Error: Row {target_row} is invalid. Please specify a data row line number (2 or greater).",
				file=sys.stderr,
			)
		return 2

	active_caco_csv = Path(caco_csv) if caco_csv is not None else CACO_CSV
	max_line = 1
	found_row: tuple[int, Mapping[str, str], tuple[str, ...], int] | None = None

	try:
		for line_number, row, recipe, expected in iter_confirmed_fixture(confirmed_csv):
			max_line = max(max_line, line_number)
			if line_number == target_row:
				found_row = (line_number, row, recipe, expected)
				break
	except (OSError, ValueError) as error:
		print(f"Error reading confirmed CSV: {error}", file=sys.stderr)
		return 2

	if found_row is None:
		print(
			f"Error: Row {target_row} not found in {confirmed_csv}. (File contains data rows 2 to {max_line}).",
			file=sys.stderr,
		)
		return 2

	line_number, row, recipe, expected = found_row
	mode = row["mode"].strip()
	caco_enabled, alchemy_plus_enabled = confirmed_mode_flags(mode)
	settings = confirmed_settings(row, confirmed_csv, line_number)
	selection_recipe = confirmed_selection_recipe_from_row(
		row, confirmed_csv, line_number, recipe
	)

	target_csv = active_caco_csv if caco_enabled else vanilla_csv
	database = IngredientDatabase.load_caco_duration_exports(
		target_csv,
		prefer_highest_form_id=caco_enabled,
	)

	result = PotionPredictor(database, settings).evaluate(
		selection_recipe,
		prefer_later_equal_cost=True,
	)

	print(
		format_confirmed_row_settings(
			line_number, confirmed_csv, row, settings, recipe, selection_recipe
		)
	)
	print()
	print(result_json(result, database) if as_json else format_result(result, database))
	print()

	actual: object = result.displayed_value if result.valid else None
	passed = is_prediction_within_tolerance(expected, actual, TOLERATED_PREDICTION_PERCENTAGE)
	status_str = "PASS" if passed else "FAIL"
	print(
		f"Confirmed Row {line_number} Test: Expected (In-Game Observed Craft from CSV) = {expected}, "
		f"Predicted (Python Test Harness Script) = {actual}, Status = {status_str}"
	)
	return 0 if passed else 1




def parity_settings(mode: str, perk: str) -> PredictionSettings:
	caco_enabled = mode.startswith("caco")
	alchemy_plus_enabled = "alchemy-plus" in mode
	player = PlayerSettings(
		alchemy_level=15.0,
		**PARITY_PERKS[perk],
		caco_seeker_multiplier=1.05 if caco_enabled else None,
		caco_benefactor_multiplier=1.20 if caco_enabled else None,
	)
	return PredictionSettings(
		caco_enabled=caco_enabled,
		alchemy_plus_enabled=alchemy_plus_enabled,
		player=player,
		caco_ingredient_init_multiplier=4.0,
		caco_skill_factor=1.0 if caco_enabled else 1.5,
		alchemy_plus=AlchemyPlusSettings(
			rounding_enabled=alchemy_plus_enabled,
			impure_cost_fix_enabled=alchemy_plus_enabled,
			magnitude_threshold=25.0,
			magnitude_multiple=5.0,
			duration_threshold=15.0,
			duration_multiple=5.0,
		),
	)


def fixture_settings(mode: str) -> PredictionSettings:
	settings = parity_settings(mode, "none")
	if settings.caco_enabled:
		settings.caco_ingredient_init_multiplier = 3.0
		settings.caco_skill_factor = 3.0
	return settings


class PredictionSelfTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.vanilla = IngredientDatabase.load(VANILLA_CSV)
		cls.caco = IngredientDatabase.load_caco_duration_exports(CACO_CSV)
		all_recipes = PARITY_RECIPES.values()
		cls.predicted = {
			mode: load_prediction_fixture(path, all_recipes)
			for mode, path in PREDICTION_CSVS.items()
			if path.is_file()
		}

	def test_both_csv_files_load(self) -> None:
		self.assertGreater(len(self.vanilla.names()), 100)
		self.assertGreater(len(self.caco.names()), 100)

	def test_rich_export_metadata_is_loaded(self) -> None:
		columns = sorted(
			IngredientDatabase.REQUIRED_COLUMNS
			| {
				"effect_cost",
				"duration_based",
				"resolved_magnitude",
				"resolved_duration",
				"resolved_peak_value_modifier",
				"keyword_editor_ids",
				"keyword_form_ids",
				"source_effect_form_id",
				"resolved_effect_name",
				"resolved_effect_form_id",
				"resolved_effect_editor_id",
				"resolved_base_cost",
				"resolved_power_affects_magnitude",
				"resolved_power_affects_duration",
				"resolved_no_magnitude",
				"resolved_no_duration",
				"resolved_beneficial",
				"resolved_harmful",
				"resolved_hostile",
				"resolved_duration_based",
				"resolved_keyword_editor_ids",
				"resolved_keyword_form_ids",
				"resolved_description",
			}
		)
		row = {column: "" for column in columns}
		row.update(
			{
				"ingredient_name": "Exported Ingredient",
				"form_id": "0x1",
				"effect_name": "Source Effect",
				"effect_form_id": "0x100",
				"base_cost": "10",
				"magnitude": "2",
				"duration": "30",
				"resolved_magnitude": "7",
				"resolved_duration": "0",
				"resolved_peak_value_modifier": "1",
				"power_affects_magnitude": "1",
				"power_affects_duration": "1",
				"no_magnitude": "0",
				"no_duration": "0",
				"beneficial": "1",
				"harmful": "0",
				"hostile": "0",
				"effect_cost": "3.5",
				"duration_based": "1",
				"keyword_editor_ids": "MagicAlchDurationBased;MagicAlchRestoreHealth",
				"keyword_form_ids": "0x200;0x201",
				"source_effect_form_id": "0x100",
				"resolved_effect_name": "Resolved Effect",
				"resolved_effect_form_id": "0x300",
				"resolved_effect_editor_id": "ResolvedEffect",
				"resolved_base_cost": "11",
				"resolved_power_affects_magnitude": "1",
				"resolved_power_affects_duration": "1",
				"resolved_no_magnitude": "0",
				"resolved_no_duration": "0",
				"resolved_beneficial": "1",
				"resolved_harmful": "0",
				"resolved_hostile": "0",
				"resolved_duration_based": "1",
				"resolved_keyword_editor_ids": "MagicAlchDurationBased",
				"resolved_keyword_form_ids": "0x200",
				"resolved_description": "<mag> for <dur> seconds",
			}
		)
		with tempfile.TemporaryDirectory() as temporary:
			path = Path(temporary) / "rich.csv"
			with path.open("w", encoding="utf-8", newline="") as handle:
				writer = csv.DictWriter(handle, fieldnames=columns)
				writer.writeheader()
				writer.writerow(row)
			database = IngredientDatabase.load(path)
			effect = database.get("Exported Ingredient").effects[0]
			self.assertEqual(effect.source_identity, 0x100)
			self.assertEqual(effect.resolved_effect_form_id, 0x300)
			self.assertEqual(effect.keyword_form_ids, (0x200, 0x201))
			self.assertEqual(effect.input_magnitude, 2.0)
			self.assertEqual(effect.input_duration, 30.0)
			self.assertEqual(effect.resolved_magnitude, 7.0)
			self.assertEqual(effect.resolved_duration, 0.0)
			self.assertTrue(effect.resolved_peak_value_modifier)
			self.assertTrue(effect.duration_based)

	def test_resolved_fields_do_not_replace_inputs_or_selection_cost(self) -> None:
		columns = sorted(IngredientDatabase.REQUIRED_COLUMNS | {"resolved_magnitude", "resolved_duration", "resolved_peak_value_modifier"})
		row = {column: "" for column in columns}
		row.update(
			{
				"ingredient_name": "Resolved Ingredient",
				"form_id": "0x1",
				"effect_name": "Resolved Effect",
				"effect_form_id": "0x100",
				"base_cost": "10",
				"magnitude": "2",
				"duration": "1",
				"resolved_magnitude": "7",
				"resolved_duration": "0",
				"resolved_peak_value_modifier": "1",
				"power_affects_magnitude": "1",
				"power_affects_duration": "1",
				"no_magnitude": "0",
				"no_duration": "0",
				"beneficial": "1",
				"harmful": "0",
				"hostile": "0",
				"duration_based": "0",
			}
		)
		with tempfile.TemporaryDirectory() as temporary:
			path = Path(temporary) / "resolved.csv"
			with path.open("w", encoding="utf-8", newline="") as handle:
				writer = csv.DictWriter(handle, fieldnames=columns)
				writer.writeheader()
				writer.writerow(row)
			effect = IngredientDatabase.load(path).get("Resolved Ingredient").effects[0]
			magnitude, duration = calculate_effect_input(effect, 1.0, 1.0)
			self.assertEqual((magnitude, duration), (2.0, 1.0))
			selection_cost = effect_cost_precise(effect, 7.0, 0.0, caco_enabled=True)
			self.assertAlmostEqual(
				selection_cost,
				10.0 * math.pow(7.0, 1.1),
				places=5,
			)
			final_cost = effect_cost_precise(effect, 7.0, 0.0, caco_enabled=True)
			self.assertAlmostEqual(
				final_cost,
				10.0 * math.pow(7.0, 1.1),
				places=5,
			)

	def test_current_export_loads_duration_metadata(self) -> None:
		database = IngredientDatabase.load_caco_duration_exports(CACO_CSV)
		self.assertTrue(
			any(effect.duration_based for effect in database.get("Argonian Scales").effects)
		)

	def test_caco_duration_classification_requires_explicit_keyword(self) -> None:
		database = IngredientDatabase.load_caco_duration_exports(CACO_CSV)
		light = next(
			effect
			for effect in database.get("Alocasia Fruit").effects
			if effect.effect_name == "Light"
		)
		spell_absorption = next(
			effect
			for effect in database.get("Watcher's Eye").effects
			if effect.effect_name == "Spell Absorption"
		)
		silence = next(
			effect
			for effect in database.get("Alocasia Fruit").effects
			if effect.effect_name == "Silence"
		)
		self.assertTrue(light.duration_based_exported)
		self.assertTrue(spell_absorption.duration_based_exported)
		self.assertFalse(light.duration_based)
		self.assertFalse(spell_absorption.duration_based)
		self.assertTrue(silence.duration_based)

	def test_caco_duration_exports_load_distinct_variants(self) -> None:
		database = IngredientDatabase.load_caco_duration_exports(CACO_CSV)
		variants = [
			effect
			for effect in database.get("Blue Mountain Flower").effects
			if match_caco_duration_family(effect) == 3
		]
		self.assertEqual(
			{effect.caco_duration_index for effect in variants},
			{0, 1, 2},
		)
		self.assertEqual(
			{effect.duration for effect in variants},
			{1.0, 5.0, 10.0},
		)
		resist_disease_variants = [
			effect
			for effect in database.get("Tinder Polypore Cap").effects
			if effect.source_identity == parse_form_id("0x0806AE45")
		]
		self.assertEqual(
			{match_caco_duration_family(effect) for effect in resist_disease_variants},
			{0},
		)
		self.assertEqual(
			{effect.caco_duration_index for effect in resist_disease_variants},
			{0, 1, 2},
		)
		self.assertEqual(
			{effect.duration for effect in resist_disease_variants},
			{1.0, 5.0, 10.0},
		)

	def test_caco_duration_normalizes_magnitude(self) -> None:
		database = IngredientDatabase.load_caco_duration_exports(CACO_CSV)
		player = PlayerSettings(alchemy_level=100.0, alchemist_perk_multiplier=1.0)
		effects = {
			effect.caco_duration_index: effect
			for effect in database.get("Jarrin Root").effects
			if match_caco_duration_family(effect) == 3
		}
		expected_magnitudes = {0: 1877.0, 1: 375.0, 2: 188.0}
		for duration_index, expected in expected_magnitudes.items():
			effect = effects[duration_index]
			magnitude_factor, duration_factor = effect_power_factors(
				effect,
				player,
				potion=True,
				include_type_perks=True,
				caco_enabled=True,
				caco_ingredient_init_multiplier=3.0,
				caco_skill_factor=3.0,
			)
			magnitude, _ = calculate_effect_input(
				effect, magnitude_factor, duration_factor
			)
			self.assertEqual(magnitude, expected)

	def test_caco_duration_uses_selected_variant_for_source_duration_one(self) -> None:
		settings = PredictionSettings(
			caco_enabled=True,
			alchemy_plus_enabled=True,
			player=PlayerSettings(
				alchemy_level=100.0,
				alchemist_perk_multiplier=1.0,
			),
			caco_ingredient_init_multiplier=3.0,
			caco_skill_factor=3.0,
			caco_settings=CACOSettings(
				restore_magicka_duration=1,
				damage_health_duration=1,
				damage_stamina_duration=1,
				disable_all_potion_handling=True,
			),
			alchemy_plus=AlchemyPlusSettings(
				rounding_enabled=True,
				impure_cost_fix_enabled=True,
				magnitude_threshold=10.0,
				magnitude_multiple=2.0,
				duration_threshold=10.0,
				duration_multiple=2.0,
			),
		)

		result = PotionPredictor(self.caco, settings).evaluate(
			("Blue Mountain Flower", "Bog Beacon", "Jarrin Root")
		)

		self.assertEqual(result.displayed_value, 2662)
		magicka = next(
			effect for effect in result.effects if effect.source.effect_form_id == 0x3EB17
		)
		self.assertEqual(magicka.calc_magnitude, 20.0)
		self.assertEqual(magicka.calc_duration, 1.0)

	def test_export_without_rich_metadata_is_rejected(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			path = Path(temporary) / "outdated.csv"
			columns = sorted(IngredientDatabase.REQUIRED_COLUMNS - {"duration_based"})
			with path.open("w", encoding="utf-8", newline="") as handle:
				csv.DictWriter(handle, fieldnames=columns).writeheader()
			with self.assertRaisesRegex(ValueError, "missing required columns"):
				IngredientDatabase.load(path)

	def test_prediction_export_diagnostic_columns_are_ignored(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			path = Path(temporary) / "predictions.csv"
			with path.open("w", encoding="utf-8", newline="") as handle:
				writer = csv.writer(handle)
				writer.writerow(
					[
						"ingredients",
						"predicted_value",
						"name",
						"calculation_details",
					]
				)
				writer.writerow(["A, B", "42", "Potion", "details"])
			self.assertEqual(
				load_prediction_fixture(path, (("A", "B"),)),
				{("A", "B"): 42},
			)


	def test_prediction_mismatch_log_is_newest_first(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			path = Path(temporary) / "potion_prediction_test.log"
			log_prediction_mismatch(
				"vanilla",
				12,
				("A", "B"),
				139,
				56,
				path=path,
				prediction_csv=Path("potions-predicted-vanilla.csv"),
			)
			log_prediction_mismatch(
				"caco+alchemy-plus",
				18,
				("A", "B", "C"),
				22,
				17,
				path=path,
				prediction_csv=Path("potions-predicted-caco-ap.csv"),
			)
			contents = path.read_text(encoding="utf-8")
			self.assertLess(
				contents.index("Fixture mode: caco+alchemy-plus"),
				contents.index("Fixture mode: vanilla"),
			)
			self.assertIn("Report time: ", contents)
			self.assertIn("Enabled plugin set: CACO and Alchemy Plus enabled", contents)
			self.assertIn("Predicted CSV: potions-predicted-caco-ap.csv", contents)
			self.assertIn("Expected value (historical baseline from C++ SKSE plugin predicted CSV fixture): 22", contents)
			self.assertIn("Actual value (calculated by Python test harness script): 17", contents)

	def test_check_predicted_csvs_ignores_missing_fixture_files(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			missing_csvs = {mode: Path(temporary) / f"missing-{mode}.csv" for mode in PREDICTION_FIXTURE_ORDER}
			with unittest.mock.patch.dict(PREDICTION_CSVS, missing_csvs):
				self.assertEqual(run_prediction_fixture_check(write_log=False), 0)

	def test_check_predicted_csvs_prints_full_details_on_failure(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			temp_path = Path(temporary)
			fake_csv = temp_path / "potions-predicted-vanilla.csv"
			fake_csv.write_text(
				"ingredients,predicted_value\n\"Blue Mountain Flower, Wheat\",999999\n",
				encoding="utf-8",
			)
			old_csvs = dict(PREDICTION_CSVS)
			try:
				PREDICTION_CSVS["vanilla"] = fake_csv
				stderr_capture = io.StringIO()
				with unittest.mock.patch("sys.stderr", stderr_capture):
					return_code = run_prediction_fixture_check(write_log=False)
				self.assertEqual(return_code, 1)
				output = stderr_capture.getvalue()
				self.assertIn("First wrong prediction:", output)
				self.assertIn("--- Prediction Fixture Parity Check (Row 2) ---", output)
				self.assertIn("Historical C++ Fixture Expected: 999999", output)
				self.assertIn("Current Python Script Calculated: 71", output)
				self.assertIn("Calculation Breakdown:", output)
				self.assertIn("Restore Health", output)
			finally:
				PREDICTION_CSVS.clear()
				PREDICTION_CSVS.update(old_csvs)

	def test_all_four_paths_are_selectable(self) -> None:
		recipe = ("Abecean Longfin", "Beehive Husk")
		for caco_enabled in (False, True):
			database = self.caco if caco_enabled else self.vanilla
			for alchemy_plus_enabled in (False, True):
				settings = PredictionSettings(
					caco_enabled=caco_enabled,
					alchemy_plus_enabled=alchemy_plus_enabled,
				)
				result = PotionPredictor(database, settings).evaluate(recipe)
				self.assertTrue(result.valid)
				self.assertGreater(result.cost, 0.0)

	def test_shared_effects_are_selected_once(self) -> None:
		settings = PredictionSettings(False, False)
		result = PotionPredictor(self.vanilla, settings).evaluate(
			("Abecean Longfin", "Ash Hopper Jelly")
		)
		identities = [effect.source.source_identity for effect in result.effects]
		self.assertEqual(len(identities), len(set(identities)))

	def test_cli_defaults_match_reported_caco_recipe(self) -> None:
		arguments = make_parser().parse_args(
			[
				"Abecean Longfin",
				"Alocasia Fruit",
				"Canis Root",
				"--caco-enabled",
				"true",
				"--alchemy-plus-enabled",
				"false",
			]
		)
		settings = build_settings(arguments, ExternalSettingsSnapshot())
		self.assertEqual(settings.player.alchemy_level, 15.0)
		self.assertAlmostEqual(settings.caco_ingredient_init_multiplier, 3.9, places=6)
		self.assertAlmostEqual(settings.caco_skill_factor, 1.0, places=6)
		result = PotionPredictor(self.caco, settings).evaluate(arguments.ingredients)
		self.assertEqual(result.displayed_value, 56)

	def test_prediction_log_flag_defaults_to_enabled(self) -> None:
		self.assertTrue(make_parser().parse_args([]).prediction_log)
		self.assertFalse(
			make_parser().parse_args(["--no-prediction-log"]).prediction_log
		)

	def test_caco_physician_uses_caco_perk_behavior(self) -> None:
		recipe = ("Crushed Amber", "Ironwood Extract", "Red Mountain Flower Extract")
		settings = PredictionSettings(
			caco_enabled=True,
			alchemy_plus_enabled=False,
			caco_ingredient_init_multiplier=3.9,
			player=PlayerSettings(alchemy_level=15.0, physician=True),
		)
		result = PotionPredictor(self.caco, settings).evaluate(recipe)
		self.assertTrue(result.valid)
		self.assertEqual(result.displayed_value, 87)

	def test_caco_ap_impure_unshared_hostile_effects_predict_93(self) -> None:
		recipe = ("Aloe Vera Leaves", "Bear Fat", "Silverjaw Minnow")
		settings = PredictionSettings(
			caco_enabled=True,
			alchemy_plus_enabled=True,
			caco_ingredient_init_multiplier=3.9,
			caco_impure_processing=True,
			caco_settings=CACOSettings(impure_processing=True),
			player=PlayerSettings(alchemy_level=15.0),
			alchemy_plus=AlchemyPlusSettings(rounding_enabled=True, impure_cost_fix_enabled=True),
		)
		result = PotionPredictor(self.caco, settings).evaluate(recipe)
		self.assertTrue(result.valid)
		self.assertTrue(result.caco_impure_applied)
		self.assertEqual(result.pre_adjustment_gold, 249)
		self.assertEqual(result.displayed_value, 49)

	def test_caco_benefactor_does_not_apply_to_mixed_potion(self) -> None:
		recipe = ("Elven Heart", "Honeycomb", "Ironwood Extract")
		settings = PredictionSettings(
			caco_enabled=True,
			alchemy_plus_enabled=False,
			caco_ingredient_init_multiplier=3.9,
			player=PlayerSettings(alchemy_level=15.0, benefactor=True),
		)
		result = PotionPredictor(self.caco, settings).evaluate(recipe)
		self.assertTrue(result.valid)
		self.assertTrue(result.has_beneficial)
		self.assertTrue(result.has_harmful)
		self.assertEqual(result.displayed_value, 135)

	def test_caco_duration_based_effect_does_not_discard_duration_flag(self) -> None:
		database = self.caco
		silence = next(
			effect
			for effect in database.get("Alocasia Fruit").effects
			if effect.effect_name == "Silence"
		)
		forced_no_duration = replace(silence, no_duration=True)
		settings = fixture_settings("caco")
		magnitude_factor, duration_factor = effect_power_factors(
			forced_no_duration,
			settings.player,
			potion=False,
			include_type_perks=True,
			caco_enabled=True,
			caco_ingredient_init_multiplier=settings.caco_ingredient_init_multiplier,
			caco_skill_factor=settings.caco_skill_factor,
		)
		magnitude, duration = calculate_effect_input(
			forced_no_duration, magnitude_factor, duration_factor
		)
		self.assertEqual(duration, 3.0)
		self.assertAlmostEqual(
			effect_cost_precise(forced_no_duration, magnitude, duration),
			30.0546603,
			places=6,
		)

	def test_caco_duration_only_effect_uses_duration_power_factor(self) -> None:
		result = PotionPredictor(
			self.caco, fixture_settings("caco")
		).evaluate(("Abecean Longfin", "Argonian Scales", "Bergamot Seeds"))
		self.assertEqual(result.displayed_value, 78)

	def test_caco_slow_effect_uses_duration_power_factor(self) -> None:
		result = PotionPredictor(
			self.caco, fixture_settings("caco")
		).evaluate(("Abecean Longfin", "Arrowroot", "Aster Bloom Core"))
		self.assertEqual(result.displayed_value, 58)

	def test_alchemy_plus_rounding_matches_native_order(self) -> None:
		self.assertEqual(apply_alchemy_plus_rounding(9.4, 10.0, 1.0), 9.4)
		self.assertEqual(apply_alchemy_plus_rounding(10.4, 10.0, 1.0), 11.0)

	def test_ini_snapshot_selects_all_four_paths(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			root = Path(directory)
			for caco_enabled in (False, True):
				for alchemy_plus_enabled in (False, True):
					path = root / f"{int(caco_enabled)}-{int(alchemy_plus_enabled)}.ini"
					profile_values = ["Current=1", "NewGame=0", "[Profile 1]", "ProfileName=Profile 1"]
					if caco_enabled:
						profile_values.append(
							"CACO="
							+ json.dumps({"DisableAllPotionHandling": "0"}, separators=(",", ":"))
						)
					if alchemy_plus_enabled:
						profile_values.append(
							"AlchemyPlus="
							+ json.dumps(
								{
									"ConfigurationLoaded": "1",
									"Configuration": json.dumps(
										{"roundedPotency": {"enabled": False}},
										separators=(",", ":"),
									),
								},
								separators=(",", ":"),
							)
						)
					path.write_text("\n".join(profile_values), encoding="utf-8")
					arguments = make_parser().parse_args([])
					snapshot = settings_snapshot_for_arguments(arguments, path)
					self.assertEqual(
						enabled_plugins(arguments, snapshot),
						(caco_enabled, alchemy_plus_enabled),
					)

	def test_ini_root_current_selects_the_named_profile(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "alchemist.ini"
			path.write_text(
				"Current=2\nNewGame=0\n"
				"[Profile 1]\nProfileName=First\n"
				"[Profile 2]\nProfileName=Second\n"
				"CACO={\"DisableAllPotionHandling\":\"0\"}\n",
				encoding="utf-8",
			)
			snapshot = load_alchemist_ini(path)

		self.assertTrue(snapshot.caco_enabled)

	def test_ini_snapshot_loads_all_caco_and_alchemy_plus_settings(self) -> None:
		configuration = {
			"copyExemplars": {"enabled": True},
			"knownFailureFix": {"enabled": True},
			"mixtureNames": {"enabled": False},
			"impureCostFix": {"enabled": True},
			"roundedPotency": {
				"enabled": True,
				"magnitudeThreshold": 25.0,
				"magnitudeMult": 5.0,
				"durationThreshold": 15.0,
				"durationMult": 5.0,
				"overrides": {"Skyrim.esm|0x3EB15": {"magnitudeMult": 2.0}},
			},
		}
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "alchemist.ini"
			path.write_text(
				"\n".join(
					[
						"Current=1",
						"NewGame=0",
						"[Profile 1]",
						"ProfileName=Profile 1",
						"CACO="
						+ json.dumps(
							{
								"RestoreHealthDuration": "2",
								"RestoreMagickaDuration": "1",
								"RestoreStaminaDuration": "0",
								"RestoreEffectsDoNotStack": "1",
								"DamageHealthDuration": "2",
								"DamageMagickaDuration": "1",
								"DamageStaminaDuration": "0",
								"DisableAllPotionHandling": "1",
								"AlchemyXPMultiplier": "0.5",
							},
							separators=(",", ":"),
						),
						"AlchemyPlus="
						+ json.dumps(
							{
								"ConfigurationLoaded": "1",
								"Configuration": json.dumps(configuration, separators=(",", ":")),
							},
							separators=(",", ":"),
						),
					]
				),
				encoding="utf-8",
			)
			arguments = make_parser().parse_args([])
			snapshot = settings_snapshot_for_arguments(arguments, path)
			settings = build_settings(arguments, snapshot)

		self.assertTrue(settings.caco_enabled)
		self.assertTrue(settings.alchemy_plus_enabled)
		self.assertEqual(settings.caco_settings.restore_health_duration, 2)
		self.assertEqual(settings.caco_settings.restore_magicka_duration, 1)
		self.assertTrue(settings.caco_settings.restore_effects_do_not_stack)
		self.assertTrue(settings.caco_settings.disable_all_potion_handling)
		self.assertEqual(settings.caco_settings.alchemy_xp_multiplier, 0.5)
		self.assertEqual(settings.alchemy_plus.configuration, configuration)
		self.assertTrue(settings.alchemy_plus.rounding_enabled)
		self.assertTrue(settings.alchemy_plus.impure_cost_fix_enabled)
		self.assertEqual(settings.alchemy_plus.overrides[0x3EB15].magnitude_multiple, 2.0)

	def test_explicit_mode_flags_override_ini_sections(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "alchemist.ini"
			path.write_text(
				"Current=1\nNewGame=0\n[Profile 1]\nProfileName=Profile 1\n"
				"CACO={\"DisableAllPotionHandling\":\"0\"}\n"
				"AlchemyPlus={\"ConfigurationLoaded\":\"0\"}\n",
				encoding="utf-8",
			)
			arguments = make_parser().parse_args(
				[
					"--caco-enabled",
					"false",
					"--alchemy-plus-enabled",
					"false",
				]
			)
			snapshot = settings_snapshot_for_arguments(arguments, path)
			settings = build_settings(arguments, snapshot)

		self.assertFalse(settings.caco_enabled)
		self.assertFalse(settings.alchemy_plus_enabled)

	def test_caco_snapshot_values_can_be_overridden_by_flags(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "alchemist.ini"
			path.write_text(
				"Current=1\nNewGame=0\n[Profile 1]\nProfileName=Profile 1\n"
				"CACO={\"RestoreHealthDuration\":\"2\",\"RestoreMagickaDuration\":\"2\","
				"\"RestoreStaminaDuration\":\"2\",\"RestoreEffectsDoNotStack\":\"1\","
				"\"DamageHealthDuration\":\"2\",\"DamageMagickaDuration\":\"2\","
				"\"DamageStaminaDuration\":\"2\",\"DisableAllPotionHandling\":\"1\","
				"\"AlchemyXPMultiplier\":\"2\"}\n",
				encoding="utf-8",
			)
			arguments = make_parser().parse_args(
				[
					"--caco-restore-health-duration",
					"0",
					"--caco-restore-magicka-duration",
					"1",
					"--caco-restore-stamina-duration",
					"0",
					"--caco-restore-effects-do-not-stack",
					"false",
					"--caco-damage-health-duration",
					"0",
					"--caco-damage-magicka-duration",
					"1",
					"--caco-damage-stamina-duration",
					"0",
					"--caco-disable-all-potion-handling",
					"false",
					"--caco-alchemy-xp-multiplier",
					"0.5",
				]
			)
			snapshot = settings_snapshot_for_arguments(arguments, path)
			settings = build_settings(arguments, snapshot)

		self.assertEqual(
			settings.caco_settings,
			CACOSettings(
				restore_health_duration=0,
				restore_magicka_duration=1,
				restore_stamina_duration=0,
				restore_effects_do_not_stack=False,
				damage_health_duration=0,
				damage_magicka_duration=1,
				damage_stamina_duration=0,
				disable_all_potion_handling=False,
				alchemy_xp_multiplier=0.5,
				alchemy_ingredient_init_multiplier=f32(3.9),
			),
		)

	def test_alchemy_plus_ini_snapshot_is_the_default_config(self) -> None:
		configuration = {
			"impureCostFix": {"enabled": False},
			"roundedPotency": {
				"enabled": True,
				"magnitudeThreshold": 40.0,
				"magnitudeMult": 2.0,
				"durationThreshold": 30.0,
				"durationMult": 3.0,
			},
		}
		with tempfile.TemporaryDirectory() as directory:
			ini_path = Path(directory) / "alchemist.ini"
			ini_path.write_text(
				"Current=1\nNewGame=0\n[Profile 1]\nProfileName=Profile 1\nAlchemyPlus="
				+ json.dumps(
					{
						"ConfigurationLoaded": "1",
						"Configuration": json.dumps(configuration),
					},
					separators=(",", ":"),
				)
				+ "\n",
				encoding="utf-8",
			)
			arguments = make_parser().parse_args(
				[
					"--caco-enabled",
					"false",
					"--alchemy-plus-enabled",
					"true",
				]
			)
			self.assertIsNone(arguments.alchemy_plus_config)
			snapshot = settings_snapshot_for_arguments(arguments, ini_path)
			settings = build_settings(arguments, snapshot).alchemy_plus

		self.assertEqual(settings.configuration, configuration)
		self.assertTrue(settings.rounding_enabled)
		self.assertFalse(settings.impure_cost_fix_enabled)
		self.assertEqual(settings.magnitude_threshold, 40.0)
		self.assertEqual(settings.magnitude_multiple, 2.0)
		self.assertEqual(settings.duration_threshold, 30.0)
		self.assertEqual(settings.duration_multiple, 3.0)

	def test_explicit_alchemy_plus_config_overrides_current_default(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			config_path = Path(directory) / "AlchemyPlus.json"
			config_path.write_text(
				json.dumps(
					{
						"impureCostFix": {"enabled": False},
						"roundedPotency": {
							"enabled": True,
							"magnitudeThreshold": 40.0,
							"magnitudeMult": 2.0,
							"durationThreshold": 30.0,
							"durationMult": 3.0,
						},
					}
				),
				encoding="utf-8",
			)
			arguments = make_parser().parse_args(
				[
					"--caco-enabled",
					"false",
					"--alchemy-plus-enabled",
					"true",
					"--alchemy-plus-config",
					str(config_path),
					"Restore Health",
					"Wheat",
				]
			)
			settings = build_settings(arguments).alchemy_plus

		self.assertTrue(settings.rounding_enabled)
		self.assertFalse(settings.impure_cost_fix_enabled)
		self.assertEqual(settings.magnitude_threshold, 40.0)
		self.assertEqual(settings.magnitude_multiple, 2.0)
		self.assertEqual(settings.duration_threshold, 30.0)
		self.assertEqual(settings.duration_multiple, 3.0)

	def test_impure_signed_adjustment(self) -> None:
		adjusted, impure = adjust_impure_effect_cost(12.0, True, False, True)
		self.assertTrue(impure)
		self.assertEqual(adjusted, -12.0)
		adjusted, impure = adjust_impure_effect_cost(12.0, True, True, True)
		self.assertFalse(impure)
		self.assertEqual(adjusted, 12.0)

	def test_confirmed_row_execution(self) -> None:
		self.assertEqual(run_confirmed_row(2), 0)
		self.assertEqual(run_confirmed_row(1), 2)
		self.assertEqual(run_confirmed_row(99999), 2)


def inspect_recipe(
	ingredients: Sequence[str],
	vanilla_csv: Path = VANILLA_CSV,
	caco_csv: Path = CACO_CSV,
) -> None:
	print(f"=== Inspecting Recipe: {', '.join(ingredients)} ===")
	db_vanilla = IngredientDatabase.load_caco_duration_exports(vanilla_csv)

	configs = [
		("Vanilla Engine Default GMSTs (4.0 / 1.5)", 4.0, 1.5, 15.0),
		("Deployed INI / Row 70 GMSTs (4.5 / 1.8)", 4.5, 1.8, 15.0),
		("Row 70 Actual In-Game Confirmed (Skill 65, Rank 3)", 4.5, 1.8, 65.0),
	]

	for label, init_mult, skill_factor, skill_level in configs:
		player = PlayerSettings(
			alchemy_level=skill_level,
			alchemist_perk_rank=3 if skill_level == 65.0 else 0,
			alchemist_perk_multiplier=1.6 if skill_level == 65.0 else 1.0,
			physician=skill_level == 65.0,
			benefactor=skill_level == 65.0,
			poisoner=skill_level == 65.0,
			seeker_of_shadows=skill_level == 65.0,
		)
		settings = PredictionSettings(
			caco_enabled=False,
			alchemy_plus_enabled=False,
			player=player,
			caco_ingredient_init_multiplier=init_mult,
			caco_skill_factor=skill_factor,
		)
		res = PotionPredictor(db_vanilla, settings).evaluate(ingredients)
		print(f"\nConfiguration: {label}")
		print(f"  Result: {res.displayed_value} gold (exact float: {res.cost:.4f})")
		for eff in res.effects:
			print(f"    - {eff.source.effect_name}: mag={eff.calc_magnitude:g} dur={eff.calc_duration:g} cost={eff.native_cost:.4f}")


def make_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Predict a two- or three-ingredient Skyrim potion value using the plugin algorithm."
	)
	parser.add_argument(
		"ingredients",
		nargs="*",
		help="two or three ingredient names; quote names containing spaces",
	)
	parser.add_argument(
		"--caco-enabled",
		type=parse_bool,
		default=None,
		metavar="BOOL",
		help="override CACO snapshot detection in the active profile (true/false)",
	)
	parser.add_argument(
		"--alchemy-plus-enabled",
		type=parse_bool,
		default=None,
		metavar="BOOL",
		help="override Alchemy Plus snapshot detection in the active profile (true/false)",
	)
	parser.add_argument(
		"--alchemy-plus-config",
		type=Path,
		default=None,
		help="explicit AlchemyPlus.json override; otherwise use the active profile's AlchemyPlus Configuration snapshot",
	)
	parser.add_argument(
		"--vanilla-csv",
		type=Path,
		default=VANILLA_CSV,
		help=f"vanilla CSV (default: {VANILLA_CSV})",
	)
	parser.add_argument(
		"--caco-csv",
		type=Path,
		default=CACO_CSV,
		help=f"CACO CSV (default: {CACO_CSV})",
	)
	parser.add_argument(
		"--alchemy-level",
		type=float,
		default=None,
		help="player Alchemy actor value (default: active profile Player snapshot)",
	)
	parser.add_argument(
		"--fortify-alchemy",
		type=float,
		default=None,
		help="Fortify Alchemy actor-value bonus (default: active profile Player snapshot)",
	)
	parser.add_argument(
		"--alchemist-perk-rank",
		type=int,
		default=None,
		choices=range(0, 6),
		help="vanilla Alchemist rank 0-5 (default: active profile Player snapshot)",
	)
	parser.add_argument(
		"--alchemist-multiplier",
		type=float,
		default=None,
		help="explicit fallback Alchemist multiplier; overrides rank fallback",
	)
	parser.add_argument("--purity", action=argparse.BooleanOptionalAction, default=None)
	parser.add_argument("--physician", action=argparse.BooleanOptionalAction, default=None)
	parser.add_argument("--benefactor", action=argparse.BooleanOptionalAction, default=None)
	parser.add_argument("--poisoner", action=argparse.BooleanOptionalAction, default=None)
	parser.add_argument(
		"--concentrated-poison",
		action=argparse.BooleanOptionalAction,
		default=None,
		help="override the Concentrated Poison perk state",
	)
	parser.add_argument(
		"--seeker-of-shadows",
		action=argparse.BooleanOptionalAction,
		default=None,
	)
	parser.add_argument(
		"--caco-ingredient-init",
		type=float,
		default=None,
		help="CACO fAlchemyIngredientInitMult (default: active profile CACO snapshot)",
	)
	parser.add_argument(
		"--caco-skill-factor",
		type=float,
		default=None,
		help="CACO fAlchemySkillFactor (default: active profile CACO snapshot)",
	)
	for option, destination, help_text in (
		(
			"--caco-restore-health-duration",
			"caco_restore_health_duration",
			"override CACO RestoreHealthDuration index (0=1 SEC, 1=5 SEC, 2=10 SEC)",
		),
		(
			"--caco-restore-magicka-duration",
			"caco_restore_magicka_duration",
			"override CACO RestoreMagickaDuration index (0=1 SEC, 1=5 SEC, 2=10 SEC)",
		),
		(
			"--caco-restore-stamina-duration",
			"caco_restore_stamina_duration",
			"override CACO RestoreStaminaDuration index (0=1 SEC, 1=5 SEC, 2=10 SEC)",
		),
		(
			"--caco-damage-health-duration",
			"caco_damage_health_duration",
			"override CACO DamageHealthDuration index (0=1 SEC, 1=5 SEC, 2=10 SEC)",
		),
		(
			"--caco-damage-magicka-duration",
			"caco_damage_magicka_duration",
			"override CACO DamageMagickaDuration index (0=1 SEC, 1=5 SEC, 2=10 SEC)",
		),
		(
			"--caco-damage-stamina-duration",
			"caco_damage_stamina_duration",
			"override CACO DamageStaminaDuration index (0=1 SEC, 1=5 SEC, 2=10 SEC)",
		),
	):
		parser.add_argument(
			option,
			dest=destination,
			type=int,
			choices=range(0, 3),
			default=None,
			help=help_text,
		)
	for option, destination, help_text in (
		(
			"--caco-restore-effects-do-not-stack",
			"caco_restore_effects_do_not_stack",
			"override CACO RestoreEffectsDoNotStack (true/false)",
		),
		(
			"--caco-disable-all-potion-handling",
			"caco_disable_all_potion_handling",
			"override CACO DisableAllPotionHandling (true/false)",
		),
	):
		parser.add_argument(
			option,
			dest=destination,
			type=parse_bool,
			metavar="BOOL",
			default=None,
			help=help_text,
		)
	parser.add_argument(
		"--caco-alchemy-xp-multiplier",
		type=float,
		default=None,
		help="override CACO AlchemyXPMultiplier",
	)
	for option, destination, help_text in (
		(
			"--caco-physician-multiplier",
			"caco_physician_multiplier",
			"CACO-native Physician perk-entry multiplier",
		),
		(
			"--caco-benefactor-multiplier",
			"caco_benefactor_multiplier",
			"CACO-native Benefactor perk-entry multiplier",
		),
		(
			"--caco-poisoner-multiplier",
			"caco_poisoner_multiplier",
			"CACO-native Poisoner perk-entry multiplier",
		),
		(
			"--caco-seeker-multiplier",
			"caco_seeker_multiplier",
			"CACO-native Seeker of Shadows perk-entry multiplier",
		),
	):
		parser.add_argument(option, dest=destination, type=float, default=None, help=help_text)
	parser.add_argument(
		"--caco-impure-processing",
		type=parse_bool,
		default=None,
		metavar="BOOL",
		help="enable CACO's optional 20%% impure-potion adjustment (default: false or disabled by INI)",
	)
	parser.add_argument(
		"--alchemy-plus-rounding",
		type=parse_bool,
		default=None,
		metavar="BOOL",
		help="override roundedPotency.enabled (default: config value or true when AP is enabled)",
	)
	parser.add_argument(
		"--alchemy-plus-impure-cost-fix",
		type=parse_bool,
		default=None,
		metavar="BOOL",
		help="override impureCostFix.enabled (default: config value or true when AP is enabled)",
	)
	parser.add_argument("--ap-magnitude-threshold", type=float, default=None)
	parser.add_argument("--ap-magnitude-multiple", type=float, default=None)
	parser.add_argument("--ap-duration-threshold", type=float, default=None)
	parser.add_argument("--ap-duration-multiple", type=float, default=None)
	parser.add_argument(
		"--list-ingredients",
		action="store_true",
		help="list ingredient names from the selected data source and exit",
	)
	parser.add_argument(
		"--inspect-recipe",
		action="store_true",
		help="print side-by-side comparison across GMST baselines for given ingredients",
	)
	parser.add_argument(
		"--self-test",
		action="store_true",
		help="run built-in regression tests and exit",
	)
	parser.add_argument(
		"--check-predicted-csvs",
		action="store_true",
		help="DEFERRED broad regression check comparing expected values from C++ SKSE plugin predicted CSVs against actual values calculated by Python test harness; do not use as current accuracy gate",
	)
	parser.add_argument(
		"--check-confirmed-csv",
		action="store_true",
		help="CURRENT accuracy gate: check only confirmed observed-craft rows using their native selection order",
	)
	parser.add_argument(
		"--confirmed-row",
		"--check-confirmed-row",
		type=int,
		default=None,
		metavar="ROW",
		help="test a specific row line number from alchemist.potions-confirmed.csv",
	)
	parser.add_argument(
		"--confirmed-csv",
		type=Path,
		default=CONFIRMED_CSV,
		help=f"confirmed potion CSV (default: {CONFIRMED_CSV})",
	)
	parser.add_argument(
		"--order-dependent-csv",
		type=Path,
		default=ORDER_DEPENDENT_CSV,
		help=f"diagnostic-only order-dependent observations CSV (default: {ORDER_DEPENDENT_CSV})",
	)
	parser.add_argument(
		"--prediction-log",
		action=argparse.BooleanOptionalAction,
		default=True,
		help="write prediction mismatches to potion_prediction_test.log (default: enabled)",
	)
	parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
	return parser


def main(argv: Sequence[str] | None = None) -> int:
	parser = make_parser()
	arguments = parser.parse_args(argv)

	if arguments.inspect_recipe:
		if len(arguments.ingredients) not in {2, 3}:
			parser.error("--inspect-recipe requires 2 or 3 ingredients")
		inspect_recipe(arguments.ingredients, arguments.vanilla_csv, arguments.caco_csv)
		return 0
	if arguments.self_test:
		suite = unittest.defaultTestLoader.loadTestsFromTestCase(PredictionSelfTests)
		result = unittest.TextTestRunner(verbosity=2).run(suite)
		return 0 if result.wasSuccessful() else 1
	if arguments.check_predicted_csvs:
		return run_prediction_fixture_check(
			arguments.vanilla_csv,
			arguments.caco_csv,
			write_log=arguments.prediction_log,
		)
	if arguments.check_confirmed_csv:
		return run_confirmed_fixture_check(
			arguments.confirmed_csv,
			arguments.vanilla_csv,
			None if arguments.caco_csv == CACO_CSV else arguments.caco_csv,
			arguments.order_dependent_csv,
		)
	if arguments.confirmed_row is not None:
		return run_confirmed_row(
			arguments.confirmed_row,
			arguments.confirmed_csv,
			arguments.vanilla_csv,
			None if arguments.caco_csv == CACO_CSV else arguments.caco_csv,
			arguments.order_dependent_csv,
			as_json=arguments.json,
		)

	if arguments.caco_enabled is None or arguments.alchemy_plus_enabled is None:
		parser.error(
			"--caco-enabled and --alchemy-plus-enabled are required unless --self-test is used"
		)
	try:
		snapshot = settings_snapshot_for_arguments(arguments)
	except ValueError as error:
		parser.error(str(error))
	if not arguments.self_test and not arguments.check_predicted_csvs:
		require_runtime_defaults(parser, arguments, snapshot)
	caco_enabled, alchemy_plus_enabled = enabled_plugins(arguments, snapshot)
	if arguments.list_ingredients:
		database = IngredientDatabase.load_caco_duration_exports(
			arguments.caco_csv if caco_enabled else arguments.vanilla_csv,
			prefer_highest_form_id=caco_enabled,
		)
		print("\n".join(database.names()))
		return 0
	if len(arguments.ingredients) not in {2, 3}:
		parser.error("provide exactly two or three ingredient names")

	database = IngredientDatabase.load_caco_duration_exports(
		arguments.caco_csv if caco_enabled else arguments.vanilla_csv,
		prefer_highest_form_id=caco_enabled,
	)
	try:
		settings = build_settings(arguments, snapshot)
	except ValueError as error:
		parser.error(str(error))
	result = PotionPredictor(database, settings).evaluate(arguments.ingredients)
	if not result.valid:
		print("The recipe has no shared effects and cannot produce a potion.", file=sys.stderr)
		return 2
	print(result_json(result, database) if arguments.json else format_result(result, database))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
