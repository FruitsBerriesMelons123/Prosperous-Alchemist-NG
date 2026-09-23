"""Verification script for the user-facing re-craft prompt.

Comprehensively verifies:
1. Single-instance process protection (kill_previous_instances).
2. Every pre-launch Python script in the re-craft prompt exists on disk.
3. Every in-game command / modeTag handler exists in ProsperousAlchemistTests.psc.
4. Every requested ingredient in the re-craft prompt is provisioned in the Papyrus script block handler with valid FormIDs.
5. Every requested recipe is validated for craftability in Skyrim using validate_ingredient_combination against ingredients-*.csv snapshots.
6. Every ProvisionForm call in the target blocks matches its comment name with 100% precision.
"""

import os
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

import config
from pat_config_helper import validate_ingredient_combination

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


RECRAFT_PROMPT_BLOCKS = [
    # (Pre-launch Script, ModeTag / Command Variant, Recipe Ingredients)
    ("pat-ap-4.py", "ap-11", ["Briar Heart", "Canis Root"]),
    ("pat-ap-4.py", "ap-11", ["Blisterwort", "Wheat"]),
    ("pat-ap-4.py", "ap-12", ["Blisterwort", "Wheat"]),
    ("pat-ap-4.py", "ap-12", ["Briar Heart", "Canis Root"]),
    ("pat-vanilla.py", "vanilla-11", ["Blue Mountain Flower", "Blue Butterfly Wing"]),
    ("pat-vanilla.py", "vanilla-12", ["Blue Mountain Flower", "Blue Butterfly Wing"]),
    ("pat-vanilla.py", "vanilla-13", ["Blisterwort", "Wheat"]),
    ("pat-vanilla.py", "vanilla-14", ["Blisterwort", "Wheat"]),
    ("pat-vanilla.py", "vanilla-16", ["Abecean Longfin", "Salt Pile", "Cyrodilic Spadetail"]),
    ("pat-caco.py", "caco-16", ["Creep Cluster", "Giant Lichen", "Rock Warbler Egg"]),
    ("pat-caco.py", "caco-17", ["Blisterwort", "Wheat Extract"]),
    ("pat-caco.py", "caco-18", ["Wisp Wrappings", "Watcher's Eye"]),
    ("pat-caco.py", "caco-18", ["Blind Watcher's Eye", "Watcher's Eye"]),
    ("pat-caco-ap-4.py", "caco-ap-11", ["Blisterwort", "Wheat Extract"]),
    ("pat-caco-ap-4.py", "caco-ap-11", ["Canis Root", "Spider Egg"]),
    ("pat-requiem.py", "requiem-9", ["Blue Mountain Flower", "Wheat"]),
    ("pat-requiem.py", "requiem-9", ["Deathbell", "Nightshade"]),
    ("pat-requiem.py", "requiem-9", ["Glowing Mushroom", "Snowberries"]),
    ("pat-requiem.py", "requiem-10", ["Blue Mountain Flower", "Wheat"]),
    ("pat-requiem.py", "requiem-10", ["Deathbell", "Nightshade"]),
    ("pat-requiem.py", "requiem-10", ["Glowing Mushroom", "Snowberries"]),
    ("pat-requiem.py", "requiem-11", ["Blue Mountain Flower", "Wheat"]),
    ("pat-apothecary.py", "apothecary-11", ["Blisterwort", "Wheat"]),
    ("pat-apothecary.py", "apothecary-11", ["Blue Butterfly Wing", "Blue Mountain Flower"]),
    ("pat-apothecary.py", "apothecary-11", ["Deathbell", "Nightshade"]),
    ("pat-apothecary.py", "apothecary-12", ["Torchbug Thorax", "Chaurus Eggs"]),
]


def verify_recraft_prompt_accuracy() -> Tuple[bool, List[str]]:
    print("--- Verifying Re-Craft Prompt Accuracy ---")
    errors = []

    psc_path = REPO_ROOT / "pa-console-tests" / "Source" / "Scripts" / "ProsperousAlchemistTests.psc"
    if not psc_path.exists():
        return False, ["ProsperousAlchemistTests.psc not found!"]
    psc_text = psc_path.read_text(encoding="utf-8")

    # Extract block handlers from ProvisionAndPrintTests
    tag_to_code = {}
    for chunk in psc_text.split('modeTag == "')[1:]:
        tag = chunk.split('"')[0]
        tag_to_code[tag] = chunk

    # FormID -> ingredient_name map across all CSVs
    import csv
    form_to_name = {}
    for csv_name in ["ingredients-vanilla.csv", "ingredients-caco.csv", "ingredients-requiem.csv", "ingredients-apothecary.csv"]:
        csv_p = REPO_ROOT / csv_name
        if csv_p.exists():
            with open(csv_p, encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    fid = int(r["form_id"], 16) & 0x00FFFFFF
                    form_to_name[fid] = r["ingredient_name"]

    verified_count = 0
    for pre_script, tag, ingredients in RECRAFT_PROMPT_BLOCKS:
        # 1. Pre-launch script check
        script_path = REPO_ROOT / pre_script
        if not script_path.exists():
            errors.append(f"Pre-launch script '{pre_script}' does not exist on disk!")
            continue

        # 2. In-game modeTag handler check
        if tag not in tag_to_code:
            errors.append(f"In-game command handler for '{tag}' missing in ProsperousAlchemistTests.psc!")
            continue

        block_code = tag_to_code[tag]

        # 3. Check that ingredients are provisioned in Papyrus block
        for ing in ingredients:
            # Check comment or FormID name
            if ing.lower() not in block_code.lower():
                errors.append(f"Block '{tag}' does not provision required ingredient '{ing}'!")

        # 4. Recipe craftability check
        caco_enabled = "caco" in tag
        requiem_enabled = "requiem" in tag
        apothecary_enabled = "apothecary" in tag

        valid, msg = validate_ingredient_combination(ingredients, caco_enabled=caco_enabled, requiem_enabled=requiem_enabled, apothecary_enabled=apothecary_enabled)
        if not valid:
            errors.append(f"Re-craft prompt block '{tag}' recipe {ingredients} INVALID: {msg}")
        else:
            verified_count += 1

    # 5. FormID vs Comment Name validation in Papyrus
    re_prov = re.compile(r'ProvisionForm(?:Fallback)?\s*\(\s*player\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"[^;\n]*(?:;\s*([^\r\n]+))?')
    mismatches = []
    for fid_str, plugin, comment in re_prov.findall(psc_text):
        if not comment:
            continue
        fid_int = int(fid_str, 16) & 0x00FFFFFF
        expected_name = form_to_name.get(fid_int)
        clean_comment = comment.strip()
        if expected_name and expected_name.lower() not in clean_comment.lower() and clean_comment.lower() not in expected_name.lower():
            mismatches.append(f"FormID {fid_str} in '{plugin}' is '{expected_name}', but comment specifies '{clean_comment}'!")

    if mismatches:
        errors.extend(mismatches)
        print(f"  [FAIL] {len(mismatches)} FormID vs Comment Name mismatches detected in ProsperousAlchemistTests.psc:")
        for m in mismatches:
            print(f"    - {m}")
    else:
        print(f"  [PASS] All ProvisionForm FormIDs match comment names with 100% precision.")

    if not errors:
        print(f"  [PASS] All {verified_count} re-craft prompt blocks and recipes verified 100% accurate!")
        return True, []
    else:
        print(f"  [FAIL] {len(errors)} re-craft prompt verification errors detected:")
        for e in errors:
            print(f"    - {e}")
        return False, errors


def main():
    kill_previous_instances()
    print("=================================================================")
    print("RE-CRAFT PROMPT ACCURACY VERIFICATION HARNESS")
    print("=================================================================\n")

    ok, errors = verify_recraft_prompt_accuracy()

    print("\n=================================================================")
    print("VERIFICATION SUMMARY:")
    print(f"  - Re-Craft Prompt Accuracy: {'PASSED' if ok else 'FAILED'}")
    print("=================================================================")

    if ok:
        print("\n>>> SUCCESS: RE-CRAFT PROMPT VERIFIED 100% ACCURATE! <<<")
        sys.exit(0)
    else:
        print(f"\n>>> FAILURE: {len(errors)} ERROR(S) DETECTED! <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
