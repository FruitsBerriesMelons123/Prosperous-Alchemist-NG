"""Helper module for pat test mode python scripts to apply disk configurations."""

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import config


def refresh_mo2_if_running() -> None:
    """If ModOrganizer.exe is running, run 'ModOrganizer.exe refresh' to force MO2 to update its in-memory state."""
    try:
        res = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ModOrganizer.exe", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        if "ModOrganizer.exe" in res.stdout:
            subprocess.run([str(config.MO2_EXECUTABLE), "refresh"], check=False)
    except Exception:
        pass


def validate_ingredient_combination(ingredients: List[str], caco_enabled: bool) -> tuple[bool, str]:
    """Validate whether an ingredient combination can craft a potion in Skyrim."""
    import csv
    repo_root = Path(__file__).resolve().parent
    csv_file = repo_root / ("ingredients-caco.csv" if caco_enabled else "ingredients-vanilla.csv")
    if not csv_file.exists():
        return (True, "CSV file not found, skipping validation")

    effects_by_ing: Dict[str, set] = {}
    with open(csv_file, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            ing = row["ingredient_name"]
            eff = row["effect_name"]
            effects_by_ing.setdefault(ing, set()).add(eff)

    for ing in ingredients:
        if ing not in effects_by_ing:
            return (False, f"Ingredient '{ing}' not found in {csv_file.name}")

    for i in range(len(ingredients)):
        for j in range(i + 1, len(ingredients)):
            ing1, ing2 = ingredients[i], ingredients[j]
            shared = effects_by_ing[ing1] & effects_by_ing[ing2]
            if shared:
                return (True, f"Valid craftable recipe: '{ing1}' + '{ing2}' share {sorted(shared)}")

    return (False, f"Invalid recipe: ingredients {ingredients} share 0 effects in {csv_file.name}")

EXEMPLARS_LIST = [
    "Skyrim.esm|E3E9A",
    "Skyrim.esm|65A72",
    "Skyrim.esm|65A3E",
    "Skyrim.esm|65A3F",
    "Skyrim.esm|65A5A",
    "Skyrim.esm|74A29",
    "Skyrim.esm|74A23",
    "Skyrim.esm|74A2D",
    "Skyrim.esm|74A27",
    "Skyrim.esm|74A21",
]

DEFAULTS: Dict[str, Any] = {
    "impureCostFix.enabled": True,
    "roundedPotency.enabled": True,
    "roundedPotency.magnitudeThreshold": 25.0,
    "roundedPotency.magnitudeMult": 5.0,
    "roundedPotency.durationThreshold": 15.0,
    "roundedPotency.durationMult": 5.0,
    "roundedPotency.overrides": {},
}


def build_ap_json(
    mag_thresh: float = 25.0,
    mag_mult: float = 5.0,
    dur_thresh: float = 15.0,
    dur_mult: float = 5.0,
    overrides: Optional[Dict[str, Any]] = None,
    impure_cost_fix: bool = True,
) -> Dict[str, Any]:
    rounded_potency: Dict[str, Any] = {
        "$comment": "Round effect potency to a multiple above a threshold.",
        "enabled": True,
        "magnitudeThreshold": mag_thresh,
        "magnitudeMult": mag_mult,
        "durationThreshold": dur_thresh,
        "durationMult": dur_mult,
        "overrides": {
            "$comment": "Define setting overrides per alchemy effect."
        },
    }
    if overrides:
        for k, v in overrides.items():
            key = k if "|" in k else f"Skyrim.esm|{k}"
            rounded_potency["overrides"][key] = v

    return {
        "knownFailureFix": {
            "$comment": "Display known failures in UI between ingredients with all effects known.",
            "enabled": True,
        },
        "mixtureNames": {
            "$comment": "Modify names to reflect additional effects/impurities.",
            "enabled": True,
        },
        "impureCostFix": {
            "$comment": "Impurities in mixtures subtract from the cost instead of adding to it.",
            "enabled": impure_cost_fix,
        },
        "copyExemplars": {
            "$comment": "Swap models and names of crafted potions to the nearest exemplar.",
            "enabled": True,
            "exemplars": EXEMPLARS_LIST,
        },
        "roundedPotency": rounded_potency,
    }


def extract_settings(json_data: Dict[str, Any]) -> Dict[str, Any]:
    res: Dict[str, Any] = {}
    res["impureCostFix.enabled"] = json_data.get("impureCostFix", {}).get("enabled", True)
    rp = json_data.get("roundedPotency", {})
    res["roundedPotency.enabled"] = rp.get("enabled", True)
    res["roundedPotency.magnitudeThreshold"] = float(rp.get("magnitudeThreshold", 25.0))
    res["roundedPotency.magnitudeMult"] = float(rp.get("magnitudeMult", 5.0))
    res["roundedPotency.durationThreshold"] = float(rp.get("durationThreshold", 15.0))
    res["roundedPotency.durationMult"] = float(rp.get("durationMult", 5.0))

    ov = {k: v for k, v in rp.get("overrides", {}).items() if not k.startswith("$")}
    res["roundedPotency.overrides"] = ov
    return res


def update_mo2_modlist(caco_enabled: bool, ap_enabled: bool) -> None:
    modlist_path = config.MO2_DEFAULT_PROFILE_DIR / "modlist.txt"
    if not modlist_path.exists():
        return

    pa_ng_mod_name = config.PA_NG_MOD_DIR.name

    target_states = {
        config.CACO_MOD_DIR.name: (caco_enabled, "disabled"),
        config.KRYPTOPYR_PATCHES_MOD_DIR.name: (caco_enabled, "disabled"),
        config.ALCHEMY_PLUS_MOD_DIR.name: (ap_enabled, "disabled"),
        pa_ng_mod_name: (True, "enabled"),
    }

    lines = modlist_path.read_text(encoding="utf-8").splitlines()

    initial_states: Dict[str, bool] = {}
    for line in lines:
        if line.startswith("+") or line.startswith("-"):
            mod_name = line[1:]
            if mod_name in target_states:
                initial_states[mod_name] = line.startswith("+")

    # Pass 1: Set CACO, Patches, AP to target states, and temporarily disable PA NG to trigger MO2 reload
    pass1_lines = []
    for line in lines:
        if line.startswith("+") or line.startswith("-"):
            mod_name = line[1:]
            if mod_name in target_states:
                should_enable = False if mod_name == pa_ng_mod_name else target_states[mod_name][0]
                prefix = "+" if should_enable else "-"
                pass1_lines.append(prefix + mod_name)
                continue
        pass1_lines.append(line)

    modlist_path.write_text("\n".join(pass1_lines) + "\n", encoding="utf-8")
    refresh_mo2_if_running()
    time.sleep(0.25)

    # Pass 2: Re-enable PA NG
    pass2_lines = []
    for line in lines:
        if line.startswith("+") or line.startswith("-"):
            mod_name = line[1:]
            if mod_name in target_states:
                should_enable = target_states[mod_name][0]
                prefix = "+" if should_enable else "-"
                pass2_lines.append(prefix + mod_name)
                continue
        pass2_lines.append(line)

    modlist_path.write_text("\n".join(pass2_lines) + "\n", encoding="utf-8")
    refresh_mo2_if_running()

    for mod_name, (final_state, default_str) in target_states.items():
        init_state = initial_states.get(mod_name)
        if init_state is not None and init_state != final_state:
            prev_str = "enabled" if init_state else "disabled"
            new_str = "enabled" if final_state else "disabled"
            print(
                f"modlist.{mod_name}: default = {default_str}, previous = {prev_str}, changed to = {new_str}"
            )



def restore_mo2_loadorder() -> None:
    pairs = [
        (config.BACKUP_LOCKEDORDER, config.MO2_DEFAULT_PROFILE_DIR / "lockedorder.txt"),
        (config.BACKUP_LOADORDER, config.MO2_DEFAULT_PROFILE_DIR / "loadorder.txt"),
        (config.BACKUP_PLUGINS, config.MO2_DEFAULT_PROFILE_DIR / "plugins.txt"),
    ]

    for src, dst in pairs:
        if src.exists() and dst.exists():
            src_text = src.read_text(encoding="utf-8")
            dst_text = dst.read_text(encoding="utf-8")
            if src_text != dst_text:
                dst.write_text(src_text, encoding="utf-8")
                print(
                    f"loadorder.{dst.name}: default = backup, previous = modified, changed to = restored from backup"
                )


def sync_mo2_plugins_txt(caco_enabled: bool) -> None:
    plugins_path = config.MO2_DEFAULT_PROFILE_DIR / "plugins.txt"
    if not plugins_path.exists():
        return
    caco_plugins = [
        "complete alchemy & cooking overhaul.esp",
        "cc-survivalmode_ussep_caco_patch.esp",
        "cc-rarecurios_caco_patch.esp",
        "cc-fishing_caco_patch.esp",
        "cc-saints&seducers_caco_patch.esp",
    ]
    lines = plugins_path.read_text(encoding="utf-8").splitlines()
    new_lines = []
    modified = False
    for line in lines:
        raw = line.lstrip("*").lower()
        if raw in caco_plugins:
            new_line = f"*{line.lstrip('*')}" if caco_enabled else line.lstrip("*")
            if new_line != line:
                modified = True
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    if modified:
        plugins_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def safe_exists(p: Path) -> bool:
    try:
        return p.exists()
    except Exception:
        return False


def apply_mode_config(
    mode_name: str,
    caco_enabled: bool,
    ap_enabled: bool,
    ap_json_data: Dict[str, Any],
) -> None:
    # 1. Update MO2 modlist, restore load order, and sync plugins.txt
    update_mo2_modlist(caco_enabled=caco_enabled, ap_enabled=ap_enabled)
    restore_mo2_loadorder()
    sync_mo2_plugins_txt(caco_enabled=caco_enabled)
    refresh_mo2_if_running()

    # 2. Target JSON files
    json_targets = [
        Path("links/AlchemyPlus.json"),
        config.CACO_SETTINGS,
    ]

    prev_json_path = json_targets[0] if safe_exists(json_targets[0]) else json_targets[1]
    if safe_exists(prev_json_path):
        try:
            prev_data = json.loads(prev_json_path.read_text(encoding="utf-8"))
            prev_settings = extract_settings(prev_data)
        except Exception:
            prev_settings = dict(DEFAULTS)
    else:
        prev_settings = dict(DEFAULTS)

    new_settings = extract_settings(ap_json_data)

    scalar_keys = [
        "impureCostFix.enabled",
        "roundedPotency.enabled",
        "roundedPotency.magnitudeThreshold",
        "roundedPotency.magnitudeMult",
        "roundedPotency.durationThreshold",
        "roundedPotency.durationMult",
    ]

    for key in scalar_keys:
        prev_val = prev_settings.get(key)
        new_val = new_settings.get(key)
        default_val = DEFAULTS.get(key)
        if prev_val != new_val:
            print(f"{key}: default = {default_val}, previous = {prev_val}, changed to = {new_val}")

    prev_overrides = prev_settings.get("roundedPotency.overrides", {})
    new_overrides = new_settings.get("roundedPotency.overrides", {})

    all_override_keys = sorted(set(list(prev_overrides.keys()) + list(new_overrides.keys())))
    for form_id in all_override_keys:
        p_val = prev_overrides.get(form_id)
        n_val = new_overrides.get(form_id)
        if p_val != n_val:
            print(
                f"roundedPotency.overrides.{form_id}: default = None, previous = {p_val}, changed to = {n_val}"
            )

    formatted_json = json.dumps(ap_json_data, indent=2)
    for p in json_targets:
        if safe_exists(p.parent):
            try:
                p.write_text(formatted_json + "\n", encoding="utf-8")
            except Exception:
                pass
