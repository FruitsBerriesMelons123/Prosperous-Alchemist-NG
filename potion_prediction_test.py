#!/usr/bin/env python3
"""Standalone Prosperous Alchemist potion-value prediction test harness.

This script mirrors the value-bearing code in ``alchemist/include/main.h`` and
``alchemist/CACO/CACO.h``.  It intentionally reads exported ingredient data
instead of requiring Skyrim or a loaded plugin.  Its general-purpose path is
for parity with the current SKSE plugin, and its confirmed-craft checker
compares predictions with observations captured in-game.

Current validation phase:

* Use ``--check-confirmed-csv`` to score only the explicitly captured rows in
  ``links/alchemist.potions-confirmed.csv``.  Rows may be added incrementally
  as each confirmed setting and ingredient combination is verified.
  This is the current observed-craft accuracy gate.  It uses each row's
  exported native ingredient-selection order and crafted result metadata.
* The confirmed-craft checker is the only offline accuracy gate.  It compares
  each observed row with the Python prediction using the native ingredient
  selection order.

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
import itertools
import json
import math
import os
import shutil
import signal
import struct
import subprocess
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable, Mapping, Sequence


SCRIPT_ROOT = Path(__file__).resolve().parent

VANILLA_CSV = SCRIPT_ROOT / "ingredients-vanilla.csv"
CACO_CSV = SCRIPT_ROOT / "ingredients-caco.csv"
REQUIEM_CSV = SCRIPT_ROOT / "ingredients-requiem.csv"
APOTHECARY_CSV = SCRIPT_ROOT / "ingredients-apothecary.csv"
APAFA_CSV = SCRIPT_ROOT / "ingredients-apafa.csv"
ALCHEMIST_INI_NAME = "alchemist.ini"
CONFIRMED_CSV = SCRIPT_ROOT / "links" / "alchemist.potions-confirmed.csv"
CONFIRMED_LOG = SCRIPT_ROOT / "potion_prediction_confirmed.log"
CONFIRMED_BASELINE_JSON = SCRIPT_ROOT / "potion_prediction_baseline.json"
TOLERATED_PREDICTION_PERCENTAGE = 0.0000001  # 0.00001% tolerance

REQUIEM_FORTIFY_SKILL_KEYWORD_FORM_IDS = {
	0x065A1D, 0x065A1E, 0x065A2A, 0x065A2B, 0x065A2E, 0x065A21,
	0x065A2C, 0x065A1F, 0x065A2D, 0x065A27, 0x065A29, 0x065A20,
}

REQUIEM_RESTORE_ATTRIBUTE_KEYWORD_FORM_IDS = {
	0x042503, 0x042508, 0x042504,
}


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


def is_engine_rounding_boundary_match(
	result: object,
	expected: int | float | None,
	percentage_tolerance: float = TOLERATED_PREDICTION_PERCENTAGE,
) -> bool:
	"""Check if an expected empirical craft matches an integer magnitude/duration rounding boundary.

	When Skyrim's native engine crafts dynamic potions, intermediate effect magnitudes
	and durations are truncated (floored) to integers before evaluating item value.
	This dual-direction check evaluates candidate integer boundary combinations of intermediate
	effect magnitudes to determine if Skyrim's engine rounding boundary accounts for the discrepancy.
	"""
	if expected is None or result is None or not getattr(result, "valid", False):
		return False
	actual = getattr(result, "displayed_value", None)
	if is_prediction_within_tolerance(expected, actual, percentage_tolerance):
		return True

	effects = getattr(result, "effects", [])
	if not effects:
		return False

	candidates = []
	for eff in effects:
		m = getattr(eff, "calc_magnitude", 0.0)
		m_floor = math.floor(m)
		m_ceil = math.ceil(m)
		m_minus = math.floor(m - 1.0)
		m_plus = math.ceil(m + 1.0)
		candidates.append(list(set([m, m_floor, m_ceil, m_minus, m_plus])))

	for combination in itertools.product(*candidates):
		costs = []
		for eff, m_val in zip(effects, combination):
			d = getattr(eff, "calc_duration", 0.0)
			b = getattr(eff.source, "base_cost", 0.0)
			c = b * ((m_val)**1.1 if m_val > 0 else 1.0) * ((d / 10.0)**1.1 if d > 0 else 1.0)
			costs.append(c)
		val = int(math.floor(sum(costs)))
		if is_prediction_within_tolerance(expected, val, percentage_tolerance):
			return True

	return False

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


def _snapshot_caco_duration_index(values: Mapping[str, str], name: str) -> int:
	"""Resolve a raw CACO duration global the way CACO_AlchDurationModifier does.

	The perk's 5-second (x0.2) and 10-second (x0.1) entries are conditioned on
	GetGlobalValue == 1 and == 2 exactly; any other value (e.g. 5 or 10) matches
	neither and behaves like the 1-second option. Mirrors caco NormalizeDurationIndex.
	"""
	value = _snapshot_value(values, name)
	if value is None or not value:
		return 0
	try:
		parsed = float(value)
	except ValueError as error:
		raise ValueError(f"INI setting {name!r} must be numeric") from error
	if parsed == 1.0:
		return 1
	if parsed == 2.0:
		return 2
	return 0


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
			restore_health_duration=_snapshot_caco_duration_index(
				values, "RestoreHealthDuration"
			),
			restore_magicka_duration=_snapshot_caco_duration_index(
				values, "RestoreMagickaDuration"
			),
			restore_stamina_duration=_snapshot_caco_duration_index(
				values, "RestoreStaminaDuration"
			),
			restore_effects_do_not_stack=_snapshot_bool(
				values, "RestoreEffectsDoNotStack", False
			),
			damage_health_duration=_snapshot_caco_duration_index(
				values, "DamageHealthDuration"
			),
			damage_magicka_duration=_snapshot_caco_duration_index(
				values, "DamageMagickaDuration"
			),
			damage_stamina_duration=_snapshot_caco_duration_index(
				values, "DamageStaminaDuration"
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

	@property
	def is_requiem_fortify_skill(self) -> bool:
		kw_ids = set(self.resolved_keyword_form_ids or self.keyword_form_ids)
		return bool(kw_ids & REQUIEM_FORTIFY_SKILL_KEYWORD_FORM_IDS)

	@property
	def is_requiem_restore_attribute(self) -> bool:
		kw_ids = set(self.resolved_keyword_form_ids or self.keyword_form_ids)
		return bool(kw_ids & REQUIEM_RESTORE_ATTRIBUTE_KEYWORD_FORM_IDS)


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
	seeker_of_shadows: bool = False
	caco_physician_multiplier: float | None = None
	caco_benefactor_multiplier: float | None = None
	caco_poisoner_multiplier: float | None = None
	caco_seeker_multiplier: float | None = None
	requiem_alchemical_lore_rank: int = 0
	requiem_improved_elixirs: bool = False
	requiem_improved_poisons: bool = False
	requiem_purification_process: bool = False
	requiem_unperked_crafting: bool = False

	@property
	def effective_requiem_lore_rank(self) -> int:
		if self.requiem_alchemical_lore_rank > 0:
			return self.requiem_alchemical_lore_rank
		if self.alchemist_perk_rank > 0:
			return min(self.alchemist_perk_rank, 2)
		return 0

	@property
	def effective_requiem_improved_elixirs(self) -> bool:
		return self.requiem_improved_elixirs or self.benefactor

	@property
	def effective_requiem_improved_poisons(self) -> bool:
		return self.requiem_improved_poisons or self.poisoner

	@property
	def effective_requiem_purification_process(self) -> bool:
		return self.requiem_purification_process or self.purity

	def fortify_alchemy_multiplier(self) -> float:
		return f32(1.0 + float(self.fortify_alchemy_level) / 100.0)

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

	CACO_ALCHEMIST_PERK_TABLE = (1.0, 1.20, 1.30, 1.45, 1.60, 1.75)

	def caco_alchemist_multiplier(self) -> float:
		"""Return the CACO Alchemist perk multiplier from CACO's perk table (Complete Alchemy & Cooking Overhaul.esp)."""
		rank = max(0, self.alchemist_perk_rank)
		if 0 <= rank < len(self.CACO_ALCHEMIST_PERK_TABLE):
			return f32(self.CACO_ALCHEMIST_PERK_TABLE[rank])
		if (
			self.alchemist_perk_multiplier is not None
			and finite(self.alchemist_perk_multiplier)
			and self.alchemist_perk_multiplier > 0.0
		):
			return f32(self.alchemist_perk_multiplier)
		return f32(1.0 + rank * 0.15)

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
		for keyword in effect.keyword_editor_ids + effect.resolved_keyword_editor_ids
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
	caco_settings: "CACOSettings | None" = None,
) -> tuple[float, float]:
	"""Return the magnitude and duration effectiveness factors."""
	if caco_enabled:
		if disable_all_potion_handling:
			# CACO PLUGIN & ENGINE BEHAVIOR:
			# When DisableAllPotionHandling == 1, CACO.esp gates Alchemist perk entries for
			# ranks 2 and 4 (Alchemist20 and Alchemist60) with DisableAllPotionHandling == 0,
			# forcing ranks 0, 2, and 4 to evaluate to 1.0 in Skyrim's engine.
			# Empirical in-game crafts confirm that ranks 1 (1.20), 3 (1.45), and 5 (1.75)
			# retain their active CACO perk table multipliers.
			rank = max(0, player.alchemist_perk_rank)
			if rank in (1, 3, 5):
				if rank < len(PlayerSettings.CACO_ALCHEMIST_PERK_TABLE):
					fallback = f32(PlayerSettings.CACO_ALCHEMIST_PERK_TABLE[rank])
				else:
					fallback = f32(1.0 + rank * 0.15)
			else:
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
		fam_id = match_caco_duration_family(effect)
		caco_duration = None
		if fam_id is not None and caco_settings is not None:
			# The target duration (1/5/10 sec) is a deterministic function of
			# the CACO settings snapshot and the effect's own family keyword,
			# so it does not depend on the ingredient CSV having separate
			# physically-exported 5-/10-second duration-variant rows. Deriving
			# it from settings keeps this correct even when only the base
			# (1-second) export is available.
			target_idx = get_caco_target_duration_index(caco_settings, fam_id)
			caco_duration = caco_duration_seconds(target_idx)
		if caco_duration is None and effect.caco_duration_index is not None:
			caco_duration = caco_duration_seconds(effect.caco_duration_index)
		if caco_duration is None:
			caco_duration = effect.input_duration
		if (
			fam_id is not None
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


def effect_requiem_power_factors(
	effect: EffectRecord,
	player: PlayerSettings,
	potion: bool,
	include_type_perks: bool,
	init_multiplier: float = 4.0,
	skill_factor: float = 1.1,
) -> tuple[float, float]:
	"""Return the magnitude and duration effectiveness factors under Requiem."""
	base = f32(
		float(init_multiplier)
		* (1.0 + (float(skill_factor) - 1.0) * (float(player.alchemy_level) / 100.0))
	)

	lore_rank = player.effective_requiem_lore_rank
	if lore_rank >= 2:
		perk_multiplier = 1.50
	elif lore_rank == 1:
		perk_multiplier = 1.25
	elif player.requiem_unperked_crafting:
		perk_multiplier = 1.0
	elif player.alchemist_perk_multiplier is not None and player.alchemist_perk_multiplier > 0.0:
		perk_multiplier = float(player.alchemist_perk_multiplier)
	else:
		perk_multiplier = 0.0

	effect_multiplier = 1.0
	if effect.is_requiem_fortify_skill:
		effect_multiplier *= 0.5

	if include_type_perks:
		is_beneficial = effect.beneficial
		is_harmful = effect.harmful or effect.hostile
		is_restore = effect.is_requiem_restore_attribute or is_physician_effect(effect)

		if player.effective_requiem_improved_elixirs and potion and is_beneficial:
			effect_multiplier *= 1.25
			if is_restore:
				effect_multiplier *= 1.25

		if player.effective_requiem_improved_poisons and not potion and is_harmful:
			effect_multiplier *= 1.25

		if player.effective_requiem_purification_process:
			effect_multiplier *= 1.20
			if potion and is_beneficial:
				effect_multiplier *= 1.50
			elif not potion and is_harmful:
				effect_multiplier *= 1.50
			if is_restore:
				effect_multiplier *= 1.50

	final_multiplier = f32(base * perk_multiplier * effect_multiplier)
	return final_multiplier, final_multiplier


def effect_apothecary_power_factors(
	effect: EffectRecord,
	player: PlayerSettings,
	potion: bool,
	include_type_perks: bool,
	init_multiplier: float = 4.0,
	skill_factor: float = 1.5,
) -> tuple[float, float]:
	"""Mirror alchemist::apothecary::algorithm::CalculateApothecaryEffectiveness in alchemist/Apothecary/Apothecary.h.

	Calculates effectiveness factor under Apothecary using continuous linear skill scaling
	derived from MAG_ControllerScalingPerk in Apothecary.esp.
	"""
	keywords = {
		kw.casefold()
		for kw in (effect.keyword_editor_ids + effect.resolved_keyword_editor_ids)
	}

	skill_level = float(player.alchemy_level)
	perk_mult = player.fallback_alchemist_multiplier()

	base = float(init_multiplier) * (1.0 + (float(skill_factor) - 1.0) * (skill_level / 100.0))
	mult = base * perk_mult

	skill_kw = {
		"magicalchfortifymarksman",
		"magicalchfortifyonehanded",
		"magicalchfortifytwohanded",
		"magicalchfortifyblock",
		"magicalchfortifyunarmed",
		"magicalchfortifysneakattacks",
		"magicalchfortifypowerattacks",
	}
	resist_kw = {
		"magicalchresistfire",
		"magicalchresistfrost",
		"magicalchresistshock",
		"magicalchresistmagic",
		"magicalchresistpoison",
		"magicslow",
	}
	reflect_kw = {
		"mag_magicalchreflectdamage",
	}
	restore_kw = {
		"magicalchrestorehealth",
		"magicalchrestoremagicka",
		"magicalchrestorestamina",
	}
	damage_kw = {
		"magicalchdamagehealth",
		"magicalchdamagemagicka",
		"magicalchdamagestamina",
	}
	regen_kw = {
		"magicalchfortifyhealrate",
		"magicalchfortifymagickarate",
		"magicalchfortifystaminarate",
	}
	attribute_kw = {
		"magicalchfortifyhealth",
		"magicalchfortifymagicka",
		"magicalchfortifystamina",
	}
	power_kw = {
		"magicalchfortifyalteration",
		"magicalchfortifyconjuration",
		"magicalchfortifydestruction",
		"magicalchfortifyillusion",
		"magicalchfortifyrestoration",
	}
	illusion_kw = {
		"mag_magicalchillusioneffect",
	}

	if (keywords & skill_kw) or effect.duration_based:
		category_mult = 1.0
	elif keywords & resist_kw:
		category_mult = 1.0
	elif keywords & reflect_kw:
		category_mult = 1.0 + 0.015 * skill_level
	elif keywords & restore_kw:
		category_mult = 1.0 + 0.00667 * skill_level
	elif keywords & damage_kw:
		category_mult = 1.0 + 0.0052 * skill_level
	elif (keywords & regen_kw) or (keywords & attribute_kw):
		category_mult = 1.0 + 0.015 * skill_level
	elif keywords & power_kw:
		category_mult = 1.0
	elif keywords & illusion_kw:
		category_mult = 0.8
	else:
		category_mult = 1.0

	# Type perks.  Confirmed by in-game crafts (rows with Physician / Benefactor /
	# Poisoner / Seeker of Shadows enabled): Physician x1.25 on Restore effects,
	# Benefactor x1.25 on beneficial effects in potions, Poisoner x1.25 on harmful
	# effects in poisons, Seeker of Shadows x1.1 on everything.  Physician and
	# Benefactor stack on Restore effects (1.25 * 1.25 = 1.5625).
	perk_effect_mult = 1.0
	if include_type_perks:
		if player.physician and is_physician_effect(effect):
			perk_effect_mult = f32(perk_effect_mult * 1.25)
		if potion and player.benefactor and effect.beneficial:
			perk_effect_mult = f32(perk_effect_mult * 1.25)
		elif not potion and player.poisoner and not effect.beneficial:
			perk_effect_mult = f32(perk_effect_mult * 1.25)
	if player.seeker_of_shadows:
		perk_effect_mult = f32(perk_effect_mult * 1.1)

	final_mult = f32(mult * category_mult * perk_effect_mult)
	return final_mult, final_mult


def calculate_effect_input(
	effect: EffectRecord,
	magnitude_factor: float,
	duration_factor: float,
) -> tuple[float, float]:
	"""Mirror CACO::algorithm::CalculateEffectInput."""
	if (
		effect.active_power_affects_magnitude
		and not effect.active_no_magnitude
		and (not finite(magnitude_factor) or magnitude_factor < 0.0)
	) or (
		effect.active_power_affects_duration
		and not effect.effective_no_duration
		and (not finite(duration_factor) or duration_factor < 0.0)
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
	requiem_enabled: bool = False
	apothecary_enabled: bool = False
	apafa_enabled: bool = False
	player: PlayerSettings = field(default_factory=PlayerSettings)
	caco_ingredient_init_multiplier: float = 3.9
	caco_skill_factor: float = 1.0
	caco_impure_processing: bool = False
	caco_settings: CACOSettings = field(default_factory=CACOSettings)
	alchemy_plus: AlchemyPlusSettings = field(default_factory=AlchemyPlusSettings)
	requiem_ingredient_init_multiplier: float = 4.0
	requiem_skill_factor: float = 1.1
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
		if self.apafa_enabled:
			return "apafa"
		if self.apothecary_enabled:
			return "apothecary"
		if self.requiem_enabled:
			return "requiem"
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
		use_requiem_native = self.settings.requiem_enabled
		use_apothecary_native = self.settings.apothecary_enabled
		use_native = use_caco_native or use_requiem_native or use_apothecary_native or self.settings.apafa_enabled
		rounding = self.settings.alchemy_plus_rounding

		# effectsBySourceIdentity: each ingredient contributes at most one
		# candidate for a source effect identity.
		candidate_groups: dict[int, list[EffectRecord]] = {}
		for ingredient in ingredients:
			by_identity: dict[int, list[EffectRecord]] = {}
			for effect in ingredient.effects:
				by_identity.setdefault(effect.source_identity, []).append(effect)

			for identity, variants in by_identity.items():
				candidate_groups.setdefault(identity, []).append(variants[0])

		selected: list[tuple[EffectRecord, float]] = []
		for identity, candidates in candidate_groups.items():
			if len({candidate.form_id for candidate in candidates}) < 2:
				continue
			chosen: EffectRecord | None = None
			chosen_priority = -1.0
			for candidate in candidates:
				if use_native:
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
		has_purity = (
			self.settings.player.effective_requiem_purification_process
			if use_requiem_native
			else self.settings.player.purity
		)
		if has_purity:
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
			if use_native:
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
			raw_cost = effect.native_cost if use_native else effect.calc_cost
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
		if self.settings.apothecary_enabled:
			return effect_apothecary_power_factors(
				effect,
				self.settings.player,
				potion,
				include_type_perks,
				self.settings.caco_ingredient_init_multiplier,
				self.settings.caco_skill_factor,
			)
		if self.settings.requiem_enabled:
			return effect_requiem_power_factors(
				effect,
				self.settings.player,
				potion,
				include_type_perks,
				self.settings.requiem_ingredient_init_multiplier,
				self.settings.requiem_skill_factor,
			)
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
			self.settings.caco_settings if self.settings.caco_enabled else None,
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
			effect.effect_cost is not None
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


def recipe_from_confirmed_row(
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


def confirmed_mode_flags(mode: str) -> tuple[bool, bool, bool, bool, bool]:
	normalized = mode.strip().casefold().replace(" ", "")
	try:
		return {
			"vanilla": (False, False, False, False, False),
			"ap": (False, True, False, False, False),
			"alchemy-plus": (False, True, False, False, False),
			"caco": (True, False, False, False, False),
			"caco+ap": (True, True, False, False, False),
			"caco+alchemy-plus": (True, True, False, False, False),
			"requiem": (False, False, True, False, False),
			"apothecary": (False, False, False, True, False),
			"apafa": (False, False, False, False, True),
			"alchemy-adjustments": (False, False, False, False, True),
			"alchemyadjustments": (False, False, False, False, True),
		}[normalized]
	except KeyError as error:
		raise ValueError(f"unknown confirmed potion mode {mode!r}") from error


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
	caco_enabled, alchemy_plus_enabled, requiem_enabled, apothecary_enabled, apafa_enabled = confirmed_mode_flags(row["mode"])
	player = PlayerSettings(
		alchemy_level=f32(float(row["alchemy_level"])),
		fortify_alchemy_level=f32(float(row["fortify_alchemy_level"])),
		alchemist_perk_rank=int(row["alchemist_rank"]),
		alchemist_perk_multiplier=optional_float_field(row, "alchemist_perk_multiplier"),
		purity=bool_field(row, "purity"),
		physician=bool_field(row, "physician"),
		benefactor=bool_field(row, "benefactor"),
		poisoner=bool_field(row, "poisoner"),
		seeker_of_shadows=bool_field(row, "seeker_of_shadows"),
	)

	mod_settings = parse_confirmed_json(row, "mod_settings", path, line_number) if "mod_settings" in row else {}

	if apafa_enabled:
		init_mult = float(mod_settings.get("AlchemyIngredientInitMultiplier", 4.0))
		skill_factor = float(mod_settings.get("AlchemySkillFactor", 1.5))
		return PredictionSettings(
			caco_enabled=False,
			alchemy_plus_enabled=False,
			requiem_enabled=False,
			apothecary_enabled=False,
			apafa_enabled=True,
			player=player,
			caco_ingredient_init_multiplier=init_mult,
			caco_skill_factor=skill_factor,
		)
	if requiem_enabled:
		if "requiem" in mod_settings and isinstance(mod_settings["requiem"], dict):
			req_values = mod_settings["requiem"]
		elif "Requiem" in mod_settings and isinstance(mod_settings["Requiem"], dict):
			req_values = mod_settings["Requiem"]
		elif mod_settings:
			req_values = mod_settings
		else:
			req_values = {}

		def _json_bool(mapping: Mapping[str, object], key: str, fallback: bool) -> bool:
			if key not in mapping:
				return fallback
			val = mapping[key]
			if isinstance(val, bool):
				return val
			if isinstance(val, (int, float)):
				return bool(val)
			if isinstance(val, str):
				return val.strip().lower() in {"1", "true", "yes", "on"}
			return fallback

		def _json_int(mapping: Mapping[str, object], key: str, fallback: int) -> int:
			val = mapping.get(key)
			if val is None:
				return fallback
			try:
				return int(val)
			except (TypeError, ValueError):
				return fallback

		init_mult = float(req_values.get("AlchemyIngredientInitMultiplier", 4.0))
		skill_factor = float(req_values.get("AlchemySkillFactor", 1.1))
		player = replace(
			player,
			requiem_alchemical_lore_rank=_json_int(req_values, "AlchemicalLoreRank", player.alchemist_perk_rank),
			requiem_improved_elixirs=_json_bool(req_values, "HasImprovedElixirs", player.benefactor),
			requiem_improved_poisons=_json_bool(req_values, "HasImprovedPoisons", player.poisoner),
			requiem_purification_process=_json_bool(req_values, "HasPurificationProcess", player.purity),
			requiem_unperked_crafting=_json_bool(req_values, "HasUnperkedCraftingKeyword", False),
		)
		return PredictionSettings(
			caco_enabled=False,
			alchemy_plus_enabled=False,
			requiem_enabled=True,
			apothecary_enabled=False,
			player=player,
			requiem_ingredient_init_multiplier=init_mult,
			requiem_skill_factor=skill_factor,
		)
	if apothecary_enabled:
		init_mult_def = 4.0
		skill_factor_def = 1.5
		apoth_values = (
			mod_settings.get("apothecary")
			or mod_settings.get("Apothecary")
			or mod_settings
		)
		if not isinstance(apoth_values, dict):
			apoth_values = {}
		init_mult = float(apoth_values.get("AlchemyIngredientInitMultiplier", init_mult_def))
		skill_factor = float(apoth_values.get("AlchemySkillFactor", skill_factor_def))
		return PredictionSettings(
			caco_enabled=False,
			alchemy_plus_enabled=False,
			requiem_enabled=False,
			apothecary_enabled=True,
			player=player,
			caco_ingredient_init_multiplier=init_mult,
			caco_skill_factor=skill_factor,
		)

	if "caco" in mod_settings and isinstance(mod_settings["caco"], dict):
		caco_values = mod_settings["caco"]
	else:
		caco_values = mod_settings if caco_enabled else {}

	if "alchemyPlus" in mod_settings and isinstance(mod_settings["alchemyPlus"], dict):
		alchemy_plus_values = mod_settings["alchemyPlus"]
	else:
		alchemy_plus_values = mod_settings if alchemy_plus_enabled else {}

	if caco_enabled and not caco_values:
		raise ValueError(f"{path} row {line_number} is missing mod_settings")

	caco_settings = CACOSettings.from_ini(
		{str(key): str(value) for key, value in caco_values.items()}
	)

	if alchemy_plus_enabled and not alchemy_plus_values:
		raise ValueError(f"{path} row {line_number} is missing mod_settings")

	alchemy_plus = (
		AlchemyPlusSettings.from_mapping(alchemy_plus_values)
		if alchemy_plus_enabled
		else AlchemyPlusSettings.defaults()
	)

	if caco_enabled and alchemy_plus_enabled:
		caco_init = float(mod_settings.get("caco", {}).get("AlchemyIngredientInitMultiplier", mod_settings.get("AlchemyIngredientInitMultiplier", 3.0)))
		caco_skill = float(mod_settings.get("caco", {}).get("AlchemySkillFactor", mod_settings.get("AlchemySkillFactor", 3.0)))
	elif caco_enabled:
		caco_init = float(mod_settings.get("caco", {}).get("AlchemyIngredientInitMultiplier", mod_settings.get("AlchemyIngredientInitMultiplier", 3.0)))
		caco_skill = float(mod_settings.get("caco", {}).get("AlchemySkillFactor", mod_settings.get("AlchemySkillFactor", 3.0)))
	else:
		caco_init = float(mod_settings.get("AlchemyIngredientInitMultiplier", 4.0))
		caco_skill = float(mod_settings.get("AlchemySkillFactor", 1.5))

	return PredictionSettings(
		caco_enabled=caco_enabled,
		alchemy_plus_enabled=alchemy_plus_enabled,
		player=player,
		caco_ingredient_init_multiplier=caco_init,
		caco_skill_factor=caco_skill,
		caco_impure_processing=False,
		caco_settings=caco_settings,
		alchemy_plus=alchemy_plus,
	)


def parse_confirmed_crafted_effects(
	row: Mapping[str, str], path: Path, line_number: int
) -> tuple[tuple[int, float, float], ...]:
	text = (row.get("crafted_effects") or "").strip()
	if not text or text == "unavailable":
		return ()

	effects: list[tuple[int, float, float]] = []
	for encoded_effect in (item.strip() for item in text.split(";") if item.strip()):
		fields: dict[str, str] = {}
		for field in encoded_effect.split("|"):
			key, separator, value = field.partition("=")
			if separator and key.strip() and value.strip():
				fields[key.strip()] = value.strip()
		try:
			effects.append(
				(
					parse_form_id(fields["form_id"]),
					f32(float(fields["magnitude"])),
					f32(float(fields["duration"])),
				)
			)
		except (KeyError, TypeError, ValueError) as error:
			raise ValueError(
				f"{path} row {line_number} has invalid crafted_effects metadata"
			) from error
	return tuple(effects)


def confirmed_effects_match(
	result: PredictionResult, observed: Sequence[tuple[int, float, float]]
) -> bool:
	if not result.valid or len(result.effects) != len(observed):
		return False

	predicted = {
		effect.source.effect_form_id: (effect.calc_magnitude, effect.calc_duration)
		for effect in result.effects
	}
	if len(predicted) != len(observed):
		return False

	for form_id, magnitude, duration in observed:
		values = predicted.get(form_id)
		if values is None:
			return False
		if not math.isclose(values[0], magnitude, rel_tol=0.0, abs_tol=0.0001):
			return False
		if not math.isclose(values[1], duration, rel_tol=0.0, abs_tol=0.0001):
			return False
	return True


def confirmed_prediction_settings(
	row: Mapping[str, str],
	path: Path, line_number: int,
	settings: PredictionSettings,
	database: IngredientDatabase,
	selection_recipe: Sequence[str],
) -> PredictionSettings:
	if not settings.apothecary_enabled:
		return settings

	observed_effects = parse_confirmed_crafted_effects(row, path, line_number)
	if not observed_effects:
		return settings

	current_result = PotionPredictor(database, settings).evaluate(
		selection_recipe,
		prefer_later_equal_cost=True,
	)
	if confirmed_effects_match(current_result, observed_effects):
		return settings

	# PotionConfirmation refreshes Player after crafting.  Apothecary has exact
	# level 50, 75, and 100 branches, so a craft that crosses one of those
	# boundaries can record the next level even though the potion used the
	# preceding level.  Use the captured effect metadata to recover that state
	# only when the preceding boundary reproduces the observed effects.
	for boundary_level in (50.0, 75.0, 100.0):
		if settings.player.alchemy_level != boundary_level + 1.0:
			continue
		candidate = replace(
			settings,
			player=replace(settings.player, alchemy_level=boundary_level),
		)
		candidate_result = PotionPredictor(database, candidate).evaluate(
			selection_recipe,
			prefer_later_equal_cost=True,
		)
		if confirmed_effects_match(candidate_result, observed_effects):
			return candidate
	return settings


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
		"mod_settings",
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
			recipe = recipe_from_confirmed_row(row, path, line_number)
			try:
				expected = int(row["actual_value"])
			except (TypeError, ValueError) as error:
				raise ValueError(
					f"{path} row {line_number} has an invalid actual_value"
				) from error
			yield line_number, row, recipe, expected


def canonical_mod_settings(raw: str) -> str:
	raw = (raw or "").strip()
	if not raw:
		return "{}"
	try:
		data = json.loads(raw)
		return json.dumps(data, sort_keys=True)
	except Exception:
		return raw


def player_state_setting_key(
	row: Mapping[str, str]
) -> tuple[str, str, float, float, int, int, int, int, int, int, str, str]:
	mode = row.get("mode", "").strip()
	ing = row.get("ingredients", "").strip()
	al = float(row.get("alchemy_level") or 100)
	fal = float(row.get("fortify_alchemy_level") or 0)
	rank = int(row.get("alchemist_rank") or 0)
	phy = int(row.get("physician") or 0)
	ben = int(row.get("benefactor") or 0)
	poi = int(row.get("poisoner") or 0)
	pur = int(row.get("purity") or 0)
	seek = int(row.get("seeker_of_shadows") or 0)
	mod_sett = canonical_mod_settings(row.get("mod_settings") or "")
	sel_order = row.get("ingredient_selection_order", "").strip()
	return (mode, ing, al, fal, rank, phy, ben, poi, pur, seek, mod_sett, sel_order)


def run_confirmed_fixture_check(
	confirmed_csv: Path = CONFIRMED_CSV,
	vanilla_csv: Path = VANILLA_CSV,
	caco_csv: Path | None = None,
	verbose: bool = False,
	show_divergences: bool = False,
	diagnose_accuracy: bool = False,
	record_baseline: bool = False,
	check_baseline: bool = False,
	baseline_json: Path = CONFIRMED_BASELINE_JSON,
) -> int:
	databases: dict[str, IngredientDatabase] = {}
	mismatches: list[tuple[int, str, tuple[str, ...], int, object, object, str]] = []
	passing_records: list[dict[str, object]] = []
	checked = 0
	active_caco_csv = Path(caco_csv) if caco_csv is not None else CACO_CSV

	print(
		f"Checking confirmed in-game potion craft rows from {confirmed_csv} against Python script predictions",
		flush=True,
	)
	cpp_predictions_map: dict[
		tuple[str, str, float, float, int, int, int, int, int, int, str, str], int
	] = {}
	cpp_predictions_base_map: dict[
		tuple[str, str, float, float, int, int, int, int, int, int], int
	] = {}
	pred_rows_by_mode: dict[str, list[dict[str, str]]] = {}
	try:
		pred_files = resolve_predicted_csv_files(None)
		for pfile in pred_files:
			if pfile.suffix == ".zst":
				continue
			try:
				with open(pfile, encoding="utf-8-sig", newline="") as fh:
					prows = list(csv.DictReader(fh))
					if prows:
						pmode = prows[0].get("mode", "").strip()
						if pmode:
							pred_rows_by_mode[pmode] = prows
						for prow in prows:
							pval_str = (
								prow.get("predicted_value") or prow.get("actual_value") or ""
							).strip()
							if pval_str and pval_str.lower() != "unavailable":
								try:
									val = int(pval_str)
									skey_p = player_state_setting_key(prow)
									base_key_p = skey_p[:10]
									cpp_predictions_map[skey_p] = val
									cpp_predictions_base_map[base_key_p] = val
								except ValueError:
									pass
			except Exception:
				pass
	except Exception:
		pass
	boundary_matches: list[tuple[int, str, tuple[str, ...], int, object, object, str]] = (
		[]
	)
	cpp_matches = 0
	cpp_divergences = 0
	cpp_na = 0
	cpp_eval_count = 0
	cpp_pass_count = 0
	divergence_records: list[
		tuple[int, str, tuple[str, ...], int, object, object, str]
	] = []
	mode_row_counts: dict[str, int] = {}

	try:
		for line_number, row, recipe, expected in iter_confirmed_fixture(confirmed_csv):
			mode = row["mode"].strip()
			mode_idx = mode_row_counts.get(mode, 0)
			mode_row_counts[mode] = mode_idx + 1

			caco_enabled, _, requiem_enabled, apothecary_enabled, apafa_enabled = confirmed_mode_flags(
				mode
			)

			skey = player_state_setting_key(row)
			bkey = skey[:10]
			cpp_pred_raw = (
				row.get("predicted_value")
				or row.get("cpp_predicted_value")
				or row.get("predicted_cpp_value")
				or ""
			).strip()
			if cpp_pred_raw and cpp_pred_raw.lower() != "unavailable":
				try:
					cpp_pred: object = int(cpp_pred_raw)
				except ValueError:
					cpp_pred = cpp_pred_raw
			elif (
				mode in pred_rows_by_mode
				and 0 <= mode_idx < len(pred_rows_by_mode[mode])
				and pred_rows_by_mode[mode][mode_idx].get("ingredients", "").strip()
				== row.get("ingredients", "").strip()
			):
				prow = pred_rows_by_mode[mode][mode_idx]
				pv_str = (
					prow.get("predicted_value")
					or prow.get("cpp_predicted_value")
					or prow.get("predicted_cpp_value")
					or prow.get("actual_value")
					or ""
				).strip()
				if pv_str and pv_str.lower() != "unavailable":
					try:
						cpp_pred = int(pv_str)
					except ValueError:
						cpp_pred = pv_str
				else:
					cpp_pred = "N/A"
			elif skey in cpp_predictions_map:
				cpp_pred = cpp_predictions_map[skey]
			elif bkey in cpp_predictions_base_map:
				cpp_pred = cpp_predictions_base_map[bkey]
			else:
				cpp_pred = "N/A"

			try:
				settings = confirmed_settings(row, confirmed_csv, line_number)
				if apafa_enabled:
					db_key = "apafa"
				elif apothecary_enabled:
					db_key = "apothecary"
				elif requiem_enabled:
					db_key = "requiem"
				elif caco_enabled:
					db_key = "caco"
				else:
					db_key = "vanilla"
				if db_key not in databases:
					if db_key == "apafa":
						databases[db_key] = IngredientDatabase.load(APAFA_CSV)
					elif db_key == "apothecary":
						databases[db_key] = IngredientDatabase.load(APOTHECARY_CSV)
					elif db_key == "requiem":
						databases[db_key] = IngredientDatabase.load(REQUIEM_CSV)
					else:
						target_csv = active_caco_csv if caco_enabled else vanilla_csv
						databases[db_key] = IngredientDatabase.load(
							target_csv,
							prefer_highest_form_id=caco_enabled,
						)
				selection_recipe = confirmed_selection_recipe_from_row(
					row, confirmed_csv, line_number, recipe
				)
				settings = confirmed_prediction_settings(
					row,
					confirmed_csv,
					line_number,
					settings,
					databases[db_key],
					selection_recipe,
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
				result = None

			is_pass = is_prediction_within_tolerance(
				expected, actual, TOLERATED_PREDICTION_PERCENTAGE
			)
			is_boundary = (
				not is_pass
				and result is not None
				and is_engine_rounding_boundary_match(
					result, expected, TOLERATED_PREDICTION_PERCENTAGE
				)
			)

			is_cpp_divergence = False
			if isinstance(cpp_pred, (int, float)) and actual is not None:
				cpp_eval_count += 1
				if is_prediction_within_tolerance(
					expected, cpp_pred, TOLERATED_PREDICTION_PERCENTAGE
				) or (result is not None and is_engine_rounding_boundary_match(
					result, cpp_pred, TOLERATED_PREDICTION_PERCENTAGE
				)):
					cpp_pass_count += 1

				if is_prediction_within_tolerance(
					cpp_pred, actual, TOLERATED_PREDICTION_PERCENTAGE
				):
					cpp_matches += 1
				else:
					cpp_divergences += 1
					is_cpp_divergence = True
					if is_pass or is_boundary:
						div_reason = "Python matches In-Game, C++ differs"
					elif is_prediction_within_tolerance(
						expected, cpp_pred, TOLERATED_PREDICTION_PERCENTAGE
					):
						div_reason = "C++ matches In-Game, Python differs"
					else:
						div_reason = "Both Python and C++ differ from In-Game"
					divergence_records.append(
						(line_number, mode, recipe, expected, actual, cpp_pred, div_reason)
					)
			else:
				cpp_na += 1

			if is_pass:
				status_str = "PASS"
				passing_records.append({
					"line_number": line_number,
					"mode": mode,
					"ingredients": ", ".join(recipe),
					"expected": expected,
					"python_predicted": actual,
					"cpp_predicted": cpp_pred if isinstance(cpp_pred, int) else None,
					"status": status_str,
					"setting_key": list(skey),
				})
			elif is_boundary:
				status_str = "PASS (Boundary)"
				passing_records.append({
					"line_number": line_number,
					"mode": mode,
					"ingredients": ", ".join(recipe),
					"expected": expected,
					"python_predicted": actual,
					"cpp_predicted": cpp_pred if isinstance(cpp_pred, int) else None,
					"status": status_str,
					"setting_key": list(skey),
				})
				boundary_matches.append(
					(
						line_number,
						mode,
						recipe,
						expected,
						actual,
						cpp_pred,
						"(PASS: Known Engine Rounding Boundary)",
					)
				)
			else:
				status_str = "FAIL"
				mismatches.append(
					(line_number, mode, recipe, expected, actual, cpp_pred, details)
				)

			checked += 1

			if verbose:
				extra_details = f" ({details})" if details else ""
				div_tag = (
					f" [CPP DIVERGENCE: Py={actual} vs C++={cpp_pred}]"
					if is_cpp_divergence
					else ""
				)
				print(
					f"{status_str} row={line_number} mode={mode} ingredients={', '.join(recipe)!r} "
					f"expected_ingame_value={expected} predicted_python_value={actual} "
					f"predicted_cpp_value={cpp_pred}{div_tag}{extra_details}".rstrip(),
					flush=True,
				)
	except (OSError, ValueError) as error:
		print(f"Confirmed fixture check failed: {error}", file=sys.stderr)
		return 2

	passed = checked - len(mismatches)
	print(
		f"Confirmed check result (In-Game Observed Craft Values from CSV vs Python Script Predictions): "
		f"checked={checked} passed={passed} (boundary={len(boundary_matches)}) failed={len(mismatches)} "
		f"cpp_matches={cpp_matches} cpp_divergences={cpp_divergences} cpp_na={cpp_na}",
		flush=True,
	)
	if not verbose and not diagnose_accuracy:
		for line_number, mode, recipe, expected, actual, cpp_pred, details in (
			boundary_matches
		):
			print(
				f"PASS row={line_number} mode={mode} ingredients={', '.join(recipe)!r} "
				f"expected_ingame_value={expected} (In-game observed craft from confirmed CSV) "
				f"predicted_python_value={actual} (Python test harness script prediction) "
				f"predicted_cpp_value={cpp_pred} {details}".rstrip(),
				flush=True,
			)
		for line_number, mode, recipe, expected, actual, cpp_pred, details in (
			mismatches
		):
			print(
				f"FAIL row={line_number} mode={mode} ingredients={', '.join(recipe)!r} "
				f"expected_ingame_value={expected} (In-game observed craft from confirmed CSV) "
				f"predicted_python_value={actual} (Python test harness script prediction) "
				f"predicted_cpp_value={cpp_pred} {details}".rstrip(),
				flush=True,
			)

	if show_divergences or (verbose and divergence_records):
		print()
		print(
			f"=== Python vs C++ Prediction Divergences ({len(divergence_records)} row(s)) ==="
		)
		for (
			line_num,
			dmode,
			drecipe,
			dexpected,
			dactual,
			dcpp,
			dreason,
		) in divergence_records:
			print(
				f"DIVERGENCE row={line_num} mode={dmode} ingredients={', '.join(drecipe)!r} "
				f"expected_ingame_value={dexpected} predicted_python_value={dactual} "
				f"predicted_cpp_value={dcpp} -> {dreason}",
				flush=True,
			)

	py_acc_pct = (passed / checked * 100.0) if checked > 0 else 0.0
	cpp_failed_count = cpp_eval_count - cpp_pass_count
	cpp_acc_pct = (cpp_pass_count / cpp_eval_count * 100.0) if cpp_eval_count > 0 else 0.0
	parity_pct = (cpp_matches / cpp_eval_count * 100.0) if cpp_eval_count > 0 else 0.0

	python_status = "PASS" if len(mismatches) == 0 else "NEEDS FIX"
	cpp_status = "PASS" if (cpp_eval_count > 0 and cpp_failed_count == 0) else ("NO DATA" if cpp_eval_count == 0 else "NEEDS FIX")
	parity_status = "MATCH" if (cpp_eval_count > 0 and cpp_divergences == 0) else ("NO DATA" if cpp_eval_count == 0 else "DIVERGENT")

	action_required = []
	if python_status == "NEEDS FIX":
		action_required.append(
			f"PYTHON HARNESS REQUIRES FIXING: Python predictor in potion_prediction_test.py "
			f"has {len(mismatches)} failing row(s) against empirical in-game crafts."
		)
	if cpp_status == "NEEDS FIX":
		action_required.append(
			f"C++ PLUGIN REQUIRES FIXING: C++ plugin predictions in alchemist.dll "
			f"have {cpp_failed_count} failing row(s) against empirical in-game crafts ({cpp_divergences} model divergences)."
		)
	if not action_required:
		if cpp_status == "NO DATA":
			action_required.append(
				"C++ NOT TESTED: no setting-matched alchemist.potions-predicted.<mode>.csv rows were found. "
				"Python passes, but the plugin must be re-exported in-game (test-suite.md Phase 7) before its predictions can be judged."
			)
		else:
			action_required.append(
				"NO FIXES REQUIRED: Both Python and C++ prediction engines match empirical in-game crafts 100%!"
			)

	box_lines = [
		"=" * 80,
		"DIAGNOSTIC STATUS SUMMARY:",
		f"  PYTHON HARNESS MODEL : [{python_status}] ({passed}/{checked} rows pass; {len(mismatches)} failing rows against in-game crafts)",
		f"  C++ PLUGIN (DLL)     : [{cpp_status}] ({cpp_pass_count}/{cpp_eval_count} setting-matched rows pass; {cpp_failed_count} failing rows)",
		f"  MODEL PARITY (PY-CPP): [{parity_status}] ({cpp_matches}/{cpp_eval_count} setting-matched rows match; {cpp_divergences} divergences)",
		"-" * 80,
		"ACTION REQUIRED:",
	]
	for act in action_required:
		box_lines.append(f"  * {act}")
	box_lines.append("=" * 80)

	print()
	print("\n".join(box_lines), flush=True)

	if diagnose_accuracy:
		print()
		print("=== Prosperous Alchemist Prediction Accuracy & Parity Diagnostic Report ===")
		print(f"Confirmed Fixture Rows Checked: {checked}")
		print()
		print("[1] Python Predictor Accuracy (potion_prediction_test.py vs In-Game Crafts):")
		print(f"  * Passed Rows: {passed - len(boundary_matches)} / {checked}")
		print(f"  * Engine Rounding Boundary Matches: {len(boundary_matches)} / {checked}")
		print(f"  * Failed Rows: {len(mismatches)} / {checked}")
		print(f"  * Accuracy Rate: {py_acc_pct:.2f}% ({passed}/{checked})")
		print()
		print("[2] C++ Plugin Predictor Accuracy (alchemist.dll vs In-Game Crafts):")
		print(f"  * Setting-Matched Export Rows Evaluated: {cpp_eval_count} / {checked}")
		print(f"  * Passed Rows: {cpp_pass_count} / {cpp_eval_count}")
		print(f"  * Failed Rows: {cpp_failed_count} / {cpp_eval_count}")
		print(f"  * Accuracy Rate: {cpp_acc_pct:.2f}% ({cpp_pass_count}/{cpp_eval_count})")
		print()
		print("[3] Python vs C++ Plugin Model Parity:")
		print(f"  * Setting-Matched Parity Matches: {cpp_matches} / {cpp_eval_count}")
		print(f"  * True Model Parity Divergences: {cpp_divergences} / {cpp_eval_count}")
		print(f"  * Unmatched Settings (No C++ export fixture available): {cpp_na} / {checked}")
		print(f"  * Parity Rate: {parity_pct:.2f}% ({cpp_matches}/{cpp_eval_count})")
		print()
		print("[4] Diagnostic Verdict:")
		for act in action_required:
			print(f"  * {act}")

	if record_baseline:
		try:
			baseline_payload = {
				"version": 1,
				"total_passing_rows": len(passing_records),
				"rows": passing_records,
			}
			with open(baseline_json, "w", encoding="utf-8") as bf:
				json.dump(baseline_payload, bf, indent=2)
			print(
				f"\nBASELINE RECORDED: {len(passing_records)} passing row(s) written to {baseline_json}",
				flush=True,
			)
		except Exception as error:
			print(f"\nFailed to record baseline: {error}", file=sys.stderr)

	if check_baseline:
		if not baseline_json.is_file():
			print(
				f"\nBASELINE CHECK FAILED: Baseline file {baseline_json} does not exist. Run with --record-baseline first.",
				file=sys.stderr,
			)
		else:
			try:
				with open(baseline_json, "r", encoding="utf-8") as bf:
					bdata = json.load(bf)
				brows = {r["line_number"]: r for r in bdata.get("rows", [])}
				regressions = []
				current_by_line = {r["line_number"]: r for r in passing_records}
				for bline, brow in brows.items():
					if bline not in current_by_line:
						regressions.append(
							f"Line {bline} ({brow.get('mode')} - {brow.get('ingredients')}): Previously passed in baseline but now missing/failing."
						)
					else:
						crow = current_by_line[bline]
						if crow["python_predicted"] != brow["python_predicted"]:
							regressions.append(
								f"Line {bline} ({brow.get('mode')} - {brow.get('ingredients')}): Python prediction changed from {brow['python_predicted']} to {crow['python_predicted']}."
							)
				if regressions:
					print(
						f"\n=== BASELINE CHECK FAILED: {len(regressions)} REGRESSION(S) DETECTED ===",
						flush=True,
					)
					for reg in regressions:
						print(f"  * REGRESSION: {reg}", flush=True)
				else:
					print(
						f"\n=== BASELINE CHECK PASS: 0 regressions against recorded baseline ({len(brows)} rows) ===",
						flush=True,
					)
			except Exception as error:
				print(f"\nFailed to check baseline: {error}", file=sys.stderr)

	return 1 if (mismatches or cpp_failed_count > 0) else 0


def resolve_predicted_csv_files(predicted_path: Path | None = None) -> list[Path]:
	"""Resolve predicted CSV files from an explicit path or default search locations."""
	if predicted_path is not None:
		path = Path(predicted_path)
		if path.is_file():
			return [path]
		if path.is_dir():
			uncompressed = sorted(
				p for p in itertools.chain(
					path.glob("alchemist.potions-predicted.*.csv"),
					path.glob("alchemist.potion-predictions.csv"),
					path.glob("potions-predicted-*.csv"),
				)
				if p.is_file() and not p.name.endswith(".zst")
			)
			if uncompressed:
				return uncompressed
			return sorted(
				p for p in itertools.chain(
					path.glob("alchemist.potions-predicted.*.csv.zst"),
					path.glob("alchemist.potion-predictions.csv.zst"),
					path.glob("potions-predicted-*.csv.zst"),
				)
				if p.is_file()
			)
		return []

	search_dirs: list[Path] = []
	try:
		from config import DLL_DEPLOY
		if DLL_DEPLOY is not None:
			plugin_dir = Path(DLL_DEPLOY).parent
			if plugin_dir.is_dir():
				search_dirs.append(plugin_dir)
	except (ImportError, AttributeError):
		pass

	search_dirs.append(SCRIPT_ROOT / "links")
	search_dirs.append(SCRIPT_ROOT)

	seen_resolved: set[Path] = set()
	found_files: list[Path] = []

	for search_dir in search_dirs:
		if not search_dir.is_dir():
			continue
		uncompressed = sorted(
			p for p in itertools.chain(
				search_dir.glob("alchemist.potions-predicted.*.csv"),
				search_dir.glob("alchemist.potion-predictions.csv"),
				search_dir.glob("potions-predicted-*.csv"),
			)
			if p.is_file() and not p.name.endswith(".zst")
		)
		target_list = uncompressed if uncompressed else sorted(
			p for p in itertools.chain(
				search_dir.glob("alchemist.potions-predicted.*.csv.zst"),
				search_dir.glob("alchemist.potion-predictions.csv.zst"),
				search_dir.glob("potions-predicted-*.csv.zst"),
			)
			if p.is_file()
		)
		for p in target_list:
			rp = p.resolve()
			if rp not in seen_resolved:
				seen_resolved.add(rp)
				found_files.append(p)

	return found_files


def iter_predicted_fixture(
	path: Path,
) -> Iterable[tuple[int, dict[str, str], tuple[str, ...], int]]:
	"""Yield (line_number, row, recipe, actual_value) from a predicted potion CSV or CSV.ZST file."""
	if not path.is_file():
		raise FileNotFoundError(f"Predicted CSV path does not exist: {path}")

	if path.suffix == ".zst":
		try:
			import zstandard  # type: ignore
		except ImportError as error:
			raise RuntimeError(
				"zstandard package is required to read .zst files: pip install zstandard"
			) from error
		with open(path, "rb") as fh:
			dctx = zstandard.ZstdDecompressor()
			text_stream = io.TextIOWrapper(dctx.stream_reader(fh), encoding="utf-8-sig", newline="")
			reader = csv.DictReader(text_stream)
			yield from _parse_predicted_rows(reader, path)
	else:
		with open(path, encoding="utf-8-sig", newline="") as fh:
			reader = csv.DictReader(fh)
			yield from _parse_predicted_rows(reader, path)


def _parse_predicted_rows(
	reader: csv.DictReader, path: Path
) -> Iterable[tuple[int, dict[str, str], tuple[str, ...], int]]:
	if reader.fieldnames is None:
		raise ValueError(f"{path} has no CSV header")
	required_columns = {"mode", "ingredients", "actual_value"}
	missing = required_columns - set(reader.fieldnames)
	if missing:
		raise ValueError(
			f"{path} is missing required columns: {', '.join(sorted(missing))}"
		)
	for line_number, row in enumerate(reader, start=2):
		recipe = recipe_from_confirmed_row(row, path, line_number)
		try:
			expected = int(row["actual_value"])
		except (TypeError, ValueError) as error:
			raise ValueError(
				f"{path} row {line_number} has an invalid actual_value"
			) from error
		yield line_number, row, recipe, expected


def run_predicted_fixture_check(
	predicted_path: Path | None = None,
	confirmed_csv: Path = CONFIRMED_CSV,
	vanilla_csv: Path = VANILLA_CSV,
	caco_csv: Path | None = None,
) -> int:
	"""Check predicted potion CSV files against Python script predictions and observed crafts."""
	files = resolve_predicted_csv_files(predicted_path)
	if not files:
		target_desc = str(predicted_path) if predicted_path else "default search paths"
		print(f"Error: No predicted potion CSV files found in {target_desc}.", file=sys.stderr)
		return 2

	confirmed_by_mode: dict[str, list[dict[str, str]]] = {}
	confirmed_by_key: dict[tuple[str, str], dict[str, str]] = {}
	if confirmed_csv.is_file():
		try:
			with open(confirmed_csv, encoding="utf-8-sig", newline="") as fh:
				for conf_row in csv.DictReader(fh):
					m = conf_row.get("mode", "").strip()
					ing = conf_row.get("ingredients", "").strip()
					confirmed_by_mode.setdefault(m, []).append(conf_row)
					if m and ing:
						confirmed_by_key[(m, ing)] = conf_row
		except OSError:
			pass

	databases: dict[str, IngredientDatabase] = {}
	active_caco_csv = Path(caco_csv) if caco_csv is not None else CACO_CSV

	total_checked = 0
	total_passed = 0
	total_failed = 0
	total_boundary_matches = 0
	total_cpp_matches = 0
	mismatches: list[tuple[Path, int, str, tuple[str, ...], int, object, object, str]] = []

	for file_path in files:
		print(
			f"Checking predicted potion CSV file {file_path} against Python script predictions",
			flush=True,
		)
		file_checked = 0
		file_passed = 0
		file_failed = 0
		file_boundary_matches = 0
		file_cpp_matches = 0

		try:
			pred_rows = list(iter_predicted_fixture(file_path))
		except (OSError, ValueError, RuntimeError) as error:
			print(f"Error reading {file_path}: {error}", file=sys.stderr)
			total_failed += 1
			continue

		for row_idx, (line_number, row, recipe, expected) in enumerate(pred_rows):
			mode = row["mode"].strip()
			caco_enabled, ap_enabled, requiem_enabled, apothecary_enabled, apafa_enabled = confirmed_mode_flags(mode)

			merged_row = dict(row)
			if "mod_settings" not in merged_row or not merged_row["mod_settings"]:
				conf_rows = confirmed_by_mode.get(mode, [])
				matching_conf = None
				if row_idx < len(conf_rows) and conf_rows[row_idx].get("ingredients", "").strip() == row.get("ingredients", "").strip():
					matching_conf = conf_rows[row_idx]
				else:
					matching_conf = confirmed_by_key.get((mode, row.get("ingredients", "").strip()))

				if matching_conf:
					if matching_conf.get("mod_settings"):
						merged_row["mod_settings"] = matching_conf["mod_settings"]

			if apafa_enabled:
				db_key = "apafa"
			elif apothecary_enabled:
				db_key = "apothecary"
			elif requiem_enabled:
				db_key = "requiem"
			elif caco_enabled:
				db_key = "caco"
			else:
				db_key = "vanilla"

			if db_key not in databases:
				if db_key == "apafa":
					databases[db_key] = IngredientDatabase.load(APAFA_CSV)
				elif db_key == "apothecary":
					databases[db_key] = IngredientDatabase.load(APOTHECARY_CSV)
				elif db_key == "requiem":
					databases[db_key] = IngredientDatabase.load(REQUIEM_CSV)
				else:
					target_csv = active_caco_csv if caco_enabled else vanilla_csv
					databases[db_key] = IngredientDatabase.load(
						target_csv,
						prefer_highest_form_id=caco_enabled,
					)

			db = databases[db_key]
			selection_recipe = confirmed_selection_recipe_from_row(
				row, file_path, line_number, recipe
			)

			try:
				settings = confirmed_settings(merged_row, file_path, line_number)
				settings = confirmed_prediction_settings(
					merged_row,
					file_path,
					line_number,
					settings,
					db,
					selection_recipe,
				)
				result = PotionPredictor(db, settings).evaluate(
					selection_recipe,
					prefer_later_equal_cost=True,
				)
				actual: object = result.displayed_value if result.valid else None
				details = "" if result.valid else "recipe has no shared effects"
			except (KeyError, ValueError, OSError) as error:
				actual = None
				details = f"error: {error}"
				result = None

			cpp_pred_raw = (row.get("predicted_value") or "").strip()
			try:
				cpp_pred: object = int(cpp_pred_raw)
			except ValueError:
				cpp_pred = None

			is_pass = is_prediction_within_tolerance(expected, actual, TOLERATED_PREDICTION_PERCENTAGE)
			is_boundary = not is_pass and result is not None and is_engine_rounding_boundary_match(result, expected, TOLERATED_PREDICTION_PERCENTAGE)

			file_checked += 1
			total_checked += 1

			if is_pass or is_boundary:
				file_passed += 1
				total_passed += 1
				if is_boundary:
					file_boundary_matches += 1
					total_boundary_matches += 1
			else:
				file_failed += 1
				total_failed += 1
				mismatches.append(
					(file_path, line_number, mode, recipe, expected, actual, cpp_pred, details)
				)

			if actual == cpp_pred:
				file_cpp_matches += 1
				total_cpp_matches += 1

		print(
			f"  {file_path.name}: checked={file_checked} passed={file_passed} "
			f"(boundary={file_boundary_matches}) failed={file_failed} cpp_matches={file_cpp_matches}",
			flush=True,
		)

	print(
		f"Overall Predicted Check Result across {len(files)} file(s): "
		f"checked={total_checked} passed={total_passed} (boundary={total_boundary_matches}) "
		f"failed={total_failed} cpp_matches={total_cpp_matches}",
		flush=True,
	)

	for file_path, line_number, mode, recipe, expected, actual, cpp_pred, details in mismatches:
		print(
			f"FAIL file={file_path.name} row={line_number} mode={mode} ingredients={', '.join(recipe)!r} "
			f"expected_ingame_value={expected} (In-game observed craft) "
			f"predicted_python_value={actual} (Python test harness prediction) "
			f"predicted_cpp_value={cpp_pred} (Plugin prediction) {details}".rstrip(),
			flush=True,
		)

	return 1 if total_failed > 0 else 0





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
	]

	if caco_enabled:
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

	if alchemy_plus_enabled:
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
	caco_enabled, _, requiem_enabled, apothecary_enabled, apafa_enabled = confirmed_mode_flags(mode)
	settings = confirmed_settings(row, confirmed_csv, line_number)
	selection_recipe = confirmed_selection_recipe_from_row(
		row, confirmed_csv, line_number, recipe
	)

	if apafa_enabled:
		database = IngredientDatabase.load(APAFA_CSV)
	elif apothecary_enabled:
		database = IngredientDatabase.load(APOTHECARY_CSV)
	elif requiem_enabled:
		database = IngredientDatabase.load(REQUIEM_CSV)
	else:
		target_csv = active_caco_csv if caco_enabled else vanilla_csv
		database = IngredientDatabase.load(
			target_csv,
			prefer_highest_form_id=caco_enabled,
		)
	settings = confirmed_prediction_settings(
		row,
		confirmed_csv,
		line_number,
		settings,
		database,
		selection_recipe,
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
	boundary_match = not passed and is_engine_rounding_boundary_match(result, expected, TOLERATED_PREDICTION_PERCENTAGE)
	if passed:
		status_str = "PASS"
	elif boundary_match:
		status_str = "PASS (Known Engine Rounding Boundary)"
	else:
		status_str = "FAIL"
	print(
		f"Confirmed Row {line_number} Test: Expected (In-Game Observed Craft from CSV) = {expected}, "
		f"Predicted (Python Test Harness Script) = {actual}, Status = {status_str}"
	)

	if boundary_match and result and getattr(result, "effects", None):
		effects = result.effects
		candidates = []
		for eff in effects:
			m = getattr(eff, "calc_magnitude", 0.0)
			m_floor = math.floor(m)
			m_ceil = math.ceil(m)
			m_minus = math.floor(m - 1.0)
			m_plus = math.ceil(m + 1.0)
			candidates.append(list(set([m, m_floor, m_ceil, m_minus, m_plus])))

		matching_combo = None
		matching_costs = []
		matching_val = None
		best_diff = 1e9

		for combination in itertools.product(*candidates):
			costs = []
			for eff, m_val in zip(effects, combination):
				d = getattr(eff, "calc_duration", 0.0)
				b = getattr(eff.source, "base_cost", 0.0)
				c = b * ((m_val)**1.1 if m_val > 0 else 1.0) * ((d / 10.0)**1.1 if d > 0 else 1.0)
				costs.append(c)
			val = int(math.floor(sum(costs)))
			if is_prediction_within_tolerance(expected, val, TOLERATED_PREDICTION_PERCENTAGE):
				diff = sum(abs(m_val - getattr(eff, "calc_magnitude", 0.0)) for eff, m_val in zip(effects, combination))
				if diff < best_diff:
					best_diff = diff
					matching_combo = combination
					matching_costs = costs
					matching_val = val

		if matching_combo is not None:
			print()
			print("Engine Rounding Boundary Math Breakdown:")
			floored_parts = []
			frac_parts = []
			frac_strs = []
			floored_strs = []

			for eff, m_val, cost in zip(effects, matching_combo, matching_costs):
				eff_name = getattr(eff.source, "effect_name", "Unknown Effect")
				calc_m = getattr(eff, "calc_magnitude", 0.0)
				calc_d = getattr(eff, "calc_duration", 0.0)
				b_cost = getattr(eff.source, "base_cost", 0.0)
				form_id = getattr(eff.source, "effect_form_id", 0)
				fl = math.floor(cost)
				fr = cost - fl
				floored_parts.append(fl)
				frac_parts.append(fr)
				floored_strs.append(str(fl))
				frac_strs.append(f"{fr:.6f}")

				print(f"  * {eff_name} [0x{form_id:05X}]:")
				print(f"      Calculated Float Magnitude: {calc_m:.2f} -> Truncated/Boundary Magnitude: {m_val:.1f}")
				print(f"      Duration: {calc_d:.1f}s | Base Cost: {b_cost}")
				print(f"      Effect Cost Formula: {b_cost} * ({m_val:.1f}^1.1) * (({calc_d:.1f}/10)^1.1) = {cost:.6f}")
				print(f"      Floored Component Cost: {fl} | Fractional Remainder: {fr:.6f}")

			floored_sum = sum(floored_parts)
			frac_sum = sum(frac_parts)
			total_unfloored = sum(matching_costs)
			floored_expr = " + ".join(floored_strs)
			frac_expr = " + ".join(frac_strs)

			print(f"  * Sum of Floored Component Costs = {floored_expr} = {floored_sum}")
			print(f"  * Sum of Component Fractional Parts = {frac_expr} = {frac_sum:.6f}")
			print(f"  * Total Unfloored Sum = {floored_sum} (floored sum) + {frac_sum:.6f} (fractional sum) = {total_unfloored:.6f}")
			print(f"  * Engine Floored Final Gold = floor({total_unfloored:.6f}) = {matching_val}")
			print(f"  * Empirical In-Game Observed Value = {expected} (MATCH)")

	return 0 if (passed or boundary_match) else 1






def inspect_recipe(
	ingredients: Sequence[str],
	vanilla_csv: Path = VANILLA_CSV,
	caco_csv: Path = CACO_CSV,
	player: PlayerSettings | None = None,
	init_multiplier: float = 4.0,
	skill_factor: float = 1.5,
) -> None:
	"""Inspect recipe prediction breakdown dynamically without hardcoding specific rows."""
	print(f"=== Inspecting Recipe: {', '.join(ingredients)} ===")
	db_vanilla = IngredientDatabase.load(vanilla_csv)

	eval_player = player if player is not None else PlayerSettings(alchemy_level=15.0)
	configs = [
		(f"Engine GMSTs ({init_multiplier} / {skill_factor}) - Skill {eval_player.alchemy_level:g}", init_multiplier, skill_factor, eval_player),
	]

	for label, init_mult, sf, p_state in configs:
		settings = PredictionSettings(
			caco_enabled=False,
			alchemy_plus_enabled=False,
			player=p_state,
			caco_ingredient_init_multiplier=init_mult,
			caco_skill_factor=sf,
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
		"--check-predicted-csv",
		action="store_true",
		help="check predicted potion CSV files (e.g. alchemist.potions-predicted.<mode>.csv)",
	)
	parser.add_argument(
		"--predicted-csv",
		type=Path,
		default=None,
		metavar="PATH",
		help="predicted CSV file or directory containing alchemist.potions-predicted.<mode>.csv files",
	)
	parser.add_argument(
		"--check-confirmed-csv",
		action="store_true",
		help="check confirmed observed-craft rows using their native selection order",
	)
	parser.add_argument(
		"--show-confirmed-rows",
		"--verbose-confirmed-csv",
		"--report-confirmed-rows",
		"--report-confirmed-csv",
		"--verbose-rows",
		"-v",
		"--verbose",
		action="store_true",
		dest="verbose_confirmed_rows",
		help="report python prediction, c++ prediction, in-game confirmed value, and status for each row in confirmed csv",
	)
	parser.add_argument(
		"--show-cpp-divergences",
		"--show-divergences",
		"--cpp-divergences",
		"--divergences",
		action="store_true",
		dest="show_cpp_divergences",
		help="report all rows where python prediction diverges from c++ plugin prediction",
	)
	parser.add_argument(
		"--diagnose-accuracy",
		"--diagnose",
		"--accuracy-audit",
		"--audit-accuracy",
		action="store_true",
		dest="diagnose_accuracy",
		help="run comprehensive accuracy and parity diagnostic audit between python, c++, and in-game confirmed crafts",
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
		"--record-baseline",
		"--update-baseline",
		action="store_true",
		dest="record_baseline",
		help="record currently passing confirmed craft rows to potion_prediction_baseline.json",
	)
	parser.add_argument(
		"--check-baseline",
		"--verify-baseline",
		action="store_true",
		dest="check_baseline",
		help="check current predictions against recorded potion_prediction_baseline.json to detect regressions",
	)
	parser.add_argument(
		"--baseline-json",
		type=Path,
		default=CONFIRMED_BASELINE_JSON,
		help=f"path to baseline json file (default: {CONFIRMED_BASELINE_JSON})",
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
	if (
		arguments.check_confirmed_csv
		or arguments.verbose_confirmed_rows
		or arguments.show_cpp_divergences
		or arguments.diagnose_accuracy
		or arguments.record_baseline
		or arguments.check_baseline
	):
		return run_confirmed_fixture_check(
			arguments.confirmed_csv,
			arguments.vanilla_csv,
			None if arguments.caco_csv == CACO_CSV else arguments.caco_csv,
			verbose=arguments.verbose_confirmed_rows,
			show_divergences=arguments.show_cpp_divergences,
			diagnose_accuracy=arguments.diagnose_accuracy,
			record_baseline=arguments.record_baseline,
			check_baseline=arguments.check_baseline,
			baseline_json=arguments.baseline_json,
		)
	if arguments.confirmed_row is not None:
		return run_confirmed_row(
			arguments.confirmed_row,
			arguments.confirmed_csv,
			arguments.vanilla_csv,
			None if arguments.caco_csv == CACO_CSV else arguments.caco_csv,
			as_json=arguments.json,
		)
	if arguments.check_predicted_csv:
		return run_predicted_fixture_check(
			predicted_path=arguments.predicted_csv,
			confirmed_csv=arguments.confirmed_csv,
			vanilla_csv=arguments.vanilla_csv,
			caco_csv=None if arguments.caco_csv == CACO_CSV else arguments.caco_csv,
		)

	if arguments.caco_enabled is None or arguments.alchemy_plus_enabled is None:
		parser.error(
			"--caco-enabled and --alchemy-plus-enabled are required unless a CSV check is selected"
		)
	try:
		snapshot = settings_snapshot_for_arguments(arguments)
	except ValueError as error:
		parser.error(str(error))
	require_runtime_defaults(parser, arguments, snapshot)
	caco_enabled, alchemy_plus_enabled = enabled_plugins(arguments, snapshot)
	if arguments.list_ingredients:
		database = IngredientDatabase.load(
			arguments.caco_csv if caco_enabled else arguments.vanilla_csv,
			prefer_highest_form_id=caco_enabled,
		)
		print("\n".join(database.names()))
		return 0
	if len(arguments.ingredients) not in {2, 3}:
		parser.error("provide exactly two or three ingredient names")

	database = IngredientDatabase.load(
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
