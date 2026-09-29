# Prosperous Alchemist NG - Full Minimal & Comprehensive Test Suite

This document defines the full minimal but comprehensive test suite for Prosperous Alchemist NG. It tests all combinations of ingredient effects, selection orders, modes (`AP`, `Vanilla`, `CACO`, `CACO+AP`, `Requiem`, `Apothecary`, `APAFA`), settings (GameSettings, CACO duration index families, AP JSON thresholds/multipliers/overrides/impure cost fix, Requiem lore/type-perk gates and effect categories, Apothecary skill/category/rank branches, APAFA-adjusted ingredient/effect records), and player levels/perks/purity filters using a minimal, deterministic set of test blocks.

---

## Overview & Architecture

1. **Two-Tier Configuration Architecture & Disk vs In-Game Setting Rule**:
   - **Pre-Launch Disk Setup**: Modes with NO disk-based configuration files (`Vanilla`, `CACO`, `Requiem`, `Apothecary`, `APAFA`) use a **single** root Python script (`pat-vanilla.py`, `pat-caco.py`, `pat-requiem.py`, `pat-apothecary.py`, `pat-apafa.py`) for observed craft testing because multiple disk scripts are redundant when on-disk settings do not change. Modes WITH disk-based configuration files (`AP`, `CACO+AP` with `AlchemyPlus.json`) use enough pre-launch disk scripts (`pat-ap.py`, `pat-ap-2.py`, `pat-ap-3.py`, `pat-ap-4.py`, `pat-caco-ap.py`, `pat-caco-ap-2.py`, `pat-caco-ap-3.py`, `pat-caco-ap-4.py`) to test all distinct on-disk setting configurations.
   - **In-Game Setting Blocks**: Every supported mode features in-game setting blocks (`pat <mode>` through variant ranges: `vanilla` 1-18, `caco` 1-27, `ap` 1-13, `caco-ap` 1-23, `requiem` 1-18, `apothecary` 1-57, `apafa` 1-10), providing 166 observed craft blocks total across the test suite. Each in-game `pat` command contains **no more than 4 tests** (crafts or gate checks).
   - **Skill Level Distribution Rule**: Across the blocks in each mode, **at least 9 blocks use Player Alchemy Level 100**, and **at least 1 block uses Player Alchemy Level < 100** (e.g. Level 50 or 75), ensuring maximum coverage at peak level while validating non-100 skill scaling.
   - **Targeted Ingredient Selection Rule**: Ingredient combinations in every block are strictly chosen to contain the specific effects modified by that block's active settings, perks, overrides, duration indices, or scaling branches (e.g., Physician tests Restore Health/Magicka/Stamina; Poisoner tests poison effects; Purity tests mixed beneficial/harmful recipes; AP magnitude overrides test Restore Health/Stamina; Apothecary tests each of its four category scaling branches).
2. **Optional Full Prediction Export Phase Scripts**:
   - Phase 9 is optional. It exercises full potion prediction exports (`potions-predicted-*.csv.zst`) across **ALL** supported modes/mods (`Vanilla`, `AP`, `CACO`, `CACO+AP`, `Requiem`, `Apothecary`, `APAFA`) using **dedicated, separate** pre-launch disk scripts for default settings (`pat-default-<mode>.py`) and changed settings (`pat-<mode>-changed.py`). These scripts are separate from the observed craft testing scripts. Skipping Phase 9 does not skip the confirmed-craft checks in Phase 8 or prevent completing the required test suite.
3. **Automated In-Game Pre-Test Cleanup & Zero Manual Overhead**:
   Every single in-game command (`pat <mode> [variant]`, e.g. `pat vanilla 2`, `pat caco 3`, `pat ap 4`, `pat requiem 5`, `pat apothecary 8`, `pat default caco`, `pat <mode>-changed`, etc.) automatically handles 100% of state resetting and inventory cleanup at the beginning of the setup function in Papyrus (`ProsperousAlchemistTests.psc`) BEFORE provisioning the new test block:
   - **Clear Player Ingredients**: Automatically removes 100% of all alchemy ingredients from player inventory (`ClearPlayerIngredients`). Utilizes `PO3_SKSEFunctions.AddItemsOfTypeToArray(player, 30)` (FormType 30 = `Ingredient`) and `PO3_SKSEFunctions.AddItemsWithKeywordStringToArray(player, "VendorItemIngredient")` to sweep and strip every single alchemy ingredient item (vanilla, DLC, Creation Club Rare Curios, CACO, Requiem, Apothecary, or any modded ingredient) from the player's inventory prior to provisioning new test block ingredients.
   - **Strip All Perks & Spells**: Automatically strips all 13 alchemy perks (`Alchemist 1-5`, `Physician`, `Benefactor`, `Poisoner`, `Experimenter 1-3`, `Snakeblood`, `Green Thumb`, `Purity`) and `Seeker of Shadows` (`ClearAllAlchemyPerks`).
   - **Unequip Gear & Reset Actor Values**: Automatically unequips Circlet & Necklace of Peerless Alchemy and resets `FortifyAlchemy` actor value back to `0` (`ClearFortifyAlchemyState`).
   - **Reset GameSettings & Mod Globals**: Resets engine GameSettings (`fAlchemyIngredientInitMult`, `fAlchemySkillFactor`) and active mod option globals/durations to match the specific block.
   - **Provision New Block Ingredients**: Grants only the specific perks/gear for that block and provisions 99x of only the required test ingredients.
   - **In-Lab Inventory Refresh**: Press **F** while the Alchemy Lab crafting table UI is focused to refresh inventory without exiting the lab.
4. **Chained Mode Flow**:
   Each `pat` command prints craft recipes line-by-line in Skyrim's console and explicitly indicates the next in-game command (e.g. `Next command: run 'pat vanilla 2'`) or disk step (e.g. `Next step: Exit Skyrim, run 'python pat-ap-2.py'`).
5. **Kryptopyr's Automated Patches & Ingredient Standardization**:
   - `kryptopyr's Automated Patches` (specifically `cc-rarecurios_caco_patch.esp`) standardizes Rare Curios Creation Club content with CACO.
   - It replaces Rare Curios `Aloe Vera Leaves` (`0x0060D0` in `ccbgssse037-curios.esl`) with CACO's native `Aloe Vera` (`0x00A100AD` in `Complete Alchemy & Cooking Overhaul.esp`).
   - Other Rare Curios ingredients (`Comberry`, `Bog Beacon`, `Ambrosia`, `Roobrush`) retain their local FormIDs and are added to CACO formlists via `cc-rarecurios_caco_flm.ini`.
   - **Graceful Provisioning Fallback**: In `ProsperousAlchemistTests.psc`, test ingredient provisioning attempts to resolve CACO's `Aloe Vera` (`0x00A100AD`) first, falling back to Rare Curios `Aloe Vera Leaves` (`0x0060D0`) if CACO or the patch is absent.
   - **Native Plugin & Verification Parity**: `alchemist.dll` and `potion_prediction_test.py` support both ingredient names and FormIDs seamlessly across all modes.
6. **Mandatory Standard for Future Mod Compatibility Additions**:
   - Any future mod integrations added to the project MUST adhere to these architectural rules by default:
     - Single pre-launch script for observed craft testing if the mod has no disk-based configuration files.
     - 10 in-game `pat <mode> [variant]` blocks (9 at Level 100, 1 at Level < 100, max 4 tests per block) covering all in-game settings, perks, engine settings, and mod globals.
     - Separate, dedicated `pat-default-<mod>.py` and `pat-<mod>-changed.py` scripts for the final prediction export phase.

---

## Phase 0: Pre-Test Alignment & Setup

1. **Preserve Existing Observations (Optional)**:
   If you want a clean capture set, back up the deployed `alchemist.potions-confirmed.csv`, `alchemist.potions-confirmed-all.csv`, and `alchemist.potion-observations.csv` before testing. Do not blank, edit, or script-rewrite these files; they are generated by the plugin.
2. **Generate New Observations In-Game**:
   Run the requested `pat` blocks and use the Developer Test Hub's explicit CSV export controls or the plugin's normal capture path. The confirmed CSV uses the plugin-generated 18-column header. After Skyrim exits, the AI validation step reads the newly generated file.

---

## Test Suite Execution Flow

Follow these step-by-step commands sequentially:

### Phase 1: Alchemy Plus (AP) Mode

#### Disk Config 1 (`pat-ap.py`)

- **Block 1 (`pat ap`)**:
  - **Modified Settings**: Disk: CACO disabled, AP enabled (`magnitudeThreshold=10.0`, `magnitudeMult=2.0`, `durationThreshold=10.0`, `durationMult=2.0`, `impureCostFix=False`, overrides for `0x0003EB15` Restore Health [mag 50/10] and `0x0003EB3D` Restore Stamina [dur 20/10]). In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Magnitude override `0x0003EB15` (Restore Health), duration override `0x0003EB3D` (Restore Stamina), Invisibility.
  - **Steps**:
    1. Exit Skyrim (if running).
    2. Run `python pat-ap.py` on disk.
    3. Run `python reset_saves_and_start_skyrim.py`.
    4. Open crafting table in Skyrim.
    5. Run `pat ap` in Skyrim console.
    6. Press **F** while crafting table UI is focused.
    7. Craft:
       - `Blisterwort + Wheat` (Restore Health — tests magnitude override `0x0003EB15`)
       - `Bear Claws + Bee` (Restore Stamina — tests duration override `0x0003EB3D`)
       - `Luna Moth Wing + Vampire Dust` (Invisibility / Health Regen)
    8. **Next Command**: `pat ap 2` in Skyrim console.

- **Block 2 (`pat ap 2`)**:
  - **Modified Settings**: Disk: Staged by `pat-ap.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 3, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: AP low magnitude/duration rounding (+60% Alchemist perk boost).
  - **Steps**:
    1. Run `pat ap 2` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Briar Heart + Canis Root` (Paralyze / Fortify Block)
        - `Blue Butterfly Wing + Blue Mountain Flower` (Restore Health / Fortify Conjuration)
        - `Glowing Mushroom + Nightshade` (Damage Health / Fortify Destruction)
    4. **Next Command**: `pat ap 3` in Skyrim console.

- **Block 3 (`pat ap 3`)**:
  - **Modified Settings**: Disk: Staged by `pat-ap.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist 5, Physician, Benefactor, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Physician (+25% Restore H/M/S) and Benefactor (+25% beneficial) under AP rounding.
  - **Steps**:
    1. Run `pat ap 3` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat` (Restore Health — tests Physician + Benefactor)
        - `Giant's Toe + Wheat` (Fortify Health — tests Benefactor)
        - `Salt Pile + Garlic` (Regen Magicka — tests Benefactor)
    4. **Next Command**: Exit Skyrim and run `python pat-ap-2.py` on disk.

#### Disk Config 2 (`pat-ap-2.py`)

- **Block 4 (`pat ap 4`)**:
  - **Modified Settings**: Disk: Default AP rounding (`magnitudeThreshold=25.0`, `magnitudeMult=5.0`, `durationThreshold=15.0`, `durationMult=5.0`), `impureCostFix=True`, override `0x0003EB15` [mag 25/5]. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: AP default rounding and `impureCostFix=True` on poisons.
  - **Steps**:
    1. Exit Skyrim. Run `python pat-ap-2.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat ap 4` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
        - `Deathbell + River Betty` (Damage Health poison — tests `impureCostFix=True`)
        - `Salt Pile + Garlic` (Regen Magicka)
        - `Chaurus Eggs + Luna Moth Wing` (Invisibility)
    7. **Next Command**: `pat ap 5` in Skyrim console.

- **Block 5 (`pat ap 5`)**:
  - **Modified Settings**: Disk: Staged by `pat-ap-2.py`. In-Game: Player Alchemy 100, Fortify 0, Poisoner perk, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Poisoner (+25% poisons) with AP default rounding and `impureCostFix=True`.
  - **Steps**:
    1. Run `pat ap 5` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Canis Root + Imp Stool` (Paralyze poison — tests Poisoner)
        - `Glowing Mushroom + Nightshade` (Damage Health poison — tests Poisoner)
        - `Deathbell + River Betty` (Damage Health / Slow poison — tests Poisoner)
    4. **Next Command**: `pat ap 6` in Skyrim console.

- **Block 6 (`pat ap 6`)**:
  - **Modified Settings**: Disk: Staged by `pat-ap-2.py`. In-Game: Player Alchemy 100, Fortify 0, Purity perk, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Purity perk stripping harmful side effects under AP rounding.
  - **Steps**:
    1. Run `pat ap 6` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blue Mountain Flower + Wheat` (Restore Health + Damage Magicka — tests Purity stripping Damage Magicka)
        - `Blisterwort + Wheat` (Restore Health + Damage Stamina — tests Purity stripping Damage Stamina)
        - `Briar Heart + Canis Root` (Fortify Block / Paralyze — tests Purity)
    4. **Next Command**: `pat ap 7` in Skyrim console.

- **Block 7 (`pat ap 7`)**:
  - **Modified Settings**: Disk: Staged by `pat-ap-2.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist 5, Physician, Benefactor, Poisoner, Purity, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Full vanilla perk tree under default AP rounding.
  - **Steps**:
    1. Run `pat ap 7` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Creep Cluster + Scaly Pholiota + Mora Tapinella` (Multi-effect beneficial potion)
        - `Abecean Longfin + Cyrodilic Spadetail + Salt Pile` (Poison / Skill craft)
        - `Giant's Toe + Wheat` (Fortify Health)
    4. **Next Command**: Exit Skyrim and run `python pat-ap-3.py` on disk.

#### Disk Config 3 (`pat-ap-3.py`)

- **Block 8 (`pat ap 8`)**:
  - **Modified Settings**: Disk: AP High Rounding (`magnitudeThreshold=30.0`, `magnitudeMult=6.0`, `durationThreshold=20.0`, `durationMult=6.0`), `impureCostFix=True`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=5.0`, `SkillFactor=2.0`.
  - **Target Effects**: High AP threshold rounding with changed GameSettings.
  - **Steps**:
    1. Exit Skyrim. Run `python pat-ap-3.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat ap 8` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
        - `Briar Heart + Canis Root` (Paralyze / Fortify Block)
        - `Dragon's Tongue + Fly Amanita` (Resist Fire / Fortify Two-Handed)
        - `Blue Butterfly Wing + Blue Mountain Flower` (Restore Health / Fortify Conjuration)
    7. **Next Command**: `pat ap 9` in Skyrim console.

- **Block 9 (`pat ap 9`)**:
  - **Modified Settings**: Disk: Staged by `pat-ap-3.py`. In-Game: Player Alchemy 100, Fortify 50 (Peerless gear), Alchemist 4, Physician, Benefactor, `InitMult=4.5`, `SkillFactor=1.8`.
  - **Target Effects**: Fortify Alchemy gear (+50%) + Alchemist 4 + Physician + Benefactor under high AP rounding.
  - **Steps**:
    1. Run `pat ap 9` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat` (Restore Health)
        - `Salt Pile + Garlic` (Regen Magicka)
        - `Giant's Toe + Wheat` (Fortify Health)
    4. **Next Command**: `pat ap 10` in Skyrim console.

- **Block 10 (`pat ap 10`) — Single < 100 Skill Block**:
  - **Modified Settings**: Disk: Staged by `pat-ap-3.py`. In-Game: Player Alchemy 50 (Level < 100), Fortify 50 (Peerless gear), Alchemist 2, Physician, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Non-100 skill scaling (Level 50) + Fortify gear under AP high rounding.
  - **Steps**:
    1. Run `pat ap 10` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Bear Claws + Bee` (Restore Stamina)
        - `Luna Moth Wing + Vampire Dust` (Invisibility / Regen Health)
        - `Berit's Ashes + Bone Meal` (Resist Fire)
    4. **Next Command**: Exit Skyrim and run `python pat-ap-4.py` on disk.

#### Disk Config 4 (`pat-ap-4.py`)

- **Block 11 (`pat ap 11`)**:
  - **Modified Settings**: Disk: AP Rounding OFF (`roundedPotency.enabled=false`, `magnitudeThreshold=25.0`, `durationThreshold=15.0`). In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Evaluation of raw unrounded AP magnitude and duration calculation.
  - **Steps**:
    1. Exit Skyrim. Run `python pat-ap-4.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat ap 11` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
        - `Briar Heart + Canis Root` (Paralyze / Fortify Block — unrounded AP)
        - `Blisterwort + Wheat` (Restore Health — unrounded AP)
    7. **Next Command**: `pat ap 12` in Skyrim console.

- **Block 12 (`pat ap 12`)**:
  - **Modified Settings**: Disk: Staged by `pat-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Full non-zero setting combo test under AP rounding.
  - **Steps**:
    1. Run `pat ap 12` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Ambrosia`
        - `Abecean Longfin + Bleeding Crown`
        - `Luna Moth Wing + Ash Creep Cluster`
    4. **Next Command**: `pat ap 13` in Skyrim console.

- **Block 13 (`pat ap 13`)**:
  - **Modified Settings**: Disk: Staged by `pat-ap-4.py`. In-Game: Player Alchemy 75, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Mid-skill check (Skill 75) under AP default rounding.
  - **Steps**:
    1. Run `pat ap 13` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Ambrosia`
        - `Abecean Longfin + Bleeding Crown`
        - `Luna Moth Wing + Ash Creep Cluster`
    4. **Next Command**: Exit Skyrim and run `python pat-vanilla.py` on disk.

---


---

### Phase 2: Vanilla Mode

Since Vanilla mode has no disk-based configuration files, a single disk script (`pat-vanilla.py`) stages the MO2 environment. All 10 in-game setting blocks run sequentially in one Skyrim session.

#### Disk Config (`pat-vanilla.py`)

- **Block 1 (`pat vanilla`)**:
  - **Modified Settings**: Disk: CACO disabled, AP disabled. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Baseline vanilla formulas across Restore Health, Damage Health, Regen Magicka, Fortify Conjuration.
  - **Steps**:
    1. Exit Skyrim. Run `python pat-vanilla.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat vanilla` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
        - `Blisterwort + Wheat` (Restore Health)
        - `Deathbell + River Betty` (Damage Health / Slow)
        - `Salt Pile + Garlic` (Regen Magicka)
        - `Blue Mountain Flower + Blue Butterfly Wing` (Restore Health / Fortify Conjuration)
    7. **Next Command**: `pat vanilla 2` in Skyrim console.

- **Block 2 (`pat vanilla 2`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 1 (+20%), `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Alchemist Rank 1 (+20% potion value).
  - **Steps**:
    1. Run `pat vanilla 2` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Briar Heart + Canis Root` (Fortify Block / Paralyze)
        - `Bear Claws + Bee` (Restore Stamina)
        - `Glowing Mushroom + Nightshade` (Damage Health / Fortify Destruction)
    4. **Next Command**: `pat vanilla 3` in Skyrim console.

- **Block 3 (`pat vanilla 3`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 3 (+60%), `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Alchemist Rank 3 (+60% potion value).
  - **Steps**:
    1. Run `pat vanilla 3` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Creep Cluster + Scaly Pholiota + Mora Tapinella` (Fortify Carry Weight / Illusion / Regen Stamina)
        - `Giant's Toe + Wheat` (Fortify Health)
        - `Dragon's Tongue + Fly Amanita` (Resist Fire / Fortify Two-Handed)
    4. **Next Command**: `pat vanilla 4` in Skyrim console.

- **Block 4 (`pat vanilla 4`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 5 (+100%), `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Alchemist Rank 5 (+100% potion value).
  - **Steps**:
    1. Run `pat vanilla 4` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat` (Restore Health)
        - `Deathbell + River Betty` (Damage Health)
        - `Salt Pile + Garlic` (Regen Magicka)
    4. **Next Command**: `pat vanilla 5` in Skyrim console.

- **Block 5 (`pat vanilla 5`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist 1 + Physician (+25% Restore H/M/S), `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Physician perk (+25% to Restore Health, Restore Magicka, Restore Stamina).
  - **Steps**:
    1. Run `pat vanilla 5` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat` (Restore Health — tests Physician)
        - `Briar Heart + Ectoplasm` (Restore Magicka — tests Physician)
        - `Bear Claws + Bee` (Restore Stamina — tests Physician)
    4. **Next Command**: `pat vanilla 6` in Skyrim console.

- **Block 6 (`pat vanilla 6`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist 1 + Physician + Benefactor (+25% beneficial), `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Benefactor perk (+25% to all beneficial potions).
  - **Steps**:
    1. Run `pat vanilla 6` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blue Mountain Flower + Blue Butterfly Wing` (Restore Health — tests Benefactor)
        - `Dragon's Tongue + Fly Amanita` (Resist Fire / Fortify Two-Handed — tests Benefactor)
        - `Salt Pile + Garlic` (Regen Magicka — tests Benefactor)
    4. **Next Command**: `pat vanilla 7` in Skyrim console.

- **Block 7 (`pat vanilla 7`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist 1 + Poisoner (+25% poisons), `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Poisoner perk (+25% to all poison/harmful effects).
  - **Steps**:
    1. Run `pat vanilla 7` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Deathbell + River Betty` (Damage Health poison — tests Poisoner)
        - `Canis Root + Imp Stool` (Paralyze / Damage Health poison — tests Poisoner)
        - `Glowing Mushroom + Nightshade` (Damage Health poison — tests Poisoner)
    4. **Next Command**: `pat vanilla 8` in Skyrim console.

- **Block 8 (`pat vanilla 8`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist 5 + Physician + Benefactor + Poisoner + Purity, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Purity perk removing harmful side effects from beneficial potions.
  - **Steps**:
    1. Run `pat vanilla 8` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blue Mountain Flower + Wheat` (Restore Health + Damage Magicka — Purity removes Damage Magicka)
        - `Blisterwort + Wheat` (Restore Health + Damage Stamina — Purity removes Damage Stamina)
        - `Briar Heart + Canis Root` (Fortify Block / Paralyze — Purity removes Paralyze)
    4. **Next Command**: `pat vanilla 9` in Skyrim console.

- **Block 9 (`pat vanilla 9`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 50 (Peerless gear), Alchemist 5 + Physician + Benefactor + Poisoner + Purity + Seeker of Shadows (+10%), `InitMult=5.0`, `SkillFactor=2.0`.
  - **Target Effects**: Seeker of Shadows (+10%) + Fortify Alchemy gear (+50%) + changed GameSettings.
  - **Steps**:
    1. Run `pat vanilla 9` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Giant's Toe + Wheat` (Fortify Health)
        - `Blue Mountain Flower + Blue Butterfly Wing` (Restore Health)
        - `Salt Pile + Garlic` (Regen Magicka)
    4. **Next Command**: `pat vanilla 10` in Skyrim console.

- **Block 10 (`pat vanilla 10`) — Single < 100 Skill Block**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 50 (Level < 100), Fortify 50 (Peerless gear), Alchemist Rank 2, Physician, `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Non-100 skill scaling (Level 50) + Fortify gear + Alchemist 2 + Physician.
  - **Steps**:
    1. Run `pat vanilla 10` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Bear Claws + Bee` (Restore Stamina)
        - `Luna Moth Wing + Vampire Dust` (Invisibility / Regen Health)
        - `Berit's Ashes + Bone Meal` (Resist Fire)
    4. **Next Command**: `pat vanilla 11` in Skyrim console.

- **Block 11 (`pat vanilla 11`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Benefactor perk isolate (Alchemist 0, Physician 0, Benefactor 1).
  - **Target Effects**: Benefactor perk boost (+25%) isolated without Physician or Alchemist perks.
  - **Steps**:
    1. Run `pat vanilla 11` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blue Mountain Flower + Blue Butterfly Wing` (Fortify Conjuration — Benefactor isolate)
    4. **Next Command**: `pat vanilla 12` in Skyrim console.

- **Block 12 (`pat vanilla 12`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Physician perk non-restore effect check (Alchemist 0, Physician 1, Benefactor 0).
  - **Target Effects**: Verification that Physician perk (+25%) does NOT apply to non-Restore Health/Magicka/Stamina effects (Fortify Conjuration).
  - **Steps**:
    1. Run `pat vanilla 12` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blue Mountain Flower + Blue Butterfly Wing` (Fortify Conjuration — 0% Physician boost)
    4. **Next Command**: `pat vanilla 13` in Skyrim console.

- **Block 13 (`pat vanilla 13`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Poisoner perk non-poison check (Alchemist 0, Poisoner 1).
  - **Target Effects**: Verification that Poisoner perk (+25%) does NOT apply to beneficial potions (Restore Health).
  - **Steps**:
    1. Run `pat vanilla 13` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat` (Restore Health — 0% Poisoner boost)
    4. **Next Command**: `pat vanilla 14` in Skyrim console.

- **Block 14 (`pat vanilla 14`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Seeker of Shadows perk isolate (Alchemist 0, Seeker of Shadows 1).
  - **Target Effects**: Seeker of Shadows (+10%) isolated without Alchemist or gear.
  - **Steps**:
    1. Run `pat vanilla 14` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat` (Restore Health — Seeker isolate)
    4. **Next Command**: `pat vanilla 15` in Skyrim console.

- **Block 15 (`pat vanilla 15`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 4 perk isolate (+80%).
  - **Target Effects**: Alchemist Rank 4 (+80% potion value).
  - **Steps**:
    1. Run `pat vanilla 15` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat` (Restore Health — Alchemist Rank 4)
    4. **Next Command**: `pat vanilla 16` in Skyrim console.

- **Block 16 (`pat vanilla 16`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist 5 + Physician + Benefactor + Poisoner + Purity + Seeker of Shadows.
  - **Target Effects**: Full perk combination on complex multi-effect recipe.
  - **Steps**:
    1. Run `pat vanilla 16` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Abecean Longfin + Salt Pile + Cyrodilic Spadetail` (Multi-effect poison/skill potion)
    4. **Next Command**: `pat vanilla 17` in Skyrim console.

- **Block 17 (`pat vanilla 17`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 15 (Level 15 baseline), Fortify 0, no perks.
  - **Target Effects**: Level 15 unperked baseline calculation.
  - **Steps**:
    1. Run `pat vanilla 17` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat` (Restore Health — Level 15 baseline)
    4. **Next Command**: `pat vanilla 18` in Skyrim console.

- **Block 18 (`pat vanilla 18`)**:
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 40, Fortify 0, Alchemist Rank 1 (+20%), `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Row 62 intermediate bracket evaluation (`ROUNDING_TIE_EPSILON` classifier validation).
  - **Steps**:
    1. Run `pat vanilla 18` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Dragon's Tongue + Elves Ear + Fly Amanita` (Row 62 intermediate pre-rounding bracket)
    4. **Next Command**: Exit Skyrim and run `python pat-caco.py` on disk.

---

### Phase 3: CACO Mode

Since CACO options (duration indices, handling flags) are managed in-game via Papyrus global variables, a single disk script (`pat-caco.py`) stages the MO2 environment. All 10 in-game setting blocks run sequentially in one Skyrim session.

#### Disk Config (`pat-caco.py`)

- **Block 1 (`pat caco`)**:
  - **Modified Settings**: Disk: CACO enabled, AP disabled. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO 5s Durations (all Index 1), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
  - **Target Effects**: CACO 5s duration index family (Index 1) on Restore/Damage effects.
  - **Steps**:
    1. Exit Skyrim. Run `python pat-caco.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat caco` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
        - `Boar Tusk + Briar Heart` (Fortify Health 5s)
        - `Creep Cluster + Giant's Toe` (Damage Stamina Regen 5s)
        - `Blisterwort + Wheat` (Restore Health 5s)
        - `Canis Root + Spider Egg` (Damage Stamina 5s)
    7. **Next Command**: `pat caco 2` in Skyrim console.

- **Block 2 (`pat caco 2`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO 10s Durations (all Index 2), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
  - **Target Effects**: CACO 10s duration index family (Index 2) and CACO `Wheat Extract` ingredient.
  - **Steps**:
    1. Run `pat caco 2` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat Extract` (Restore Health 10s — tests CACO extract)
        - `Deathbell + River Betty` (Damage Health 10s)
        - `Ancestor Moth + Blue Mountain Flower` (Fortify Conjuration 10s)
        - `Briar Heart + Ectoplasm` (Restore Magicka 10s)
    4. **Next Command**: `pat caco 3` in Skyrim console.

- **Block 3 (`pat caco 3`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=5.0`, `SkillFactor=2.0`, CACO 0s Durations (all Index 0), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
  - **Target Effects**: Click Selection Order Permutation Matrix (`Roobrush`, `Slaughterfish Egg`, `Large Antlers`) Orders 1 to 4 under CACO 0s duration index.
  - **Steps**:
    1. Run `pat caco 3` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft Permutation Matrix:
        - Order 1: `Roobrush` -> `Slaughterfish Egg` -> `Large Antlers`
        - Order 2: `Slaughterfish Egg` -> `Roobrush` -> `Large Antlers`
        - Order 3: `Large Antlers` -> `Roobrush` -> `Slaughterfish Egg`
        - Order 4: `Large Antlers` -> `Slaughterfish Egg` -> `Roobrush`
    4. **Next Command**: `pat caco 4` in Skyrim console.

- **Block 4 (`pat caco 4`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, CACO 0s Durations (all Index 0).
  - **Target Effects**: Click Selection Order Permutation Matrix Orders 5 & 6, plus CACO native `Aloe Vera` ingredient (`0x00A100AD`).
  - **Steps**:
    1. Run `pat caco 4` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Order 5: Roobrush -> Large Antlers -> Slaughterfish Egg`
        - `Order 6: Slaughterfish Egg -> Large Antlers -> Roobrush`
        - `Aloe Vera + Daedra Heart` (Restore Health — tests CACO `Aloe Vera` ingredient)
    4. **Next Command**: `pat caco 5` in Skyrim console.

- **Block 5 (`pat caco 5`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 2, `InitMult=3.0`, `SkillFactor=3.0`, CACO 5s Durations (Index 1).
  - **Target Effects**: Alchemist Rank 2 boost under CACO 5s durations.
  - **Steps**:
    1. Run `pat caco 5` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Boar Tusk + Briar Heart` (Fortify Health 5s)
        - `Canis Root + Spider Egg` (Damage Stamina 5s)
        - `Blisterwort + Wheat` (Restore Health 5s)
    4. **Next Command**: `pat caco 6` in Skyrim console.

- **Block 6 (`pat caco 6`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, Physician perk, `InitMult=3.0`, `SkillFactor=3.0`, CACO Mixed Durations (RestoreHealth 5s [Index 1], RestoreMagicka 10s [Index 2], DamageHealth 0s [Index 0]).
  - **Target Effects**: Physician perk (+25%) under CACO Mixed Duration indices (5s vs 10s vs 0s).
  - **Steps**:
    1. Run `pat caco 6` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat Extract` (Restore Health 5s — tests Physician + 5s duration)
        - `Briar Heart + Ectoplasm` (Restore Magicka 10s — tests Physician + 10s duration)
        - `Chaurus Eggs + Vampire Dust` (Invisibility / Damage Health 0s — tests 0s duration)
    4. **Next Command**: `pat caco 7` in Skyrim console.

- **Block 7 (`pat caco 7`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, Poisoner perk, `InitMult=3.0`, `SkillFactor=3.0`, CACO 10s Durations (Index 2).
  - **Target Effects**: Poisoner perk (+25%) under CACO 10s duration index.
  - **Steps**:
    1. Run `pat caco 7` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Deathbell + River Betty` (Damage Health 10s poison — tests Poisoner)
        - `Canis Root + Spider Egg` (Damage Stamina 10s poison — tests Poisoner)
        - `Swamp Fungal Pod + Wheat Extract` (Damage Magicka Regen 10s poison — tests Poisoner)
    4. **Next Command**: `pat caco 8` in Skyrim console.

- **Block 8 (`pat caco 8`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, Benefactor perk, `InitMult=3.0`, `SkillFactor=3.0`, CACO 5s Durations (Index 1).
  - **Target Effects**: Benefactor perk (+25%) under CACO 5s duration index.
  - **Steps**:
    1. Run `pat caco 8` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Dragon's Tongue + Fly Amanita` (Resist Fire / Fortify Two-Handed — tests Benefactor)
         - `Ancestor Moth + Blue Mountain Flower` (Fortify Conjuration — tests Benefactor)
         - `Salt Pile + Garlic` (Regen Magicka — tests Benefactor)
    4. **Next Command**: `pat caco 9` in Skyrim console.

- **Block 9 (`pat caco 9`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 50 (Peerless gear), Alchemist 5 + Physician + Benefactor + Poisoner + Purity, `InitMult=3.0`, `SkillFactor=3.0`, CACO Mixed Durations (RestoreHealth 5s [Index 1], RestoreMagicka 10s [Index 2], RestoreStamina 1s [Index 0], DamageHealth 1s [Index 0], DamageMagicka 1s [Index 0], DamageStamina 1s [Index 0]).
  - **Target Effects**: Purity perk + Fortify Alchemy gear (+50%) under CACO mixed durations.
  - **Steps**:
    1. Run `pat caco 9` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Red Mountain Flower + Wheat` (Health + Damage Magicka Regen — Purity strips Damage Magicka Regen under CACO)
         - `Boar Tusk + Briar Heart` (Fortify Health)
         - `Deathbell + River Betty` (Damage Health)
    4. **Next Command**: `pat caco 10` in Skyrim console.

- **Block 10 (`pat caco 10`) — Single < 100 Skill Block**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 50 (Level < 100), Fortify 50 (Peerless gear), Alchemist 3 + Physician, `InitMult=3.0`, `SkillFactor=3.0`, CACO 5s Durations (Index 1).
  - **Target Effects**: Non-100 skill scaling (Level 50) + Fortify gear under CACO 5s durations.
  - **Steps**:
    1. Run `pat caco 10` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat Extract` (Restore Health 5s)
         - `Mudcrab Chitin + Vampire Dust` (Cure Disease)
         - `Dragon's Tongue + Fly Amanita` (Resist Fire)
    4. **Next Command**: `pat caco 11` in Skyrim console.

- **Block 11 (`pat caco 11`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, `RestoreHealthDuration=1` (5s).
  - **Target Effects**: Individual CACO duration MCM slider check: Restore Health 5s slider (Index 1).
  - **Steps**:
    1. Run `pat caco 11` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat Extract` (Restore Health 5s MCM slider)
    4. **Next Command**: `pat caco 12` in Skyrim console.

- **Block 12 (`pat caco 12`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, `RestoreHealthDuration=2` (10s).
  - **Target Effects**: Individual CACO duration MCM slider check: Restore Health 10s slider (Index 2).
  - **Steps**:
    1. Run `pat caco 12` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat Extract` (Restore Health 10s MCM slider)
    4. **Next Command**: `pat caco 13` in Skyrim console.

- **Block 13 (`pat caco 13`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, `DamageHealthDuration=2` (10s), `RestoreMagickaDuration=2` (10s), `RestoreStaminaDuration=2` (10s).
  - **Target Effects**: Individual CACO duration MCM sliders for Damage Health, Restore Magicka, and Restore Stamina.
  - **Steps**:
    1. Run `pat caco 13` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Deathbell + River Betty` (Damage Health 10s slider)
        - `Briar Heart + Ectoplasm` (Restore Magicka 10s slider)
        - `Bear Claws + Bee` (Restore Stamina 10s slider)
    4. **Next Command**: `pat caco 14` in Skyrim console.

- **Block 14 (`pat caco 14`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, Restore Health duration 10s (Index 2).
  - **Target Effects**: CACO Duration Isolation Check: Base Cost 54g effect duration isolate.
  - **Steps**:
    1. Run `pat caco 14` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat Extract` (54g Base Cost effect duration isolate)
    4. **Next Command**: `pat caco 15` in Skyrim console.

- **Block 15 (`pat caco 15`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO 5s Durations (all Index 1).
  - **Target Effects**: CACO Record Exception: Resist Disease Aliasing (`fAlchemyResistDiseaseMult`).
  - **Steps**:
    1. Run `pat caco 15` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Garlic + Mudcrab Chitin` (Resist Disease aliasing)
    4. **Next Command**: `pat caco 16` in Skyrim console.

- **Block 16 (`pat caco 16`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO 10s Durations (all Index 2).
  - **Target Effects**: CACO Record Exception: Damage Undead base cost 8.3 check.
  - **Steps**:
    1. Run `pat caco 16` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Monarch Butterfly + Nightshade` (Damage Undead base cost 8.3)
        - `Creep Cluster + Giant Lichen + Rock Warbler Egg`
    4. **Next Command**: `pat caco 17` in Skyrim console.

- **Block 17 (`pat caco 17`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, Seeker of Shadows active under CACO mode, `InitMult=3.0`, `SkillFactor=3.0`, CACO 5s Durations (all Index 1).
  - **Target Effects**: Verification of zero Seeker of Shadows rows under CACO (CACO disables vanilla Seeker actor value multiplier).
  - **Steps**:
    1. Run `pat caco 17` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat Extract` (Verify zero CACO Seeker rows)
    4. **Next Command**: `pat caco 18` in Skyrim console.

- **Block 18 (`pat caco 18`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, Green Thumb active, `InitMult=3.0`, `SkillFactor=3.0`, CACO 5s Durations (all Index 1).
  - **Target Effects**: Non-potency perk verification (Green Thumb).
  - **Steps**:
    1. Run `pat caco 18` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera + Ambrosia`
    4. **Next Command**: `pat caco 19` in Skyrim console.

- **Block 19 (`pat caco 19`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO RestoreMagicka (1s), RestoreStamina (5s), DamageHealth (5s) durations.
  - **Target Effects**: CACO specific duration family settings baseline.
  - **Steps**:
    1. Run `pat caco 19` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Alkanet Flower + Barley`
        - `Aloe Vera + Bear Claws`
        - `Blue Mountain Flower + Cecropia Moth`
    4. **Next Command**: `pat caco 20` in Skyrim console.

- **Block 20 (`pat caco 20`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO RestoreMagicka (5s) duration.
  - **Target Effects**: CACO Restore Magicka 5s duration setting.
  - **Steps**:
    1. Run `pat caco 20` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Alkanet Flower + Barley`
    4. **Next Command**: `pat caco 21` in Skyrim console.

- **Block 21 (`pat caco 21`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO DamageMagicka (1s) duration.
  - **Target Effects**: CACO Damage Magicka 1s duration setting.
  - **Steps**:
    1. Run `pat caco 21` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Chaurus Eggs + Clouded Funnel Cap`
    4. **Next Command**: `pat caco 22` in Skyrim console.

- **Block 22 (`pat caco 22`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO DamageMagicka (5s) duration.
  - **Target Effects**: CACO Damage Magicka 5s duration setting.
  - **Steps**:
    1. Run `pat caco 22` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Chaurus Eggs + Clouded Funnel Cap`
    4. **Next Command**: `pat caco 23` in Skyrim console.

- **Block 23 (`pat caco 23`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO DamageMagicka (10s) duration.
  - **Target Effects**: CACO Damage Magicka 10s duration setting.
  - **Steps**:
    1. Run `pat caco 23` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Chaurus Eggs + Clouded Funnel Cap`
    4. **Next Command**: `pat caco 24` in Skyrim console.

- **Block 24 (`pat caco 24`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 75, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`.
  - **Target Effects**: CACO mid-skill check (Skill 75) & Lingering Damage Undead verification.
  - **Steps**:
    1. Run `pat caco 24` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera + Ambrosia`
        - `Aloe Vera + Banded Pennant`
    4. **Next Command**: `pat caco 25` in Skyrim console.

- **Block 25 (`pat caco 25`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO RestoreHealth (5s) duration.
  - **Target Effects**: CACO Restore Health 5s duration setting.
  - **Steps**:
    1. Run `pat caco 25` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera + Ambrosia`
    4. **Next Command**: `pat caco 26` in Skyrim console.

- **Block 26 (`pat caco 26`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO RestoreStamina (10s) duration.
  - **Target Effects**: CACO Restore Stamina 10s duration setting.
  - **Steps**:
    1. Run `pat caco 26` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera + Bear Claws`
    4. **Next Command**: `pat caco 27` in Skyrim console.

- **Block 27 (`pat caco 27`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO DamageHealth (10s) duration.
  - **Target Effects**: CACO Damage Health 10s duration setting.
  - **Steps**:
    1. Run `pat caco 27` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blue Mountain Flower + Cecropia Moth`
    4. **Next Command**: Exit Skyrim and run `python pat-caco-ap.py` on disk.

---

### Phase 4: CACO + AP Mode

#### Disk Config 1 (`pat-caco-ap.py`)

- **Block 1 (`pat caco-ap`)**:
  - **Modified Settings**: Disk: CACO enabled, AP enabled, AP Defaults (`magnitudeThreshold=25.0`, `magnitudeMult=5.0`, `durationThreshold=15.0`, `durationMult=5.0`, `impureCostFix=True`). In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO 0s Durations (Index 0).
  - **Target Effects**: CACO + AP default rounding integration with 0s durations.
  - **Steps**:
    1. Exit Skyrim. Run `python pat-caco-ap.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat caco-ap` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
         - `Blisterwort + Wheat Extract` (Restore Health)
         - `Deathbell + River Betty` (Damage Health)
         - `Ash Creep Cluster + Comberry` (Fortify Destruction)
         - `Aloe Vera + Daedra Heart + Large Antlers` (Multi-effect CACO+AP craft)
    7. **Next Command**: `pat caco-ap 2` in Skyrim console.

- **Block 2 (`pat caco-ap 2`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 4, `InitMult=4.0`, `SkillFactor=1.5`, CACO 0s Durations (Index 0).
  - **Target Effects**: Alchemist Rank 4 under CACO+AP default rounding.
  - **Steps**:
    1. Run `pat caco-ap 2` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Mountain Flower + Bog Beacon + Jarrin Root` (Damage Health / Restore Health)
         - `Ash Creep Cluster + Crimson Nirnroot` (Invisibility / Damage Stamina)
         - `Canis Root + Spider Egg` (Damage Stamina)
         - `Dragon's Tongue + Fly Amanita` (Resist Fire)
    4. **Next Command**: `pat caco-ap 3` in Skyrim console.

- **Block 3 (`pat caco-ap 3`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap.py`. In-Game: Player Alchemy 100, Fortify 0, Physician perk, `InitMult=3.0`, `SkillFactor=3.0`, CACO 5s Durations (Index 1).
  - **Target Effects**: Physician perk (+25%) under CACO 5s durations and AP rounding.
  - **Steps**:
    1. Run `pat caco-ap 3` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat Extract` (Restore Health 5s — tests Physician)
         - `Boar Tusk + Briar Heart` (Fortify Health 5s — tests Physician)
         - `Briar Heart + Ectoplasm` (Restore Magicka 5s — tests Physician)
    4. **Next Command**: Exit Skyrim and run `python pat-caco-ap-2.py` on disk.

#### Disk Config 2 (`pat-caco-ap-2.py`)

- **Block 4 (`pat caco-ap 4`)**:
  - **Modified Settings**: Disk: AP Low Rounding (`magnitudeThreshold=10.0`, `magnitudeMult=2.0`, `durationThreshold=10.0`, `durationMult=2.0`, `impureCostFix=True`). In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO 5s Durations (Index 1).
  - **Target Effects**: AP low threshold rounding + CACO 5s duration index.
  - **Steps**:
    1. Exit Skyrim. Run `python pat-caco-ap-2.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat caco-ap 4` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
         - `Boar Tusk + Briar Heart` (Fortify Health 5s)
         - `Creep Cluster + Giant's Toe` (Damage Stamina Regen 5s)
         - `Blue Mountain Flower + Bog Beacon + Jarrin Root` (Damage Health)
         - `Ash Creep Cluster + Crimson Nirnroot` (Invisibility)
    7. **Next Command**: `pat caco-ap 5` in Skyrim console.

- **Block 5 (`pat caco-ap 5`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-2.py`. In-Game: Player Alchemy 100, Fortify 0, Poisoner perk, `InitMult=3.0`, `SkillFactor=3.0`, CACO 10s Durations (Index 2).
  - **Target Effects**: Poisoner perk (+25%) under CACO 10s durations + AP low rounding.
  - **Steps**:
    1. Run `pat caco-ap 5` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + River Betty` (Damage Health 10s poison — tests Poisoner)
         - `Canis Root + Spider Egg` (Damage Stamina 10s poison — tests Poisoner)
         - `Swamp Fungal Pod + Wheat Extract` (Damage Magicka Regen 10s poison — tests Poisoner)
    4. **Next Command**: `pat caco-ap 6` in Skyrim console.

- **Block 6 (`pat caco-ap 6`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-2.py`. In-Game: Player Alchemy 100, Fortify 0, Benefactor perk, `InitMult=3.0`, `SkillFactor=3.0`, CACO 10s Durations (Index 2).
  - **Target Effects**: Benefactor perk (+25%) under CACO 10s durations + AP low rounding.
  - **Steps**:
    1. Run `pat caco-ap 6` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Ash Creep Cluster + Comberry` (Fortify Destruction 10s — tests Benefactor)
         - `Dragon's Tongue + Fly Amanita` (Resist Fire — tests Benefactor)
         - `Salt Pile + Garlic` (Regen Magicka — tests Benefactor)
    4. **Next Command**: `pat caco-ap 7` in Skyrim console.

- **Block 7 (`pat caco-ap 7`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-2.py`. In-Game: Player Alchemy 100, Fortify 0, Purity perk, `InitMult=3.0`, `SkillFactor=3.0`, CACO Mixed Durations (RestoreH 5s, RestoreM 10s, DmgH 0s).
  - **Target Effects**: Purity perk stripping harmful side effects under CACO+AP.
  - **Steps**:
    1. Run `pat caco-ap 7` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Red Mountain Flower + Wheat` (Health + Damage Magicka Regen — Purity strips Damage Magicka Regen)
         - `Blisterwort + Wheat Extract` (Restore Health)
         - `Boar Tusk + Briar Heart` (Fortify Health)
    4. **Next Command**: Exit Skyrim and run `python pat-caco-ap-3.py` on disk.

#### Disk Config 3 (`pat-caco-ap-3.py`)

- **Block 8 (`pat caco-ap 8`)**:
  - **Modified Settings**: Disk: AP High Rounding (`magnitudeThreshold=30.0`, `magnitudeMult=6.0`, `durationThreshold=20.0`, `durationMult=6.0`, `impureCostFix=True`). In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=5.0`, `SkillFactor=2.0`, CACO 10s Durations (Index 2).
  - **Target Effects**: High AP threshold rounding + CACO 10s duration index + changed GameSettings.
  - **Steps**:
    1. Exit Skyrim. Run `python pat-caco-ap-3.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat caco-ap 8` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
         - `Aloe Vera + Daedra Heart` (Restore Health 10s)
         - `Creep Cluster + Scaly Pholiota` (Fortify Carry Weight 10s)
         - `Ancestor Moth + Blue Mountain Flower` (Fortify Conjuration 10s)
    7. **Next Command**: `pat caco-ap 9` in Skyrim console.

- **Block 9 (`pat caco-ap 9`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-3.py`. In-Game: Player Alchemy 100, Fortify 50 (Peerless gear), Alchemist 5, Physician, Benefactor, Poisoner, `InitMult=3.0`, `SkillFactor=3.0`, CACO 5s Durations (Index 1).
  - **Target Effects**: Full perk tree + Fortify gear (+50%) under high AP rounding and CACO 5s durations.
  - **Steps**:
    1. Run `pat caco-ap 9` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat Extract` (Restore Health 5s)
         - `Deathbell + River Betty` (Damage Health 5s)
         - `Ash Creep Cluster + Comberry` (Fortify Destruction 5s)
    4. **Next Command**: `pat caco-ap 10` in Skyrim console.

- **Block 10 (`pat caco-ap 10`) — Single < 100 Skill Block**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-3.py`. In-Game: Player Alchemy 50 (Level < 100), Fortify 50 (Peerless gear), Alchemist 2, Physician, Benefactor, `InitMult=3.0`, `SkillFactor=3.0`, CACO 10s Durations (Index 2).
  - **Target Effects**: Non-100 skill scaling (Level 50) + Fortify gear under CACO+AP high rounding.
  - **Steps**:
    1. Run `pat caco-ap 10` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat Extract` (Restore Health 10s)
         - `Ash Creep Cluster + Comberry` (Fortify Destruction 10s)
         - `Mudcrab Chitin + Vampire Dust` (Cure Disease)
    4. **Next Command**: Exit Skyrim and run `python pat-caco-ap-4.py` on disk.

#### Disk Config 4 (`pat-caco-ap-4.py`)

- **Block 11 (`pat caco-ap 11`)**:
  - **Modified Settings**: Disk: CACO+AP Rounding OFF (`roundedPotency.enabled=false`, `magnitudeThreshold=25.0`, `durationThreshold=15.0`). In-Game: Player Alchemy 100, Fortify 0, Green Thumb active, `InitMult=3.0`, `SkillFactor=3.0`, CACO 1s Durations (all Index 0).
  - **Target Effects**: CACO+AP non-potency perk verification (Green Thumb).
  - **Steps**:
    1. Exit Skyrim. Run `python pat-caco-ap-4.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat caco-ap 11` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
        - `Aloe Vera + Ambrosia`
    7. **Next Command**: `pat caco-ap 12` in Skyrim console.

- **Block 12 (`pat caco-ap 12`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO RestoreMagicka (10s), RestoreStamina (5s) durations under AP rounding.
  - **Target Effects**: CACO+AP duration families baseline.
  - **Steps**:
    1. Run `pat caco-ap 12` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Alkanet Flower + Barley`
        - `Aloe Vera + Bear Claws`
    4. **Next Command**: `pat caco-ap 13` in Skyrim console.

- **Block 13 (`pat caco-ap 13`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO RestoreStamina (10s) duration under AP rounding.
  - **Target Effects**: CACO+AP Restore Stamina 10s duration setting.
  - **Steps**:
    1. Run `pat caco-ap 13` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera + Bear Claws`
    4. **Next Command**: `pat caco-ap 14` in Skyrim console.

- **Block 14 (`pat caco-ap 14`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO DamageMagicka (1s) duration under AP rounding.
  - **Target Effects**: CACO+AP Damage Magicka 1s duration setting.
  - **Steps**:
    1. Run `pat caco-ap 14` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Chaurus Eggs + Clouded Funnel Cap`
    4. **Next Command**: `pat caco-ap 15` in Skyrim console.

- **Block 15 (`pat caco-ap 15`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO DamageMagicka (5s) duration under AP rounding.
  - **Target Effects**: CACO+AP Damage Magicka 5s duration setting.
  - **Steps**:
    1. Run `pat caco-ap 15` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Chaurus Eggs + Clouded Funnel Cap`
    4. **Next Command**: `pat caco-ap 16` in Skyrim console.

- **Block 16 (`pat caco-ap 16`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO DamageMagicka (10s) duration under AP rounding.
  - **Target Effects**: CACO+AP Damage Magicka 10s duration setting.
  - **Steps**:
    1. Run `pat caco-ap 16` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Chaurus Eggs + Clouded Funnel Cap`
    4. **Next Command**: `pat caco-ap 17` in Skyrim console.

- **Block 17 (`pat caco-ap 17`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 75, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`.
  - **Target Effects**: CACO+AP mid-skill check (Skill 75) & Lingering Damage Undead verification.
  - **Steps**:
    1. Run `pat caco-ap 17` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera + Ambrosia`
        - `Aloe Vera + Banded Pennant`
    4. **Next Command**: `pat caco-ap 18` in Skyrim console.

- **Block 18 (`pat caco-ap 18`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, Seeker of Shadows active, no perks.
  - **Target Effects**: CACO+AP Seeker of Shadows unperked check.
  - **Steps**:
    1. Run `pat caco-ap 18` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera + Ambrosia`
        - `Black Pearl + Blue Clipper Butterfly`
    4. **Next Command**: `pat caco-ap 19` in Skyrim console.

- **Block 19 (`pat caco-ap 19`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, Seeker of Shadows active, Alchemist 1.
  - **Target Effects**: CACO+AP Seeker of Shadows + Alchemist 1 check.
  - **Steps**:
    1. Run `pat caco-ap 19` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera + Ambrosia`
    4. **Next Command**: `pat caco-ap 20` in Skyrim console.

- **Block 20 (`pat caco-ap 20`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, Seeker of Shadows active, Alchemist 3.
  - **Target Effects**: CACO+AP Seeker of Shadows + Alchemist 3 check.
  - **Steps**:
    1. Run `pat caco-ap 20` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera + Ambrosia`
    4. **Next Command**: `pat caco-ap 21` in Skyrim console.

- **Block 21 (`pat caco-ap 21`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO RestoreHealth (5s) duration.
  - **Target Effects**: CACO+AP Restore Health 5s duration setting.
  - **Steps**:
    1. Run `pat caco-ap 21` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera + Ambrosia`
    4. **Next Command**: `pat caco-ap 22` in Skyrim console.

- **Block 22 (`pat caco-ap 22`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO RestoreMagicka (1s) duration.
  - **Target Effects**: CACO+AP Restore Magicka 1s duration setting.
  - **Steps**:
    1. Run `pat caco-ap 22` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Alkanet Flower + Barley`
    4. **Next Command**: `pat caco-ap 23` in Skyrim console.

- **Block 23 (`pat caco-ap 23`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO RestoreMagicka (5s) duration.
  - **Target Effects**: CACO+AP Restore Magicka 5s duration setting.
  - **Steps**:
    1. Run `pat caco-ap 23` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Alkanet Flower + Barley`
    4. **Next Command**: Exit Skyrim and run `python pat-requiem.py` on disk.

---

### Phase 5: Requiem Mode

Requiem is tested as an independent mode with CACO and Alchemy Plus disabled. Since Requiem has no disk configuration files, a single disk script (`pat-requiem.py`) stages Requiem in `modlist.txt` and the load order. All 10 in-game setting blocks run sequentially in one Skyrim session. In Requiem blocks, salt is provisioned as `0x034CDF` from `Skyrim.esm`; Requiem renames it `Salt`, so craft lines say `Salt`. (`0x074A19` is `REQ_NULL_MS03BlackBriarSecretIngredient` in Requiem and is not used.)

#### Disk Config (`pat-requiem.py`)

- **Block 1 (`pat requiem`)**:
  - **Modified Settings**: Disk: Requiem enabled; CACO disabled; AP disabled. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore 1, `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Requiem Alchemical Lore 1 baseline formula.
  - **Steps**:
    1. Exit Skyrim if running. Run `python pat-requiem.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat requiem` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
         - `Blue Mountain Flower + Wheat` (Restore Health)
         - `Deathbell + Nightshade` (Damage Health)
         - `Glowing Mushroom + Nightshade` (Fortify Destruction)
    7. **Next Command**: `pat requiem 2` in Skyrim console.

- **Block 2 (`pat requiem 2`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore 1 + 2 (effective tier 2), `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Requiem Alchemical Lore 2 tier scaling.
  - **Steps**:
    1. Run `pat requiem 2` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Mountain Flower + Wheat` (Restore Health)
         - `Deathbell + Nightshade` (Damage Health)
         - `Glowing Mushroom + Nightshade` (Fortify Destruction)
         - `Glowing Mushroom + Snowberries` (Resist Shock)
    4. **Next Command**: `pat requiem 3` in Skyrim console.

- **Block 3 (`pat requiem 3`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore 1 + 2 + Improved Elixirs only, `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Improved Elixirs (+25% magnitude to Elixirs; zero boost to poisons).
  - **Steps**:
    1. Run `pat requiem 3` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Mountain Flower + Wheat` (Elixir — receives +25% Improved Elixirs boost)
         - `Salt + Garlic` (Elixir — receives +25% Improved Elixirs boost)
         - `Deathbell + Nightshade` (Poison — no Improved Elixirs boost)
    4. **Next Command**: `pat requiem 4` in Skyrim console.

- **Block 4 (`pat requiem 4`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore 1 + 2 + Improved Poisons only, `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Improved Poisons (+25% magnitude/duration to Poisons; zero boost to elixirs).
  - **Steps**:
    1. Run `pat requiem 4` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Poison — receives +25% Improved Poisons boost)
         - `Briar Heart + Creep Cluster` (Poison — receives +25% Improved Poisons boost)
         - `Blue Mountain Flower + Wheat` (Elixir — no Improved Poisons boost)
    4. **Next Command**: `pat requiem 5` in Skyrim console.

- **Block 5 (`pat requiem 5`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore 1 + 2 + Purification Process only, `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Purification Process stripping negative side effects from beneficial potions.
  - **Steps**:
    1. Run `pat requiem 5` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Mountain Flower + Wheat` (Restore Health + Damage Magicka Regen — purified)
         - `Blue Mountain Flower + Blue Butterfly Wing` (Restore Health + Damage Magicka Regen — purified)
         - `Salt + Garlic` (Regen Magicka)
    4. **Next Command**: `pat requiem 6` in Skyrim console.

- **Block 6 (`pat requiem 6`) — No-Lore Gate Check**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, no Alchemical Lore perks (Unperked gate check), `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Requiem unperked/no-Lore crafting availability gate check.
  - **Steps**:
    1. Run `pat requiem 6` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Attempt:
         - `Blue Mountain Flower + Wheat` (Verify recipe availability/suppression)
         - `Deathbell + Nightshade` (Verify recipe availability/suppression)
    4. **Next Command**: `pat requiem 7` in Skyrim console.

- **Block 7 (`pat requiem 7`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore 1 + 2 + Improved Elixirs + Improved Poisons, `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Combined Improved Elixirs (+25%) and Improved Poisons (+25%).
  - **Steps**:
    1. Run `pat requiem 7` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Mountain Flower + Wheat` (Elixir — +25%)
         - `Deathbell + Nightshade` (Poison — +25%)
         - `Salt + Garlic` (Elixir — +25%)
    4. **Next Command**: `pat requiem 8` in Skyrim console.

- **Block 8 (`pat requiem 8`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore 1 + 2 + Improved Elixirs + Improved Poisons + Purification Process (Full tree), `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Full Requiem perk tree (Elixirs + Poisons + Purification).
  - **Steps**:
    1. Run `pat requiem 8` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Mountain Flower + Wheat` (Purified Elixir)
         - `Briar Heart + Creep Cluster` (Improved Poison)
         - `Dragon's Tongue + Fly Amanita` (Improved Elixir)
    4. **Next Command**: `pat requiem 9` in Skyrim console.

- **Block 9 (`pat requiem 9`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 50 (Peerless gear), Alchemical Lore 1 + 2 + Improved Elixirs + Improved Poisons + Purification Process, `InitMult=4.5`, `SkillFactor=1.8`.
  - **Target Effects**: Fortify Alchemy gear (+50%) + changed GameSettings under full Requiem perks.
  - **Steps**:
    1. Run `pat requiem 9` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Mountain Flower + Wheat`
         - `Deathbell + Nightshade`
         - `Glowing Mushroom + Snowberries`
    4. **Next Command**: `pat requiem 10` in Skyrim console.

- **Block 10 (`pat requiem 10`) — Single < 100 Skill Block**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 50 (Level < 100), Fortify 50 (Peerless gear), Alchemical Lore 1 + 2, `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Non-100 skill scaling (Level 50) + Fortify gear under Requiem Lore 2.
  - **Steps**:
    1. Run `pat requiem 10` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Mountain Flower + Wheat`
         - `Glowing Mushroom + Snowberries`
         - `Deathbell + Nightshade`
    4. **Next Command**: `pat requiem 11` in Skyrim console.

- **Block 11 (`pat requiem 11`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, unperked crafting keyword `REQ_RacialSkills_CreatePotionsUnperked` (`0x00AD3A3B` in `Requiem.esp`) present without Lore perks.
  - **Target Effects**: Requiem Lore 0 unperked keyword crafting availability check.
  - **Steps**:
    1. Run `pat requiem 11` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Mountain Flower + Wheat` (Unperked keyword craft)
    4. **Next Command**: `pat requiem 12` in Skyrim console.

- **Block 12 (`pat requiem 12`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore 1 + 2 + Improved Elixirs perk.
  - **Target Effects**: Improved Elixirs Fortify Skill x0.5 multiplier check on skill fortify potions.
  - **Steps**:
    1. Run `pat requiem 12` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Glowing Mushroom + Nightshade` (Fortify Destruction — Improved Elixirs x0.5 skill factor)
    4. **Next Command**: `pat requiem 13` in Skyrim console.

- **Block 13 (`pat requiem 13`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore rank 2, `InitMult=4.0`, `SkillFactor=1.1`, no type perks.
  - **Target Effects**: Requiem Fortify-skill x0.5 keyword checks 1 (Alteration, Barter, Block, Conjuration).
  - **Steps**:
    1. Run `pat requiem 13` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blind Watcher's Eye + Burnt Spriggan Wood` (Fortify Alteration — x0.5 check)
        - `Butterfly Wing + Dragon's Tongue` (Fortify Barter — x0.5 check)
        - `Aster Bloom Core + Boar Tusk` (Fortify Block — x0.5 check)
        - `Ancestor Moth Wing + Congealed Putrescence` (Fortify Conjuration — x0.5 check)
    4. **Next Command**: `pat requiem 14` in Skyrim console.

- **Block 14 (`pat requiem 14`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore rank 2, `InitMult=4.0`, `SkillFactor=1.1`, no type perks.
  - **Target Effects**: Requiem Fortify-skill x0.5 keyword checks 2 (Enchanting, Illusion, Marksman, One-Handed).
  - **Steps**:
    1. Run `pat requiem 14` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Dreugh Wax + Stoneflower Petals` (Fortify Enchanting — x0.5 check)
        - `Bliss Bug Thorax + Dwarven Oil` (Fortify Illusion — x0.5 check)
        - `Angelfish + Canis Root` (Fortify Marksman — x0.5 check)
        - `Canis Root + Hanging Moss` (Fortify One-Handed — x0.5 check)
    4. **Next Command**: `pat requiem 15` in Skyrim console.

- **Block 15 (`pat requiem 15`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Green Thumb (nulled by Requiem) active, `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Nulled perk verification (Green Thumb is `REQ_NULL_GreenThumb` in Requiem; no bonus expected).
  - **Steps**:
    1. Run `pat requiem 15` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera Leaves + Ambrosia`
    4. **Next Command**: `pat requiem 16` in Skyrim console.

- **Block 16 (`pat requiem 16`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 75, Fortify 0, Alchemical Lore rank 2, `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Requiem mid-skill check (Skill 75 Alchemical Lore 2).
  - **Steps**:
    1. Run `pat requiem 16` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera Leaves + Ambrosia`
    4. **Next Command**: `pat requiem 17` in Skyrim console.

- **Block 17 (`pat requiem 17`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore rank 2, Physician (nulled by Requiem) active, `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Nulled perk verification (Physician is `REQ_NULL_Physician` in Requiem; no +25% expected).
  - **Steps**:
    1. Run `pat requiem 17` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera Leaves + Ambrosia`
    4. **Next Command**: `pat requiem 18` in Skyrim console.

- **Block 18 (`pat requiem 18`)**:
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore rank 2, Seeker of Shadows active, `InitMult=4.0`, `SkillFactor=1.1`.
  - **Target Effects**: Requiem Seeker of Shadows perk verification.
  - **Steps**:
    1. Run `pat requiem 18` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aloe Vera Leaves + Ambrosia`
    4. **Next Command**: Exit Skyrim and run `python pat-apothecary.py` on disk.

---

### Phase 6: Apothecary Mode

Apothecary is tested with CACO and Alchemy Plus disabled. Since Apothecary has no disk configuration files, a single disk script (`pat-apothecary.py`) stages Apothecary in `modlist.txt` and the load order. 10 in-game setting blocks run sequentially in one Skyrim session. The configured SPID profile distributes `MAG_ControllerScalingPerk` (`0x050CB06C`, `0A725C~Skyrim.esm`) to the player. In Apothecary blocks, `Salt Pile` is provisioned as `0x034CDF` from `Skyrim.esm` (Apothecary overrides it as `MAG_SaltPile`). (`0x074A19` is `MAG_MS03BlackBriarSecretIngredient`, the Black-Briar secret ingredient, and is not used.)

#### Disk Config (`pat-apothecary.py`)

- **Block 1 (`pat apothecary`)**:
  - **Modified Settings**: Disk: Apothecary enabled, CACO/AP disabled. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`; SPID perk present.
  - **Target Effects**: Baseline Level 100 scaling across ALL 4 Apothecary formula categories (Fortify Skill +1.5%/lvl, Restore Attribute +0.667%/lvl, Fortify Regen Rate +0.52%/lvl, Generic/Poison +1.25%/lvl).
  - **Steps**:
    1. Exit Skyrim if running. Run `python pat-apothecary.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat apothecary` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
         - `Blue Butterfly Wing + Blue Mountain Flower` (Fortify Skill branch: +1.5%/lvl above 15)
         - `Blisterwort + Wheat` (Restore Attribute branch: +0.667%/lvl above 15)
         - `Salt Pile + Garlic` (Fortify Regen Rate branch: +0.52%/lvl above 15)
         - `Canis Root + Spider Egg` (Generic / Poison branch: +1.25%/lvl above 15)
    7. **Next Command**: `pat apothecary 2` in Skyrim console.

- **Block 2 (`pat apothecary 2`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 1, `InitMult=4.0`, `SkillFactor=1.5`; SPID perk present.
  - **Target Effects**: Alchemist Rank 1 multiplier across Apothecary categories.
  - **Steps**:
    1. Run `pat apothecary 2` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat` (Restore Health)
         - `Blue Butterfly Wing + Blue Mountain Flower` (Fortify Conjuration)
         - `Salt Pile + Garlic` (Regen Magicka)
    4. **Next Command**: `pat apothecary 3` in Skyrim console.

- **Block 3 (`pat apothecary 3`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 3, `InitMult=4.0`, `SkillFactor=1.5`; SPID perk present.
  - **Target Effects**: Alchemist Rank 3 multiplier.
  - **Steps**:
    1. Run `pat apothecary 3` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat` (Restore Health)
         - `Deathbell + Nightshade` (Damage Health)
         - `Luna Moth Wing + Vampire Dust` (Regen Health)
    4. **Next Command**: `pat apothecary 4` in Skyrim console.

- **Block 4 (`pat apothecary 4`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 5, `InitMult=4.0`, `SkillFactor=1.5`; SPID perk present.
  - **Target Effects**: Alchemist Rank 5 multiplier across all four formula categories.
  - **Steps**:
    1. Run `pat apothecary 4` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Butterfly Wing + Blue Mountain Flower` (Fortify Skill)
         - `Blisterwort + Wheat` (Restore Attribute)
         - `Salt Pile + Garlic` (Fortify Regen Rate)
         - `Canis Root + Spider Egg` (Generic / Poison)
    4. **Next Command**: `pat apothecary 5` in Skyrim console.

- **Block 5 (`pat apothecary 5`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 50 (Peerless gear), Alchemist Rank 3, `InitMult=4.0`, `SkillFactor=1.5`; SPID perk present.
  - **Target Effects**: Fortify Alchemy gear scaling (+50%) under Apothecary formulas.
  - **Steps**:
    1. Run `pat apothecary 5` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat` (Restore Health)
         - `Blue Butterfly Wing + Blue Mountain Flower` (Fortify Conjuration)
         - `Salt Pile + Garlic` (Regen Magicka)
    4. **Next Command**: `pat apothecary 6` in Skyrim console.

- **Block 6 (`pat apothecary 6`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 4, `InitMult=4.5`, `SkillFactor=1.8`; SPID perk present.
  - **Target Effects**: Changed GameSettings (`InitMult=4.5`, `SkillFactor=1.8`) under Apothecary Alchemist Rank 4.
  - **Steps**:
    1. Run `pat apothecary 6` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat` (Restore Health)
         - `Deathbell + Nightshade` (Damage Health)
         - `Luna Moth Wing + Vampire Dust` (Regen Health)
    4. **Next Command**: `pat apothecary 7` in Skyrim console.

- **Block 7 (`pat apothecary 7`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`; SPID perk present.
  - **Target Effects**: Focused evaluation of Fortify Skill (+1.5%/lvl) and Fortify Regen Rate (+0.52%/lvl) scaling categories.
  - **Steps**:
    1. Run `pat apothecary 7` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Butterfly Wing + Blue Mountain Flower` (Fortify Skill branch: +1.5%/lvl)
         - `Dragon's Tongue + Fly Amanita` (Fortify Skill branch: +1.5%/lvl)
         - `Salt Pile + Garlic` (Fortify Regen Rate branch: +0.52%/lvl)
         - `Luna Moth Wing + Vampire Dust` (Fortify Regen Rate branch: +0.52%/lvl)
    4. **Next Command**: `pat apothecary 8` in Skyrim console.

- **Block 8 (`pat apothecary 8`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`; SPID perk present.
  - **Target Effects**: Focused evaluation of Restore Attribute (+0.667%/lvl) and Generic / Poison (+1.25%/lvl) scaling categories.
  - **Steps**:
    1. Run `pat apothecary 8` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat` (Restore Attribute branch: +0.667%/lvl)
         - `Briar Heart + Ectoplasm` (Restore Attribute branch: +0.667%/lvl)
         - `Deathbell + Nightshade` (Generic / Poison branch: +1.25%/lvl)
         - `Canis Root + Spider Egg` (Generic / Poison branch: +1.25%/lvl)
    4. **Next Command**: `pat apothecary 9` in Skyrim console.

- **Block 9 (`pat apothecary 9`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 2, `InitMult=4.0`, `SkillFactor=1.5`; SPID perk present.
  - **Target Effects**: Alchemist Rank 2 scaling across mixed categories.
  - **Steps**:
    1. Run `pat apothecary 9` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat` (Restore Health)
         - `Blue Butterfly Wing + Blue Mountain Flower` (Fortify Conjuration)
         - `Deathbell + Nightshade` (Damage Health)
    4. **Next Command**: `pat apothecary 10` in Skyrim console.

- **Block 10 (`pat apothecary 10`) — Single < 100 Skill Block**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 50 (Level < 100), Fortify 50 (Peerless gear), Alchemist Rank 3, `InitMult=4.0`, `SkillFactor=1.5`; SPID perk present.
  - **Target Effects**: Non-100 intermediate skill scaling (Level 50 = +35 levels above 15) + Fortify gear under Apothecary.
  - **Steps**:
    1. Run `pat apothecary 10` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat` (Restore Attribute: +0.667%/lvl x 35)
         - `Blue Butterfly Wing + Blue Mountain Flower` (Fortify Skill: +1.5%/lvl x 35)
         - `Salt Pile + Garlic` (Regen Rate: +0.52%/lvl x 35)
         - `Deathbell + Nightshade` (Generic: +1.25%/lvl x 35)
    4. **Next Command**: `pat apothecary 11` in Skyrim console.

- **Block 11 (`pat apothecary 11`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 75 (Level 75 = +60 levels above 15), Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Level 75 scaling across Restore Attribute (+0.667%/lvl x 60), Fortify Skill (+1.5%/lvl x 60), Generic (+1.25%/lvl x 60) + Level 60 stepped scaling boundary check.
  - **Steps**:
    1. Run `pat apothecary 11` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat` (Restore Attribute: +0.667%/lvl x 60)
         - `Blue Butterfly Wing + Blue Mountain Flower` (Fortify Skill: +1.5%/lvl x 60)
         - `Deathbell + Nightshade` (Generic / Poison: +1.25%/lvl x 60)
    4. **Next Command**: `pat apothecary 12` in Skyrim console.

- **Block 12 (`pat apothecary 12`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Fortify Stamina 2.5 multiplier category scaling branch check.
  - **Steps**:
    1. Run `pat apothecary 12` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Torchbug Thorax + Chaurus Eggs` (Fortify Stamina — 2.5 multiplier category)
    4. **Next Command**: `pat apothecary 13` in Skyrim console.

- **Block 13 (`pat apothecary 13`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Resist-Family scaling branch (`category_mult = 1.0` vs generic `1 + 0.0125*(skill-15)`).
  - **Steps**:
    1. Run `pat apothecary 13` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Fly Amanita + Snowberries` (Resist Fire at Skill 100)
         - `Frost Mirriam + Snowberries` (Resist Frost at Skill 100)
         - `Glowing Mushroom + Snowberries` (Resist Shock at Skill 100)
         - `Beehive Husk + Thistle Branch` (Resist Poison at Skill 100)
    4. **Next Command**: `pat apothecary 14` in Skyrim console.

- **Block 14 (`pat apothecary 14`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 50, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Reflect Damage scaling formula verification at Skill 50 (`1 + 0.015*skill`).
  - **Steps**:
    1. Run `pat apothecary 14` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Daedra Heart + Eye of Sabre Cat` (Reflect Damage at Skill 50)
    4. **Next Command**: `pat apothecary 15` in Skyrim console.

- **Block 15 (`pat apothecary 15`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Reflect Damage scaling formula verification at Skill 100 (`1 + 0.015*skill`).
  - **Steps**:
    1. Run `pat apothecary 15` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Daedra Heart + Eye of Sabre Cat` (Reflect Damage at Skill 100)
    4. **Next Command**: `pat apothecary 16` in Skyrim console.

- **Block 16 (`pat apothecary 16`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Damage Health perk rank bracketing — Rank 0 baseline (R1) & direct single-effect Resist Magic verification at Skill 100 (RM1).
  - **Steps**:
    1. Run `pat apothecary 16` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Damage Health Rank 0 Baseline — R1)
         - `Chicken's Egg + Tundra Cotton` (Resist Magic at Skill 100 — RM1)
    4. **Next Command**: `pat apothecary 17` in Skyrim console.

- **Block 17 (`pat apothecary 17`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 1, all perks 0.
  - **Target Effects**: Damage Health perk rank bracketing — Rank 1 bracket.
  - **Steps**:
    1. Run `pat apothecary 17` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Damage Health Rank 1 Bracket)
    4. **Next Command**: `pat apothecary 18` in Skyrim console.

- **Block 18 (`pat apothecary 18`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 2, all perks 0.
  - **Target Effects**: Damage Health perk rank bracketing — Rank 2 bracket (R2).
  - **Steps**:
    1. Run `pat apothecary 18` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Damage Health Rank 2 Bracket — R2)
    4. **Next Command**: `pat apothecary 19` in Skyrim console.

- **Block 19 (`pat apothecary 19`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 4, all perks 0.
  - **Target Effects**: Damage Health perk rank bracketing — Rank 4 bracket.
  - **Steps**:
    1. Run `pat apothecary 19` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Damage Health Rank 4 Bracket)
    4. **Next Command**: `pat apothecary 20` in Skyrim console.

- **Block 20 (`pat apothecary 20`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 15, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Restore Health/Magicka direct `skill` vs `(skill - 15)` baseline offset verification at Skill 15.
  - **Steps**:
    1. Run `pat apothecary 20` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Wheat` (Restore Health at Skill 15)
         - `Red Mountain Flower + Tundra Cotton` (Restore Magicka at Skill 15)
    4. **Next Command**: `pat apothecary 21` in Skyrim console.

- **Block 21 (`pat apothecary 21`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 25, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Damage Health skill scaling lower bracket map (D1).
  - **Steps**:
    1. Run `pat apothecary 21` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Damage Health at Skill 25 — D1)
    4. **Next Command**: `pat apothecary 22` in Skyrim console.

- **Block 22 (`pat apothecary 22`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 40, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Damage Health skill scaling interpolation (D2), Restore Magicka low-mid skill point (RS1), and Restore Stamina low-mid skill point (RS3).
  - **Steps**:
    1. Run `pat apothecary 22` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Damage Health at Skill 40 — D2)
         - `Red Mountain Flower + Mora Tapinella` (Restore Magicka at Skill 40 — RS1)
         - `Purple Mountain Flower + Sabre Cat Tooth` (Restore Stamina at Skill 40 — RS3)
    4. **Next Command**: `pat apothecary 23` in Skyrim console.

- **Block 23 (`pat apothecary 23`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 50, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Damage Stamina cross-effect check (D6), Reflect Damage single-effect isolation at Skill 50 (RF1), and Resist Magic skill independence check (RM2).
  - **Steps**:
    1. Run `pat apothecary 23` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Canis Root + Spider Egg` (Damage Stamina at Skill 50 — D6)
         - `Dwarven Oil + Scaly Pholiota` (Reflect Damage at Skill 50 — RF1)
         - `Chicken's Egg + Tundra Cotton` (Resist Magic at Skill 50 — RM2)
    4. **Next Command**: `pat apothecary 24` in Skyrim console.

- **Block 24 (`pat apothecary 24`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 60, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Damage Health skill scaling above skill 50 pin point (D3).
  - **Steps**:
    1. Run `pat apothecary 24` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Damage Health at Skill 60 — D3)
    4. **Next Command**: `pat apothecary 25` in Skyrim console.

- **Block 25 (`pat apothecary 25`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 75, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Damage Health skill scaling midpoint (D4), Damage Stamina curve shape verification (D7), and Reflect Damage scaling curve verification at Skill 75 (RF2).
  - **Steps**:
    1. Run `pat apothecary 25` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Damage Health at Skill 75 — D4)
         - `Canis Root + Spider Egg` (Damage Stamina at Skill 75 — D7)
         - `Dwarven Oil + Scaly Pholiota` (Reflect Damage at Skill 75 — RF2)
    4. **Next Command**: `pat apothecary 26` in Skyrim console.

- **Block 26 (`pat apothecary 26`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 75, Fortify 0, Alchemist Rank 2, all perks 0.
  - **Target Effects**: Restore Magicka with perked multiplier at Skill 75 (RS2) and Restore Stamina with perked multiplier at Skill 75 (RS4).
  - **Steps**:
    1. Run `pat apothecary 26` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Red Mountain Flower + Mora Tapinella` (Restore Magicka at Skill 75 Rank 2 — RS2)
         - `Purple Mountain Flower + Sabre Cat Tooth` (Restore Stamina at Skill 75 Rank 2 — RS4)
    4. **Next Command**: `pat apothecary 27` in Skyrim console.

- **Block 27 (`pat apothecary 27`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 90, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Damage Health near-cap skill scaling behavior check (D5).
  - **Steps**:
    1. Run `pat apothecary 27` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Damage Health at Skill 90 — D5)
    4. **Next Command**: `pat apothecary 28` in Skyrim console.

- **Block 28 (`pat apothecary 28`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 5, all perks 0.
  - **Target Effects**: Damage Health rank bracket completion — Rank 5 ceiling rank (R3).
  - **Steps**:
    1. Run `pat apothecary 28` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Nightshade` (Damage Health Rank 5 Ceiling — R3)
    4. **Next Command**: `pat apothecary 29` in Skyrim console.

- **Block 29 (`pat apothecary 29`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Probe untested "else" category scaling branch at Skill 100 (Weakness to Fire, Fear, Fortify Carry Weight, Damage Weapon).
  - **Steps**:
    1. Run `pat apothecary 29` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Bleeding Crown + Bliss Bug Thorax` (Weakness to Fire at Skill 100)
         - `Blue Dartwing + Bog Beacon` (Fear at Skill 100)
         - `Coda Flower + Creep Cluster` (Fortify Carry Weight at Skill 100)
         - `Ancestor Moth Wing + Burnt Spriggan Wood` (Damage Weapon at Skill 100)
    4. **Next Command**: `pat apothecary 30` in Skyrim console.

- **Block 30 (`pat apothecary 30`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Untested categories & siblings at Skill 100 (Lingering Damage Health, Stamina Regeneration, Fortify Health, and baseline Deathbell + Jarrin Root Damage Health).
  - **Steps**:
    1. Run `pat apothecary 30` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Imp Stool + Orange Dartwing` (Lingering Damage Health at Skill 100)
         - `Bee + Scaly Pholiota` (Stamina Regeneration at Skill 100)
         - `Bear Claws + Giant's Toe` (Fortify Health at Skill 100)
         - `Deathbell + Jarrin Root` (Damage Health at Skill 100 Rank 0)
    4. **Next Command**: `pat apothecary 31` in Skyrim console.

- **Block 31 (`pat apothecary 31`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 15, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Weakness to Fire scaling curve shape probe at Skill 15.
  - **Steps**:
    1. Run `pat apothecary 31` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Bleeding Crown + Bliss Bug Thorax` (Weakness to Fire at Skill 15)
    4. **Next Command**: `pat apothecary 32` in Skyrim console.

- **Block 32 (`pat apothecary 32`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 50, Fortify 0, Alchemist Rank 0, all perks 0.
  - **Target Effects**: Weakness to Fire scaling curve shape probe at Skill 50.
  - **Steps**:
    1. Run `pat apothecary 32` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Bleeding Crown + Bliss Bug Thorax` (Weakness to Fire at Skill 50)
    4. **Next Command**: `pat apothecary 33` in Skyrim console.

- **Block 33 (`pat apothecary 33`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 75, Fortify 0, Alchemist Rank 3, all perks 0.
  - **Target Effects**: Damage Health scaling slope interval pinning — Skill 75, Rank 3 (`Deathbell + Jarrin Root`).
  - **Steps**:
    1. Run `pat apothecary 33` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Jarrin Root` (Damage Health at Skill 75 Rank 3)
    4. **Next Command**: `pat apothecary 34` in Skyrim console.

- **Block 34 (`pat apothecary 34`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 75, Fortify 0, Alchemist Rank 4, all perks 0.
  - **Target Effects**: Damage Health scaling slope interval pinning — Skill 75, Rank 4 (`Deathbell + Jarrin Root`).
  - **Steps**:
    1. Run `pat apothecary 34` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Jarrin Root` (Damage Health at Skill 75 Rank 4)
    4. **Next Command**: `pat apothecary 35` in Skyrim console.

- **Block 35 (`pat apothecary 35`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 85, Fortify 0, Alchemist Rank 2, all perks 0.
  - **Target Effects**: Damage Health scaling slope interval pinning — Skill 85, Rank 2 (`Deathbell + Jarrin Root`).
  - **Steps**:
    1. Run `pat apothecary 35` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Jarrin Root` (Damage Health at Skill 85 Rank 2)
    4. **Next Command**: `pat apothecary 36` in Skyrim console.

- **Block 36 (`pat apothecary 36`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 2, all perks 0.
  - **Target Effects**: Damage Health scaling slope interval pinning — Skill 100, Rank 2 (`Deathbell + Jarrin Root`).
  - **Steps**:
    1. Run `pat apothecary 36` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Jarrin Root` (Damage Health at Skill 100 Rank 2)
    4. **Next Command**: `pat apothecary 37` in Skyrim console.

- **Block 37 (`pat apothecary 37`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 4, all perks 0.
  - **Target Effects**: Damage Health scaling slope interval pinning — Skill 100, Rank 4 (`Deathbell + Jarrin Root`).
  - **Steps**:
    1. Run `pat apothecary 37` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Jarrin Root` (Damage Health at Skill 100 Rank 4)
    4. **Next Command**: `pat apothecary 38` in Skyrim console.

- **Block 38 (`pat apothecary 38`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Alchemist Rank 5, all perks 0.
  - **Target Effects**: Damage Health scaling slope interval pinning — Skill 100, Rank 5 (`Deathbell + Jarrin Root`).
  - **Steps**:
    1. Run `pat apothecary 38` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Deathbell + Jarrin Root` (Damage Health at Skill 100 Rank 5)
    4. **Next Command**: `pat apothecary 39` in Skyrim console.

- **Block 39 (`pat apothecary 39`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 15, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Isolated Fear scaling curve shape probe at Skill 15 (`Blue Dartwing + Cyrodilic Spadetail`).
  - **Steps**:
    1. Run `pat apothecary 39` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Dartwing + Cyrodilic Spadetail` (Fear at Skill 15)
    4. **Next Command**: `pat apothecary 40` in Skyrim console.

- **Block 40 (`pat apothecary 40`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 50, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Isolated Fear scaling curve shape probe at Skill 50 (`Blue Dartwing + Cyrodilic Spadetail`).
  - **Steps**:
    1. Run `pat apothecary 40` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Dartwing + Cyrodilic Spadetail` (Fear at Skill 50)
    4. **Next Command**: `pat apothecary 41` in Skyrim console.

- **Block 41 (`pat apothecary 41`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Illusion keyword family verification (Frenzy) and Weakness family verification (Weakness to Frost, Weakness to Shock, Weakness to Poison).
  - **Steps**:
    1. Run `pat apothecary 41` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blisterwort + Falmer Ear` (Frenzy at Skill 100 — Illusion keyword family check)
         - `Abecean Longfin + Elves Ear` (Weakness to Frost at Skill 100)
         - `Ashen Grass Pod + Bee` (Weakness to Shock at Skill 100)
         - `Chaurus Eggs + Deathbell` (Weakness to Poison at Skill 100)
    4. **Next Command**: `pat apothecary 42` in Skyrim console.

- **Block 42 (`pat apothecary 42`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Additional "else" bucket effects verification (Fortify Sneak, Fortify Speed, Fortify Armor Rating, Fortify Lockpicking).
  - **Steps**:
    1. Run `pat apothecary 42` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Abecean Longfin + Beehive Husk` (Fortify Sneak at Skill 100)
         - `Abecean Longfin + Deathbell` (Fortify Speed at Skill 100)
         - `Blisterwort + Glowing Mushroom` (Fortify Armor Rating at Skill 100)
         - `Ashen Grass Pod + Falmer Ear` (Fortify Lockpicking at Skill 100)
    4. **Next Command**: `pat apothecary 43` in Skyrim console.

- **Block 43 (`pat apothecary 43`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Additional "else" bucket effects & Lingering Damage family verification (Fortify Pickpocket, Damage Armor, Lingering Damage Stamina, Lingering Damage Magicka).
  - **Steps**:
    1. Run `pat apothecary 43` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Blue Dartwing + Orange Dartwing` (Fortify Pickpocket at Skill 100)
         - `Bear Claws + Glow Dust` (Damage Armor at Skill 100)
         - `Butterfly Wing + Chicken's Egg` (Lingering Damage Stamina at Skill 100)
         - `Hagraven Claw + Purple Mountain Flower` (Lingering Damage Magicka at Skill 100)
    4. **Next Command**: `pat apothecary 44` in Skyrim console.

- **Block 44 (`pat apothecary 44`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Lingering Damage Health clean single-effect craft and untested power/skill siblings (Fortify Alteration Power, Fortify Block, Fortify One-handed).
  - **Steps**:
    1. Run `pat apothecary 44` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
         - `Imp Stool + Orange Dartwing` (Lingering Damage Health clean craft at Skill 100)
         - `Grass Pod + River Betty` (Fortify Alteration Power at Skill 100)
         - `Briar Heart + Honeycomb` (Fortify Block at Skill 100)
         - `Bear Claws + Canis Root` (Fortify One-handed at Skill 100)
    4. **Next Command**: `pat apothecary 45` in Skyrim console.

- **Block 45 (`pat apothecary 45`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Untested duration-scaled effects 1 (Become Ethereal, Muffle, Night Eye, Waterwalking).
  - **Steps**:
    1. Run `pat apothecary 45` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Bone Meal + Giant's Toe` (Become Ethereal at Skill 100)
        - `Ambrosia + Bittergreen Petals` (Muffle at Skill 100)
        - `Blister Pod Cap + Kagouti Hide` (Night Eye at Skill 100)
        - `Falmer Ear + Skeever Tail` (Waterwalking at Skill 100)
    4. **Next Command**: `pat apothecary 46` in Skyrim console.

- **Block 46 (`pat apothecary 46`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Untested duration-scaled & Illusion family effects (Light, Waterbreathing, Calm, Command).
  - **Steps**:
    1. Run `pat apothecary 46` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Alocasia Fruit + Blind Watcher's Eye` (Light at Skill 100)
        - `Angelfish + Angler Larvae` (Waterbreathing at Skill 100)
        - `Bone Meal + Bungler's Bane` (Calm at Skill 100)
        - `Bee + Berit's Ashes` (Command at Skill 100)
    4. **Next Command**: `pat apothecary 47` in Skyrim console.

- **Block 47 (`pat apothecary 47`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Untested Illusion & Else bucket effects (Paralysis, Silence, Cure Disease, Fortify Barter).
  - **Steps**:
    1. Run `pat apothecary 47` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Aster Bloom Core + Canis Root` (Paralysis at Skill 100)
        - `Frost Mirriam + Grass Pod` (Silence at Skill 100)
        - `Charred Skeever Hide + Hawk Feathers` (Cure Disease at Skill 100)
        - `Butterfly Wing + Imp Gall` (Fortify Barter at Skill 100)
    4. **Next Command**: `pat apothecary 48` in Skyrim console.

- **Block 48 (`pat apothecary 48`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, no perks; SPID perk present.
  - **Target Effects**: Untested Power & Else bucket effects (Fortify Destruction Power, Fortify Power Attacks, Fortify Shouts, Fortify Sneak Attacks).
  - **Steps**:
    1. Run `pat apothecary 48` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Ash Creep Cluster + Beehive Husk` (Fortify Destruction Power at Skill 100)
        - `Ash Hopper Jelly + Beehive Husk` (Fortify Power Attacks at Skill 100)
        - `Bliss Bug Thorax + Bog Beacon` (Fortify Shouts at Skill 100)
        - `Ancestor Moth Wing + Hagraven Claw` (Fortify Sneak Attacks at Skill 100)
    4. **Next Command**: `pat apothecary 49` in Skyrim console.

- **Block 49 (`pat apothecary 49`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Green Thumb active.
  - **Target Effects**: Non-potency perk verification (Green Thumb).
  - **Steps**:
    1. Run `pat apothecary 49` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Ambrosia`
    4. **Next Command**: `pat apothecary 50` in Skyrim console.

- **Block 50 (`pat apothecary 50`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Physician, Benefactor, Poisoner, Seeker of Shadows flags ON.
  - **Target Effects**: Full perk combination check under Apothecary.
  - **Steps**:
    1. Run `pat apothecary 50` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Ambrosia`
        - `Angelfish + Canis Root`
        - `Coda Flower + Jarrin Root`
    4. **Next Command**: `pat apothecary 51` in Skyrim console.

- **Block 51 (`pat apothecary 51`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 100, Fortify 0, Physician, Benefactor, Poisoner flags ON.
  - **Target Effects**: Physician + Benefactor + Poisoner baseline check.
  - **Steps**:
    1. Run `pat apothecary 51` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Ambrosia`
    4. **Next Command**: `pat apothecary 52` in Skyrim console.

- **Block 52 (`pat apothecary 52`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 90, Fortify 0, no perks.
  - **Target Effects**: Skill 90 unperked poison verification.
  - **Steps**:
    1. Run `pat apothecary 52` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Deathbell + Jarrin Root`
    4. **Next Command**: `pat apothecary 53` in Skyrim console.

- **Block 53 (`pat apothecary 53`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 65, Fortify 0, Alchemist rank 1.
  - **Target Effects**: Skill 65 Alchemist 1 poison verification.
  - **Steps**:
    1. Run `pat apothecary 53` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Deathbell + Jarrin Root`
    4. **Next Command**: `pat apothecary 54` in Skyrim console.

- **Block 54 (`pat apothecary 54`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 85, Fortify 0, Alchemist rank 1.
  - **Target Effects**: Skill 85 Alchemist 1 poison verification.
  - **Steps**:
    1. Run `pat apothecary 54` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Deathbell + Jarrin Root`
    4. **Next Command**: `pat apothecary 55` in Skyrim console.

- **Block 55 (`pat apothecary 55`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 25, Fortify 0, no perks.
  - **Target Effects**: Skill 25 unperked potion & regenerate magicka verification.
  - **Steps**:
    1. Run `pat apothecary 55` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Ambrosia`
        - `Dwarven Oil + Garlic`
    4. **Next Command**: `pat apothecary 56` in Skyrim console.

- **Block 56 (`pat apothecary 56`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 60, Fortify 0, no perks.
  - **Target Effects**: Skill 60 unperked potion verification.
  - **Steps**:
    1. Run `pat apothecary 56` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Ambrosia`
    4. **Next Command**: `pat apothecary 57` in Skyrim console.

- **Block 57 (`pat apothecary 57`)**:
  - **Modified Settings**: Disk: Staged by `pat-apothecary.py`. In-Game: Player Alchemy 90, Fortify 0, no perks.
  - **Target Effects**: Skill 90 unperked potion & invisibility verification.
  - **Steps**:
    1. Run `pat apothecary 57` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Ambrosia`
        - `Dwarven Oil + Garlic`
        - `Angelfish + Ash Creep Cluster`
        4. **Next Command**: Exit Skyrim and run `python pat-apafa.py` on disk.

---

### Phase 7: APAFA Mode

APAFA replaces ingredient/effect records and exposes two potion-relevant MCM controls backed by the engine settings `fAlchemyIngredientInitMult` and `fAlchemySkillFactor`. The exporter records those true APAFA MCM values in the unified `mod_settings` JSON. The observed craft blocks keep both values at defaults except block 10, which checks changed MCM values.

#### Disk Config (`pat-apafa.py`)

Each block uses the MO2 `Default` profile, APAFA enabled, and Alchemy Plus, CACO, Requiem, and Apothecary disabled. APAFA has no disk JSON; `AlchemyPlus.json` is at defaults but inactive; CACO duration indices are inactive. The listed commands clear ingredients, perks, gear, actor values, and settings before provisioning the listed recipe. Press **F** with the Alchemy Lab UI focused after each setup.

- **Block 1 (`pat apafa`)**:
  - **Modified Settings**: Disk: APAFA on, AP/CACO/Requiem/Apothecary off; APAFA no disk JSON; MO2 Default profile. In-Game: Alchemy 100, Fortify 0, Alchemist rank 0, no type perks; InitMult 4.0, SkillFactor 1.5; CACO duration indices inactive.
  - **Target Effects**: APAFA Resist Frost ingredient records.
  - **Steps**:
    1. Press **F** while the Alchemy Lab UI is focused.
    2. Craft:
       - `Thistle Branch + Snowberries`
    3. **Next Command**: `pat apafa 2`.
- **Block 2 (`pat apafa 2`)**:
  - **Modified Settings**: Disk: APAFA on, AP/CACO/Requiem/Apothecary off; APAFA no disk JSON; MO2 Default profile. In-Game: Alchemy 100, Fortify 0, Alchemist rank 1, no type perks; InitMult 4.0, SkillFactor 1.5; CACO duration indices inactive.
  - **Target Effects**: APAFA Restore Health ingredient records.
  - **Steps**:
    1. Press **F** while the Alchemy Lab UI is focused.
    2. Craft:
       - `Blisterwort + Wheat`
    3. **Next Command**: `pat apafa 3`.
- **Block 3 (`pat apafa 3`)**:
  - **Modified Settings**: Disk: APAFA on, AP/CACO/Requiem/Apothecary off; APAFA no disk JSON; MO2 Default profile. In-Game: Alchemy 100, Fortify 0, Alchemist rank 2, no type perks; InitMult 4.0, SkillFactor 1.5; CACO duration indices inactive.
  - **Target Effects**: APAFA Fortify Health ingredient records.
  - **Steps**:
    1. Press **F** while the Alchemy Lab UI is focused.
    2. Craft:
       - `Ambrosia + Bear Claws`
    3. **Next Command**: `pat apafa 4`.
- **Block 4 (`pat apafa 4`)**:
  - **Modified Settings**: Disk: APAFA on, AP/CACO/Requiem/Apothecary off; APAFA no disk JSON; MO2 Default profile. In-Game: Alchemy 100, Fortify 0, Alchemist rank 3, Benefactor; InitMult 4.0, SkillFactor 1.5; CACO duration indices inactive.
  - **Target Effects**: APAFA Resist Fire ingredient records and Benefactor.
  - **Steps**:
    1. Press **F** while the Alchemy Lab UI is focused.
    2. Craft:
       - `Angelfish + Ash Creep Cluster`
    3. **Next Command**: `pat apafa 5`.
- **Block 5 (`pat apafa 5`)**:
  - **Modified Settings**: Disk: APAFA on, AP/CACO/Requiem/Apothecary off; APAFA no disk JSON; MO2 Default profile. In-Game: Alchemy 100, Fortify 0, Alchemist rank 4, Physician and Benefactor; InitMult 4.0, SkillFactor 1.5; CACO duration indices inactive.
  - **Target Effects**: APAFA Regenerate Health ingredient records.
  - **Steps**:
    1. Press **F** while the Alchemy Lab UI is focused.
    2. Craft:
       - `Alocasia Fruit + Ambrosia`
    3. **Next Command**: `pat apafa 6`.
- **Block 6 (`pat apafa 6`)**:
  - **Modified Settings**: Disk: APAFA on, AP/CACO/Requiem/Apothecary off; APAFA no disk JSON; MO2 Default profile. In-Game: Alchemy 100, Fortify 0, Alchemist rank 5, no type perks; InitMult 4.0, SkillFactor 1.5; CACO duration indices inactive.
  - **Target Effects**: APAFA Invisibility ingredient records.
  - **Steps**:
    1. Press **F** while the Alchemy Lab UI is focused.
    2. Craft:
       - `Ash Creep Cluster + Bittergreen Petals`
    3. **Next Command**: `pat apafa 7`.
- **Block 7 (`pat apafa 7`)**:
  - **Modified Settings**: Disk: APAFA on, AP/CACO/Requiem/Apothecary off; APAFA no disk JSON; MO2 Default profile. In-Game: Alchemy 100, Fortify 0, Alchemist rank 5, Physician; InitMult 4.0, SkillFactor 1.5; CACO duration indices inactive.
  - **Target Effects**: APAFA Damage Health ingredient records and Physician.
  - **Steps**:
    1. Press **F** while the Alchemy Lab UI is focused.
    2. Craft:
       - `Chokeberry + Coda Flower`
    3. **Next Command**: `pat apafa 8`.
- **Block 8 (`pat apafa 8`)**:
  - **Modified Settings**: Disk: APAFA on, AP/CACO/Requiem/Apothecary off; APAFA no disk JSON; MO2 Default profile. In-Game: Alchemy 100, Fortify 0, Alchemist rank 5, Poisoner; InitMult 4.0, SkillFactor 1.5; CACO duration indices inactive.
  - **Target Effects**: APAFA Weakness to Poison ingredient records and Poisoner.
  - **Steps**:
    1. Press **F** while the Alchemy Lab UI is focused.
    2. Craft:
       - `Abecean Longfin + Deathbell`
    3. **Next Command**: `pat apafa 9`.
- **Block 9 (`pat apafa 9`)**:
  - **Modified Settings**: Disk: APAFA on, AP/CACO/Requiem/Apothecary off; APAFA no disk JSON; MO2 Default profile. In-Game: Alchemy 100, Fortify 0, Alchemist rank 5, Purity; InitMult 4.0, SkillFactor 1.5; CACO duration indices inactive.
  - **Target Effects**: APAFA Lingering Damage Stamina ingredient records.
  - **Steps**:
    1. Press **F** while the Alchemy Lab UI is focused.
    2. Craft:
       - `Bittergreen Petals + Coda Flower`
    3. **Next Command**: `pat apafa 10`.
- **Block 10 (`pat apafa 10`)**:
  - **Modified Settings**: Disk: APAFA on, AP/CACO/Requiem/Apothecary off; APAFA no disk JSON; MO2 Default profile. In-Game: Alchemy 75, Fortify 0, Alchemist rank 3, no type perks; APAFA MCM InitMult 5.0 and SkillFactor 2.0; CACO duration indices inactive.
  - **Target Effects**: APAFA Restore Magicka records and non-100 skill scaling.
  - **Steps**:
    1. Press **F** while the Alchemy Lab UI is focused.
    2. Craft:
       - `Blister Pod Cap + Bog Beacon`
    3. **Optional Next Step**: For Phase 9A, exit Skyrim and run `python pat-default-apafa.py`.

1. Exit Skyrim. Run `python pat-apafa.py`, then `python reset_saves_and_start_skyrim.py`.
2. In the Alchemy Lab, run `pat apafa`, then `pat apafa 2` through `pat apafa 10` in order without exiting Skyrim. Craft the one recipe listed for each block.
3. Optional: exit Skyrim and run `python pat-default-apafa.py` to begin Phase 9A.

---

### Phase 8: Confirmed-Potion Prediction Export Verification (All Modes)

This phase verifies the C++ plugin's predictions against every row of `alchemist.potions-confirmed.csv`. For each confirmed row the plugin rebuilds the craft from the row's own recorded ingredients, player state, and `mod_settings`, predicts the potion, and writes the result to `alchemist.potions-predicted.<mode>.csv` next to `alchemist.dll`. `python potion_prediction_test.py --check-confirmed-csv` then reports, for each row, the in-game value, the Python prediction, and the C++ prediction. Because every row supplies its own settings, no `pat` command and no in-game setting changes are needed. Only the enabled-mod combination must match the mode being exported, and each export covers only the confirmed rows of the active mode.

Re-run this phase after every rebuild of `alchemist.dll` and after adding new confirmed rows. The `alchemist.potions-predicted.<mode>.csv` files are generated by the plugin; do not edit, blank, or rewrite them.

1. **Vanilla Mode (Confirmed Rows)**:
   - **Disk**: CACO, AP, Requiem and Apothecary disabled. Alchemy Plus settings and in-game player state do not matter because each row supplies its own.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-vanilla.py` on disk.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In the Developer Test Hub (requires `developer=1`), press **Export confirmed-potion predictions to CSV** (not "Export potion predictions to CSV") and wait for the completion message. This writes `alchemist.potions-predicted.vanilla.csv`.
      4. **Next Command**: Exit Skyrim and run `python pat-default-ap.py` on disk.

2. **Alchemy Plus (AP) Mode (Confirmed Rows)**:
   - **Disk**: AP enabled; CACO, Requiem and Apothecary disabled. Alchemy Plus settings and in-game player state do not matter because each row supplies its own.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-ap.py` on disk.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In the Developer Test Hub (requires `developer=1`), press **Export confirmed-potion predictions to CSV** (not "Export potion predictions to CSV") and wait for the completion message. This writes `alchemist.potions-predicted.ap.csv`.
      4. **Next Command**: Exit Skyrim and run `python pat-default-caco.py` on disk.

3. **CACO Mode (Confirmed Rows)**:
   - **Disk**: CACO enabled; AP, Requiem and Apothecary disabled. Alchemy Plus settings and in-game player state do not matter because each row supplies its own.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-caco.py` on disk.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In the Developer Test Hub (requires `developer=1`), press **Export confirmed-potion predictions to CSV** (not "Export potion predictions to CSV") and wait for the completion message. This writes `alchemist.potions-predicted.caco.csv`.
      4. **Next Command**: Exit Skyrim and run `python pat-default-caco-ap.py` on disk.

4. **CACO + AP Mode (Confirmed Rows)**:
   - **Disk**: CACO and AP enabled; Requiem and Apothecary disabled. Alchemy Plus settings and in-game player state do not matter because each row supplies its own.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-caco-ap.py` on disk.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In the Developer Test Hub (requires `developer=1`), press **Export confirmed-potion predictions to CSV** (not "Export potion predictions to CSV") and wait for the completion message. This writes `alchemist.potions-predicted.caco+ap.csv`.
      4. **Next Command**: Exit Skyrim and run `python pat-default-requiem.py` on disk.

5. **Requiem Mode (Confirmed Rows)**:
   - **Disk**: Requiem enabled; CACO, AP and Apothecary disabled. Alchemy Plus settings and in-game player state do not matter because each row supplies its own.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-requiem.py` on disk.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In the Developer Test Hub (requires `developer=1`), press **Export confirmed-potion predictions to CSV** (not "Export potion predictions to CSV") and wait for the completion message. This writes `alchemist.potions-predicted.requiem.csv`.
      4. **Next Command**: Exit Skyrim and run `python pat-default-apothecary.py` on disk.

6. **Apothecary Mode (Confirmed Rows)**:
   - **Disk**: Apothecary enabled; CACO, AP and Requiem disabled. Alchemy Plus settings and in-game player state do not matter because each row supplies its own.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-apothecary.py` on disk.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In the Developer Test Hub (requires `developer=1`), press **Export confirmed-potion predictions to CSV** (not "Export potion predictions to CSV") and wait for the completion message. This writes `alchemist.potions-predicted.apothecary.csv`.
      4. **Next Command**: Exit Skyrim and run `python pat-default-apafa.py` on disk.

7. **APAFA Mode (Confirmed Rows)**:
   - **Disk**: APAFA enabled; CACO, AP, Requiem, and Apothecary disabled. APAFA's MCM values are captured per row; defaults are InitMult 4.0 and SkillFactor 1.5.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-apafa.py` on disk.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In the Developer Test Hub (requires `developer=1`), press **Export confirmed-potion predictions to CSV** and wait for completion. This writes `alchemist.potions-predicted.apafa.csv`.
      4. **Next Command**: Run `python potion_prediction_test.py --check-confirmed-csv --check-baseline` on disk.

8. **Verify**:
   - **Steps**:
      1. Run `python potion_prediction_test.py --check-confirmed-csv --check-baseline`.
      2. Confirm the Python harness passes every row, the baseline reports zero regressions, and the C++ plugin line reports no failing rows (`cpp_divergences=0`). Rows whose C++ value is `N/A` had no matching prediction in the export and must be explained, not ignored.
      3. **Next Command**: Optionally run Phase 9 prediction exports; otherwise the required test suite is complete.

---

### Phase 9 (Optional): Full Potion Prediction Export Verification (Default & Changed Settings)

This optional phase verifies the full in-game potion value prediction exports (`alchemist.potion-predictions.csv.zst` and the per-mode `potions-predicted-*.csv.zst` fixtures) generated by the SKSE plugin across all supported modes (`Vanilla`, `AP`, `CACO`, `CACO+AP`, `Requiem`, `Apothecary`, `APAFA`) under both **Default Settings** and **Changed (Non-Default) Settings**. It is supplementary: the required suite and confirmed-craft validation are complete after Phase 8. Skip this entire phase if full prediction-export fixtures are not needed. When run, use separate, dedicated pre-launch scripts (`pat-default-<mode>.py` and `pat-<mode>-changed.py`), distinct from the observed craft testing scripts.

#### Sub-Phase 9A (Optional): Default Settings Prediction Exports

1. **Vanilla Mode (Default Settings)**:
   - **Default Settings**: Disk: CACO disabled, AP disabled. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-vanilla.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default vanilla`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-vanilla.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-ap.py` on disk.

2. **Alchemy Plus (AP) Mode (Default Settings)**:
   - **Default Settings**: Disk: CACO disabled, AP enabled (`magnitudeThreshold=25.0`, `magnitudeMult=5.0`, `durationThreshold=15.0`, `durationMult=5.0`, `impureCostFix=True`). In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-ap.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default ap`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-ap.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-caco.py` on disk.

3. **CACO Mode (Default Settings)**:
   - **Default Settings**: Disk: CACO enabled, AP disabled. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.9`, `SkillFactor=1.0`, CACO 0s Durations (all index 0), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-caco.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default caco`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-caco.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-caco-ap.py` on disk.

4. **CACO + AP Mode (Default Settings)**:
   - **Default Settings**: Disk: CACO enabled, AP enabled (`magnitudeThreshold=25.0`, `magnitudeMult=5.0`, `durationThreshold=15.0`, `durationMult=5.0`, `impureCostFix=True`). In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.9`, `SkillFactor=1.0`, CACO 0s Durations (all index 0), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-caco-ap.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default caco-ap`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-caco-ap.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-requiem.py` on disk.

5. **Requiem Mode (Default Settings)**:
   - **Default Settings**: Disk: Requiem enabled, CACO disabled, AP disabled. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore 1, `InitMult=4.0`, `SkillFactor=1.1`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-requiem.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default requiem`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-requiem.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-apothecary.py` on disk.

6. **Apothecary Mode (Default Settings)**:
   - **Default Settings**: Disk: Apothecary enabled, CACO disabled, AP disabled. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-apothecary.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default apothecary`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-apothecary.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-apafa.py` on disk.

7. **APAFA Mode (Default Settings)**:
   - **Default Settings**: Disk: APAFA enabled; CACO, AP, Requiem, and Apothecary disabled; APAFA has no disk JSON. In-Game: Player Alchemy 100, Fortify 0, no perks, APAFA MCM InitMult 4.0 and SkillFactor 1.5; CACO duration indices inactive.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-apafa.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default apafa`.
      4. In the Developer Test Hub, press **Export potion predictions to CSV** and wait for completion.
      5. Run `python sync_potion_predictions.py` -> syncs to `potions-predicted-apafa.csv.zst`.
      6. **Next Command**: Run `python potion_prediction_test.py --check-confirmed-csv` on disk.

8. **Verify & Archive Default Predictions**:
   - **Steps**:
      1. Run `python potion_prediction_test.py --check-confirmed-csv`.
      2. Run `python save_predicted_default_settings.py` on disk to archive default setting CSV fixtures to:
          - `potions-predicted-vanilla.default.settings.csv.zst`
          - `potions-predicted-ap.default.settings.csv.zst`
          - `potions-predicted-caco.default.settings.csv.zst`
          - `potions-predicted-caco-ap.default.settings.csv.zst`
          - `potions-predicted-requiem.default.settings.csv.zst`
          - `potions-predicted-apothecary.default.settings.csv.zst`
          - `potions-predicted-apafa.default.settings.csv.zst`
      3. **Next Command**: Exit Skyrim and run `python pat-vanilla-changed.py` on disk.

---

#### Sub-Phase 9B (Optional): Changed Settings Prediction Exports

1. **Vanilla Mode (Changed Settings)**:
   - **Modified Settings**: Disk: CACO disabled, AP disabled. In-Game: Player Alchemy 65, Fortify 50 (Peerless gear), Alchemist 3, Physician, Benefactor, Poisoner, Seeker of Shadows, `InitMult=4.5`, `SkillFactor=1.8`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-vanilla-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat vanilla changed`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-vanilla.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-ap-changed.py` on disk.

2. **Alchemy Plus (AP) Mode (Changed Settings)**:
   - **Modified Settings**: Disk: CACO disabled, AP enabled (`magnitudeThreshold=10.0`, `magnitudeMult=2.0`, `durationThreshold=10.0`, `durationMult=2.0`, `impureCostFix=False`, override for `0x0003EB15`: `magnitudeThreshold=50.0`, `magnitudeMult=2.0`). In-Game: Player Alchemy 75, Fortify 50 (Peerless gear), Alchemist 4, Physician, Benefactor, `InitMult=4.2`, `SkillFactor=1.6`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-ap-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat ap changed`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-ap.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-caco-changed.py` on disk.

3. **CACO Mode (Changed Settings)**:
   - **Modified Settings**: Disk: CACO enabled, AP disabled. In-Game: Player Alchemy 55, Fortify 50 (Peerless gear), Alchemist 2, Physician, Poisoner, `InitMult=3.2`, `SkillFactor=2.8`, CACO 10s Durations (all index 2), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-caco-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat caco changed`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-caco.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-caco-ap-changed.py` on disk.

4. **CACO + AP Mode (Changed Settings)**:
   - **Modified Settings**: Disk: CACO enabled, AP enabled (`magnitudeThreshold=30.0`, `magnitudeMult=6.0`, `durationThreshold=20.0`, `durationMult=6.0`, `impureCostFix=True`). In-Game: Player Alchemy 85, Fortify 50 (Peerless gear), Alchemist 4, Physician, Benefactor, Poisoner, `InitMult=3.5`, `SkillFactor=2.5`, CACO Mixed Durations (RestoreHealth 5s, RestoreMagicka 10s, RestoreStamina 0s, DamageHealth 10s, DamageMagicka 5s, DamageStamina 0s), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-caco-ap-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat caco-ap changed`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-caco-ap.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-requiem-changed.py` on disk.

5. **Requiem Mode (Changed Settings)**:
   - **Modified Settings**: Disk: Requiem enabled, CACO disabled, AP disabled. In-Game: Player Alchemy 75, Fortify 0, Alchemical Lore 1 + 2 (effective tier 2), Improved Elixirs, Improved Poisons, `InitMult=4.0`, `SkillFactor=1.1`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-requiem-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat requiem changed`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-requiem.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-apothecary-changed.py` on disk.

6. **Apothecary Mode (Changed Settings)**:
   - **Modified Settings**: Disk: Apothecary enabled, CACO disabled, AP disabled. In-Game: Player Alchemy 65, Fortify 50 (Peerless gear), Alchemist 3, `InitMult=4.5`, `SkillFactor=1.8`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-apothecary-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat apothecary changed`.
      4. In the Developer Test Hub (requires `developer=1`), press **Export potion predictions to CSV** (not "Export confirmed-potion predictions to CSV") and wait for the completion message.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-apothecary.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-apafa-changed.py` on disk.

7. **APAFA Mode (Changed Settings)**:
   - **Modified Settings**: Disk: APAFA enabled; CACO, AP, Requiem, and Apothecary disabled; APAFA has no disk JSON. In-Game: Player Alchemy 75, Fortify 0, Alchemist rank 3, no type perks, APAFA MCM InitMult 5.0 and SkillFactor 2.0; CACO duration indices inactive.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-apafa-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat apafa changed`.
      4. In the Developer Test Hub, press **Export potion predictions to CSV** and wait for completion.
      5. Run `python sync_potion_predictions.py` -> syncs to `potions-predicted-apafa.csv.zst`.
      6. **Next Command**: Run `python potion_prediction_test.py --check-confirmed-csv` on disk.

8. **Verify & Archive Changed Predictions**:
   - **Steps**:
      1. Run `python potion_prediction_test.py --check-confirmed-csv`.
      2. Run `python save_predicted_changed_settings.py` on disk to archive changed setting CSV fixtures to:
          - `potions-predicted-vanilla.changed.settings.csv.zst`
          - `potions-predicted-ap.changed.settings.csv.zst`
          - `potions-predicted-caco.changed.settings.csv.zst`
          - `potions-predicted-caco-ap.changed.settings.csv.zst`
          - `potions-predicted-requiem.changed.settings.csv.zst`
          - `potions-predicted-apothecary.changed.settings.csv.zst`
          - `potions-predicted-apafa.changed.settings.csv.zst`
      3. **Next Step**: Suite Complete! Run `python verify_test_suite_alignment.py` to confirm 100% test suite alignment.

---

#### Sub-Phase 9C (Optional): Toggling Active Prediction Baseline Fixtures

To switch active baseline files (`potions-predicted-*.csv.zst`) between archived **Default Settings** and **Changed Settings** fixtures without re-exporting:
- **Toggle Automatically**: Run `python toggle-predicted-settings.py` on disk. Automatically detects current active state (`default` vs `changed`) and switches to the opposite set.
- **Set to Default Settings**: Run `python toggle-predicted-settings.py default`.
- **Set to Changed Settings**: Run `python toggle-predicted-settings.py changed`.

---

## Post-Test AI Verification Procedure

Once the user completes the in-game test suite execution, the AI agent must perform the following automated and manual verification procedure:

360. **Automated Prediction Harness Scoring**:
   - Execute the confirmed CSV validator command:
     ```powershell
     python potion_prediction_test.py --check-confirmed-csv
     python potion_prediction_test.py --diagnose
     ```
   - Verify that all newly logged potion crafts pass without error.
   - **Reading the DIAGNOSTIC STATUS SUMMARY Box**:
     Every run of `potion_prediction_test.py --check-confirmed-csv` or `--diagnose` displays an explicit, un-missable status box:
     ```text
     ================================================================================
     DIAGNOSTIC STATUS SUMMARY:
       PYTHON HARNESS MODEL : [PASS] (308/308 rows pass; 0 failing rows against in-game crafts)
       C++ PLUGIN (DLL)     : [NEEDS FIX] (218/307 setting-matched rows pass; 89 failing rows)
       MODEL PARITY (PY-CPP): [DIVERGENT] (229/307 setting-matched rows match; 78 divergences)
     --------------------------------------------------------------------------------
     ACTION REQUIRED:
       * C++ PLUGIN REQUIRES FIXING: C++ plugin predictions in alchemist.dll have 89 failing row(s) against empirical in-game crafts (78 model divergences).
     ================================================================================
     ```
     - **`PYTHON HARNESS MODEL`**: `[PASS]` means Python prediction logic matches empirical crafts; `[NEEDS FIX]` means Python code must be updated.
     - **`C++ PLUGIN (DLL)`**: `[PASS]` means `alchemist.dll` plugin predictions match empirical crafts; `[NEEDS FIX]` means C++ header/source files must be updated.
     - **`MODEL PARITY (PY-CPP)`**: `[MATCH]` means Python and C++ prediction engines are identical; `[DIVERGENT]` means C++ plugin predictions differ from Python.
     - **`ACTION REQUIRED`**: States exactly what component requires code modification.
   - The confirmed CSV checker compares each captured row directly with the analytical Python prediction (`PotionPredictor`).
   - **Dual-Direction Engine Rounding Boundary Verification**:
     - If a row reports `PASS (Known Engine Rounding Boundary)` (such as row 62 *Berit's Ashes + Bone Meal*: expected 422, predicted 430), Skyrim's native engine intermediate integer magnitude truncation (`uint32_t` floor vs `std::round`) accounts for the gold value difference.
     - To inspect the exact mathematical effect-by-effect breakdown for a rounding boundary match, run `python potion_prediction_test.py --check-confirmed-row <row_num>` (e.g. row 62). The harness will print the **Engine Rounding Boundary Math Breakdown** showing truncated component magnitudes, individual effect costs, and final sum evaluations.
     - Rows passing via `Known Engine Rounding Boundary` return Exit Code `0` and are treated as verified passes. AI agents MUST NOT modify prediction algorithm parameters, introduce hardcoded exceptions, or alter player settings to force these rows to display standard `PASS`.
   - **No Test Harness Bypasses, Native Replays, or Fixture Fallbacks**: Agents MUST NEVER edit `potion_prediction_test.py` or any test harness script to add native-effect replays, CSV `crafted_effects` fallbacks, or fixture-matching workarounds (such as `replay_confirmed_vanilla_effects` or replaying captured CSV effect magnitudes/durations) to substitute for actual `PotionPredictor` evaluation. The test harness must strictly test the analytical prediction model (`PotionPredictor`) directly against empirical observations. Overriding, intercepting, or bypassing prediction evaluation when predictions mismatch observed crafts is strictly prohibited.
361. **Row-by-Row Confirmation Audit**:
   - Open `alchemist.potions-confirmed.csv` in `SKSE\Plugins\`.
   - Perform an explicit row-by-row comparison against the requested test plan, confirming:
     - All 70 requested observed-craft setting blocks across all 7 modes are present (10 AP, 10 Vanilla, 10 CACO, 10 CACO+AP, 10 Requiem, 10 Apothecary, 10 APAFA blocks).
     - Mode flags (`caco_enabled`, `alchemy_plus_enabled`, Requiem mode, Apothecary mode, APAFA mode) match the block specification.
     - In-game parameters (`player_alchemy_level`, `player_fortify_alchemy`, `player_perks`, `game_settings`, `mod_settings`) match the block specification.
     - Each requested ingredient recipe and click selection order is recorded exactly as requested.

---

## Full Test Suite Plan & Specification (AI Reference & Reset)

This section contains the comprehensive technical breakdown of all test phases, setting configurations, ingredient recipes, click order matrices, and script reset procedures.

### Technical Matrix & Setting Specification

| Phase | Mode Tag | Pre-Launch Script | In-Game Command | Disk AP Settings | GameSettings | CACO Durations | Player Perks / State | Target Recipes |
|---|---|---|---|---|---|---|---|---|
| **AP-1** | `AP-1` | `pat-ap.py` | `pat ap` | mag 10/2, dur 10/2, impureFix=False, overrides (0x3EB15, 0x3EB3D) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Blisterwort+Wheat (RestH mag override 0x3EB15); Bear Claws+Bee (RestS dur override 0x3EB3D); Luna Moth Wing+Vampire Dust |
| **AP-2** | `AP-2` | `pat-ap.py` | `pat ap 2` | Same as AP-1 disk setup | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 3 | Briar Heart+Canis Root; Blue Butterfly Wing+Blue Mountain Flower; Glowing Mushroom+Nightshade |
| **AP-3** | `AP-3` | `pat-ap.py` | `pat ap 3` | Same as AP-1 disk setup | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 5, Physician, Benefactor | Blisterwort+Wheat (Physician+Benefactor); Giant's Toe+Wheat (Benefactor); Salt Pile+Garlic (Benefactor) |
| **AP-4** | `AP-4` | `pat-ap-2.py` | `pat ap 4` | mag 25/5, dur 15/5, impureFix=True, override 0x3EB15 | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Deathbell+River Betty (impureCostFix=True); Salt Pile+Garlic; Chaurus Eggs+Luna Moth Wing |
| **AP-5** | `AP-5` | `pat-ap-2.py` | `pat ap 5` | Same as AP-4 disk setup | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Poisoner | Canis Root+Imp Stool (Poisoner); Glowing Mushroom+Nightshade (Poisoner); Deathbell+River Betty (Poisoner) |
| **AP-6** | `AP-6` | `pat-ap-2.py` | `pat ap 6` | Same as AP-4 disk setup | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Purity | Blue Mountain Flower+Wheat (Purity AP strip); Blisterwort+Wheat (Purity AP strip); Briar Heart+Canis Root |
| **AP-7** | `AP-7` | `pat-ap-2.py` | `pat ap 7` | Same as AP-4 disk setup | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 5, Physician, Benefactor, Poisoner, Purity | Creep Cluster+Scaly Pholiota+Mora Tapinella; Abecean Longfin+Cyrodilic Spadetail+Salt Pile; Giant's Toe+Wheat |
| **AP-8** | `AP-8` | `pat-ap-3.py` | `pat ap 8` | mag 30/6, dur 20/6, impureFix=True | InitMult 5.0, SkillFactor 2.0 | N/A | Skill 100, Fortify 0, Perks: None | Briar Heart+Canis Root; Dragon's Tongue+Fly Amanita; Blue Butterfly Wing+Blue Mountain Flower |
| **AP-9** | `AP-9` | `pat-ap-3.py` | `pat ap 9` | Same as AP-8 disk setup | InitMult 4.5, SkillFactor 1.8 | N/A | Skill 100, Fortify 50 (Peerless gear), Perks: Alchemist 4, Physician, Benefactor | Blisterwort+Wheat; Salt Pile+Garlic; Giant's Toe+Wheat |
| **AP-10** | `AP-10` | `pat-ap-3.py` | `pat ap 10` | Same as AP-8 disk setup | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 50 (Level < 100), Fortify 50 (Peerless gear), Perks: Alchemist 2, Physician | Bear Claws+Bee; Luna Moth Wing+Vampire Dust; Berit's Ashes+Bone Meal |
| **AP-11** | `AP-11` | `pat-ap-4.py` | `pat ap 11` | mag 25/5, dur 15/5, roundedPotency.enabled=false | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Briar Heart+Canis Root (unrounded AP); Blisterwort+Wheat (unrounded AP) |
| **AP-12** | `AP-12` | `pat-ap-4.py` | `pat ap 12` | Same as AP-11 disk setup | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Blisterwort+Ambrosia; Abecean Longfin+Bleeding Crown; Luna Moth Wing+Ash Creep Cluster |
| **AP-13** | `AP-13` | `pat-ap-4.py` | `pat ap 13` | Same as AP-11 disk setup | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 75, Fortify 0, Perks: None | Blisterwort+Ambrosia; Abecean Longfin+Bleeding Crown; Luna Moth Wing+Ash Creep Cluster |
| **Vanilla-1** | `Vanilla-1` | `pat-vanilla.py` | `pat vanilla` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Blisterwort+Wheat (RestH); Deathbell+River Betty (DmgH); Salt Pile+Garlic (RegenM); Blue Mountain Flower+Blue Butterfly Wing |
| **Vanilla-2** | `Vanilla-2` | `pat-vanilla.py` | `pat vanilla 2` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 1 (+20%) | Briar Heart+Canis Root; Bear Claws+Bee; Glowing Mushroom+Nightshade |
| **Vanilla-3** | `Vanilla-3` | `pat-vanilla.py` | `pat vanilla 3` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 3 (+60%) | Creep Cluster+Scaly Pholiota+Mora Tapinella; Giant's Toe+Wheat; Dragon's Tongue+Fly Amanita |
| **Vanilla-4** | `Vanilla-4` | `pat-vanilla.py` | `pat vanilla 4` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 5 (+100%) | Blisterwort+Wheat; Deathbell+River Betty; Salt Pile+Garlic |
| **Vanilla-5** | `Vanilla-5` | `pat-vanilla.py` | `pat vanilla 5` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 1, Physician (+25% Rest H/M/S) | Blisterwort+Wheat (RestH); Briar Heart+Ectoplasm (RestM); Bear Claws+Bee (RestS) |
| **Vanilla-6** | `Vanilla-6` | `pat-vanilla.py` | `pat vanilla 6` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 1, Physician, Benefactor (+25% Beneficial) | Blue Mountain Flower+Blue Butterfly Wing (Beneficial); Dragon's Tongue+Fly Amanita (Beneficial); Salt Pile+Garlic (Beneficial) |
| **Vanilla-7** | `Vanilla-7` | `pat-vanilla.py` | `pat vanilla 7` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 1, Poisoner (+25% Poisons) | Deathbell+River Betty (Poisoner); Canis Root+Imp Stool (Poisoner); Glowing Mushroom+Nightshade (Poisoner) |
| **Vanilla-8** | `Vanilla-8` | `pat-vanilla.py` | `pat vanilla 8` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 5, Physician, Benefactor, Poisoner, Purity | Blue Mountain Flower+Wheat (Purity strips DmgM); Blisterwort+Wheat (Purity strips DmgS); Briar Heart+Canis Root (Purity strips Paralyze) |
| **Vanilla-9** | `Vanilla-9` | `pat-vanilla.py` | `pat vanilla 9` | N/A (AP Disabled) | InitMult 5.0, SkillFactor 2.0 | N/A | Skill 100, Fortify 50 (Peerless gear), Perks: Alchemist 5, Physician, Benefactor, Poisoner, Purity, Seeker of Shadows (+10%) | Giant's Toe+Wheat; Blue Mountain Flower+Blue Butterfly Wing; Salt Pile+Garlic |
| **Vanilla-10** | `Vanilla-10` | `pat-vanilla.py` | `pat vanilla 10` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 50 (Level < 100), Fortify 50 (Peerless gear), Perks: Alchemist 2, Physician | Bear Claws+Bee; Luna Moth Wing+Vampire Dust; Berit's Ashes+Bone Meal |
| **Vanilla-11** | `Vanilla-11` | `pat-vanilla.py` | `pat vanilla 11` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Benefactor isolate | Blue Mountain Flower+Blue Butterfly Wing (Benefactor isolate) |
| **Vanilla-12** | `Vanilla-12` | `pat-vanilla.py` | `pat vanilla 12` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Physician non-restore check | Blue Mountain Flower+Blue Butterfly Wing (Physician 0% check) |
| **Vanilla-13** | `Vanilla-13` | `pat-vanilla.py` | `pat vanilla 13` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Poisoner non-poison check | Blisterwort+Wheat (Poisoner 0% check) |
| **Vanilla-14** | `Vanilla-14` | `pat-vanilla.py` | `pat vanilla 14` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Seeker of Shadows isolate | Blisterwort+Wheat (Seeker isolate) |
| **Vanilla-15** | `Vanilla-15` | `pat-vanilla.py` | `pat vanilla 15` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist Rank 4 (+80%) | Blisterwort+Wheat (Alchemist 4 isolate) |
| **Vanilla-16** | `Vanilla-16` | `pat-vanilla.py` | `pat vanilla 16` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Alchemist 5, Physician, Benefactor, Poisoner, Purity, Seeker of Shadows | Abecean Longfin+Salt Pile+Cyrodilic Spadetail |
| **Vanilla-17** | `Vanilla-17` | `pat-vanilla.py` | `pat vanilla 17` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 15 (Level 15 baseline), Fortify 0, Perks: None | Blisterwort+Wheat (Level 15 baseline) |
| **Vanilla-18** | `Vanilla-18` | `pat-vanilla.py` | `pat vanilla 18` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 40 (Level 40), Fortify 0, Perks: Alchemist 1 (+20%) | Dragon's Tongue+Elves Ear+Fly Amanita (Row 62 intermediate bracket) |
| **CACO-1** | `CACO-1` | `pat-caco.py` | `pat caco` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Boar Tusk+Briar Heart (FortH 5s); Creep Cluster+Giant's Toe (DmgS 5s); Blisterwort+Wheat (RestH 5s); Canis Root+Spider Egg (DmgS 5s) |
| **CACO-2** | `CACO-2` | `pat-caco.py` | `pat caco 2` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 10s (Index 2), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Blisterwort+Wheat Extract (RestH 10s CACO Extract); Deathbell+River Betty (DmgH 10s); Ancestor Moth+Blue Mountain Flower (FortConj 10s); Briar Heart+Ectoplasm (RestM 10s) |
| **CACO-3** | `CACO-3` | `pat-caco.py` | `pat caco 3` | N/A (AP Disabled) | InitMult 5.0, SkillFactor 2.0 | All 0s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Click Order Permutation Matrix: Roobrush, Slaughterfish Egg, Large Antlers (Orders 1, 2, 3, 4) |
| **CACO-4** | `CACO-4` | `pat-caco.py` | `pat caco 4` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 0s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Click Order Permutation Matrix: Roobrush, Slaughterfish Egg, Large Antlers (Orders 5, 6); Aloe Vera+Daedra Heart (RestH CACO Aloe Vera) |
| **CACO-5** | `CACO-5` | `pat-caco.py` | `pat caco 5` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Alchemist 2 | Boar Tusk+Briar Heart; Canis Root+Spider Egg; Blisterwort+Wheat |
| **CACO-6** | `CACO-6` | `pat-caco.py` | `pat caco 6` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | Mixed: RestH 5s, RestM 10s, DmgH 0s, DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Physician | Blisterwort+Wheat Extract (RestH 5s Physician); Briar Heart+Ectoplasm (RestM 10s Physician); Chaurus Eggs+Vampire Dust (DmgH 0s) |
| **CACO-7** | `CACO-7` | `pat-caco.py` | `pat caco 7` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 10s (Index 2), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Poisoner | Deathbell+River Betty (DmgH 10s Poisoner); Canis Root+Spider Egg (DmgS 10s Poisoner); Swamp Fungal Pod+Wheat Extract (DmgM 10s Poisoner) |
| **CACO-8** | `CACO-8` | `pat-caco.py` | `pat caco 8` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Benefactor | Dragon's Tongue+Fly Amanita (Benefactor); Ancestor Moth+Blue Mountain Flower (Benefactor); Salt Pile+Garlic (Benefactor) |
| **CACO-9** | `CACO-9` | `pat-caco.py` | `pat caco 9` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | Mixed: RestH 5s, RestM 10s, DmgH 0s, DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 50 (Peerless gear), Perks: Alchemist 5, Physician, Benefactor, Poisoner, Purity | Red Mountain Flower+Wheat (Purity CACO strip); Boar Tusk+Briar Heart; Deathbell+River Betty |
| **CACO-10** | `CACO-10` | `pat-caco.py` | `pat caco 10` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 50 (Level < 100), Fortify 50 (Peerless gear), Perks: Alchemist 3, Physician | Blisterwort+Wheat Extract; Mudcrab Chitin+Vampire Dust; Dragon's Tongue+Fly Amanita |
| **CACO-11** | `CACO-11` | `pat-caco.py` | `pat caco 11` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | RestH 5s (Index 1) MCM slider | Skill 100, Fortify 0, Perks: None | Blisterwort+Wheat Extract (RestH 5s MCM slider) |
| **CACO-12** | `CACO-12` | `pat-caco.py` | `pat caco 12` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | RestH 10s (Index 2) MCM slider | Skill 100, Fortify 0, Perks: None | Blisterwort+Wheat Extract (RestH 10s MCM slider) |
| **CACO-13** | `CACO-13` | `pat-caco.py` | `pat caco 13` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | DmgH 10s, RestM 10s, RestS 10s MCM sliders | Skill 100, Fortify 0, Perks: None | Deathbell+River Betty; Briar Heart+Ectoplasm; Bear Claws+Bee |
| **CACO-14** | `CACO-14` | `pat-caco.py` | `pat caco 14` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | RestH 10s (Index 2) | Skill 100, Fortify 0, Perks: None | Blisterwort+Wheat Extract (54g base cost duration isolate) |
| **CACO-15** | `CACO-15` | `pat-caco.py` | `pat caco 15` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Garlic+Mudcrab Chitin (Resist Disease aliasing) |
| **CACO-16** | `CACO-16` | `pat-caco.py` | `pat caco 16` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 10s (Index 2), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Monarch Butterfly+Nightshade (Damage Undead base cost 8.3); Creep Cluster+Giant Lichen+Rock Warbler Egg |
| **CACO-17** | `CACO-17` | `pat-caco.py` | `pat caco 17` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Seeker of Shadows active | Blisterwort+Wheat Extract (Verify zero CACO Seeker rows) |
| **CACO-18** | `CACO-18` | `pat-caco.py` | `pat caco 18` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Green Thumb | Aloe Vera+Ambrosia (non-potency perk check) |
| **CACO-19** | `CACO-19` | `pat-caco.py` | `pat caco 19` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | RestS 5s (Index 1), DmgH 5s (Index 1), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Alkanet Flower+Barley; Aloe Vera+Bear Claws; Blue Mountain Flower+Cecropia Moth |
| **CACO-20** | `CACO-20` | `pat-caco.py` | `pat caco 20` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | RestM 5s (Index 1), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Alkanet Flower+Barley |
| **CACO-21** | `CACO-21` | `pat-caco.py` | `pat caco 21` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Chaurus Eggs+Clouded Funnel Cap |
| **CACO-22** | `CACO-22` | `pat-caco.py` | `pat caco 22` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | DmgM 5s (Index 1), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Chaurus Eggs+Clouded Funnel Cap |
| **CACO-23** | `CACO-23` | `pat-caco.py` | `pat caco 23` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | DmgM 10s (Index 2), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Chaurus Eggs+Clouded Funnel Cap |
| **CACO-24** | `CACO-24` | `pat-caco.py` | `pat caco 24` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 75, Fortify 0, Perks: None | Aloe Vera+Ambrosia; Aloe Vera+Banded Pennant |
| **CACO-25** | `CACO-25` | `pat-caco.py` | `pat caco 25` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | RestH 5s (Index 1), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Aloe Vera+Ambrosia |
| **CACO-26** | `CACO-26` | `pat-caco.py` | `pat caco 26` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | RestS 10s (Index 2), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Aloe Vera+Bear Claws |
| **CACO-27** | `CACO-27` | `pat-caco.py` | `pat caco 27` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | DmgH 10s (Index 2), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Blue Mountain Flower+Cecropia Moth |
| **CACO-AP-1**| `CACO-AP-1`| `pat-caco-ap.py` | `pat caco-ap` | mag 25/5, dur 15/5, impureFix=True | InitMult 3.0, SkillFactor 3.0 | All 0s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Blisterwort+Wheat Extract; Deathbell+River Betty; Ash Creep Cluster+Comberry; Aloe Vera+Daedra Heart+Large Antlers |
| **CACO-AP-2**| `CACO-AP-2`| `pat-caco-ap.py` | `pat caco-ap 2` | Same as CACO-AP-1 disk setup | InitMult 4.0, SkillFactor 1.5 | All 0s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Alchemist 4 | Blue Mountain Flower+Bog Beacon+Jarrin Root; Ash Creep Cluster+Crimson Nirnroot; Canis Root+Spider Egg; Dragon's Tongue+Fly Amanita |
| **CACO-AP-3**| `CACO-AP-3`| `pat-caco-ap.py` | `pat caco-ap 3` | Same as CACO-AP-1 disk setup | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Physician | Blisterwort+Wheat Extract (RestH 5s Physician); Boar Tusk+Briar Heart (FortH 5s Physician); Briar Heart+Ectoplasm (RestM 5s Physician) |
| **CACO-AP-4**| `CACO-AP-4`| `pat-caco-ap-2.py`| `pat caco-ap 4` | mag 10/2, dur 10/2, impureFix=True | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Boar Tusk+Briar Heart; Creep Cluster+Giant's Toe; Blue Mountain Flower+Bog Beacon+Jarrin Root; Ash Creep Cluster+Crimson Nirnroot |
| **CACO-AP-5**| `CACO-AP-5`| `pat-caco-ap-2.py`| `pat caco-ap 5` | Same as CACO-AP-4 disk setup | InitMult 3.0, SkillFactor 3.0 | All 10s (Index 2), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Poisoner | Deathbell+River Betty (DmgH 10s Poisoner); Canis Root+Spider Egg (DmgS 10s Poisoner); Swamp Fungal Pod+Wheat Extract (DmgM 10s Poisoner) |
| **CACO-AP-6**| `CACO-AP-6`| `pat-caco-ap-2.py`| `pat caco-ap 6` | Same as CACO-AP-4 disk setup | InitMult 3.0, SkillFactor 3.0 | All 10s (Index 2), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Benefactor | Ash Creep Cluster+Comberry (FortDest 10s Benefactor); Dragon's Tongue+Fly Amanita (Benefactor); Salt Pile+Garlic (Benefactor) |
| **CACO-AP-7**| `CACO-AP-7`| `pat-caco-ap-2.py`| `pat caco-ap 7` | Same as CACO-AP-4 disk setup | InitMult 3.0, SkillFactor 3.0 | Mixed: RestH 5s, RestM 10s, DmgH 0s, DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Purity | Red Mountain Flower+Wheat (Purity CACO+AP strip); Blisterwort+Wheat Extract; Boar Tusk+Briar Heart |
| **CACO-AP-8**| `CACO-AP-8`| `pat-caco-ap-3.py`| `pat caco-ap 8` | mag 30/6, dur 20/6, impureFix=True | InitMult 5.0, SkillFactor 2.0 | All 10s (Index 2), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Aloe Vera+Daedra Heart; Creep Cluster+Scaly Pholiota; Ancestor Moth+Blue Mountain Flower |
| **CACO-AP-9**| `CACO-AP-9`| `pat-caco-ap-3.py`| `pat caco-ap 9` | Same as CACO-AP-8 disk setup | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 50 (Peerless gear), Perks: Alchemist 5, Physician, Benefactor, Poisoner | Blisterwort+Wheat Extract; Deathbell+River Betty; Ash Creep Cluster+Comberry |
| **CACO-AP-10**| `CACO-AP-10`| `pat-caco-ap-3.py`| `pat caco-ap 10` | Same as CACO-AP-8 disk setup | InitMult 3.0, SkillFactor 3.0 | All 10s (Index 2), DisableHandling=1, ImpureProc=0 | Skill 50 (Level < 100), Fortify 50 (Peerless gear), Perks: Alchemist 2, Physician, Benefactor | Blisterwort+Wheat Extract; Ash Creep Cluster+Comberry; Mudcrab Chitin+Vampire Dust |
| **CACO-AP-11**| `CACO-AP-11`| `pat-caco-ap-4.py`| `pat caco-ap 11` | mag 25/5, dur 15/5, roundedPotency.enabled=false | InitMult 3.0, SkillFactor 3.0 | All 0s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Green Thumb | Aloe Vera+Ambrosia (non-potency perk check, unrounded AP) |
| **CACO-AP-12** | `CACO-AP-12` | `pat-caco-ap-4.py` | `pat caco-ap 12` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | RestM 10s (Index 2), RestS 5s (Index 1), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Alkanet Flower+Barley; Aloe Vera+Bear Claws |
| **CACO-AP-13** | `CACO-AP-13` | `pat-caco-ap-4.py` | `pat caco-ap 13` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | RestS 10s (Index 2), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Aloe Vera+Bear Claws |
| **CACO-AP-14** | `CACO-AP-14` | `pat-caco-ap-4.py` | `pat caco-ap 14` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | All 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Chaurus Eggs+Clouded Funnel Cap |
| **CACO-AP-15** | `CACO-AP-15` | `pat-caco-ap-4.py` | `pat caco-ap 15` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | DmgM 5s (Index 1), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Chaurus Eggs+Clouded Funnel Cap |
| **CACO-AP-16** | `CACO-AP-16` | `pat-caco-ap-4.py` | `pat caco-ap 16` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | DmgM 10s (Index 2), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Chaurus Eggs+Clouded Funnel Cap |
| **CACO-AP-17** | `CACO-AP-17` | `pat-caco-ap-4.py` | `pat caco-ap 17` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | All 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 75, Fortify 0, Perks: None | Aloe Vera+Ambrosia; Aloe Vera+Banded Pennant |
| **CACO-AP-18** | `CACO-AP-18` | `pat-caco-ap-4.py` | `pat caco-ap 18` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | All 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Seeker of Shadows | Aloe Vera+Ambrosia; Black Pearl+Blue Clipper Butterfly |
| **CACO-AP-19** | `CACO-AP-19` | `pat-caco-ap-4.py` | `pat caco-ap 19` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | All 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Alchemist 1, Seeker of Shadows | Aloe Vera+Ambrosia |
| **CACO-AP-20** | `CACO-AP-20` | `pat-caco-ap-4.py` | `pat caco-ap 20` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | All 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Alchemist 3, Seeker of Shadows | Aloe Vera+Ambrosia |
| **CACO-AP-21** | `CACO-AP-21` | `pat-caco-ap-4.py` | `pat caco-ap 21` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | RestH 5s (Index 1), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Aloe Vera+Ambrosia |
| **CACO-AP-22** | `CACO-AP-22` | `pat-caco-ap-4.py` | `pat caco-ap 22` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | All 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Alkanet Flower+Barley |
| **CACO-AP-23** | `CACO-AP-23` | `pat-caco-ap-4.py` | `pat caco-ap 23` | Same as CACO-AP-11 disk setup | InitMult 3.0, SkillFactor 3.0 | RestM 5s (Index 1), others 1s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Alkanet Flower+Barley |
| **Requiem-1** | `Requiem-1` | `pat-requiem.py` | `pat requiem` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 | Blue Mountain Flower+Wheat (RestH); Deathbell+Nightshade (DmgH); Glowing Mushroom+Nightshade (FortDest) |
| **Requiem-2** | `Requiem-2` | `pat-requiem.py` | `pat requiem 2` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2 (tier 2) | Blue Mountain Flower+Wheat; Deathbell+Nightshade; Glowing Mushroom+Nightshade; Glowing Mushroom+Snowberries |
| **Requiem-3** | `Requiem-3` | `pat-requiem.py` | `pat requiem 3` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2, Improved Elixirs (+25% Elixirs only) | Blue Mountain Flower+Wheat (Elixir +25%); Salt+Garlic (Elixir +25%); Deathbell+Nightshade (Poison 0%) |
| **Requiem-4** | `Requiem-4` | `pat-requiem.py` | `pat requiem 4` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2, Improved Poisons (+25% Poisons only) | Deathbell+Nightshade (Poison +25%); Briar Heart+Creep Cluster (Poison +25%); Blue Mountain Flower+Wheat (Elixir 0%) |
| **Requiem-5** | `Requiem-5` | `pat-requiem.py` | `pat requiem 5` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2, Purification Process | Blue Mountain Flower+Wheat (Purified); Blue Mountain Flower+Blue Butterfly Wing (Purified); Salt+Garlic |
| **Requiem-6** | `Requiem-6` | `pat-requiem.py` | `pat requiem 6` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None (Unperked gate check) | Blue Mountain Flower+Wheat (Gate check); Deathbell+Nightshade (Gate check) |
| **Requiem-7** | `Requiem-7` | `pat-requiem.py` | `pat requiem 7` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Lore 1 + 2, Improved Elixirs (+25%), Improved Poisons (+25%) | Blue Mountain Flower+Wheat (Elixir +25%); Deathbell+Nightshade (Poison +25%); Salt+Garlic (Elixir +25%) |
| **Requiem-8** | `Requiem-8` | `pat-requiem.py` | `pat requiem 8` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Lore 1 + 2, Improved Elixirs, Improved Poisons, Purification Process (Full tree) | Blue Mountain Flower+Wheat (Purified Elixir); Briar Heart+Creep Cluster (Improved Poison); Dragon's Tongue+Fly Amanita (Improved Elixir) |
| **Requiem-9** | `Requiem-9` | `pat-requiem.py` | `pat requiem 9` | AP disabled; Requiem enabled | InitMult 4.5, SkillFactor 1.8 | N/A (CACO disabled) | Skill 100, Fortify 50 (Peerless gear), Perks: Alchemical Lore 1 + 2, Improved Elixirs, Improved Poisons, Purification Process | Blue Mountain Flower+Wheat; Deathbell+Nightshade; Glowing Mushroom+Snowberries |
| **Requiem-10** | `Requiem-10` | `pat-requiem.py` | `pat requiem 10` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 50 (Level < 100), Fortify 50 (Peerless gear), Perks: Alchemical Lore 1 + 2 | Blue Mountain Flower+Wheat; Glowing Mushroom+Snowberries; Deathbell+Nightshade |
| **Requiem-11** | `Requiem-11` | `pat-requiem.py` | `pat requiem 11` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: REQ_RacialSkills_CreatePotionsUnperked active | Blue Mountain Flower+Wheat (Unperked keyword craft) |
| **Requiem-12** | `Requiem-12` | `pat-requiem.py` | `pat requiem 12` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Lore 1 + 2, Improved Elixirs | Glowing Mushroom+Nightshade (Fortify Destruction x0.5 skill factor) |
| **Requiem-13** | `Requiem-13` | `pat-requiem.py` | `pat requiem 13` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2 | Blind Watcher's Eye+Burnt Spriggan Wood; Butterfly Wing+Dragon's Tongue; Aster Bloom Core+Boar Tusk; Ancestor Moth Wing+Congealed Putrescence |
| **Requiem-14** | `Requiem-14` | `pat-requiem.py` | `pat requiem 14` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2 | Dreugh Wax+Stoneflower Petals; Bliss Bug Thorax+Dwarven Oil; Angelfish+Canis Root; Canis Root+Hanging Moss |
| **Requiem-15** | `Requiem-15` | `pat-requiem.py` | `pat requiem 15` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Green Thumb (nulled by Requiem) | Aloe Vera Leaves+Ambrosia |
| **Requiem-16** | `Requiem-16` | `pat-requiem.py` | `pat requiem 16` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 75, Fortify 0, Perks: Alchemical Lore 1 + 2 | Aloe Vera Leaves+Ambrosia |
| **Requiem-17** | `Requiem-17` | `pat-requiem.py` | `pat requiem 17` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2, Physician (nulled by Requiem) | Aloe Vera Leaves+Ambrosia |
| **Requiem-18** | `Requiem-18` | `pat-requiem.py` | `pat requiem 18` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2, Seeker of Shadows | Aloe Vera Leaves+Ambrosia |
| **Apothecary-1** | `Apothecary-1` | `pat-apothecary.py` | `pat apothecary` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Blue Butterfly Wing+Blue Mountain Flower (Fortify Skill: +1.5%/lvl); Blisterwort+Wheat (Restore Attribute: +0.667%/lvl); Salt Pile+Garlic (Regen Rate: +0.52%/lvl); Canis Root+Spider Egg (Generic: +1.25%/lvl) |
| **Apothecary-2** | `Apothecary-2` | `pat-apothecary.py` | `pat apothecary 2` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 1; SPID perk present | Blisterwort+Wheat; Blue Butterfly Wing+Blue Mountain Flower; Salt Pile+Garlic |
| **Apothecary-3** | `Apothecary-3` | `pat-apothecary.py` | `pat apothecary 3` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 3; SPID perk present | Blisterwort+Wheat; Deathbell+Nightshade; Luna Moth Wing+Vampire Dust |
| **Apothecary-4** | `Apothecary-4` | `pat-apothecary.py` | `pat apothecary 4` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 5; SPID perk present | Blue Butterfly Wing+Blue Mountain Flower (FortSkill); Blisterwort+Wheat (RestAttr); Salt Pile+Garlic (RegenRate); Canis Root+Spider Egg (Generic) |
| **Apothecary-5** | `Apothecary-5` | `pat-apothecary.py` | `pat apothecary 5` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 50 (Peerless gear), Perks: Alchemist 3; SPID perk present | Blisterwort+Wheat; Blue Butterfly Wing+Blue Mountain Flower; Salt Pile+Garlic |
| **Apothecary-6** | `Apothecary-6` | `pat-apothecary.py` | `pat apothecary 6` | AP disabled; Apothecary enabled | InitMult 4.5, SkillFactor 1.8 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 4; SPID perk present | Blisterwort+Wheat; Deathbell+Nightshade; Luna Moth Wing+Vampire Dust |
| **Apothecary-7** | `Apothecary-7` | `pat-apothecary.py` | `pat apothecary 7` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Blue Butterfly Wing+Blue Mountain Flower (FortSkill +1.5%/lvl); Dragon's Tongue+Fly Amanita (FortSkill +1.5%/lvl); Salt Pile+Garlic (RegenRate +0.52%/lvl); Luna Moth Wing+Vampire Dust (RegenRate +0.52%/lvl) |
| **Apothecary-8** | `Apothecary-8` | `pat-apothecary.py` | `pat apothecary 8` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Blisterwort+Wheat (RestAttr +0.667%/lvl); Briar Heart+Ectoplasm (RestAttr +0.667%/lvl); Deathbell+Nightshade (Generic +1.25%/lvl); Canis Root+Spider Egg (Generic +1.25%/lvl) |
| **Apothecary-9** | `Apothecary-9` | `pat-apothecary.py` | `pat apothecary 9` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 2; SPID perk present | Blisterwort+Wheat; Blue Butterfly Wing+Blue Mountain Flower; Deathbell+Nightshade |
| **Apothecary-10** | `Apothecary-10` | `pat-apothecary.py` | `pat apothecary 10` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 50 (Level < 100), Fortify 50 (Peerless gear), Perks: Alchemist 3; SPID perk present | Blisterwort+Wheat (RestAttr x 35); Blue Butterfly Wing+Blue Mountain Flower (FortSkill x 35); Salt Pile+Garlic (RegenRate x 35); Deathbell+Nightshade (Generic x 35) |
| **Apothecary-11** | `Apothecary-11` | `pat-apothecary.py` | `pat apothecary 11` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 75 (Level 75), Fortify 0, Perks: None; SPID perk present | Blisterwort+Wheat (RestAttr x 60); Blue Butterfly Wing+Blue Mountain Flower (FortSkill x 60); Deathbell+Nightshade (Generic x 60) |
| **Apothecary-12** | `Apothecary-12` | `pat-apothecary.py` | `pat apothecary 12` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Torchbug Thorax+Chaurus Eggs (Fortify Stamina 2.5 multiplier category) |
| **Apothecary-13** | `Apothecary-13` | `pat-apothecary.py` | `pat apothecary 13` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Fly Amanita+Snowberries (Resist Fire); Frost Mirriam+Snowberries (Resist Frost); Glowing Mushroom+Snowberries (Resist Shock); Beehive Husk+Thistle Branch (Resist Poison) |
| **Apothecary-14** | `Apothecary-14` | `pat-apothecary.py` | `pat apothecary 14` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 50, Fortify 0, Perks: None; SPID perk present | Daedra Heart+Eye of Sabre Cat (Reflect Damage at Skill 50) |
| **Apothecary-15** | `Apothecary-15` | `pat-apothecary.py` | `pat apothecary 15` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Daedra Heart+Eye of Sabre Cat (Reflect Damage at Skill 100) |
| **Apothecary-16** | `Apothecary-16` | `pat-apothecary.py` | `pat apothecary 16` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Deathbell+Nightshade (Damage Health Rank 0 Baseline); Chicken's Egg+Tundra Cotton (Resist Magic at Skill 100) |
| **Apothecary-17** | `Apothecary-17` | `pat-apothecary.py` | `pat apothecary 17` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 1; SPID perk present | Deathbell+Nightshade (Damage Health Rank 1 Bracket) |
| **Apothecary-18** | `Apothecary-18` | `pat-apothecary.py` | `pat apothecary 18` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 2; SPID perk present | Deathbell+Nightshade (Damage Health Rank 2 Bracket) |
| **Apothecary-19** | `Apothecary-19` | `pat-apothecary.py` | `pat apothecary 19` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 4; SPID perk present | Deathbell+Nightshade (Damage Health Rank 4 Bracket) |
| **Apothecary-20** | `Apothecary-20` | `pat-apothecary.py` | `pat apothecary 20` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 15 (Level 15), Fortify 0, Perks: None; SPID perk present | Blisterwort+Wheat (Restore Health at Skill 15); Red Mountain Flower+Tundra Cotton (Restore Magicka at Skill 15) |
| **Apothecary-21** | `Apothecary-21` | `pat-apothecary.py` | `pat apothecary 21` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 25, Fortify 0, Perks: None; SPID perk present | Deathbell+Nightshade (Damage Health at Skill 25) |
| **Apothecary-22** | `Apothecary-22` | `pat-apothecary.py` | `pat apothecary 22` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 40, Fortify 0, Perks: None; SPID perk present | Deathbell+Nightshade; Red Mountain Flower+Mora Tapinella; Purple Mountain Flower+Sabre Cat Tooth |
| **Apothecary-23** | `Apothecary-23` | `pat-apothecary.py` | `pat apothecary 23` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 50, Fortify 0, Perks: None; SPID perk present | Canis Root+Spider Egg; Dwarven Oil+Scaly Pholiota; Chicken's Egg+Tundra Cotton |
| **Apothecary-24** | `Apothecary-24` | `pat-apothecary.py` | `pat apothecary 24` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 60, Fortify 0, Perks: None; SPID perk present | Deathbell+Nightshade (Damage Health at Skill 60) |
| **Apothecary-25** | `Apothecary-25` | `pat-apothecary.py` | `pat apothecary 25` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 75, Fortify 0, Perks: None; SPID perk present | Deathbell+Nightshade; Canis Root+Spider Egg; Dwarven Oil+Scaly Pholiota |
| **Apothecary-26** | `Apothecary-26` | `pat-apothecary.py` | `pat apothecary 26` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 75, Fortify 0, Perks: Alchemist 2; SPID perk present | Red Mountain Flower+Mora Tapinella; Purple Mountain Flower+Sabre Cat Tooth |
| **Apothecary-27** | `Apothecary-27` | `pat-apothecary.py` | `pat apothecary 27` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 90, Fortify 0, Perks: None; SPID perk present | Deathbell+Nightshade (Damage Health at Skill 90) |
| **Apothecary-28** | `Apothecary-28` | `pat-apothecary.py` | `pat apothecary 28` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 5; SPID perk present | Deathbell+Nightshade (Damage Health Rank 5 Ceiling) |
| **Apothecary-29** | `Apothecary-29` | `pat-apothecary.py` | `pat apothecary 29` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Bleeding Crown+Bliss Bug Thorax; Blue Dartwing+Bog Beacon; Coda Flower+Creep Cluster; Ancestor Moth Wing+Burnt Spriggan Wood |
| **Apothecary-30** | `Apothecary-30` | `pat-apothecary.py` | `pat apothecary 30` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Imp Stool+Orange Dartwing; Bee+Scaly Pholiota; Bear Claws+Giant's Toe; Deathbell+Jarrin Root |
| **Apothecary-31** | `Apothecary-31` | `pat-apothecary.py` | `pat apothecary 31` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 15, Fortify 0, Perks: None; SPID perk present | Bleeding Crown+Bliss Bug Thorax (Weakness to Fire at Skill 15) |
| **Apothecary-32** | `Apothecary-32` | `pat-apothecary.py` | `pat apothecary 32` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 50, Fortify 0, Perks: None; SPID perk present | Bleeding Crown+Bliss Bug Thorax (Weakness to Fire at Skill 50) |
| **Apothecary-33** | `Apothecary-33` | `pat-apothecary.py` | `pat apothecary 33` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 75, Fortify 0, Perks: Alchemist 3; SPID perk present | Deathbell+Jarrin Root (Damage Health at Skill 75 Rank 3) |
| **Apothecary-34** | `Apothecary-34` | `pat-apothecary.py` | `pat apothecary 34` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 75, Fortify 0, Perks: Alchemist 4; SPID perk present | Deathbell+Jarrin Root (Damage Health at Skill 75 Rank 4) |
| **Apothecary-35** | `Apothecary-35` | `pat-apothecary.py` | `pat apothecary 35` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 85, Fortify 0, Perks: Alchemist 2; SPID perk present | Deathbell+Jarrin Root (Damage Health at Skill 85 Rank 2) |
| **Apothecary-36** | `Apothecary-36` | `pat-apothecary.py` | `pat apothecary 36` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 2; SPID perk present | Deathbell+Jarrin Root (Damage Health at Skill 100 Rank 2) |
| **Apothecary-37** | `Apothecary-37` | `pat-apothecary.py` | `pat apothecary 37` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 4; SPID perk present | Deathbell+Jarrin Root (Damage Health at Skill 100 Rank 4) |
| **Apothecary-38** | `Apothecary-38` | `pat-apothecary.py` | `pat apothecary 38` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemist 5; SPID perk present | Deathbell+Jarrin Root (Damage Health at Skill 100 Rank 5) |
| **Apothecary-39** | `Apothecary-39` | `pat-apothecary.py` | `pat apothecary 39` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 15, Fortify 0, Perks: None; SPID perk present | Blue Dartwing+Cyrodilic Spadetail (Fear at Skill 15) |
| **Apothecary-40** | `Apothecary-40` | `pat-apothecary.py` | `pat apothecary 40` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 50, Fortify 0, Perks: None; SPID perk present | Blue Dartwing+Cyrodilic Spadetail (Fear at Skill 50) |
| **Apothecary-41** | `Apothecary-41` | `pat-apothecary.py` | `pat apothecary 41` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Blisterwort+Falmer Ear (Frenzy); Abecean Longfin+Elves Ear (Weakness to Frost); Ashen Grass Pod+Bee (Weakness to Shock); Chaurus Eggs+Deathbell (Weakness to Poison) |
| **Apothecary-42** | `Apothecary-42` | `pat-apothecary.py` | `pat apothecary 42` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Abecean Longfin+Beehive Husk (Fortify Sneak); Abecean Longfin+Deathbell (Fortify Speed); Blisterwort+Glowing Mushroom (Fortify Armor Rating); Ashen Grass Pod+Falmer Ear (Fortify Lockpicking) |
| **Apothecary-43** | `Apothecary-43` | `pat-apothecary.py` | `pat apothecary 43` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Blue Dartwing+Orange Dartwing (Fortify Pickpocket); Bear Claws+Glow Dust (Damage Armor); Butterfly Wing+Chicken's Egg (Lingering Damage Stamina); Hagraven Claw+Purple Mountain Flower (Lingering Damage Magicka) |
| **Apothecary-44** | `Apothecary-44` | `pat-apothecary.py` | `pat apothecary 44` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Imp Stool+Orange Dartwing (Lingering Damage Health); Grass Pod+River Betty (Fortify Alteration Power); Briar Heart+Honeycomb (Fortify Block); Bear Claws+Canis Root (Fortify One-handed) |
| **Apothecary-45** | `Apothecary-45` | `pat-apothecary.py` | `pat apothecary 45` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Bone Meal+Giant's Toe; Ambrosia+Bittergreen Petals; Blister Pod Cap+Kagouti Hide; Falmer Ear+Skeever Tail |
| **Apothecary-46** | `Apothecary-46` | `pat-apothecary.py` | `pat apothecary 46` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Alocasia Fruit+Blind Watcher's Eye; Angelfish+Angler Larvae; Bone Meal+Bungler's Bane; Bee+Berit's Ashes |
| **Apothecary-47** | `Apothecary-47` | `pat-apothecary.py` | `pat apothecary 47` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Aster Bloom Core+Canis Root; Frost Mirriam+Grass Pod; Charred Skeever Hide+Hawk Feathers; Butterfly Wing+Imp Gall |
| **Apothecary-48** | `Apothecary-48` | `pat-apothecary.py` | `pat apothecary 48` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None; SPID perk present | Ash Creep Cluster+Beehive Husk; Ash Hopper Jelly+Beehive Husk; Bliss Bug Thorax+Bog Beacon; Ancestor Moth Wing+Hagraven Claw |
| **Apothecary-49** | `Apothecary-49` | `pat-apothecary.py` | `pat apothecary 49` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Green Thumb; SPID perk present | Blisterwort+Ambrosia |
| **Apothecary-50** | `Apothecary-50` | `pat-apothecary.py` | `pat apothecary 50` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Benefactor, Physician, Poisoner, Seeker of Shadows; SPID perk present | Blisterwort+Ambrosia; Angelfish+Canis Root; Coda Flower+Jarrin Root |
| **Apothecary-51** | `Apothecary-51` | `pat-apothecary.py` | `pat apothecary 51` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Benefactor, Physician, Poisoner; SPID perk present | Blisterwort+Ambrosia |
| **Apothecary-52** | `Apothecary-52` | `pat-apothecary.py` | `pat apothecary 52` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 90, Fortify 0, Perks: None; SPID perk present | Deathbell+Jarrin Root |
| **Apothecary-53** | `Apothecary-53` | `pat-apothecary.py` | `pat apothecary 53` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 65, Fortify 0, Perks: Alchemist 1; SPID perk present | Deathbell+Jarrin Root |
| **Apothecary-54** | `Apothecary-54` | `pat-apothecary.py` | `pat apothecary 54` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 85, Fortify 0, Perks: Alchemist 1; SPID perk present | Deathbell+Jarrin Root |
| **Apothecary-55** | `Apothecary-55` | `pat-apothecary.py` | `pat apothecary 55` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 25, Fortify 0, Perks: None; SPID perk present | Blisterwort+Ambrosia; Dwarven Oil+Garlic |
| **Apothecary-56** | `Apothecary-56` | `pat-apothecary.py` | `pat apothecary 56` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 60, Fortify 0, Perks: None; SPID perk present | Blisterwort+Ambrosia |
| **Apothecary-57** | `Apothecary-57` | `pat-apothecary.py` | `pat apothecary 57` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 90, Fortify 0, Perks: None; SPID perk present | Blisterwort+Ambrosia; Dwarven Oil+Garlic; Angelfish+Ash Creep Cluster |
| **APAFA-1** | `APAFA-1` | `pat-apafa.py` | `pat apafa` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Alchemist 0, no type perks | Thistle Branch+Snowberries |
| **APAFA-2** | `APAFA-2` | `pat-apafa.py` | `pat apafa 2` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Alchemist 1, no type perks | Blisterwort+Wheat |
| **APAFA-3** | `APAFA-3` | `pat-apafa.py` | `pat apafa 3` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Alchemist 2, no type perks | Ambrosia+Bear Claws |
| **APAFA-4** | `APAFA-4` | `pat-apafa.py` | `pat apafa 4` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Alchemist 3, Benefactor | Angelfish+Ash Creep Cluster |
| **APAFA-5** | `APAFA-5` | `pat-apafa.py` | `pat apafa 5` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Alchemist 4, Physician, Benefactor | Alocasia Fruit+Ambrosia |
| **APAFA-6** | `APAFA-6` | `pat-apafa.py` | `pat apafa 6` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Alchemist 5, no type perks | Ash Creep Cluster+Bittergreen Petals |
| **APAFA-7** | `APAFA-7` | `pat-apafa.py` | `pat apafa 7` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Alchemist 5, Physician | Chokeberry+Coda Flower |
| **APAFA-8** | `APAFA-8` | `pat-apafa.py` | `pat apafa 8` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Alchemist 5, Poisoner | Abecean Longfin+Deathbell |
| **APAFA-9** | `APAFA-9` | `pat-apafa.py` | `pat apafa 9` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 4.0, SkillFactor 1.5 | N/A (CACO disabled) | Skill 100, Fortify 0, Alchemist 5, Purity | Bittergreen Petals+Coda Flower |
| **APAFA-10** | `APAFA-10` | `pat-apafa.py` | `pat apafa 10` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 5.0, SkillFactor 2.0 | N/A (CACO disabled) | Skill 75, Fortify 0, Alchemist 3, no type perks | Blister Pod Cap+Bog Beacon |
| **Pred-Default-Vanilla** | `Vanilla-Default` | `pat-default-vanilla.py` | `pat default vanilla` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Default-AP** | `AP-Default` | `pat-default-ap.py` | `pat default ap` | mag 25/5, dur 15/5, impureFix=True | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Default-CACO** | `CACO-Default` | `pat-default-caco.py` | `pat default caco` | N/A (AP Disabled) | InitMult 3.9, SkillFactor 1.0 | All 0s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Default-CACO+AP** | `CACO-AP-Default` | `pat-default-caco-ap.py` | `pat default caco-ap` | mag 25/5, dur 15/5, impureFix=True | InitMult 3.9, SkillFactor 1.0 | All 0s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Default-Requiem** | `Requiem-Default` | `pat-default-requiem.py` | `pat default requiem` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A | Skill 100, Fortify 0, Perks: Alchemical Lore 1 | Full Potion Prediction Export |
| **Pred-Default-Apothecary** | `Apothecary-Default` | `pat-default-apothecary.py` | `pat default apothecary` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Default-APAFA** | `APAFA-Default` | `pat-default-apafa.py` | `pat default apafa` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Changed-Vanilla** | `Vanilla-Changed` | `pat-vanilla-changed.py` | `pat vanilla changed` | N/A (AP Disabled) | InitMult 4.5, SkillFactor 1.8 | N/A | Skill 65, Fortify 50 (Peerless gear), Perks: Alchemist 3, Physician, Benefactor, Poisoner, Seeker of Shadows | Full Potion Prediction Export |
| **Pred-Changed-AP** | `AP-Changed` | `pat-ap-changed.py` | `pat ap changed` | mag 10/2, dur 10/2, impureFix=False, overrides (0x3EB15) | InitMult 4.2, SkillFactor 1.6 | N/A | Skill 75, Fortify 50 (Peerless gear), Perks: Alchemist 4, Physician, Benefactor | Full Potion Prediction Export |
| **Pred-Changed-CACO** | `CACO-Changed` | `pat-caco-changed.py` | `pat caco changed` | N/A (AP Disabled) | InitMult 3.2, SkillFactor 2.8 | All 10s (Index 2), DisableHandling=1, ImpureProc=0 | Skill 55, Fortify 50 (Peerless gear), Perks: Alchemist 2, Physician, Poisoner | Full Potion Prediction Export |
| **Pred-Changed-CACO+AP** | `CACO-AP-Changed` | `pat-caco-ap-changed.py` | `pat caco-ap changed` | mag 30/6, dur 20/6, impureFix=True | InitMult 3.5, SkillFactor 2.5 | Mixed: RestH 5s, RestM 10s, RestS 0s, DmgH 10s, DmgM 5s, DmgS 0s, DisableHandling=1, ImpureProc=0 | Skill 85, Fortify 50 (Peerless gear), Perks: Alchemist 4, Physician, Benefactor, Poisoner | Full Potion Prediction Export |
| **Pred-Changed-Requiem** | `Requiem-Changed` | `pat-requiem-changed.py` | `pat requiem changed` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A | Skill 75, Fortify 0, Perks: Lore 2, Improved Elixirs, Improved Poisons | Full Potion Prediction Export |
| **Pred-Changed-Apothecary** | `Apothecary-Changed` | `pat-apothecary-changed.py` | `pat apothecary changed` | AP disabled; Apothecary enabled | InitMult 4.5, SkillFactor 1.8 | N/A | Skill 65, Fortify 50 (Peerless gear), Perks: Alchemist 3 | Full Potion Prediction Export |
| **Pred-Changed-APAFA** | `APAFA-Changed` | `pat-apafa-changed.py` | `pat apafa changed` | APAFA enabled; AP/CACO/Requiem/Apothecary disabled; no disk JSON | InitMult 5.0, SkillFactor 2.0 | N/A | Skill 75, Fortify 0, Alchemist 3, no type perks | Full Potion Prediction Export |

---

## AI Agent Reset Procedure

If other test tasks or agents modify `pa-console-tests/Source/Scripts/ProsperousAlchemistTests.psc`, `pa-console-tests/SKSE/CustomConsole/pa-tests.yaml`, or root `pat-*.py` scripts, an AI agent can restore the full minimal test suite by following these exact steps:

1. **Verify Console Definition (`pa-tests.yaml`)**:
   Ensure `pa-console-tests/SKSE/CustomConsole/pa-tests.yaml` contains subcommands for `default`, `vanilla`, `caco`, `ap`, `caco-ap`, `requiem`, `apothecary`, and `apafa` with optional `variant` string parameters. The help strings for `vanilla` (2-18), `caco` (2-27), `ap` (2-13), `caco-ap` (2-23), `requiem` (2-18), `apothecary` (2-57), and `apafa` (2-10, changed) must cover all mode variants.
2. **Verify Papyrus Test Script (`ProsperousAlchemistTests.psc`)**:
   Ensure `pa-console-tests/Source/Scripts/ProsperousAlchemistTests.psc` implements all 166 in-game test block handlers in `ProvisionAndPrintTests` as specified in the technical matrix.
3. **Recompile Papyrus Script**:
   Execute the PowerShell build script:
   ```powershell
   cd pa-console-tests
   .\compile.ps1
   ```
4. **Verify Root Python Mode Scripts**:
   Ensure all 27 pre-launch mode scripts include `pat-apafa.py`, `pat-default-apafa.py`, and `pat-apafa-changed.py`; each uses `apply_mode_config` to enable APAFA and disable the inactive overhauls.
5. **Rebuild & Deploy SKSE Plugin**:
   Run `python build.py` from repository root and verify that the built and deployed DLL timestamps match.
6. **Final Verification Check**:
   Run `python verify_test_suite_alignment.py` and ensure output reports 100% PASS across all verification modules before completing work.
