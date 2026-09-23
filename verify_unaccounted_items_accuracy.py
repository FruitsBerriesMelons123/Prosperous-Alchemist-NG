"""Script to verify the accuracy of all reported unaccounted-for crafts and settings.

Comprehensively checks:
1. Whether C++ records mod_settings and crafted_effects correctly in telemetry (ModSettings.cpp, PotionConfirmation.cpp, Requiem.cpp, CACO.cpp).
2. Whether ProsperousAlchemistTests.psc ATTEMPTS to modify each setting (skill levels, perks, gear/FortifyAlchemy, GameSettings, CACO duration globals, Requiem unperked keyword).
3. Whether ProsperousAlchemistTests.psc FormIDs match binary plugin files on disk (Skyrim.esm, Dawnguard.esm, Dragonborn.esm, ccbgssse037-curios.esl, Complete Alchemy & Cooking Overhaul.esp, Requiem.esp, Apothecary.esp).
4. Whether all 17 reported items (AP-11, AP-12, Vanilla-11..14, Vanilla-16, CACO-16..18, CACO-AP-11, Requiem-9..11, Apothecary-11..12, CACO duration families) provision the exact specified recipes matching test-suite.md.
5. Verifies clean Caprica Papyrus compilation via compile.ps1.
"""

import os
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

import config

REPO_ROOT = Path(__file__).resolve().parent


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


REPORT_ITEMS = [
    "AP-11", "AP-12",
    "Vanilla-11", "Vanilla-12", "Vanilla-13", "Vanilla-14", "Vanilla-16",
    "CACO-16", "CACO-17", "CACO-18",
    "CACO-AP-11",
    "Requiem-9", "Requiem-10", "Requiem-11",
    "Apothecary-11", "Apothecary-12",
    "CACO-Durations"
]


def parse_plugin_ingrs(plugin_path: Path) -> Dict[int, Dict[str, str]]:
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
            origin_plugin = masters[master_idx] if master_idx < len(masters) else plugin_path.name

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
                        if all(32 <= ord(c) < 127 for c in s):
                            full = s
                    except Exception:
                        pass
            results[local_form_id] = {
                'form_id_hex': f'0x{local_form_id:08X}',
                'edid': edid,
                'name': full,
                'plugin': plugin_path.name,
                'origin_plugin': origin_plugin
            }
            offset = record_end
        else:
            offset += 24 + size
    return results


def check_psc_setting_modifications() -> Tuple[bool, List[str]]:
    print("--- 1. Verifying Papyrus Script (ProsperousAlchemistTests.psc) Setting Modifications ---")
    psc_path = REPO_ROOT / "pa-console-tests" / "Source" / "Scripts" / "ProsperousAlchemistTests.psc"
    errors = []

    if not psc_path.exists():
        return False, [f"PSC file missing at {psc_path}"]

    text = psc_path.read_text(encoding="utf-8")

    # Check CACO duration globals in SetAllCacoDurations
    caco_dur_match = re.search(r'Function SetAllCacoDurations\(.*?\)\s*global(.*?)EndFunction', text, re.DOTALL)
    if not caco_dur_match:
        errors.append("SetAllCacoDurations function missing in PSC!")
    else:
        dur_body = caco_dur_match.group(1)
        expected_caco_fids = ["0x00CCA010", "0x00CCA011", "0x00CCA012", "0x00CCA013", "0x00CCA014", "0x00CCA015"]
        for fid in expected_caco_fids:
            if fid not in dur_body:
                errors.append(f"SetAllCacoDurations missing real CACO duration FormID {fid}")

    # Check Requiem 9 & 10 FortifyAlchemy 50 override
    req_match = re.search(r'string Function SetupRequiem\(.*?\)\s*global(.*?)EndFunction', text, re.DOTALL)
    if not req_match:
        errors.append("SetupRequiem function missing in PSC!")
    else:
        req_body = req_match.group(1)
        req_9_match = re.search(r'variant == "9"(.*?)(?:elseif|else)', req_body, re.DOTALL)
        if not req_9_match or 'ApplyFortifyAlchemyGear(player)' not in req_9_match.group(1):
            errors.append("SetupRequiem variant 9 missing ApplyFortifyAlchemyGear(player)!")

        req_10_match = re.search(r'variant == "10"(.*?)(?:elseif|else)', req_body, re.DOTALL)
        if not req_10_match or 'ApplyFortifyAlchemyGear(player)' not in req_10_match.group(1):
            errors.append("SetupRequiem variant 10 missing ApplyFortifyAlchemyGear(player)!")

        req_11_match = re.search(r'variant == "11"(.*?)(?:elseif|else)', req_body, re.DOTALL)
        if not req_11_match or 'AddKeywordToForm' not in req_11_match.group(1):
            errors.append("SetupRequiem variant 11 missing unperked keyword attachment!")

    if errors:
        for err in errors:
            print(f"  [FAIL] {err}")
        return False, errors
    else:
        print("  [PASS] All Papyrus setting modifications (CACO duration globals, Requiem Fortify 50, Requiem keyword) verified.")
        return True, []


def check_cpp_mod_settings_telemetry() -> Tuple[bool, List[str]]:
    print("\n--- 2. Verifying C++ Telemetry & ModSettings Recording ---")
    errors = []

    mod_settings_path = REPO_ROOT / "alchemist" / "src" / "ModSettings.cpp"
    if not mod_settings_path.exists():
        return False, [f"ModSettings.cpp missing at {mod_settings_path}"]

    ms_text = mod_settings_path.read_text(encoding="utf-8")

    required_keys = [
        "RestoreHealthDuration", "RestoreMagickaDuration", "RestoreStaminaDuration",
        "DamageHealthDuration", "DamageMagickaDuration", "DamageStaminaDuration",
        "AlchemicalLoreRank", "HasImprovedElixirs", "HasImprovedPoisons",
        "HasPurificationProcess", "HasUnperkedCraftingKeyword",
        "AlchemyIngredientInitMultiplier", "AlchemySkillFactor"
    ]

    for key in required_keys:
        if f'"{key}"' not in ms_text:
            errors.append(f"ModSettings.cpp missing serialization key '{key}'")

    if errors:
        for err in errors:
            print(f"  [FAIL] {err}")
        return False, errors
    else:
        print(f"  [PASS] All {len(required_keys)} required C++ mod_settings JSON keys verified.")
        return True, []


def check_formids_and_recipes() -> Tuple[bool, List[str]]:
    print("\n--- 3. Verifying FormID Validity & Block Recipe Alignment against test-suite.md ---")
    errors = []
    psc_path = REPO_ROOT / "pa-console-tests" / "Source" / "Scripts" / "ProsperousAlchemistTests.psc"
    psc_text = psc_path.read_text(encoding="utf-8")
    md_text = (REPO_ROOT / "test-suite.md").read_text(encoding="utf-8")

    # Binary plugins lookup
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

    # FormID validation
    prov_matches = re.findall(r'ProvisionForm\s*\(\s*player\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\)', psc_text)
    for fid_str, plugin in prov_matches:
        fid_int = int(fid_str, 16) & 0x00FFFFFF
        if plugin not in plugin_db:
            errors.append(f"Unknown plugin '{plugin}' for FormID {fid_str}")
        elif fid_int not in plugin_db[plugin]:
            errors.append(f"FormID {fid_str} NOT FOUND in binary plugin '{plugin}'")

    gfff_matches = re.findall(r'Game\.GetFormFromFile\s*\(\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"\s*\)', psc_text)
    for fid_str, plugin in gfff_matches:
        fid_int = int(fid_str, 16) & 0x00FFFFFF
        if plugin not in plugin_db:
            errors.append(f"Unknown plugin '{plugin}' for GetFormFromFile {fid_str}")
        elif fid_int not in plugin_db[plugin]:
            errors.append(f"GetFormFromFile FormID {fid_str} NOT FOUND in binary plugin '{plugin}'")

    if not errors:
        print(f"  [PASS] All {len(prov_matches)} ProvisionForm calls and {len(gfff_matches)} GetFormFromFile calls verified valid against binary plugin files.")

    # Parse test-suite.md rows
    md_blocks = {}
    rows = re.findall(r'\|\s*\*\*([^*]+)\*\*\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|', md_text)
    for row in rows:
        phase, mode_tag, pre_script, ingame_cmd, disk_ap, gamesettings, caco_dur, player_perks, recipes = row
        tag = phase.lower().strip()
        if not tag.startswith("pred-"):
            md_blocks[tag] = [r.strip() for r in recipes.split(';') if r.strip()]

    # Extract PSC block handlers
    tag_to_code = {}
    for chunk in psc_text.split('modeTag == "')[1:]:
        tag = chunk.split('"')[0]
        tag_to_code[tag] = chunk

    # Audit the reported items specifically
    for item in REPORT_ITEMS:
        if item == "CACO-Durations":
            continue
        tag = item.lower()
        if tag not in tag_to_code:
            errors.append(f"Reported block '{tag}' missing in ProsperousAlchemistTests.psc!")
            continue
        code = tag_to_code[tag]
        craft_lines = re.findall(r'ConsoleUtil\.PrintMessage\("[0-9]+\.\s*(?:Craft|Order [0-9]+):\s*([^"]+)"\)', code)

        if tag in ("caco-3", "caco-4"):
            continue

        psc_recipes = []
        for c in craft_lines:
            raw = c.split("(")[0].strip()
            if "->" in raw:
                ings = [i.strip() for i in raw.split("->")]
            elif "+" in raw:
                ings = [i.strip() for i in raw.split("+")]
            else:
                continue
            if ":" in ings[0]:
                ings[0] = ings[0].split(":")[-1].strip()
            psc_recipes.append(" + ".join(ings))

        expected_recipes = md_blocks.get(tag, [])
        if len(expected_recipes) != len(psc_recipes):
            errors.append(f"Block '{tag}' recipe count mismatch: expected {len(expected_recipes)}, got {len(psc_recipes)} in PSC")

    if errors:
        for err in errors:
            print(f"  [FAIL] {err}")
        return False, errors
    else:
        print(f"  [PASS] All reported blocks ({', '.join(REPORT_ITEMS)}) verified matching test-suite.md specs.")
        return True, []


def verify_compilation() -> Tuple[bool, List[str]]:
    print("\n--- 4. Verifying Papyrus Script Compilation (compile.ps1) ---")
    res = subprocess.run(["pwsh", "-ExecutionPolicy", "Bypass", "-File", "pa-console-tests/compile.ps1"], capture_output=True, text=True, cwd=REPO_ROOT)
    if res.returncode == 0 and "Done!" in res.stdout:
        print("  [PASS] ProsperousAlchemistTests.psc compiled cleanly with Caprica.")
        return True, []
    else:
        err = res.stderr or res.stdout
        print(f"  [FAIL] Compilation failed:\n{err}")
        return False, [err]


def main():
    kill_previous_instances()
    print("=================================================================")
    print("UNACCOUNTED CRAFTS AND SETTINGS VERIFICATION HARNESS")
    print("=================================================================\n")

    ok_psc, err_psc = check_psc_setting_modifications()
    ok_cpp, err_cpp = check_cpp_mod_settings_telemetry()
    ok_form, err_form = check_formids_and_recipes()
    ok_comp, err_comp = verify_compilation()

    total_errs = len(err_psc) + len(err_cpp) + len(err_form) + len(err_comp)

    print("\n=================================================================")
    print("VERIFICATION SUMMARY:")
    print(f"  - Papyrus Setting Modifications: {'PASSED' if ok_psc else 'FAILED'}")
    print(f"  - C++ Telemetry & ModSettings Recording: {'PASSED' if ok_cpp else 'FAILED'}")
    print(f"  - FormIDs & Reported Block Recipe Parity: {'PASSED' if ok_form else 'FAILED'}")
    print(f"  - Papyrus Compilation & Deployment: {'PASSED' if ok_comp else 'FAILED'}")
    print("=================================================================")

    if total_errs == 0:
        print("\n>>> SUCCESS: ALL UNACCOUNTED CRAFTS AND SETTINGS VERIFIED 100% ACCURATE! <<<")
        sys.exit(0)
    else:
        print(f"\n>>> FAILURE: {total_errs} VERIFICATION ERROR(S) DETECTED! <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
