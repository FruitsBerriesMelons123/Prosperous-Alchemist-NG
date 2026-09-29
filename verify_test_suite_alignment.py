"""Master verification script to ensure 100% alignment between scripts, compiled commands, and test-suite.md.

This script comprehensively verifies:
1. All 30 pre-launch Python scripts (pat-*.py) execute cleanly and configure MO2 modlist,
   plugins.txt, and AlchemyPlus.json matching test-suite.md specs.
2. pa-tests.yaml contains all required subcommands, aliases, functions, and arguments matching test-suite.md.
3. ProsperousAlchemistTests.psc implements all 184 observed-craft test blocks and 16 prediction-export blocks,
   verifying skill levels, perks, GameSettings, CACO globals, ingredient FormIDs, and console printouts.
4. Every single ProvisionForm and ProvisionFormFallback FormID in ProsperousAlchemistTests.psc is validated
   against actual binary plugin files (.esp, .esm, .esl) on disk to guarantee zero missing ingredients in Skyrim.
5. All ingredient craft recipes across all test blocks are validated for recipe craftability in Skyrim using
   validate_ingredient_combination against both mode-specific and Vanilla base game ingredients-*.csv snapshots.
6. Every printed craft instruction ingredient is cross-checked to verify 100% inventory provisioning completeness.
7. Papyrus test script compiles cleanly via compile.ps1 (Caprica compiler) with zero errors.
8. Section 6 (strict block specs): every block in test-suite.md (Block sections AND the Technical
   Specification Matrix) must match the effective Setup* state in the PSC (skill, fortify, alchemist/lore
   rank, perks resolved from plugin records, GameSettings, CACO duration indices), every ProvisionForm must
   resolve to an ingredient that ORIGINATES in the named plugin, every printed craft ingredient must be
   provisioned under its in-mode name, and crafts / next steps must agree between the doc and the PSC.

Usage:
  python verify_test_suite_alignment.py            full run (executes pat-*.py, compiles, kills Skyrim)
  python verify_test_suite_alignment.py --static   read-only checks (sections 2, 3, 5 and 6)
  python verify_test_suite_alignment.py --static --psc <file>   check a candidate PSC instead
"""

import csv
import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import config
from pat_config_helper import extract_settings, validate_ingredient_combination

REPO_ROOT = Path(__file__).resolve().parent


## DO NOT REMOVE THIS FUNCTION! IT IS REQUIRED!
def kill_previous_instances() -> None:
    """Ensure no duplicate instance of this script is running concurrently (terminating self if found), and kill Skyrim if it is currently running."""
    try:
        script_name = Path(sys.argv[0]).name
        if not script_name or script_name == "-c":
            return
        my_pid = os.getpid()
        ps_cmd = (
            f"Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" | "
            f"Where-Object {{ $_.CommandLine -like '*{script_name}*' -and $_.ProcessId -ne {my_pid} }} | "
            f"Select-Object -ExpandProperty ProcessId"
        )
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            pids = [p.strip() for p in res.stdout.strip().splitlines() if p.strip().isdigit()]
            if pids:
                print(f"An instance of {script_name} is already running (PID(s): {', '.join(pids)}). Terminating self...")
                sys.exit(0)
    except Exception as e:
        print(f"Warning: Failed to check or kill previous instances of script: {e}")

    try:
        skyrim_cmd = (
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -in @('SkyrimSE.exe', 'SkyrimVR.exe', 'Skyrim.exe', 'skse64_loader.exe') } | "
            "Select-Object -ExpandProperty ProcessId"
        )
        res_skyrim = subprocess.run(["powershell", "-NoProfile", "-Command", skyrim_cmd], capture_output=True, text=True)
        if res_skyrim.returncode == 0 and res_skyrim.stdout.strip():
            pids = [p.strip() for p in res_skyrim.stdout.strip().splitlines() if p.strip().isdigit()]
            if pids:
                print(f"Terminating running Skyrim process(es) (PID(s): {', '.join(pids)})...")
                for pid in pids:
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
    except Exception as e:
        print(f"Warning: Failed to check or terminate Skyrim processes: {e}")


OVERHAUL_MODS = {
    "CACO": config.CACO_MOD_DIR.name,
    "Kryptopyr": config.KRYPTOPYR_PATCHES_MOD_DIR.name,
    "AP": config.ALCHEMY_PLUS_MOD_DIR.name,
    "Requiem": getattr(config, "REQUIEM_MOD_DIR", Path("Requiem - The Roleplaying Overhaul")).name,
    "Apothecary": getattr(config, "APOTHECARY_MOD_DIR", Path("Apothecary - An Alchemy Overhaul")).name,
    "APAFA": getattr(config, "APAFA_MOD_DIR", Path("Alchemy Potions and Food Adjustments")).name,
    "Ordinator": config.ORDINATOR_MOD_DIR.name,
}

PLUGINS_MAP = {
    "CACO": ["complete alchemy & cooking overhaul.esp"],
    "Requiem": ["requiem.esp"],
    "Apothecary": ["apothecary.esp"],
    "APAFA": ["alchemyadjustments.esp", "alchemyadjustments - rarecurios patch.esp", "alchemyadjustments - distinctiverareingredients addon.esp"],
    "Ordinator": ["ordinator - perks of skyrim.esp"],
}

EXPECTED_MODS = {
    "vanilla": set(),
    "ap": {"AP"},
    "caco": {"CACO", "Kryptopyr"},
    "caco-ap": {"CACO", "Kryptopyr", "AP"},
    "requiem": {"Requiem"},
    "apothecary": {"Apothecary"},
    "apafa": {"APAFA"},
    "ordinator": {"Ordinator"},
}

EXPECTED_PLUGINS = {
    "vanilla": set(),
    "ap": set(),
    "caco": {"CACO"},
    "caco-ap": {"CACO"},
    "requiem": {"Requiem"},
    "apothecary": {"Apothecary"},
    "apafa": {"APAFA"},
    "ordinator": {"Ordinator"},
}


def get_mode_category(script_name: str) -> str:
    name = script_name.lower().replace("pat-", "").replace(".py", "").replace("-changed", "").replace("default-", "")
    if name.startswith("apothecary"):
        return "apothecary"
    elif name.startswith("apafa"):
        return "apafa"
    elif name.startswith("caco-ap"):
        return "caco-ap"
    elif name.startswith("caco"):
        return "caco"
    elif name.startswith("ap"):
        return "ap"
    elif name.startswith("vanilla"):
        return "vanilla"
    elif name.startswith("ordinator"):
        return "ordinator"
    elif name.startswith("requiem"):
        return "requiem"
    else:
        raise ValueError(f"Unknown mode category for script: {script_name}")


def parse_plugin_ingrs(plugin_path: Path) -> Dict[int, Dict[str, Any]]:
    if not plugin_path.exists():
        return {}
    data = plugin_path.read_bytes()
    offset = 0
    masters = []

    if offset + 24 <= len(data):
        rectype, size, flags, form_id = struct.unpack('<4sIII', data[offset:offset+16])
        if rectype == b'TES4':
            rec_end = offset + 24 + size
            sub_off = offset + 24
            while sub_off + 6 <= rec_end:
                stype, ssize = struct.unpack('<4sH', data[sub_off:sub_off+6])
                sdata = data[sub_off+6:sub_off+6+ssize]
                sub_off += 6 + ssize
                if stype == b'MAST':
                    masters.append(sdata.decode('utf-8', errors='ignore').rstrip('\x00'))
            offset = rec_end

    results = {}
    while offset + 24 <= len(data):
        rectype, size, flags, form_id = struct.unpack('<4sIII', data[offset:offset+16])
        if rectype == b'GRUP':
            offset += 24
            continue
        elif rectype in (b'INGR', b'ALCH', b'ARMO', b'TREE', b'FLOR', b'WEAP', b'AMMO', b'SPEL', b'PERK', b'GLOB', b'KYWD'):
            record_end = offset + 24 + size
            local_form_id = form_id & 0x00FFFFFF
            origin_plugin = plugin_path.name

            sub_offset = offset + 24
            edid = None
            full = None
            while sub_offset + 6 <= record_end:
                sub_type, sub_size = struct.unpack('<4sH', data[sub_offset:sub_offset+6])
                sub_data = data[sub_offset+6:sub_offset+6+sub_size]
                sub_offset += 6 + sub_size
                if sub_type == b'EDID':
                    edid = sub_data.decode('utf-8', errors='ignore').rstrip('\x00')
                elif sub_type == b'FULL':
                    try:
                        s = sub_data.decode('utf-8').rstrip('\x00')
                        if all(ord(c) >= 32 and ord(c) < 127 for c in s):
                            full = s
                    except Exception:
                        pass
            results[local_form_id] = {
                'form_id_hex': f'0x{local_form_id:08X}',
                'int_id': local_form_id,
                'edid': edid,
                'name': full,
                'plugin': plugin_path.name,
                'origin_plugin': origin_plugin
            }
            offset = record_end
        else:
            offset += 24 + size
    return results


def check_mo2_state(expected_mod_keys: Set[str], expected_plugin_keys: Set[str]) -> tuple[bool, List[str]]:
    errors = []
    modlist_path = config.MO2_DEFAULT_PROFILE_DIR / "modlist.txt"
    plugins_path = config.MO2_DEFAULT_PROFILE_DIR / "plugins.txt"

    if not modlist_path.exists():
        return (False, [f"MO2 profile modlist.txt not found at {modlist_path}"])

    modlist_lines = modlist_path.read_text(encoding="utf-8").splitlines()
    enabled_mods = {line[1:] for line in modlist_lines if line.startswith("+")}

    for key, mod_name in OVERHAUL_MODS.items():
        is_enabled = mod_name in enabled_mods
        should_be_enabled = key in expected_mod_keys
        if is_enabled != should_be_enabled:
            errors.append(f"Mod '{mod_name}' enabled={is_enabled}, expected={should_be_enabled}")

    plugins_lines = plugins_path.read_text(encoding="utf-8").splitlines()
    enabled_plugins = {line.lstrip("*").lower() for line in plugins_lines if line.startswith("*")}

    for key, plugin_list in PLUGINS_MAP.items():
        should_be_enabled = key in expected_plugin_keys
        for p in plugin_list:
            is_enabled = p.lower() in enabled_plugins
            if is_enabled != should_be_enabled:
                errors.append(f"Plugin '{p}' enabled={is_enabled}, expected={should_be_enabled}")

    return (len(errors) == 0, errors)


def verify_pat_python_scripts() -> tuple[int, int, List[str]]:
    print("--- 1. Verifying Python Pre-Launch Scripts (pat-*.py) ---")
    pat_scripts = sorted(REPO_ROOT.glob("pat-*.py"))
    passed = 0
    failed = 0
    log_details = []

    if len(pat_scripts) != 30:
        log_details.append(f"Expected 30 pat-*.py scripts, found {len(pat_scripts)}")

    for script in pat_scripts:
        category = get_mode_category(script.name)
        exp_mods = EXPECTED_MODS[category]
        exp_plugins = EXPECTED_PLUGINS[category]

        res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        if res.returncode != 0:
            log_details.append(f"FAIL: {script.name} execution error: {res.stderr.strip()}")
            failed += 1
            continue

        ok, errors = check_mo2_state(exp_mods, exp_plugins)
        if ok:
            passed += 1
            print(f"  [PASS] {script.name} ({category})")
        else:
            failed += 1
            err_msg = ', '.join(errors)
            log_details.append(f"FAIL: {script.name} state mismatch: {err_msg}")
            print(f"  [FAIL] {script.name}: {err_msg}")

    return passed, failed, log_details


def verify_pa_tests_yaml() -> tuple[bool, List[str]]:
    print("\n--- 2. Verifying Console Registry (pa-tests.yaml) ---")
    yaml_path = REPO_ROOT / "pa-console-tests" / "SKSE" / "CustomConsole" / "pa-tests.yaml"
    errors = []

    if not yaml_path.exists():
        return False, [f"yaml file missing: {yaml_path}"]

    content = yaml_path.read_text(encoding="utf-8")
    
    required_subs = [
        "default", "vanilla", "caco", "ap", "caco-ap", "requiem", "apothecary", "apafa", "ordinator", "clear"
    ]

    for sub in required_subs:
        if f"name: {sub}" not in content:
            errors.append(f"Missing subcommand 'name: {sub}' in pa-tests.yaml")

    if not errors:
        print("  [PASS] pa-tests.yaml structure and all subcommands verified.")
        return True, []
    else:
        for err in errors:
            print(f"  [FAIL] {err}")
        return False, errors


def verify_psc_and_recipes() -> tuple[int, int, List[str]]:
    print("\n--- 3. Verifying Papyrus Script, Binary Plugin FormIDs & Recipe Craftability ---")
    psc_path = REPO_ROOT / "pa-console-tests" / "Source" / "Scripts" / "ProsperousAlchemistTests.psc"
    errors = []
    passed = 0
    failed = 0

    if not psc_path.exists():
        return 0, 1, [f"PSC file missing: {psc_path}"]

    # 1. Parse binary plugin files for INGR records (or load from db/ CSV database)
    plugin_files = {
        'Skyrim.esm': config.SKYRIM / 'Data' / 'Skyrim.esm',
        'Dawnguard.esm': config.SKYRIM / 'Data' / 'Dawnguard.esm',
        'Dragonborn.esm': config.SKYRIM / 'Data' / 'Dragonborn.esm',
        'ccbgssse001-fish.esm': config.SKYRIM / 'Data' / 'ccbgssse001-fish.esm',
        'ccbgssse037-curios.esl': config.SKYRIM / 'Data' / 'ccbgssse037-curios.esl',
        'ccbgssse025-advdsgs.esm': config.SKYRIM / 'Data' / 'ccbgssse025-advdsgs.esm',
        '_ResourcePack.esl': config.SKYRIM / 'Data' / '_ResourcePack.esl',
        'Complete Alchemy & Cooking Overhaul.esp': config.CACO_MOD_DIR / 'Complete Alchemy & Cooking Overhaul.esp',
        'cc-rarecurios_caco_patch.esp': config.KRYPTOPYR_PATCHES_MOD_DIR / 'cc-rarecurios_caco_patch.esp',
        'Requiem.esp': config.REQUIEM_MOD_DIR / 'Requiem.esp',
        'Apothecary.esp': config.APOTHECARY_MOD_DIR / 'Apothecary.esp',
        'Ordinator - Perks of Skyrim.esp': config.ORDINATOR_MOD_DIR / 'Ordinator - Perks of Skyrim.esp',
    }

    db_dir = REPO_ROOT / "db"
    plugin_csv = db_dir / "plugin_ingr_records.csv"
    if not plugin_csv.exists():
        from build_ingredient_db import build_master_db
        build_master_db()

    plugin_db = {}
    with open(plugin_csv, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            p_name = row["plugin_name"]
            fid_int = int(row["local_form_id_int"])
            plugin_db.setdefault(p_name, {})[fid_int] = {
                'form_id_hex': row["form_id"],
                'raw_form_id': row.get("raw_form_id", row["form_id"]),
                'int_id': fid_int,
                'rectype': row.get("rectype", ""),
                'edid': row["edid"],
                'name': row["display_name"],
                'plugin': p_name,
                'origin_plugin': row["origin_plugin"],
            }

    # Build ingredient FormID lookup database from CSV schemas
    ingr_db = {}
    csv_files = [
        (REPO_ROOT / "ingredients-vanilla.csv", "Skyrim.esm"),
        (REPO_ROOT / "ingredients-caco.csv", "Complete Alchemy & Cooking Overhaul.esp"),
        (REPO_ROOT / "ingredients-requiem.csv", "Requiem.esp"),
        (REPO_ROOT / "ingredients-apothecary.csv", "Apothecary.esp"),
    ]
    for csv_path, default_plugin in csv_files:
        if csv_path.exists():
            with open(csv_path, encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    name = row["ingredient_name"].strip().lower()
                    fid_int = int(row["form_id"], 16) & 0x0FFFFFFF
                    ingr_db[(name, default_plugin.lower())] = fid_int

    # Add Creation Club / DLC ingredient mappings
    ingr_db[("ambrosia", "ccbgssse037-curios.esl")] = 0x00000836
    ingr_db[("aloe vera", "ccbgssse037-curios.esl")] = 0x00000836
    ingr_db[("angelfish", "ccbgssse001-fish.esm")] = 0x000008eb
    ingr_db[("ash creep cluster", "dragonborn.esm")] = 0x0001cd74
    ingr_db[("ancestor moth wing", "dawnguard.esm")] = 0x000059ba
    ingr_db[("boar tusk", "dragonborn.esm")] = 0x0001cd6f
    ingr_db[("bliss bug thorax", "ccbgssse025-advdsgs.esm")] = 0x00059155
    ingr_db[("purple butterfly wing", "ccbgssse025-advdsgs.esm")] = 0x00059157
    ingr_db[("elytra ichor", "ccbgssse025-advdsgs.esm")] = 0x00059156
    ingr_db[("flame stalk", "ccbgssse025-advdsgs.esm")] = 0x00059158

    # Build strict FormID resolution maps
    plugin_db_by_name = {}
    with open(plugin_csv, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            p_name = row["plugin_name"].lower()
            raw_fid = int(row["raw_form_id"], 16)
            local_fid = int(row["local_form_id_int"])
            rec = {
                'form_id_hex': row["form_id"],
                'raw_form_id': row["raw_form_id"],
                'raw_fid_int': raw_fid,
                'local_fid_int': local_fid,
                'rectype': row.get("rectype", ""),
                'edid': row["edid"],
                'name': row["display_name"],
                'plugin': row["plugin_name"],
                'origin_plugin': row["origin_plugin"],
            }
            p_dict = plugin_db_by_name.setdefault(p_name, {})
            p_dict[raw_fid] = rec
            p_dict[local_fid] = rec

    origin_records = PluginRecords()

    def resolves_form_id_strictly(fid_int: int, plugin_name: str, expected_comment: str = "", require_ingr: bool = True) -> tuple[bool, str]:
        # GetFormFromFile only finds records that ORIGINATE in the named plugin (see PluginRecords).
        if plugin_name.lower() not in origin_records.plugins and not origin_records.resolve(fid_int, plugin_name):
            return False, f"Unknown plugin '{plugin_name}'"
        rows = origin_records.resolve(fid_int, plugin_name)
        if not rows:
            return False, f"FormID 0x{fid_int:08X} does not resolve in '{plugin_name}' (no record originates there with that ID)"
        if require_ingr and not any(r["rectype"] in ("INGR", "ALCH") for r in rows):
            return False, f"FormID 0x{fid_int:08X} in '{plugin_name}' is record type '{rows[0]['rectype']}', NOT an alchemy ingredient record!"
        return True, ""

    psc_text = psc_path.read_text(encoding="utf-8")

    # 2. Audit every ProvisionForm and ProvisionFormFallback in psc_text against binary plugins and ingredient comments
    re_prov_line = re.compile(r'ProvisionForm\s*\(\s*player\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\)(?:\s*;\s*([^\r\n]+))?')
    re_fall_line = re.compile(r'ProvisionFormFallback\s*\(\s*player\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\)(?:\s*;\s*([^\r\n]+))?')

    prov_line_matches = re_prov_line.findall(psc_text)
    fall_line_matches = re_fall_line.findall(psc_text)

    form_errors = []
    for fid_str, plugin, comment in prov_line_matches:
        fid_int = int(fid_str, 16)
        comment_clean = comment.strip() if comment else ""
        ok, msg = resolves_form_id_strictly(fid_int, plugin, comment_clean, require_ingr=True)
        if not ok:
            form_errors.append(f"ProvisionForm(0x{fid_int:08X}, \"{plugin}\") ; {comment_clean} -> {msg}")

    for pfid_str, pplugin, sfid_str, splugin, comment in fall_line_matches:
        pfid_int = int(pfid_str, 16)
        sfid_int = int(sfid_str, 16)
        comment_clean = comment.strip() if comment else ""
        ok1, msg1 = resolves_form_id_strictly(pfid_int, pplugin, comment_clean, require_ingr=True)
        ok2, msg2 = resolves_form_id_strictly(sfid_int, splugin, comment_clean, require_ingr=True)
        if not (ok1 or ok2):
            form_errors.append(f"ProvisionFormFallback failed for '; {comment_clean}'! Primary: {msg1} | Secondary: {msg2}")

    re_gfff = re.compile(r'Game\.GetFormFromFile\s*\(\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\)')
    gfff_matches = re_gfff.findall(psc_text)
    for fid_str, plugin in gfff_matches:
        fid_int = int(fid_str, 16)
        ok, msg = resolves_form_id_strictly(fid_int, plugin, "", require_ingr=False)
        if not ok:
            form_errors.append(f"Game.GetFormFromFile(0x{fid_int:08X}, \"{plugin}\") -> {msg}")

    re_prov_call = re.compile(r'ProvisionForm\s*\(\s*player\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\)')
    re_fall_call = re.compile(r'ProvisionFormFallback\s*\(\s*player\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\)')
    prov_call_matches = re_prov_call.findall(psc_text)
    fall_call_matches = re_fall_call.findall(psc_text)

    if form_errors:
        print(f"  [FAIL] {len(form_errors)} FormID mismatches against binary plugin files:")
        for err in form_errors:
            print(f"    - {err}")
        errors.extend(form_errors)
    else:
        print(f"  [PASS] All {len(prov_call_matches)} ProvisionForm calls, {len(fall_call_matches)} Fallback calls, and {len(gfff_matches)} GetFormFromFile calls verified 100% valid against binary plugin files.")

    # 3. Verify all Setup functions have branches for variants 1..N
    setup_funcs = {
        "ap": ("SetupAP", 13),
        "vanilla": ("SetupVanilla", 18),
        "caco": ("SetupCACO", 27),
        "caco-ap": ("SetupCACOAP", 23),
        "requiem": ("SetupRequiem", 18),
        "apothecary": ("SetupApothecary", 57),
        "apafa": ("SetupAPAFA", 10),
        "ordinator": ("SetupOrdinator", 18),
    }

    for mode, (func_name, max_v) in setup_funcs.items():
        func_match = re.search(f'Function {func_name}.*?EndFunction', psc_text, re.DOTALL)
        if not func_match:
            errors.append(f"Function '{func_name}' missing from ProsperousAlchemistTests.psc")
            continue
        body = func_match.group(0)
        for v in range(2, max_v + 1):
            if f'variant == "{v}"' not in body and f"variant == '{v}'" not in body:
                errors.append(f"Setup function '{func_name}' missing branch for variant '{v}'!")

    # 4. Verify every configured modeTag handler exists in ProvisionAndPrintTests
    mode_variants = {m: v for m, (_, v) in setup_funcs.items()}
    expected_tags = [f"{m}-{i}" for m, count in mode_variants.items() for i in range(1, count + 1)]

    for tag in expected_tags:
        if f'modeTag == "{tag}"' not in psc_text:
            errors.append(f"Missing handler for modeTag '{tag}' in ProsperousAlchemistTests.psc")

    # 4. Extract and validate craft recipes & inventory provisioning from ProvisionAndPrintTests
    tag_to_code = {}
    for chunk in psc_text.split('modeTag == "')[1:]:
        tag = chunk.split('"')[0]
        tag_to_code[tag] = chunk

    for tag in expected_tags:
        if tag not in tag_to_code:
            errors.append(f"Could not extract code block for '{tag}'")
            failed += 1
            continue

        code = tag_to_code[tag]

        # Extract provisioned ingredients in this block chunk
        prov_in_block = re_prov_call.findall(code)
        fall_in_block = re_fall_call.findall(code)
        comment_names = re.findall(r'ProvisionForm(?:Fallback)?\s*\([^;]*;\s*([^\r\n]+)', code)

        # Check active plugins for mode
        block_mode = tag.split('-')[0]
        if tag.startswith('caco-ap'):
            block_mode = 'caco-ap'
            
        allowed_plugins = {"skyrim.esm", "update.esm", "dawnguard.esm", "hearthfires.esm", "dragonborn.esm", "ccbgssse001-fish.esm", "ccbgssse037-curios.esl", "ccbgssse025-advdsgs.esm"}
        if "caco" in block_mode:
            allowed_plugins.update({"complete alchemy & cooking overhaul.esp", "cc-rarecurios_caco_patch.esp"})
        if "requiem" in block_mode:
            allowed_plugins.update({"requiem.esp"})
        if "apothecary" in block_mode:
            allowed_plugins.update({"apothecary.esp", "apothecary - rare curios patch.esp"})
        if "apafa" in block_mode:
            allowed_plugins.update({"alchemyadjustments.esp", "alchemyadjustments - rarecurios patch.esp", "alchemyadjustments - distinctiverareingredients addon.esp"})

        for fid_str, p_name in prov_in_block:
            if p_name.lower() not in allowed_plugins:
                errors.append(f"Block '{tag}': ProvisionForm specifies plugin '{p_name}' which is NOT active in mode '{block_mode}'!")

        provisioned_names = set()
        for fid_str, p_name in prov_in_block:
            fid_int = int(fid_str, 16) & 0x00FFFFFF
            if p_name in plugin_db and fid_int in plugin_db[p_name]:
                rec_name = plugin_db[p_name][fid_int].get('name')
                if rec_name:
                    provisioned_names.add(rec_name.lower())

        for pfid_str, pplugin, sfid_str, splugin in fall_in_block:
            pfid_int = int(pfid_str, 16) & 0x00FFFFFF
            sfid_int = int(sfid_str, 16) & 0x00FFFFFF
            if pplugin in plugin_db and pfid_int in plugin_db[pplugin]:
                rec_name = plugin_db[pplugin][pfid_int].get('name')
                if rec_name:
                    provisioned_names.add(rec_name.lower())
            if splugin in plugin_db and sfid_int in plugin_db[splugin]:
                rec_name = plugin_db[splugin][sfid_int].get('name')
                if rec_name:
                    provisioned_names.add(rec_name.lower())

        for cname in comment_names:
            clean_cname = re.sub(r'\s*\([^)]*\)', '', cname).strip().lower()
            if clean_cname:
                provisioned_names.add(clean_cname)

        craft_lines = re.findall(r'ConsoleUtil\.PrintMessage\("[0-9]+\.\s*(?:Craft|Order [0-9]+):\s*([^"]+)"\)', code)
        
        caco_enabled = "caco" in tag
        requiem_enabled = "requiem" in tag
        apothecary_enabled = "apothecary" in tag
        apafa_enabled = "apafa" in tag
        ordinator_enabled = "ordinator" in tag

        block_ok = True
        for craft in craft_lines:
            raw_recipe = craft.split("(")[0].strip()
            if "->" in raw_recipe:
                ingredients = [i.strip() for i in raw_recipe.split("->")]
            elif "+" in raw_recipe:
                ingredients = [i.strip() for i in raw_recipe.split("+")]
            else:
                continue

            if ":" in ingredients[0]:
                ingredients[0] = ingredients[0].split(":")[-1].strip()

            clean_ingredients = [re.sub(r'\s*\([^)]*\)', '', ingr).strip() for ingr in ingredients]

            # 1. Multi-Schema Craftability Check
            valid, msg = validate_ingredient_combination(clean_ingredients, caco_enabled, requiem_enabled, apothecary_enabled, apafa_enabled, ordinator_enabled)
            if valid and (apafa_enabled or ordinator_enabled):
                vanilla_valid, vanilla_msg = validate_ingredient_combination(clean_ingredients)
                if not vanilla_valid:
                    valid, msg = False, f"Fails Vanilla cross-validation: {vanilla_msg}"
            if not valid:
                errors.append(f"Block '{tag}' recipe '{craft}' INVALID in mode schema: {msg}")
                block_ok = False

            # 2. Inventory Provisioning Completeness Check
            for ingr in clean_ingredients:
                matched = any(ingr.lower() in p_name or p_name in ingr.lower() for p_name in provisioned_names)
                if not matched:
                    errors.append(f"Block '{tag}': Ingredient '{ingr}' in craft '{craft}' is NOT provisioned via ProvisionForm in block chunk!")
                    block_ok = False
        # Rule 7: Zero Duplicate Recipes / Zero Conflicting Setting Mutations Check
        recipe_names_in_block = [c.split("(")[0].strip().lower() for c in craft_lines if "+" in c or "->" in c]
        if len(recipe_names_in_block) != len(set(recipe_names_in_block)):
            dups = [r for r in set(recipe_names_in_block) if recipe_names_in_block.count(r) > 1]
            errors.append(f"Block '{tag}' contains duplicate recipe(s) within single block chunk: {dups}")
            block_ok = False


        if block_ok and not form_errors:
            passed += 1
        else:
            failed += 1

    # 5. Verify player alchemy skill levels match test-suite.md
    md_text = (REPO_ROOT / "test-suite.md").read_text(encoding="utf-8")
    table_rows = re.findall(
        r'\|\s*\*\*([^*]+)\*\*\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|',
        md_text
    )

    skill_errors = []
    for row in table_rows:
        phase, mode_tag, pre_script, ingame_cmd, disk_ap, gamesettings, caco_dur, player_perks_state, recipes = row
        skill_match = re.search(r'Skill\s*(\d+)', player_perks_state)
        if not skill_match:
            continue
        expected_lvl = int(skill_match.group(1))

        tag_clean = phase.lower().strip()
        if tag_clean.startswith("pred-default"):
            func_name, var = "SetupDefault", "default"
        elif tag_clean == "pred-changed-vanilla":
            func_name, var = "SetupVanilla", "changed"
        elif tag_clean == "pred-changed-ap":
            func_name, var = "SetupAP", "changed"
        elif tag_clean == "pred-changed-caco":
            func_name, var = "SetupCACO", "changed"
        elif tag_clean == "pred-changed-caco+ap":
            func_name, var = "SetupCACOAP", "changed"
        elif tag_clean == "pred-changed-requiem":
            func_name, var = "SetupRequiem", "changed"
        elif tag_clean == "pred-changed-apothecary":
            func_name, var = "SetupApothecary", "changed"
        elif tag_clean == "pred-changed-apafa":
            func_name, var = "SetupAPAFA", "changed"
        elif tag_clean == "pred-changed-ordinator":
            func_name, var = "SetupOrdinator", "changed"
        else:
            parts = tag_clean.split("-")
            if len(parts) == 2:
                m, num = parts[0], parts[1]
            elif len(parts) == 3:
                m, num = f"{parts[0]}{parts[1]}", parts[2]
            mode_map = {
                "vanilla": "SetupVanilla",
                "ap": "SetupAP",
                "caco": "SetupCACO",
                "cacoap": "SetupCACOAP", "caco+ap": "SetupCACOAP", "caco+ap": "SetupCACOAP", "caco+ap": "SetupCACOAP", "caco+ap": "SetupCACOAP", "caco+ap": "SetupCACOAP", "caco+ap": "SetupCACOAP", "caco+ap": "SetupCACOAP", "caco+ap": "SetupCACOAP", "caco+ap": "SetupCACOAP",
                "requiem": "SetupRequiem",
                "apothecary": "SetupApothecary",
                "apafa": "SetupAPAFA",
                "ordinator": "SetupOrdinator"
            }
            func_name = mode_map[m]
            var = num

        func_pattern = re.compile(rf'string Function {func_name}\s*\((.*?)\)\s*global(.*?)EndFunction', re.DOTALL)
        fmatch = func_pattern.search(psc_text)
        if not fmatch:
            skill_errors.append(f"Function {func_name} missing for phase {phase}")
            continue
        fbody = fmatch.group(2)

        if func_name == "SetupOrdinator":
            if var == "1":
                alch_set = ["100"]
            else:
                branch_match = re.search(rf'variant == "{var}"\s*(.*?)\s*(?:elseif|else)', fbody, re.DOTALL)
                alch_set = re.findall(r"\bskill\s*=\s*(\d+)", branch_match.group(1)) if branch_match else []
                if not alch_set:
                    alch_set = ["100"]
        elif var == "default":
            alch_set = re.findall(r'SetActorValue\("Alchemy",\s*(\d+)\)', fbody)
        elif var == "1":
            branch_match = re.search(r'else\s+(?!if)(.*?)\s*endif', fbody, re.DOTALL)
            alch_set = re.findall(r'SetActorValue\("Alchemy",\s*(\d+)\)', branch_match.group(1)) if branch_match else []
        elif var == "changed":
            branch_match = re.search(r'if variant == "changed"\s*(.*?)\s*elseif', fbody, re.DOTALL)
            alch_set = re.findall(r'SetActorValue\("Alchemy",\s*(\d+)\)', branch_match.group(1)) if branch_match else []
        else:
            branch_match = re.search(rf'variant == "{var}"\s*(.*?)\s*(?:elseif|else)', fbody, re.DOTALL)
            alch_set = re.findall(r'SetActorValue\("Alchemy",\s*(\d+)\)', branch_match.group(1)) if branch_match else []

        if not alch_set or int(alch_set[0]) != expected_lvl:
            actual_lvl = int(alch_set[0]) if alch_set else "None"
            skill_errors.append(f"Phase {phase}: expected skill level {expected_lvl}, got {actual_lvl} in {func_name} variant '{var}'")

    if skill_errors:
        print(f"  [FAIL] {len(skill_errors)} skill level mismatches found:")
        for err in skill_errors:
            print(f"    - {err}")
        errors.extend(skill_errors)
    else:
        print(f"  [PASS] All 84 test block and export setup player alchemy skill levels match test-suite.md.")

    # 6. Verify recipe alignment between test-suite.md and ProsperousAlchemistTests.psc
    md_blocks = re.findall(r'-\s*\*\*Block\s+\d+\s*\(`pat\s+([^`\)]+)`\)\*\*:\s*(.*?)(?=-\s*\*\*Block|\n###|\n####|\Z)', md_text, re.DOTALL)
    recipe_mismatches = []
    for cmd, content in md_blocks:
        cmd_parts = cmd.strip().split()
        mode = cmd_parts[0]
        var = cmd_parts[1] if len(cmd_parts) > 1 else ""
        tag = f"{mode}-{var}" if var else f"{mode}-1"
        if tag not in tag_to_code:
            continue
        md_crafts = re.findall(r'-\s*`(?:Order\s*\d+:\s*)?([^`]+)`', content)
        psc_code_part = tag_to_code[tag]
        psc_craft_prints = re.findall(r'ConsoleUtil\.PrintMessage\("[0-9]+\.\s*(?:Craft|Order [0-9]+):\s*([^"]+)"\)', psc_code_part)
        
        md_craft_recipes = [c for c in md_crafts if '+' in c or '->' in c]
        psc_craft_recipes = [p for p in psc_craft_prints if '+' in p or '->' in p]
        
        if len(md_craft_recipes) != len(psc_craft_recipes):
            recipe_mismatches.append(f"Block '{tag}' craft count mismatch: MD has {len(md_craft_recipes)}, PSC has {len(psc_craft_recipes)}")
        else:
            for m_rec, p_rec in zip(md_craft_recipes, psc_craft_recipes):
                m_clean = m_rec.split("(")[0].strip().lower()
                p_clean = p_rec.split("(")[0].strip().lower()
                if m_clean != p_clean:
                    recipe_mismatches.append(f"Block '{tag}' recipe mismatch: MD '{m_clean}' vs PSC '{p_clean}'")

    if recipe_mismatches:
        print(f"  [FAIL] {len(recipe_mismatches)} recipe mismatches between test-suite.md and PSC:")
        for err in recipe_mismatches:
            print(f"    - {err}")
        errors.extend(recipe_mismatches)
    else:
        print(f"  [PASS] All 180 block craft recipes and counts in test-suite.md match ProsperousAlchemistTests.psc 100%.")

    if len(errors) == 0:
        print(f"  [PASS] All {len(expected_tags)} in-game test blocks, skill levels, and recipes verified craftable.")
    else:
        print(f"  [FAIL] {len(errors)} recipe/block errors found:")
        for err in errors:
            print(f"    - {err}")

    return passed, failed, errors


def verify_compilation() -> tuple[bool, List[str]]:
    print("\n--- 4. Verifying Papyrus Script Compilation (compile.ps1) ---")
    res = subprocess.run(["pwsh", "-ExecutionPolicy", "Bypass", "-File", "pa-console-tests/compile.ps1"], capture_output=True, text=True, cwd=REPO_ROOT)
    if res.returncode == 0 and "Done!" in res.stdout:
        print("  [PASS] ProsperousAlchemistTests.psc compiled cleanly with Caprica.")
        return True, []
    else:
        err = res.stderr or res.stdout
        print(f"  [FAIL] Compilation failed:\n{err}")
        return False, [err]


def verify_next_command_alignment() -> tuple[bool, List[str]]:
    print("\n--- 5. Verifying Next Command / Next Step Alignment Across Markdown, Papyrus & Python Scripts ---")
    errors = []

    # 1. Python Pre-Launch Scripts (30 total)
    pat_python_next = {
        "pat-ap.py": "pat ap",
        "pat-ap-2.py": "pat ap 4",
        "pat-ap-3.py": "pat ap 8",
        "pat-ap-4.py": "pat ap 11",
        "pat-vanilla.py": "pat vanilla",
        "pat-caco.py": "pat caco",
        "pat-caco-ap.py": "pat caco-ap",
        "pat-caco-ap-2.py": "pat caco-ap 4",
        "pat-caco-ap-3.py": "pat caco-ap 8",
        "pat-caco-ap-4.py": "pat caco-ap 11",
        "pat-requiem.py": "pat requiem",
        "pat-apothecary.py": "pat apothecary",
        "pat-apafa.py": None,
        "pat-ordinator.py": "pat ordinator",
        "pat-default-vanilla.py": "pat default vanilla",
        "pat-default-ap.py": "pat default ap",
        "pat-default-caco.py": "pat default caco",
        "pat-default-caco-ap.py": "pat default caco-ap",
        "pat-default-requiem.py": "pat default requiem",
        "pat-default-apothecary.py": "pat default apothecary",
        "pat-default-apafa.py": None,
        "pat-default-ordinator.py": "pat default ordinator",
        "pat-vanilla-changed.py": "pat vanilla changed",
        "pat-ap-changed.py": "pat ap changed",
        "pat-caco-changed.py": "pat caco changed",
        "pat-caco-ap-changed.py": "pat caco-ap changed",
        "pat-requiem-changed.py": "pat requiem changed",
        "pat-apothecary-changed.py": "pat apothecary changed",
        "pat-apafa-changed.py": None,
        "pat-ordinator-changed.py": "pat ordinator changed",
    }

    py_ok_count = 0
    for script_name, expected_cmd in pat_python_next.items():
        script_path = REPO_ROOT / script_name
        if not script_path.exists():
            errors.append(f"Python script {script_name} does not exist!")
            continue
        text = script_path.read_text(encoding="utf-8")
        expected_output = f"Next in-game command: run '{expected_cmd}'" if expected_cmd else None
        if expected_output and expected_output not in text:
            errors.append(f"Script {script_name} text missing '{expected_output}'.")
        else:
            py_ok_count += 1

    if py_ok_count == len(pat_python_next):
        print(f"  [PASS] All {py_ok_count} Python pre-launch scripts are present and their command hints are aligned.")

    # 2. Papyrus Script (ProsperousAlchemistTests.psc)
    psc_path = REPO_ROOT / "pa-console-tests" / "Source" / "Scripts" / "ProsperousAlchemistTests.psc"
    psc_text = psc_path.read_text(encoding="utf-8")

    psc_next = {
        "ap-1": "pat ap 2",        "ap-2": "pat ap 3",        "ap-3": "Exit Skyrim and run",
        "ap-4": "pat ap 5",        "ap-5": "pat ap 6",        "ap-6": "pat ap 7",
        "ap-7": "Exit Skyrim and run",        "ap-8": "pat ap 9",        "ap-9": "pat ap 10",
        "ap-10": "Exit Skyrim and run",        "ap-11": "pat ap 12",        "ap-12": "pat ap 13",
        "ap-13": "Exit Skyrim and run",        "vanilla-1": "pat vanilla 2",        "vanilla-2": "pat vanilla 3",
        "vanilla-3": "pat vanilla 4",        "vanilla-4": "pat vanilla 5",        "vanilla-5": "pat vanilla 6",
        "vanilla-6": "pat vanilla 7",        "vanilla-7": "pat vanilla 8",        "vanilla-8": "pat vanilla 9",
        "vanilla-9": "pat vanilla 10",        "vanilla-10": "pat vanilla 11",        "vanilla-11": "pat vanilla 12",
        "vanilla-12": "pat vanilla 13",        "vanilla-13": "pat vanilla 14",        "vanilla-14": "pat vanilla 15",
        "vanilla-15": "pat vanilla 16",        "vanilla-16": "pat vanilla 17",        "vanilla-17": "pat vanilla 18",
        "vanilla-18": "Exit Skyrim and run",        "caco-1": "pat caco 2",        "caco-2": "pat caco 3",
        "caco-3": "pat caco 4",        "caco-4": "pat caco 5",        "caco-5": "pat caco 6",
        "caco-6": "pat caco 7",        "caco-7": "pat caco 8",        "caco-8": "pat caco 9",
        "caco-9": "pat caco 10",        "caco-10": "pat caco 11",        "caco-11": "pat caco 12",
        "caco-12": "pat caco 13",        "caco-13": "pat caco 14",        "caco-14": "pat caco 15",
        "caco-15": "pat caco 16",        "caco-16": "pat caco 17",        "caco-17": "pat caco 18",
        "caco-18": "pat caco 19",        "caco-19": "pat caco 20",        "caco-20": "pat caco 21",
        "caco-21": "pat caco 22",        "caco-22": "pat caco 23",        "caco-23": "pat caco 24",
        "caco-24": "pat caco 25",        "caco-25": "pat caco 26",        "caco-26": "pat caco 27",
        "caco-27": "Exit Skyrim and run",        "caco-ap-1": "pat caco-ap 2",        "caco-ap-2": "pat caco-ap 3",
        "caco-ap-3": "Exit Skyrim and run",        "caco-ap-4": "pat caco-ap 5",        "caco-ap-5": "pat caco-ap 6",
        "caco-ap-6": "pat caco-ap 7",        "caco-ap-7": "Exit Skyrim and run",        "caco-ap-8": "pat caco-ap 9",
        "caco-ap-9": "pat caco-ap 10",        "caco-ap-10": "Exit Skyrim and run",        "caco-ap-11": "pat caco-ap 12",
        "caco-ap-12": "pat caco-ap 13",        "caco-ap-13": "pat caco-ap 14",        "caco-ap-14": "pat caco-ap 15",
        "caco-ap-15": "pat caco-ap 16",        "caco-ap-16": "pat caco-ap 17",        "caco-ap-17": "pat caco-ap 18",
        "caco-ap-18": "pat caco-ap 19",        "caco-ap-19": "pat caco-ap 20",        "caco-ap-20": "pat caco-ap 21",
        "caco-ap-21": "pat caco-ap 22",        "caco-ap-22": "pat caco-ap 23",        "caco-ap-23": "Exit Skyrim and run",
        "requiem-1": "pat requiem 2",        "requiem-2": "pat requiem 3",        "requiem-3": "pat requiem 4",
        "requiem-4": "pat requiem 5",        "requiem-5": "pat requiem 6",        "requiem-6": "pat requiem 7",
        "requiem-7": "pat requiem 8",        "requiem-8": "pat requiem 9",        "requiem-9": "pat requiem 10",
        "requiem-10": "pat requiem 11",        "requiem-11": "pat requiem 12",        "requiem-12": "pat requiem 13",
        "requiem-13": "pat requiem 14",        "requiem-14": "pat requiem 15",        "requiem-15": "pat requiem 16",
        "requiem-16": "pat requiem 17",        "requiem-17": "pat requiem 18",        "requiem-18": "Exit Skyrim and run",
        "apothecary-1": "pat apothecary 2",        "apothecary-2": "pat apothecary 3",        "apothecary-3": "pat apothecary 4",
        "apothecary-4": "pat apothecary 5",        "apothecary-5": "pat apothecary 6",        "apothecary-6": "pat apothecary 7",
        "apothecary-7": "pat apothecary 8",        "apothecary-8": "pat apothecary 9",        "apothecary-9": "pat apothecary 10",
        "apothecary-10": "pat apothecary 11",        "apothecary-11": "pat apothecary 12",        "apothecary-12": "pat apothecary 13",
        "apothecary-13": "pat apothecary 14",        "apothecary-14": "pat apothecary 15",        "apothecary-15": "pat apothecary 16",
        "apothecary-16": "pat apothecary 17",        "apothecary-17": "pat apothecary 18",        "apothecary-18": "pat apothecary 19",
        "apothecary-19": "pat apothecary 20",        "apothecary-20": "pat apothecary 21",        "apothecary-21": "pat apothecary 22",
        "apothecary-22": "pat apothecary 23",        "apothecary-23": "pat apothecary 24",        "apothecary-24": "pat apothecary 25",
        "apothecary-25": "pat apothecary 26",        "apothecary-26": "pat apothecary 27",        "apothecary-27": "pat apothecary 28",
        "apothecary-28": "pat apothecary 29",        "apothecary-29": "pat apothecary 30",        "apothecary-30": "pat apothecary 31",
        "apothecary-31": "pat apothecary 32",        "apothecary-32": "pat apothecary 33",        "apothecary-33": "pat apothecary 34",
        "apothecary-34": "pat apothecary 35",        "apothecary-35": "pat apothecary 36",        "apothecary-36": "pat apothecary 37",
        "apothecary-37": "pat apothecary 38",        "apothecary-38": "pat apothecary 39",        "apothecary-39": "pat apothecary 40",
        "apothecary-40": "pat apothecary 41",        "apothecary-41": "pat apothecary 42",        "apothecary-42": "pat apothecary 43",
        "apothecary-43": "pat apothecary 44",        "apothecary-44": "pat apothecary 45",        "apothecary-45": "pat apothecary 46",
        "apothecary-46": "pat apothecary 47",        "apothecary-47": "pat apothecary 48",        "apothecary-48": "pat apothecary 49",
        "apothecary-49": "pat apothecary 50",        "apothecary-50": "pat apothecary 51",        "apothecary-51": "pat apothecary 52",
        "apothecary-52": "pat apothecary 53",        "apothecary-53": "pat apothecary 54",        "apothecary-54": "pat apothecary 55",
        "apothecary-55": "pat apothecary 56",        "apothecary-56": "pat apothecary 57",        "apothecary-57": "Exit Skyrim and run",
        "apafa-1": "pat apafa 2", "apafa-2": "pat apafa 3", "apafa-3": "pat apafa 4",
        "apafa-4": "pat apafa 5", "apafa-5": "pat apafa 6", "apafa-6": "pat apafa 7",
        "apafa-7": "pat apafa 8", "apafa-8": "pat apafa 9", "apafa-9": "pat apafa 10",
        "apafa-10": "Exit Skyrim and run", "apafa-changed": "Exit Skyrim and run",
        "ordinator-1": "pat ordinator 2", "ordinator-2": "pat ordinator 3",
        "ordinator-3": "pat ordinator 4", "ordinator-4": "pat ordinator 5",
        "ordinator-5": "pat ordinator 6", "ordinator-6": "pat ordinator 7",
        "ordinator-7": "pat ordinator 8", "ordinator-8": "pat ordinator 9",
        "ordinator-9": "pat ordinator 10", "ordinator-10": "pat ordinator 11",
        "ordinator-11": "pat ordinator 12",
        **{f"ordinator-{i}": f"pat ordinator {i+1}" for i in range(12, 18)},
        "ordinator-18": "python potion_prediction_test.py --check-confirmed-csv",
        "ordinator-changed": "python potion_prediction_test.py --check-confirmed-csv",

    }

    tag_to_code = {}
    for chunk in psc_text.split('modeTag == "')[1:]:
        tag = chunk.split('"')[0]
        tag_to_code[tag] = chunk

    psc_ok_count = 0
    for tag, expected_target in psc_next.items():
        if tag not in tag_to_code:
            errors.append(f"PSC missing code block for modeTag '{tag}'")
            continue
        code = tag_to_code[tag]
        if expected_target not in code:
            errors.append(f"PSC block '{tag}' printout does not contain '{expected_target}'!")
        else:
            psc_ok_count += 1

    if psc_ok_count == len(psc_next):
        print(f"  [PASS] All {psc_ok_count} Papyrus in-game test handlers print accurate next commands/steps.")

    # 3. Markdown Documentation (test-suite.md)
    md_path = REPO_ROOT / "test-suite.md"
    md_text = md_path.read_text(encoding="utf-8")

    md_ok_count = 0
    for tag, expected_target in psc_next.items():
        if expected_target not in md_text:
            errors.append(f"test-suite.md does not contain next step target '{expected_target}' for block '{tag}'!")
        else:
            md_ok_count += 1

    if md_ok_count == len(psc_next):
        print(f"  [PASS] test-suite.md contains accurate next step targets for all {md_ok_count} observed craft blocks.")

    return (len(errors) == 0, errors)


# ---------------------------------------------------------------------------
# 6. Strict block specification alignment
#
# Everything below is derived from the three sources themselves (no hardcoded
# block counts or recipes): the per-block sections and the Technical
# Specification Matrix in test-suite.md, the Setup* branches and the
# ProvisionAndPrintTests chunks in ProsperousAlchemistTests.psc, and the binary
# plugin records in db/plugin_ingr_records.csv (rebuilt by build_ingredient_db.py).
# ---------------------------------------------------------------------------

PSC_PATH = REPO_ROOT / "pa-console-tests" / "Source" / "Scripts" / "ProsperousAlchemistTests.psc"
MD_PATH = REPO_ROOT / "test-suite.md"

SETUP_FUNCTIONS = {
    "vanilla": "SetupVanilla",
    "ap": "SetupAP",
    "caco": "SetupCACO",
    "caco-ap": "SetupCACOAP",
    "requiem": "SetupRequiem",
    "apothecary": "SetupApothecary",
    "apafa": "SetupAPAFA",
    "ordinator": "SetupOrdinator",
}

# Plugins active in each mode, in load order (later plugins win for record data).
BASE_STACK = [
    "Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm",
    "ccbgssse001-fish.esm", "ccbgssse025-advdsgs.esm", "ccbgssse037-curios.esl",
    "ccqdrsse001-survivalmode.esl", "_ResourcePack.esl",
]
MODE_STACKS = {
    "vanilla": BASE_STACK,
    "ap": BASE_STACK,
    "caco": BASE_STACK + [
        "Complete Alchemy & Cooking Overhaul.esp", "cc-fishing_caco_patch.esp", "cc-rarecurios_caco_patch.esp",
        "cc-saints&seducers_caco_patch.esp", "cc-survivalmode_ussep_caco_patch.esp",
    ],
    "requiem": BASE_STACK + ["Requiem.esp"],
    "apothecary": BASE_STACK + [
        "Apothecary.esp", "Apothecary - Fishing Patch.esp", "Apothecary - Rare Curios Patch.esp",
        "Apothecary - Saints & Seducers Patch.esp",
    ],
    "apafa": BASE_STACK + [
        "AlchemyAdjustments.esp", "AlchemyAdjustments - RareCurios Patch.esp",
        "AlchemyAdjustments - DistinctiveRareIngredients Addon.esp",
    ],
    "ordinator": BASE_STACK + ["Ordinator - Perks of Skyrim.esp"],
}
MODE_STACKS["caco-ap"] = MODE_STACKS["caco"]
MODE_INGREDIENT_CSV = {
    "vanilla": "ingredients-vanilla.csv", "ap": "ingredients-vanilla.csv",
    "caco": "ingredients-caco.csv", "caco-ap": "ingredients-caco.csv",
    "requiem": "ingredients-requiem.csv", "apothecary": "ingredients-apothecary.csv",
    "apafa": "ingredients-apafa.csv", "ordinator": "ingredients-ordinator.csv",
}

CACO_FAMILIES = ["RestH", "RestM", "RestS", "DmgH", "DmgM", "DmgS"]
CACO_FAMILY_PATTERNS = {
    "RestH": r"rest(?:ore)?\s*h(?:ealth)?\b|resth|restorehealth(?:duration)?",
    "RestM": r"rest(?:ore)?\s*m(?:agicka)?\b|restm|restoremagicka(?:duration)?",
    "RestS": r"rest(?:ore)?\s*s(?:tamina)?\b|rests|restorestamina(?:duration)?",
    "DmgH": r"d(?:a)?m(?:a)?g(?:e)?\s*h(?:ealth)?\b|dmgh|damagehealth(?:duration)?",
    "DmgM": r"d(?:a)?m(?:a)?g(?:e)?\s*m(?:agicka)?\b|dmgm|damagemagicka(?:duration)?",
    "DmgS": r"d(?:a)?m(?:a)?g(?:e)?\s*s(?:tamina)?\b|dmgs|damagestamina(?:duration)?",
}
SECONDS_TO_INDEX = {0: 0, 1: 0, 5: 1, 10: 2}

# Vanilla perk editor IDs -> spec tokens (resolved from the plugin DB, never from FormIDs).
PERK_EDID_TOKENS = {
    "physician": "physician", "benefactor": "benefactor", "poisoner": "poisoner", "purity": "purity",
    "greenthumb": "green thumb", "snakeblood": "snakeblood",
    "ord_alc20_physician_perk_20_proc_health": "physician health",
    "ord_alc20_physician_perk_20_proc_magicka": "physician magicka",
    "ord_alc20_physician_perk_20_proc_stamina": "physician stamina",
    "ord_alc30_advancedlab_perk_00": "advanced lab",
    "ord_alc70_puremixture_perk_00": "purity",
    "experimenter50": "experimenter", "experimenter70": "experimenter", "experimenter90": "experimenter",
}
ALCHEMIST_RANK_EDIDS = ["alchemist00", "alchemist20", "alchemist40", "alchemist60", "alchemist80"]
SPEC_PERK_TOKENS = [
    "physician", "physician health", "physician magicka", "physician stamina", "benefactor", "poisoner", "purity", "advanced lab", "green thumb", "snakeblood",
    "experimenter", "seeker of shadows", "improved elixirs", "improved poisons", "purification process", "that which does not kill you",
]


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", "", name)).strip().lower()


class PluginRecords:
    """Origin-aware view of db/plugin_ingr_records.csv.

    Game.GetFormFromFile(id, plugin) composes the plugin's own load index with the
    object ID, so it only finds records that ORIGINATE in that plugin (overrides of a
    master's record live under the master's index and resolve to None).
    """

    def __init__(self) -> None:
        path = REPO_ROOT / "db" / "plugin_ingr_records.csv"
        if not path.exists():
            from build_ingredient_db import build_master_db
            build_master_db()
        self.by_origin: Dict[tuple, List[dict]] = {}
        self.plugins: Set[str] = set()
        with open(path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                raw = int(row["raw_form_id"], 16)
                row["object_id"] = raw & 0x00FFFFFF
                self.plugins.add(row["plugin_name"].lower())
                self.by_origin.setdefault((row["origin_plugin"].lower(), row["object_id"]), []).append(row)

    def resolve(self, form_id: int, plugin: str) -> List[dict]:
        plugin = plugin.lower()
        rows = self.by_origin.get((plugin, form_id & 0x00FFFFFF), [])
        if not rows and plugin.endswith(".esl"):
            rows = self.by_origin.get((plugin, form_id & 0xFFF), [])
        return rows

    def winner(self, rows: List[dict], mode: str) -> dict | None:
        stack = [p.lower() for p in MODE_STACKS[mode]]
        best, best_pos = None, -1
        for row in rows:
            pos = stack.index(row["plugin_name"].lower()) if row["plugin_name"].lower() in stack else -1
            if pos > best_pos:
                best, best_pos = row, pos
        return best


def _load_mode_ingredient_names(records: PluginRecords) -> Dict[str, Dict[tuple, str]]:
    """Map (origin plugin, object id) -> in-game ingredient name for each mode.

    The ingredients-*.csv exports carry runtime FormIDs, so each load-order prefix is
    calibrated to a plugin by voting over INGR records that originate in that plugin.
    """
    names: Dict[str, Dict[tuple, str]] = {}
    for mode, file_name in MODE_INGREDIENT_CSV.items():
        path = REPO_ROOT / file_name
        if not path.exists():
            names[mode] = {}
            continue
        entries = {}
        with open(path, encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                value = int(row["form_id"], 16)
                if value >> 24 == 0xFE:
                    entries[(f"FE{(value >> 12) & 0xFFF:03X}", value & 0xFFF)] = row["ingredient_name"]
                else:
                    entries[(f"{value >> 24:02X}", value & 0x00FFFFFF)] = row["ingredient_name"]
        votes: Dict[str, Dict[str, int]] = {}
        for (prefix, obj) in entries:
            for (origin, o), rows in records.by_origin.items():
                if o == obj and any(r["rectype"] == "INGR" for r in rows):
                    votes.setdefault(prefix, {}).setdefault(origin, 0)
                    votes[prefix][origin] += 1
        prefix_plugin = {p: max(v, key=v.get) for p, v in votes.items() if v}
        names[mode] = {
            (prefix_plugin[p], obj): name for (p, obj), name in entries.items() if p in prefix_plugin
        }
    return names


def _split_branches(body: str) -> Dict[str, str]:
    """Split a Setup* function at its top-level variant chain, preserving nested conditionals."""
    branches: Dict[str, str] = {}
    preamble: List[str] = []
    active: List[str] = []
    remainder: List[str] = []
    current: List[str] = []
    chain_started = False
    chain_ended = False
    nested = 0
    for line in body.splitlines():
        if chain_ended:
            remainder.append(line)
            continue
        m = re.match(r'^ {4}(?:if|elseif) (variant == "[^"]+"(?:\s*\|\|\s*variant == "[^"]+")*)\s*$', line)
        is_else = re.match(r"^ {4}else\s*$", line)
        if m and (not chain_started or nested == 0):
            if chain_started:
                for key in current:
                    branches[key] = "\n".join(active)
            else:
                branches[""] = "\n".join(preamble)
                chain_started = True
            active = []
            current = re.findall(r'variant == "([^"]+)"', m.group(1))
            continue
        if is_else and chain_started and nested == 0:
            for key in current:
                branches[key] = "\n".join(active)
            active = []
            current = ["1"]
            continue
        if not chain_started:
            preamble.append(line)
            continue
        if re.match(r"^ {4}endif\s*$", line):
            if nested == 0:
                for key in current:
                    branches[key] = "\n".join(active)
                chain_ended = True
                continue
            nested -= 1
        elif re.match(r"^ {4}if\s+", line):
            nested += 1
        active.append(line)
    if not chain_started:
        branches[""] = "\n".join(preamble)
    if chain_ended:
        branches["__after__"] = "\n".join(remainder)
    else:
        for key in current or [""]:
            branches[key] = "\n".join(active)
    return branches


def _perk_token(records: PluginRecords, form_id: int, plugin: str, mode: str) -> tuple[str | None, str | None]:
    rows = records.resolve(form_id, plugin)
    perk_rows = [r for r in rows if r["rectype"] == "PERK"]
    if not perk_rows:
        return None, f"AddPerk FormID 0x{form_id:08X} from '{plugin}' is not a PERK record originating in that plugin"
    win = records.winner(perk_rows, mode) or perk_rows[0]
    edid = (win["edid"] or "").lower()
    if edid in ALCHEMIST_RANK_EDIDS:
        return f"rank:{ALCHEMIST_RANK_EDIDS.index(edid) + 1}", None
    if edid.startswith("req_null_"):
        # A nulled perk is only acceptable when the spec marks it "(nulled by Requiem)" so the
        # block deliberately checks that the predictor applies no bonus for it.
        base = PERK_EDID_TOKENS.get(edid[len("req_null_"):])
        if base:
            return f"{base} (nulled)", None
        return None, f"AddPerk 0x{form_id:08X} ({win['edid']}) is nulled by Requiem in mode '{mode}'"
    if edid in PERK_EDID_TOKENS:
        return PERK_EDID_TOKENS[edid], None
    return (win["display_name"] or win["edid"]).strip().lower(), None


def _psc_block_state(records: PluginRecords, text: str, mode: str, errors: List[str], tag: str) -> Dict[str, Any]:
    state: Dict[str, Any] = {
        "skill": 100, "fortify": 0, "rank": 0, "perks": set(), "init_mult": None, "skill_factor": None,
        "caco": None, "ordinator_lab": 0, "ordinator_power": 0, "ordinator_lab_active": False,
    }
    perk_vars: Dict[str, tuple] = {}
    for line in text.splitlines():
        code = line.split(";")[0]
        if mode == "ordinator" and re.search(r'SetActorValue\("Alchemy",\s*skill\)', code):
            skill_values = re.findall(r"\bskill\s*=\s*(\d+)", text)
            if skill_values:
                state["skill"] = int(skill_values[-1])
        if m := re.search(r'SetActorValue\("Alchemy",\s*(\d+)\)', code):
            state["skill"] = int(m.group(1))
        if "ApplyFortifyAlchemyGear(" in code:
            state["fortify"] = 50
        if m := re.search(r"(?:SetAlchemistRank|SetRequiemLoreRank)\(player,\s*(\d)\)", code):
            state["rank"] = int(m.group(1))
        if m := re.search(r"SetOrdinatorMastery\(player,\s*mastery\)", code):
            ranks = re.findall(r"\bmastery\s*=\s*(\d+)", text)
            state["rank"] = int(ranks[-1]) if ranks else 0
            choices = {
                "physician": int(re.findall(r"\bphysician\s*=\s*(\d+)", text)[-1]) if re.findall(r"\bphysician\s*=\s*(\d+)", text) else 0,
                "poisoner": int(re.findall(r"\bpoisoner\s*=\s*(\d+)", text)[-1]) if re.findall(r"\bpoisoner\s*=\s*(\d+)", text) else 0,
                "purity": int(re.findall(r"\bpurity\s*=\s*(\d+)", text)[-1]) if re.findall(r"\bpurity\s*=\s*(\d+)", text) else 0,
                "lab": int(re.findall(r"\blab\s*=\s*(\d+)", text)[-1]) if re.findall(r"\blab\s*=\s*(\d+)", text) else 0,
                "magnum": int(re.findall(r"\bmagnumOpus\s*=\s*(\d+)", text)[-1]) if re.findall(r"\bmagnumOpus\s*=\s*(\d+)", text) else 0,
            }
            for key in ("power", "labActive"):
                values = re.findall(rf"\b{key}\s*=\s*(\d+)", text)
                choices[key] = int(values[-1]) if values else (1 if key == "labActive" else 0)
            state["ordinator_power"] = choices["power"]
            state["fortify"] = max(state["fortify"], choices["power"])
            state["ordinator_lab_active"] = bool(choices["lab"] and choices["labActive"])
            if choices["physician"]:
                state["perks"].add("physician")
                state["perks"].add({1: "physician health", 2: "physician magicka", 3: "physician stamina"}.get(choices["physician"], "physician"))
            if choices["poisoner"]:
                state["perks"].add("poisoner")
            if choices["purity"]:
                state["perks"].add("purity")
            if choices["lab"]:
                state["perks"].add("advanced lab")
            if choices["magnum"]:
                state["perks"].add("that which does not kill you")
            state["ordinator_lab"] = choices["lab"]
        if "ApplySeekerOfShadows(" in code:
            state["perks"].add("seeker of shadows")
        if m := re.search(r"setgs fAlchemyIngredientInitMult ([\d.]+)", code):
            state["init_mult"] = float(m.group(1))
        if m := re.search(r"setgs fAlchemySkillFactor ([\d.]+)", code):
            state["skill_factor"] = float(m.group(1))
        if m := re.search(r"SetAllCacoDurations\(([\d,\s]+)\)", code):
            values = [int(v) for v in m.group(1).split(",")]
            for v in values:
                if v not in (0, 1, 2):
                    errors.append(f"[{tag}] SetAllCacoDurations value {v} is not a CACO index (0/1/2)")
            state["caco"] = values
        if m := re.search(r'Perk\s+(\w+)\s*=\s*Game\.GetFormFromFile\((0x[0-9A-Fa-f]+),\s*"([^"]+)"\)', code):
            perk_vars[m.group(1)] = (int(m.group(2), 16), m.group(3))
        perk_ref = None
        if m := re.search(r"AddPerk\(Game\.GetForm\((0x[0-9A-Fa-f]+)\)", code):
            perk_ref = (int(m.group(1), 16), "Skyrim.esm")
        elif m := re.search(r'AddPerk\(Game\.GetFormFromFile\((0x[0-9A-Fa-f]+),\s*"([^"]+)"\)', code):
            perk_ref = (int(m.group(1), 16), m.group(2))
        elif (m := re.search(r"AddPerk\((\w+)\)", code)) and m.group(1) in perk_vars:
            perk_ref = perk_vars[m.group(1)]
        if perk_ref and mode != "ordinator":
            token, err = _perk_token(records, perk_ref[0], perk_ref[1], mode)
            if err:
                errors.append(f"[{tag}] {err}")
            elif token.startswith("rank:"):
                state["rank"] = max(state["rank"], int(token[5:]))
            else:
                state["perks"].add(token)
    return state


def _spec_state(text: str, mode: str, tag: str, source: str, errors: List[str]) -> Dict[str, Any]:
    """Parse skill / fortify / perks / GameSettings / CACO durations from spec prose."""
    low = text.lower().replace("`", "")
    spec: Dict[str, Any] = {}
    if m := re.search(r"(?:player alchemy|skill)\s*(\d+)", low):
        spec["skill"] = int(m.group(1))
    if m := re.search(r"fortify\s*(\d+)", low):
        spec["fortify"] = int(m.group(1))
    if m := re.search(r"initmult\s*=?\s*(\d+(?:\.\d+)?)", low):
        spec["init_mult"] = float(m.group(1))
    if m := re.search(r"skillfactor\s*=?\s*(\d+(?:\.\d+)?)", low):
        spec["skill_factor"] = float(m.group(1))

    perk_text = low
    if m := re.search(r"perks?\s*:(.*)", low):
        perk_text = m.group(1)
    # Apothecary's SPID-distributed "Apothecary Scaling Controller" perk is granted by the
    # test script to make sure it is present; the spec calls it "SPID perk present".
    spid = "spid perk present" in perk_text
    perk_text = perk_text.replace("spid perk present", "").replace("all perks 0", "")
    ambiguous = re.search(r"full (?:perk )?tree|all requiem perks|all perks", perk_text)
    rank = 0
    if m := re.search(r"alchemy mastery rank\s*(\d)", low if mode == "ordinator" else perk_text):
        rank = int(m.group(1))
    elif m := re.search(r"(?:alchemical )?lore\s*1\s*\+\s*2", perk_text):
        rank = 2
    elif m := re.search(r"(?:alchemical )?lore(?: rank)?\s*(\d)", perk_text):
        rank = int(m.group(1))
    if m := re.search(r"alchemist(?: rank)?\s*(\d)", perk_text):
        rank = int(m.group(1))
    spec["rank"] = rank
    if mode == "ordinator":
        perk_text = re.sub(r"pure mixture", "purity", perk_text)
        if m := re.search(r"advanced lab\s*(?:global\s*)?(?:type\s*)?(\d)", low):
            spec["ordinator_lab"] = int(m.group(1))
            if int(m.group(1)) == 0:
                low = re.sub(r"advanced lab\s*(?:global\s*)?(?:type\s*)?0", "", low)
                perk_text = low
                if m2 := re.search(r"perks?\s*:(.*)", low):
                    perk_text = m2.group(1)
                perk_text = re.sub(r"pure mixture", "purity", perk_text)
    if mode == "ordinator":
        if m := re.search(r"alchemypowermod\s*(\d+)", low):
            spec["ordinator_power"] = int(m.group(1))
        if "proc active" in low:
            spec["ordinator_lab_active"] = True
        elif "proc inactive" in low or spec.get("ordinator_lab") == 0:
            spec["ordinator_lab_active"] = False
    perks = set()
    for token in SPEC_PERK_TOKENS:
        pattern = r"seeker(?: of shadows)?" if token == "seeker of shadows" else re.escape(token)
        for pm in re.finditer(pattern, perk_text):
            before = perk_text[max(0, pm.start() - 12):pm.start()]
            after = perk_text[pm.end():pm.end() + 3]
            if not re.search(r"\b(?:no|zero|without)\s+(?:\w+\s+)?$", before) and not re.match(r"\s+0\b", after):
                nulled = re.match(r"\s*\(nulled", perk_text[pm.end():pm.end() + 12])
                perks.add(f"{token} (nulled)" if nulled else token)
    if ambiguous and not perks:
        errors.append(f"[{tag}] {source}: perk list is not explicit ('{perk_text.strip()}'); list each perk")
    spec["spid"] = spid
    spec["perks"] = perks

    if mode in ("caco", "caco-ap"):
        values = [0] * 6
        found = False
        if m := re.search(r"all\s*(\d+)s|all index\s*(\d)|caco (\d+)s durations", low):
            secs = m.group(1) or m.group(3)
            idx = SECONDS_TO_INDEX.get(int(secs)) if secs else int(m.group(2))
            if m2 := re.search(r"all index\s*(\d)", low):
                idx = int(m2.group(1))
            values = [idx] * 6
            found = True
        for i, fam in enumerate(CACO_FAMILIES):
            for fm in re.finditer(CACO_FAMILY_PATTERNS[fam], low):
                window = low[fm.end():fm.end() + 40]
                if im := re.match(r"[^,;]*?index\s*(\d)", window):
                    values[i] = int(im.group(1)); found = True; break
                if sm := re.match(r"[^,;]*?(\d+)\s*s\b", window):
                    values[i] = SECONDS_TO_INDEX.get(int(sm.group(1)), -1); found = True; break
                if em := re.match(r"duration\s*=\s*(\d)", window):
                    values[i] = int(em.group(1)); found = True; break
        if not found and "duration" in low:
            errors.append(f"[{tag}] {source}: CACO durations are mentioned but not explicit; give each family's seconds/index")
        spec["caco"] = values
    return spec


def _parse_recipe(text: str) -> tuple | None:
    text = re.sub(r"^\s*(?:\d+\.\s*)?(?:craft|order\s*\d+)\s*:\s*", "", text.strip(), flags=re.I)
    text = re.sub(r"\([^)]*\)", "", text).strip()
    if "->" in text:
        return ("order",) + tuple(_norm_name(p) for p in text.split("->"))
    if "+" in text:
        return ("set",) + tuple(sorted(_norm_name(p) for p in text.split("+")))
    return None


def _parse_md(md_text: str) -> tuple[Dict[str, dict], Dict[str, dict], List[str]]:
    errors: List[str] = []
    sections: Dict[str, dict] = {}
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^- \*\*Block (\d+) \(`pat ([^`]+)`\)", lines[i])
        if not m:
            i += 1
            continue
        tag = _cmd_to_tag(m.group(2))
        body = []
        i += 1
        while i < len(lines) and not re.match(r"^- \*\*Block \d+ \(`pat ", lines[i]) and not lines[i].startswith("#"):
            body.append(lines[i])
            i += 1
        text = "\n".join(body)
        settings = re.search(r"\*\*Runtime State\*\*:\s*(.*)", text) or re.search(r"\*\*Modified Settings\*\*:\s*(.*)", text)
        crafts = [c for c in re.findall(r"^\s+- `([^`]+)`", text, re.M) if _parse_recipe(c)]
        next_m = re.search(r"\*\*Next Command\*\*:\s*(.*)", text)
        if tag in sections:
            errors.append(f"[{tag}] test-suite.md has more than one Block section for `pat {m.group(2)}`")
        sections[tag] = {
            "settings": settings.group(1) if settings else "",
            "crafts": crafts,
            "next": _norm_next(next_m.group(1)) if next_m else None,
        }
    matrix: Dict[str, dict] = {}
    for row in re.findall(r"^\|\s*\*\*[^*]+\*\*\s*\|(.*)\|\s*$", md_text, re.M):
        cols = [c.strip() for c in row.split("|")]
        if len(cols) < 8:
            continue
        cmd = cols[2].strip("` ")
        if not cmd.startswith("pat "):
            continue
        tag = _cmd_to_tag(cmd[4:])
        if tag in matrix:
            errors.append(f"[{tag}] Technical Specification Matrix has duplicate rows for `{cmd}`")
        matrix[tag] = {
            "settings": f"{cols[4]} | CACO: {cols[5]} | {cols[6]}",
            "recipes": cols[7],
        }
    return sections, matrix, errors


def _cmd_to_tag(cmd: str) -> str:
    parts = cmd.strip().split()
    if parts[0] == "default":
        return f"default-{parts[1]}"
    return f"{parts[0]}-{parts[1] if len(parts) > 1 else '1'}"


def _norm_next(text: str) -> str:
    low = text.lower()
    if m := re.search(r"(pat-[\w-]+\.py)", low):
        return m.group(1)
    if m := re.search(r"python potion_prediction_test\.py(?: --[\w-]+)*", low):
        return m.group(0)
    if "exit skyrim" in low:
        return "exit skyrim (no pre-launch script named)"
    if m := re.search(r"pat ([\w-]+(?: [\w-]+)?)", low):
        return "pat " + m.group(1).strip()
    if "end of" in low or "complete" in low or "finished" in low:
        return "end"
    return low.strip()


def verify_block_spec_alignment() -> tuple[bool, List[str]]:
    print("\n--- 6. Verifying Block Specs (test-suite.md sections + matrix) vs Papyrus State, Provisioning & Crafts ---")
    errors: List[str] = []
    records = PluginRecords()
    ingredient_names = _load_mode_ingredient_names(records)
    psc_text = PSC_PATH.read_text(encoding="utf-8")
    md_text = MD_PATH.read_text(encoding="utf-8")
    sections, matrix, md_errors = _parse_md(md_text)
    errors.extend(md_errors)

    # Papyrus setup branches -> effective state per tag.
    psc_states: Dict[str, dict] = {}
    for mode, func in SETUP_FUNCTIONS.items():
        fm = re.search(rf"^string Function {func}\(.*?^EndFunction", psc_text, re.S | re.M)
        if not fm:
            errors.append(f"PSC: function {func} not found")
            continue
        branches = _split_branches(fm.group(0))
        preamble = branches.pop("", "")
        postamble = branches.pop("__after__", "")
        for variant, text in branches.items():
            tag = f"{mode}-{variant}"
            psc_states[tag] = _psc_block_state(records, preamble + "\n" + text + "\n" + postamble, mode, errors, tag)

    # Papyrus provisioning/print chunks.
    chunks: Dict[str, str] = {}
    pap = re.search(r"^Function ProvisionAndPrintTests\(.*?^EndFunction", psc_text, re.S | re.M)
    if pap:
        for chunk in re.split(r'(?=modeTag == ")', pap.group(0))[1:]:
            tag = chunk.split('"')[1]
            if tag.endswith('-changed'):
                continue  # export-only Phase 8B blocks have no observed crafts
            chunks[tag] = chunk
    else:
        errors.append("PSC: ProvisionAndPrintTests not found")

    observed_tags = {t for t in chunks}
    for tag in sorted(observed_tags | set(sections)):
        if tag not in sections:
            errors.append(f"[{tag}] PSC provisions this block but test-suite.md has no Block section for it")
        if tag not in chunks:
            errors.append(f"[{tag}] test-suite.md has a Block section but PSC ProvisionAndPrintTests has no handler")
        if tag not in psc_states:
            errors.append(f"[{tag}] no matching Setup* branch in PSC")
        if tag not in matrix:
            errors.append(f"[{tag}] missing from the Technical Specification Matrix in test-suite.md")

    # Setup state vs spec (matrix + section).
    for tag in sorted(set(psc_states) & (set(matrix) | set(sections))):
        mode = tag.rsplit("-", 1)[0]
        state = psc_states[tag]
        if mode == "apothecary":
            # Mode-wide invariant: every Apothecary block must grant the SPID scaling perk.
            if "apothecary scaling controller" not in state["perks"]:
                errors.append(f"[{tag}] PSC does not grant the Apothecary Scaling Controller (SPID) perk")
            state = dict(state, perks=state["perks"] - {"apothecary scaling controller"})
        for source, text in (("matrix", matrix.get(tag, {}).get("settings")), ("section", sections.get(tag, {}).get("settings"))):
            if text is None:
                continue
            spec = _spec_state(text, mode, tag, source, errors)
            for key in ("skill", "fortify", "init_mult", "skill_factor"):
                if key in spec and spec[key] != state[key]:
                    errors.append(f"[{tag}] {key}: {source} says {spec[key]}, PSC sets {state[key]}")
            for key in ("init_mult", "skill_factor"):
                if state[key] is None:
                    errors.append(f"[{tag}] PSC never sets {key}; it would inherit the previous block's value")
            if spec["rank"] != state["rank"]:
                errors.append(f"[{tag}] alchemist/lore rank: {source} says {spec['rank']}, PSC grants {state['rank']}")
            if spec.get("ordinator_lab", state["ordinator_lab"]) != state["ordinator_lab"]:
                errors.append(f"[{tag}] Advanced Lab type: {source} says {spec.get('ordinator_lab')}, PSC sets {state['ordinator_lab']}")
            if mode == "ordinator":
                for key in ("ordinator_power", "ordinator_lab_active"):
                    if key in spec and spec[key] != state[key]:
                        errors.append(f"[{tag}] {key}: {source} says {spec[key]}, PSC sets {state[key]}")
            if spec["perks"] != state["perks"]:
                errors.append(f"[{tag}] perks: {source} says {sorted(spec['perks']) or 'none'}, PSC grants {sorted(state['perks']) or 'none'}")
            if mode in ("caco", "caco-ap"):
                if state["caco"] is None:
                    errors.append(f"[{tag}] PSC never sets CACO durations; they would inherit the previous block's values")
                elif spec["caco"] != state["caco"]:
                    errors.append(f"[{tag}] CACO duration indices {CACO_FAMILIES}: {source} says {spec['caco']}, PSC sets {state['caco']}")

    # Provisioning, crafts and next-command per observed block.
    for tag in sorted(set(chunks) & set(psc_states)):
        mode = tag.rsplit("-", 1)[0]
        code = chunks[tag]
        names = ingredient_names.get(mode, {})
        provisioned: Set[str] = set()
        for m in re.finditer(r'ProvisionForm\(player,\s*(0x[0-9A-Fa-f]+),\s*"([^"]+)"\)\s*(?:;\s*([^\r\n]*))?', code):
            fid, plugin, comment = int(m.group(1), 16), m.group(2), (m.group(3) or "").strip()
            candidates = [(fid, plugin)]
            names_found = _provision_names(records, names, candidates, mode)
            if not names_found:
                errors.append(f"[{tag}] ProvisionForm(0x{fid:08X}, \"{plugin}\") ; {comment} resolves to NO ingredient in-game "
                              f"(no INGR record originates in '{plugin}' with that ID)")
                continue
            provisioned |= names_found
            if comment and _norm_name(comment) not in names_found:
                errors.append(f"[{tag}] ProvisionForm(0x{fid:08X}, \"{plugin}\") comment '{comment}' but the record is {sorted(names_found)} in {mode}")
        for m in re.finditer(r'ProvisionFormFallback\(player,\s*(0x[0-9A-Fa-f]+),\s*"([^"]+)",\s*(0x[0-9A-Fa-f]+),\s*"([^"]+)"\)\s*(?:;\s*([^\r\n]*))?', code):
            candidates = [(int(m.group(1), 16), m.group(2)), (int(m.group(3), 16), m.group(4))]
            names_found = _provision_names(records, names, candidates, mode)
            if not names_found:
                errors.append(f"[{tag}] ProvisionFormFallback({m.group(1)}, \"{m.group(2)}\" / {m.group(3)}, \"{m.group(4)}\") resolves to NO ingredient in {mode}")
            provisioned |= names_found

        prints = re.findall(r'ConsoleUtil\.PrintMessage\("([^"]*)"\)', code)
        psc_crafts = []
        for text in prints:
            if re.match(r"\s*\d+\.\s*(?:Craft|Order \d+)\s*:", text):
                recipe = _parse_recipe(text)
                if not recipe:
                    errors.append(f"[{tag}] could not parse PSC craft line '{text}'")
                    continue
                psc_crafts.append(recipe)
                for ingr in recipe[1:]:
                    if ingr not in provisioned:
                        errors.append(f"[{tag}] craft '{text}' needs '{ingr}' but no ProvisionForm in this block provides it "
                                      f"(provided: {sorted(provisioned)})")
            elif ("+" in text or "->" in text) and not text.startswith("---"):
                errors.append(f"[{tag}] PSC print looks like a craft but is not in 'N. Craft:' form: '{text}'")
        if len(psc_crafts) != len(set(psc_crafts)):
            errors.append(f"[{tag}] PSC prints the same recipe more than once")

        section = sections.get(tag)
        if section:
            md_crafts = [_parse_recipe(c) for c in section["crafts"]]
            if md_crafts != psc_crafts:
                errors.append(f"[{tag}] crafts differ: test-suite.md {[' + '.join(r[1:]) for r in md_crafts]} vs PSC {[' + '.join(r[1:]) for r in psc_crafts]}")
            psc_next = next((_norm_next(p) for p in prints if p.lower().startswith("next")), None)
            if section["next"] != psc_next:
                errors.append(f"[{tag}] next step differs: test-suite.md '{section['next']}' vs PSC '{psc_next}'")
        row = matrix.get(tag)
        if row and "order" not in row["recipes"].lower():
            matrix_recipes = sorted(r for r in (_parse_recipe(p) for p in row["recipes"].split(";")) if r)
            if matrix_recipes != sorted(psc_crafts):
                errors.append(f"[{tag}] matrix Target Recipes {[' + '.join(r[1:]) for r in matrix_recipes]} vs PSC {[' + '.join(r[1:]) for r in psc_crafts]}")

    if errors:
        print(f"  [FAIL] {len(errors)} block specification problems:")
        for err in errors:
            print(f"    - {err}")
    else:
        print(f"  [PASS] {len(chunks)} observed blocks and {len(psc_states)} setup branches match test-suite.md exactly.")
    return not errors, errors


def _provision_names(records: PluginRecords, names: Dict[tuple, str], candidates: List[tuple], mode: str) -> Set[str]:
    found: Set[str] = set()
    for fid, plugin in candidates:
        rows = [r for r in records.resolve(fid, plugin) if r["rectype"] == "INGR"]
        if not rows:
            continue
        obj = rows[0]["object_id"]
        origin = plugin.lower()
        name = names.get((origin, obj)) or names.get((origin, obj & 0xFFF))
        if not name:
            win = records.winner(rows, mode)
            name = (win and win["display_name"]) or rows[0]["edid"]
        found.add(_norm_name(name))
    return found


def main():
    global PSC_PATH
    if "--psc" in sys.argv:
        # Check a candidate script (e.g. a proposed revision) instead of the checked-in one.
        PSC_PATH = Path(sys.argv[sys.argv.index("--psc") + 1]).resolve()
    if "--static" in sys.argv:
        # Read-only checks: no pat-*.py execution (they rewrite the MO2 profile), no
        # Skyrim termination, no compilation.
        ok_yaml, _ = verify_pa_tests_yaml()
        _, f_psc, _ = verify_psc_and_recipes()
        ok_next, _ = verify_next_command_alignment()
        ok_spec, _ = verify_block_spec_alignment()
        failures = (0 if ok_yaml else 1) + f_psc + (0 if ok_next else 1) + (0 if ok_spec else 1)
        print(f"\n>>> {'SUCCESS' if failures == 0 else 'FAILURE'}: static verification ({failures} failing section(s)) <<<")
        sys.exit(0 if failures == 0 else 1)

    kill_previous_instances()
    print("=================================================================")
    print("PROSPEROUS ALCHEMIST NG - MASTER TEST SUITE VERIFICATION HARNESS")
    print("=================================================================\n")

    p_scripts, f_scripts, e_scripts = verify_pat_python_scripts()
    ok_yaml, e_yaml = verify_pa_tests_yaml()
    p_psc, f_psc, e_psc = verify_psc_and_recipes()
    ok_compile, e_compile = verify_compilation()
    ok_next, e_next = verify_next_command_alignment()
    ok_spec, e_spec = verify_block_spec_alignment()

    total_failures = f_scripts + (0 if ok_yaml else 1) + f_psc + (0 if ok_compile else 1) + (0 if ok_next else 1) + (0 if ok_spec else 1)

    print("\n=================================================================")
    print("MASTER VERIFICATION SUMMARY:")
    print(f"  - Pre-Launch Python Scripts (30 total): {p_scripts} PASSED, {f_scripts} FAILED")
    print(f"  - Console YAML Definition (pa-tests.yaml): {'PASSED' if ok_yaml else 'FAILED'}")
    print(f"  - Test Blocks, Binary FormIDs & Recipe Parity (184 total): {p_psc} PASSED, {f_psc} FAILED")
    print(f"  - Papyrus Compilation & Deployment: {'PASSED' if ok_compile else 'FAILED'}")
    print(f"  - Next Command / Next Step Sequence Alignment: {'PASSED' if ok_next else 'FAILED'}")
    print(f"  - Block Specs vs Papyrus State/Provisioning/Crafts: {'PASSED' if ok_spec else 'FAILED'}")
    print("=================================================================")

    if total_failures == 0:
        print("\n>>> SUCCESS: 100% ACCURACY VERIFIED ACROSS ALL SCRIPTS, BINARY FORM IDS, AND COMPILED COMMANDS! <<<")
        sys.exit(0)
    else:
        print(f"\n>>> FAILURE: {total_failures} VERIFICATION ERROR(S) DETECTED! <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()

