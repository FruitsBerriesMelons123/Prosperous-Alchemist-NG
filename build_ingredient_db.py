"""Generates canonical ingredient database CSV files in the db/ directory.

Parses:
1. Binary plugin files (.esm, .esp, .esl) for INGR records, FormIDs, EDIDs, display names, and master origin plugins.
2. ingredients-*.csv snapshots for static ingredient/effect data across Vanilla, CACO, Requiem, and Apothecary schemas.

Outputs into repo_root/db/:
- db/master_ingredients.csv
- db/plugin_ingr_records.csv
- db/mode_effects.csv
"""

import csv
import struct
import sys
import zlib
from pathlib import Path
from typing import Any, Dict, List

import config

REPO_ROOT = Path(__file__).resolve().parent
DB_DIR = REPO_ROOT / "db"

PLUGIN_FILES = {
    # Base Game & DLC
    'Skyrim.esm': config.SKYRIM / 'Data' / 'Skyrim.esm',
    'Dawnguard.esm': config.SKYRIM / 'Data' / 'Dawnguard.esm',
    'Dragonborn.esm': config.SKYRIM / 'Data' / 'Dragonborn.esm',
    'HearthFires.esm': config.SKYRIM / 'Data' / 'HearthFires.esm',
    'Update.esm': config.SKYRIM / 'Data' / 'Update.esm',

    # Creation Club Plugins
    'ccbgssse001-fish.esm': config.SKYRIM / 'Data' / 'ccbgssse001-fish.esm',
    'ccbgssse025-advdsgs.esm': config.SKYRIM / 'Data' / 'ccbgssse025-advdsgs.esm',
    'ccbgssse037-curios.esl': config.SKYRIM / 'Data' / 'ccbgssse037-curios.esl',
    'ccqdrsse001-survivalmode.esl': config.SKYRIM / 'Data' / 'ccqdrsse001-survivalmode.esl',
    '_ResourcePack.esl': config.SKYRIM / 'Data' / '_ResourcePack.esl',

    # CACO & Kryptopyr Patches
    'Complete Alchemy & Cooking Overhaul.esp': config.CACO_MOD_DIR / 'Complete Alchemy & Cooking Overhaul.esp',
    'cc-fishing_caco_patch.esp': config.KRYPTOPYR_PATCHES_MOD_DIR / 'cc-fishing_caco_patch.esp',
    'cc-rarecurios_caco_patch.esp': config.KRYPTOPYR_PATCHES_MOD_DIR / 'cc-rarecurios_caco_patch.esp',
    'cc-saints&seducers_caco_patch.esp': config.KRYPTOPYR_PATCHES_MOD_DIR / 'cc-saints&seducers_caco_patch.esp',
    'cc-survivalmode_ussep_caco_patch.esp': config.KRYPTOPYR_PATCHES_MOD_DIR / 'cc-survivalmode_ussep_caco_patch.esp',

    # Requiem
    'Requiem.esp': config.REQUIEM_MOD_DIR / 'Requiem.esp',

    # Apothecary & Patches
    'Apothecary.esp': config.APOTHECARY_MOD_DIR / 'Apothecary.esp',
    'Apothecary - Fishing Patch.esp': config.APOTHECARY_MOD_DIR / 'Apothecary - Fishing Patch.esp',
    'Apothecary - Rare Curios Patch.esp': config.APOTHECARY_MOD_DIR / 'Apothecary - Rare Curios Patch.esp',
    'Apothecary - Saints & Seducers Patch.esp': config.APOTHECARY_MOD_DIR / 'Apothecary - Saints & Seducers Patch.esp',
}


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
        elif rectype in (b'INGR', b'ALCH', b'ARMO', b'TREE', b'FLOR', b'WEAP', b'AMMO', b'SPEL', b'PERK', b'GLOB', b'KYWD', b'MGEF'):
            record_end = offset + 24 + size
            local_form_id = form_id & 0x00FFFFFF
            # The high byte indexes this plugin's master list; an index past the list
            # means the record is new in this plugin, otherwise it overrides a master's.
            master_index = form_id >> 24
            origin_plugin = masters[master_index] if master_index < len(masters) else plugin_path.name

            body = data[offset + 24:record_end]
            if flags & 0x00040000:  # compressed: uint32 decompressed size + zlib stream
                try:
                    body = zlib.decompress(body[4:])
                except zlib.error:
                    body = b''
            sub_offset = 0
            edid = None
            full = None
            while sub_offset + 6 <= len(body):
                sub_type, sub_size = struct.unpack('<4sH', body[sub_offset:sub_offset+6])
                sub_data = body[sub_offset+6:sub_offset+6+sub_size]
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
            results[form_id] = {
                'form_id_hex': f'0x{local_form_id:08X}',
                'raw_form_id_hex': f'0x{form_id:08X}',
                'int_id': local_form_id,
                'rectype': rectype.decode('utf-8', errors='ignore'),
                'edid': edid,
                'name': full,
                'plugin': plugin_path.name,
                'origin_plugin': origin_plugin
            }
            offset = record_end
        else:
            offset += 24 + size
    return results


def build_master_db() -> None:
    print("Building master ingredient CSV database in db/...")
    DB_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Parse binary plugin files -> db/plugin_ingr_records.csv
    plugin_records_csv = DB_DIR / "plugin_ingr_records.csv"
    all_plugin_records = []
    
    for p_name, p_path in PLUGIN_FILES.items():
        if p_path.exists():
            records = parse_plugin_ingrs(p_path)
            for fid, rec in records.items():
                all_plugin_records.append({
                    "plugin_name": p_name,
                    "form_id": rec["form_id_hex"],
                    "raw_form_id": rec["raw_form_id_hex"],
                    "local_form_id_int": rec["int_id"],
                    "rectype": rec["rectype"],
                    "edid": rec.get("edid") or "",
                    "display_name": rec.get("name") or "",
                    "origin_plugin": rec["origin_plugin"],
                })
            print(f"  - Parsed {len(records)} records from binary plugin '{p_name}'")

    with open(plugin_records_csv, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["plugin_name", "form_id", "raw_form_id", "local_form_id_int", "rectype", "edid", "display_name", "origin_plugin"])
        writer.writeheader()
        writer.writerows(all_plugin_records)
    print(f"  -> Written {len(all_plugin_records)} rows to {plugin_records_csv}")

    # 2. Parse mode CSV schemas -> db/mode_effects.csv & db/master_ingredients.csv
    csv_schemas = {
        "vanilla": REPO_ROOT / "ingredients-vanilla.csv",
        "caco": REPO_ROOT / "ingredients-caco.csv",
        "requiem": REPO_ROOT / "ingredients-requiem.csv",
        "apothecary": REPO_ROOT / "ingredients-apothecary.csv",
    }

    mode_effects_rows = []
    master_ingredients_dict: Dict[str, Dict[str, Any]] = {}

    for mode, csv_path in csv_schemas.items():
        if not csv_path.exists():
            print(f"  - Warning: CSV schema '{csv_path.name}' not found")
            continue
        with open(csv_path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                ing = row["ingredient_name"]
                fid = row["form_id"]
                eff_name = row["effect_name"]
                eff_fid = row.get("effect_form_id", "")
                base_cost = row.get("base_cost", "")
                mag = row.get("magnitude", "")
                dur = row.get("duration", "")
                eff_idx = row.get("effect_index", "")

                mode_effects_rows.append({
                    "mode": mode,
                    "ingredient_name": ing,
                    "form_id": fid,
                    "effect_index": eff_idx,
                    "effect_name": eff_name,
                    "effect_form_id": eff_fid,
                    "base_cost": base_cost,
                    "magnitude": mag,
                    "duration": dur,
                })

                ing_key = ing.lower()
                if ing_key not in master_ingredients_dict:
                    master_ingredients_dict[ing_key] = {
                        "ingredient_name": ing,
                        "form_id": fid,
                        "edid": "",
                        "origin_plugin": "",
                        "containing_plugin": "",
                    }

    mode_effects_csv = DB_DIR / "mode_effects.csv"
    with open(mode_effects_csv, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["mode", "ingredient_name", "form_id", "effect_index", "effect_name", "effect_form_id", "base_cost", "magnitude", "duration"])
        writer.writeheader()
        writer.writerows(mode_effects_rows)
    print(f"  -> Written {len(mode_effects_rows)} rows to {mode_effects_csv}")

    # 3. Cross-link master ingredients to origin plugins from binary records
    plugin_lookup = {}
    for rec in all_plugin_records:
        fid_int = rec["local_form_id_int"]
        p_name = rec["plugin_name"]
        plugin_lookup[(p_name, fid_int)] = rec
        plugin_lookup[fid_int] = rec

    for ing_key, ing_data in master_ingredients_dict.items():
        fid_int = int(ing_data["form_id"], 16) & 0x00FFFFFF
        if fid_int in plugin_lookup:
            rec = plugin_lookup[fid_int]
            ing_data["origin_plugin"] = rec["origin_plugin"]
            ing_data["containing_plugin"] = rec["plugin_name"]
            if rec.get("edid"):
                ing_data["edid"] = rec["edid"]

    master_ingredients_csv = DB_DIR / "master_ingredients.csv"
    with open(master_ingredients_csv, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["ingredient_name", "form_id", "edid", "origin_plugin", "containing_plugin"])
        writer.writeheader()
        writer.writerows(list(master_ingredients_dict.values()))
    print(f"  -> Written {len(master_ingredients_dict)} rows to {master_ingredients_csv}")

    print("Master ingredient database CSV files created successfully in db/\n")


if __name__ == "__main__":
    build_master_db()
