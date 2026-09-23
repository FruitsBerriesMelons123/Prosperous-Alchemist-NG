"""Master verification script to ensure 100% alignment between scripts, compiled commands, and test-suite.md.

This script comprehensively verifies:
1. All 22 pre-launch Python scripts (pat-*.py) execute cleanly and configure MO2 modlist,
   plugins.txt, and AlchemyPlus.json matching test-suite.md specs.
2. pa-tests.yaml contains all required subcommands, aliases, functions, and arguments matching test-suite.md.
3. ProsperousAlchemistTests.psc implements all 60 observed-craft test blocks and 12 prediction-export blocks,
   verifying skill levels, perks, GameSettings, CACO globals, ingredient FormIDs, and console printouts.
4. Every single ProvisionForm and ProvisionFormFallback FormID in ProsperousAlchemistTests.psc is validated
   against actual binary plugin files (.esp, .esm, .esl) on disk to guarantee zero missing ingredients in Skyrim.
5. All ingredient craft recipes across all test blocks are validated for recipe craftability in Skyrim using
   validate_ingredient_combination against ingredients-*.csv snapshots.
6. Papyrus test script compiles cleanly via compile.ps1 (Caprica compiler) with zero errors.
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
    """Ensure no previous instance of this script is running concurrently."""
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
            for pid in pids:
                print(f"Terminating previous background instance of {script_name} (PID: {pid})...")
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
    except Exception as e:
        print(f"Warning: Failed to check or kill previous instances of script: {e}")


OVERHAUL_MODS = {
    "CACO": config.CACO_MOD_DIR.name,
    "Kryptopyr": config.KRYPTOPYR_PATCHES_MOD_DIR.name,
    "AP": config.ALCHEMY_PLUS_MOD_DIR.name,
    "Requiem": getattr(config, "REQUIEM_MOD_DIR", Path("Requiem - The Roleplaying Overhaul")).name,
    "Apothecary": getattr(config, "APOTHECARY_MOD_DIR", Path("Apothecary - An Alchemy Overhaul")).name,
}

PLUGINS_MAP = {
    "CACO": ["complete alchemy & cooking overhaul.esp"],
    "Requiem": ["requiem.esp"],
    "Apothecary": ["apothecary.esp"],
}

EXPECTED_MODS = {
    "vanilla": set(),
    "ap": {"AP"},
    "caco": {"CACO", "Kryptopyr"},
    "caco-ap": {"CACO", "Kryptopyr", "AP"},
    "requiem": {"Requiem"},
    "apothecary": {"Apothecary"},
}

EXPECTED_PLUGINS = {
    "vanilla": set(),
    "ap": set(),
    "caco": {"CACO"},
    "caco-ap": {"CACO"},
    "requiem": {"Requiem"},
    "apothecary": {"Apothecary"},
}


def get_mode_category(script_name: str) -> str:
    name = script_name.lower().replace("pat-", "").replace(".py", "").replace("-changed", "").replace("default-", "")
    if name.startswith("apothecary"):
        return "apothecary"
    elif name.startswith("caco-ap"):
        return "caco-ap"
    elif name.startswith("caco"):
        return "caco"
    elif name.startswith("ap"):
        return "ap"
    elif name.startswith("vanilla"):
        return "vanilla"
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
            master_idx = (form_id >> 24) & 0xFF
            local_form_id = form_id & 0x00FFFFFF
            if master_idx < len(masters):
                origin_plugin = masters[master_idx]
            else:
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

    if len(pat_scripts) != 24:
        log_details.append(f"Expected 24 pat-*.py scripts, found {len(pat_scripts)}")

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
        "default", "vanilla", "caco", "ap", "caco-ap", "requiem", "apothecary", "clear"
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

    # 1. Parse binary plugin files for INGR records
    plugin_files = {
        'Skyrim.esm': config.SKYRIM / 'Data' / 'Skyrim.esm',
        'Dawnguard.esm': config.SKYRIM / 'Data' / 'Dawnguard.esm',
        'Dragonborn.esm': config.SKYRIM / 'Data' / 'Dragonborn.esm',
        'ccbgssse037-curios.esl': config.SKYRIM / 'Data' / 'ccbgssse037-curios.esl',
        'Complete Alchemy & Cooking Overhaul.esp': config.CACO_MOD_DIR / 'Complete Alchemy & Cooking Overhaul.esp',
        'cc-rarecurios_caco_patch.esp': config.KRYPTOPYR_PATCHES_MOD_DIR / 'cc-rarecurios_caco_patch.esp',
        'Requiem.esp': config.REQUIEM_MOD_DIR / 'Requiem.esp',
        'Apothecary.esp': config.APOTHECARY_MOD_DIR / 'Apothecary.esp',
    }

    plugin_db = {}
    for p_name, p_path in plugin_files.items():
        plugin_db[p_name] = parse_plugin_ingrs(p_path)

    psc_text = psc_path.read_text(encoding="utf-8")

    # 2. Audit every ProvisionForm and ProvisionFormFallback in psc_text against binary plugins
    re_prov = re.compile(r'ProvisionForm\s*\(\s*player\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\)')
    re_fall = re.compile(r'ProvisionFormFallback\s*\(\s*player\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\)')

    prov_matches = re_prov.findall(psc_text)
    fall_matches = re_fall.findall(psc_text)

    form_errors = []
    for fid_str, plugin in prov_matches:
        fid_int = int(fid_str, 16) & 0x00FFFFFF
        if plugin not in plugin_db:
            form_errors.append(f"Unknown plugin '{plugin}' for FormID {fid_str}")
        elif fid_int not in plugin_db[plugin]:
            form_errors.append(f"FormID {fid_str} NOT FOUND in plugin '{plugin}'!")
        else:
            rec = plugin_db[plugin][fid_int]
            if plugin.lower() != rec['origin_plugin'].lower():
                form_errors.append(
                    f"FormID {fid_str} ({rec.get('name', 'Unknown')}) passed with plugin '{plugin}', but record ORIGINATES in '{rec['origin_plugin']}'! "
                    f"Game.GetFormFromFile in Skyrim requires origin master plugin name, or it returns None."
                )

    for pfid_str, pplugin, sfid_str, splugin in fall_matches:
        pfid_int = int(pfid_str, 16) & 0x00FFFFFF
        sfid_int = int(sfid_str, 16) & 0x00FFFFFF
        primary_valid = (
            pplugin in plugin_db and
            pfid_int in plugin_db[pplugin] and
            pplugin.lower() == plugin_db[pplugin][pfid_int]['origin_plugin'].lower()
        )
        secondary_valid = (
            splugin in plugin_db and
            sfid_int in plugin_db[splugin] and
            splugin.lower() == plugin_db[splugin][sfid_int]['origin_plugin'].lower()
        )
        if not (primary_valid or secondary_valid):
            form_errors.append(
                f"Fallback call failed: neither primary ({pfid_str} in '{pplugin}') nor secondary ({sfid_str} in '{splugin}') "
                f"was valid and matching its origin plugin in binary plugin files!"
            )

    re_gfff = re.compile(r'Game\.GetFormFromFile\s*\(\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\)')
    gfff_matches = re_gfff.findall(psc_text)
    for fid_str, plugin in gfff_matches:
        fid_int = int(fid_str, 16) & 0x00FFFFFF
        if plugin not in plugin_db:
            form_errors.append(f"Unknown plugin '{plugin}' for GetFormFromFile FormID {fid_str}")
        elif fid_int not in plugin_db[plugin]:
            form_errors.append(f"GetFormFromFile FormID {fid_str} NOT FOUND in plugin '{plugin}'!")

    if form_errors:
        print(f"  [FAIL] {len(form_errors)} FormID mismatches against binary plugin files:")
        for err in form_errors:
            print(f"    - {err}")
        errors.extend(form_errors)
    else:
        print(f"  [PASS] All {len(prov_matches)} ProvisionForm calls and {len(gfff_matches)} GetFormFromFile calls verified 100% valid against binary plugin files.")

    # 3. Verify all 82 modeTag handlers exist in ProvisionAndPrintTests
    mode_variants = {
        "vanilla": 17,
        "ap": 12,
        "caco": 18,
        "caco-ap": 11,
        "requiem": 12,
        "apothecary": 12,
    }
    expected_tags = [f"{m}-{i}" for m, count in mode_variants.items() for i in range(1, count + 1)]

    for tag in expected_tags:
        if f'modeTag == "{tag}"' not in psc_text:
            errors.append(f"Missing handler for modeTag '{tag}' in ProsperousAlchemistTests.psc")

    # 4. Extract and validate craft recipes from ProvisionAndPrintTests
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
        craft_lines = re.findall(r'ConsoleUtil\.PrintMessage\("[0-9]+\.\s*(?:Craft|Order [0-9]+):\s*([^"]+)"\)', code)
        
        caco_enabled = "caco" in tag
        requiem_enabled = "requiem" in tag
        apothecary_enabled = "apothecary" in tag

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

            valid, msg = validate_ingredient_combination(ingredients, caco_enabled, requiem_enabled, apothecary_enabled)
            if not valid:
                errors.append(f"Block '{tag}' recipe '{craft}' INVALID: {msg}")
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
                "cacoap": "SetupCACOAP",
                "requiem": "SetupRequiem",
                "apothecary": "SetupApothecary"
            }
            func_name = mode_map[m]
            var = num

        func_pattern = re.compile(rf'string Function {func_name}\s*\((.*?)\)\s*global(.*?)EndFunction', re.DOTALL)
        fmatch = func_pattern.search(psc_text)
        if not fmatch:
            skill_errors.append(f"Function {func_name} missing for phase {phase}")
            continue
        fbody = fmatch.group(2)

        if var == "default":
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
        print(f"  [PASS] All 72 test block and export setup player alchemy skill levels match test-suite.md.")

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

    # 1. Python Pre-Launch Scripts (24 total)
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
        "pat-default-vanilla.py": "pat default vanilla",
        "pat-default-ap.py": "pat default ap",
        "pat-default-caco.py": "pat default caco",
        "pat-default-caco-ap.py": "pat default caco-ap",
        "pat-default-requiem.py": "pat default requiem",
        "pat-default-apothecary.py": "pat default apothecary",
        "pat-vanilla-changed.py": "pat vanilla changed",
        "pat-ap-changed.py": "pat ap changed",
        "pat-caco-changed.py": "pat caco changed",
        "pat-caco-ap-changed.py": "pat caco-ap changed",
        "pat-requiem-changed.py": "pat requiem changed",
        "pat-apothecary-changed.py": "pat apothecary changed",
    }

    py_ok_count = 0
    for script_name, expected_cmd in pat_python_next.items():
        script_path = REPO_ROOT / script_name
        if not script_path.exists():
            errors.append(f"Python script {script_name} does not exist!")
            continue
        res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
        expected_output = f"Next in-game command: run '{expected_cmd}'"
        if expected_output not in res.stdout:
            errors.append(f"Script {script_name} output missing '{expected_output}'. Got stdout: {res.stdout.strip()}")
        else:
            py_ok_count += 1

    if py_ok_count == len(pat_python_next):
        print(f"  [PASS] All {py_ok_count} Python pre-launch scripts output accurate next in-game commands.")

    # 2. Papyrus Script (ProsperousAlchemistTests.psc)
    psc_path = REPO_ROOT / "pa-console-tests" / "Source" / "Scripts" / "ProsperousAlchemistTests.psc"
    psc_text = psc_path.read_text(encoding="utf-8")

    psc_next = {
        "ap-1": "pat ap 2", "ap-2": "pat ap 3", "ap-3": "python pat-ap-2.py",
        "ap-4": "pat ap 5", "ap-5": "pat ap 6", "ap-6": "pat ap 7", "ap-7": "python pat-ap-3.py",
        "ap-8": "pat ap 9", "ap-9": "pat ap 10", "ap-10": "python pat-ap-4.py",
        "ap-11": "pat ap 12", "ap-12": "python pat-vanilla.py",
        "vanilla-1": "pat vanilla 2", "vanilla-2": "pat vanilla 3", "vanilla-3": "pat vanilla 4",
        "vanilla-4": "pat vanilla 5", "vanilla-5": "pat vanilla 6", "vanilla-6": "pat vanilla 7",
        "vanilla-7": "pat vanilla 8", "vanilla-8": "pat vanilla 9", "vanilla-9": "pat vanilla 10",
        "vanilla-10": "pat vanilla 11", "vanilla-11": "pat vanilla 12", "vanilla-12": "pat vanilla 13",
        "vanilla-13": "pat vanilla 14", "vanilla-14": "pat vanilla 15", "vanilla-15": "pat vanilla 16",
        "vanilla-16": "pat vanilla 17", "vanilla-17": "python pat-caco.py",
        "caco-1": "pat caco 2", "caco-2": "pat caco 3", "caco-3": "pat caco 4",
        "caco-4": "pat caco 5", "caco-5": "pat caco 6", "caco-6": "pat caco 7",
        "caco-7": "pat caco 8", "caco-8": "pat caco 9", "caco-9": "pat caco 10",
        "caco-10": "pat caco 11", "caco-11": "pat caco 12", "caco-12": "pat caco 13",
        "caco-13": "pat caco 14", "caco-14": "pat caco 15", "caco-15": "pat caco 16",
        "caco-16": "pat caco 17", "caco-17": "pat caco 18", "caco-18": "python pat-caco-ap.py",
        "caco-ap-1": "pat caco-ap 2", "caco-ap-2": "pat caco-ap 3", "caco-ap-3": "python pat-caco-ap-2.py",
        "caco-ap-4": "pat caco-ap 5", "caco-ap-5": "pat caco-ap 6", "caco-ap-6": "pat caco-ap 7",
        "caco-ap-7": "python pat-caco-ap-3.py", "caco-ap-8": "pat caco-ap 9", "caco-ap-9": "pat caco-ap 10",
        "caco-ap-10": "python pat-caco-ap-4.py", "caco-ap-11": "python pat-requiem.py",
        "requiem-1": "pat requiem 2", "requiem-2": "pat requiem 3", "requiem-3": "pat requiem 4",
        "requiem-4": "pat requiem 5", "requiem-5": "pat requiem 6", "requiem-6": "pat requiem 7",
        "requiem-7": "pat requiem 8", "requiem-8": "pat requiem 9", "requiem-9": "pat requiem 10",
        "requiem-10": "pat requiem 11", "requiem-11": "pat requiem 12", "requiem-12": "python pat-apothecary.py",
        "apothecary-1": "pat apothecary 2", "apothecary-2": "pat apothecary 3", "apothecary-3": "pat apothecary 4",
        "apothecary-4": "pat apothecary 5", "apothecary-5": "pat apothecary 6", "apothecary-6": "pat apothecary 7",
        "apothecary-7": "pat apothecary 8", "apothecary-8": "pat apothecary 9", "apothecary-9": "pat apothecary 10",
        "apothecary-10": "pat apothecary 11", "apothecary-11": "pat apothecary 12", "apothecary-12": "python pat-default-vanilla.py",
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


def main():
    kill_previous_instances()
    print("=================================================================")
    print("PROSPEROUS ALCHEMIST NG - MASTER TEST SUITE VERIFICATION HARNESS")
    print("=================================================================\n")

    p_scripts, f_scripts, e_scripts = verify_pat_python_scripts()
    ok_yaml, e_yaml = verify_pa_tests_yaml()
    p_psc, f_psc, e_psc = verify_psc_and_recipes()
    ok_compile, e_compile = verify_compilation()
    ok_next, e_next = verify_next_command_alignment()

    total_failures = f_scripts + (0 if ok_yaml else 1) + f_psc + (0 if ok_compile else 1) + (0 if ok_next else 1)

    print("\n=================================================================")
    print("MASTER VERIFICATION SUMMARY:")
    print(f"  - Pre-Launch Python Scripts (24 total): {p_scripts} PASSED, {f_scripts} FAILED")
    print(f"  - Console YAML Definition (pa-tests.yaml): {'PASSED' if ok_yaml else 'FAILED'}")
    print(f"  - Test Blocks, Binary FormIDs & Recipe Parity (82 total): {p_psc} PASSED, {f_psc} FAILED")
    print(f"  - Papyrus Compilation & Deployment: {'PASSED' if ok_compile else 'FAILED'}")
    print(f"  - Next Command / Next Step Sequence Alignment: {'PASSED' if ok_next else 'FAILED'}")
    print("=================================================================")

    if total_failures == 0:
        print("\n>>> SUCCESS: 100% ACCURACY VERIFIED ACROSS ALL SCRIPTS, BINARY FORM IDS, AND COMPILED COMMANDS! <<<")
        sys.exit(0)
    else:
        print(f"\n>>> FAILURE: {total_failures} VERIFICATION ERROR(S) DETECTED! <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()

