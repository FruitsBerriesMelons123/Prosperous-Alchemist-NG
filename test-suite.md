# Prosperous Alchemist NG - Full Minimal & Comprehensive Test Suite

This document defines the full minimal but comprehensive test suite for Prosperous Alchemist NG. It tests all combinations of ingredient effects, selection orders, modes (`AP`, `Vanilla`, `CACO`, `CACO+AP`, `Requiem`, `Apothecary`), settings (GameSettings, CACO duration index families, AP JSON thresholds/multipliers/overrides/impure cost fix, Requiem lore/type-perk gates and effect categories, Apothecary skill/category/rank branches), and player levels/perks/purity filters using a minimal, deterministic set of test blocks.

---

## Overview & Architecture

1. **Two-Tier Configuration Architecture & Disk vs In-Game Setting Rule**:
   - **Pre-Launch Disk Setup**: Modes with NO disk-based configuration files (`Vanilla`, `CACO`, `Requiem`, `Apothecary`) use a **single** root Python script (`pat-vanilla.py`, `pat-caco.py`, `pat-requiem.py`, `pat-apothecary.py`) for observed craft testing because multiple disk scripts are redundant when on-disk settings do not change. Modes WITH disk-based configuration files (`AP`, `CACO+AP` with `AlchemyPlus.json`) use enough pre-launch disk scripts (`pat-ap.py`, `pat-ap-2.py`, `pat-ap-3.py`, `pat-ap-4.py`, `pat-caco-ap.py`, `pat-caco-ap-2.py`, `pat-caco-ap-3.py`, `pat-caco-ap-4.py`) to test all distinct on-disk setting configurations.
   - **In-Game Setting Blocks**: Every supported mode features in-game setting blocks (`pat <mode>` through variant ranges: `vanilla` 1-17, `caco` 1-18, `ap` 1-12, `caco-ap` 1-11, `requiem` 1-12, `apothecary` 1-12), providing 82 observed craft blocks total across the test suite. Each in-game `pat` command contains **no more than 4 tests** (crafts or gate checks).
   - **Skill Level Distribution Rule**: Across the blocks in each mode, **at least 9 blocks use Player Alchemy Level 100**, and **at least 1 block uses Player Alchemy Level < 100** (e.g. Level 50 or 75), ensuring maximum coverage at peak level while validating non-100 skill scaling.
   - **Targeted Ingredient Selection Rule**: Ingredient combinations in every block are strictly chosen to contain the specific effects modified by that block's active settings, perks, overrides, duration indices, or scaling branches (e.g., Physician tests Restore Health/Magicka/Stamina; Poisoner tests poison effects; Purity tests mixed beneficial/harmful recipes; AP magnitude overrides test Restore Health/Stamina; Apothecary tests each of its four category scaling branches).
2. **Dedicated Final Prediction Export Phase Scripts**:
   - The final phase (Phase 7) tests full potion prediction exports across **ALL** supported modes/mods (`Vanilla`, `AP`, `CACO`, `CACO+AP`, `Requiem`, `Apothecary`) and uses **dedicated, separate** pre-launch disk scripts for default settings (`pat-default-<mode>.py`) and changed settings (`pat-<mode>-changed.py`). These prediction export phase scripts are separate files from the observed craft testing phase scripts.
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
   Run the requested `pat` blocks and use the Developer Test Hub's explicit CSV export controls or the plugin's normal capture path. The confirmed CSV uses the plugin-generated 19-column header. After Skyrim exits, the AI validation step reads the newly generated file.

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
  - **Modified Settings**: Disk: Staged by `pat-ap-4.py`. In-Game: Player Alchemy 100, Fortify 0, Seeker of Shadows (+10%), `InitMult=4.0`, `SkillFactor=1.5`.
  - **Target Effects**: Interaction of Seeker of Shadows multiplier (+10%) with unrounded AP calculations.
  - **Steps**:
    1. Run `pat ap 12` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat` (Restore Health — Seeker x unrounded AP)
        - `Briar Heart + Canis Root` (Fortify Block — Seeker x unrounded AP)
    4. **Next Step**: Exit Skyrim and run `python pat-vanilla.py` on disk.

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
  - **Modified Settings**: Disk: Staged by `pat-vanilla.py`. In-Game: Player Alchemy 100, Fortify 0, Full Vanilla Perk Tree + Seeker of Shadows.
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
    4. **Next Step**: Exit Skyrim and run `python pat-caco.py` on disk.

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
        - Order 5: `Roobrush` -> `Large Antlers` -> `Slaughterfish Egg`
        - Order 6: `Slaughterfish Egg` -> `Large Antlers` -> `Roobrush`
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
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 50 (Peerless gear), Alchemist 5 + Physician + Benefactor + Poisoner + Purity, `InitMult=3.0`, `SkillFactor=3.0`, CACO Mixed Durations.
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
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`.
  - **Target Effects**: CACO Record Exception: Resist Disease Aliasing (`fAlchemyResistDiseaseMult`).
  - **Steps**:
    1. Run `pat caco 15` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Garlic + Mudcrab Chitin` (Resist Disease aliasing)
    4. **Next Command**: `pat caco 16` in Skyrim console.

- **Block 16 (`pat caco 16`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`.
  - **Target Effects**: CACO Record Exception: Damage Undead base cost 8.3 check.
  - **Steps**:
    1. Run `pat caco 16` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Monarch Butterfly + Nightshade` (Damage Undead base cost 8.3)
        - `Creep Cluster + Giant Lichen + Rock Warbler Egg`
    4. **Next Command**: `pat caco 17` in Skyrim console.

- **Block 17 (`pat caco 17`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, Seeker of Shadows active under CACO mode.
  - **Target Effects**: Verification of zero Seeker of Shadows rows under CACO (CACO disables vanilla Seeker actor value multiplier).
  - **Steps**:
    1. Run `pat caco 17` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Blisterwort + Wheat Extract` (Verify zero CACO Seeker rows)
    4. **Next Command**: `pat caco 18` in Skyrim console.

- **Block 18 (`pat caco 18`)**:
  - **Modified Settings**: Disk: Staged by `pat-caco.py`. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`.
  - **Target Effects**: CACO Record Flags: Etherealize, Detect Life, and Light flags.
  - **Steps**:
    1. Run `pat caco 18` in Skyrim console.
    2. Press **F** while crafting table UI is focused.
    3. Craft:
        - `Wisp Wrappings + Glowing Mushroom` (Etherealize)
        - `Wisp Wrappings + Watcher's Eye` (Detect Life)
        - `Blind Watcher's Eye + Watcher's Eye` (Light)
    4. **Next Step**: Exit Skyrim and run `python pat-caco-ap.py` on disk.

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
  - **Modified Settings**: Disk: CACO enabled, AP enabled, AP Rounding OFF (`roundedPotency.enabled=false`). In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.0`, `SkillFactor=3.0`, CACO 0s Durations (Index 0).
  - **Target Effects**: CACO + unrounded AP potency calculations.
  - **Steps**:
    1. Exit Skyrim. Run `python pat-caco-ap-4.py` on disk.
    2. Run `python reset_saves_and_start_skyrim.py`.
    3. Open crafting table in Skyrim.
    4. Run `pat caco-ap 11` in Skyrim console.
    5. Press **F** while crafting table UI is focused.
    6. Craft:
         - `Blisterwort + Wheat Extract` (Restore Health — CACO + unrounded AP)
         - `Canis Root + Spider Egg` (Damage Stamina — CACO + unrounded AP)
    7. **Next Step**: Exit Skyrim and run `python pat-requiem.py` on disk.

---

### Phase 5: Requiem Mode

Requiem is tested as an independent mode with CACO and Alchemy Plus disabled. Since Requiem has no disk configuration files, a single disk script (`pat-requiem.py`) stages Requiem in `modlist.txt` and the load order. All 10 in-game setting blocks run sequentially in one Skyrim session. In Requiem blocks, `Salt Pile` must be provisioned with local FormID `0x74A19` from `Requiem.esp`.

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
         - `Salt Pile + Garlic` (Elixir — receives +25% Improved Elixirs boost)
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
         - `Salt Pile + Garlic` (Regen Magicka)
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
         - `Salt Pile + Garlic` (Elixir — +25%)
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
  - **Modified Settings**: Disk: Staged by `pat-requiem.py`. In-Game: Player Alchemy 100, Fortify 50 (Peerless gear), Lore 1 + 2 + All Requiem perks, `InitMult=4.5`, `SkillFactor=1.8`.
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
    4. **Next Step**: Exit Skyrim and run `python pat-apothecary.py` on disk.

---

### Phase 6: Apothecary Mode

Apothecary is tested with CACO and Alchemy Plus disabled. Since Apothecary has no disk configuration files, a single disk script (`pat-apothecary.py`) stages Apothecary in `modlist.txt` and the load order. 10 in-game setting blocks run sequentially in one Skyrim session. The configured SPID profile distributes `MAG_ControllerScalingPerk` (`0x050CB06C`, `0A725C~Skyrim.esm`) to the player. In Apothecary blocks, `Salt Pile` must be provisioned with local FormID `0x74A19` from `Apothecary.esp`.

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
    4. **Next Step**: Exit Skyrim and run `python pat-default-vanilla.py` on disk for Phase 7 prediction exports.

---

### Phase 7: Potion Prediction Export Verification Suite (Default & Changed Settings)

This phase verifies the complete in-game potion value prediction export (`alchemist.potion-predictions.csv.zst`) generated by the SKSE plugin across ALL supported modes (`Vanilla`, `AP`, `CACO`, `CACO+AP`, `Requiem`, `Apothecary`) under both **Default Settings** and **Changed (Non-Default) Settings**. Each mode uses separate, dedicated pre-launch disk scripts (`pat-default-<mode>.py` and `pat-<mode>-changed.py`) that are distinct from the observed craft testing phase files.

#### Sub-Phase 7A: Default Settings Prediction Export Suite

1. **Vanilla Mode (Default Settings)**:
   - **Default Settings**: Disk: CACO disabled, AP disabled. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-vanilla.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default vanilla`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-vanilla.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-ap.py` on disk.

2. **Alchemy Plus (AP) Mode (Default Settings)**:
   - **Default Settings**: Disk: CACO disabled, AP enabled (`magnitudeThreshold=25.0`, `magnitudeMult=5.0`, `durationThreshold=15.0`, `durationMult=5.0`, `impureCostFix=True`). In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-ap.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default ap`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-ap.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-caco.py` on disk.

3. **CACO Mode (Default Settings)**:
   - **Default Settings**: Disk: CACO enabled, AP disabled. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.9`, `SkillFactor=1.0`, CACO 0s Durations (all index 0), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-caco.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default caco`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-caco.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-caco-ap.py` on disk.

4. **CACO + AP Mode (Default Settings)**:
   - **Default Settings**: Disk: CACO enabled, AP enabled (`magnitudeThreshold=25.0`, `magnitudeMult=5.0`, `durationThreshold=15.0`, `durationMult=5.0`, `impureCostFix=True`). In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=3.9`, `SkillFactor=1.0`, CACO 0s Durations (all index 0), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-caco-ap.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default caco-ap`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-caco-ap.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-requiem.py` on disk.

5. **Requiem Mode (Default Settings)**:
   - **Default Settings**: Disk: Requiem enabled, CACO disabled, AP disabled. In-Game: Player Alchemy 100, Fortify 0, Alchemical Lore 1, `InitMult=4.0`, `SkillFactor=1.1`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-requiem.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default requiem`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-requiem.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-default-apothecary.py` on disk.

6. **Apothecary Mode (Default Settings)**:
   - **Default Settings**: Disk: Apothecary enabled, CACO disabled, AP disabled. In-Game: Player Alchemy 100, Fortify 0, no perks, `InitMult=4.0`, `SkillFactor=1.5`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-default-apothecary.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat default apothecary`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-apothecary.csv.zst`.
      6. **Next Command**: `python potion_prediction_test.py --check-confirmed-csv` on disk.

7. **Verify & Archive Default Predictions**:
   - **Steps**:
      1. Run `python potion_prediction_test.py --check-confirmed-csv`.
      2. Run `python save_predicted_default_settings.py` on disk to archive default setting CSV fixtures to:
          - `potions-predicted-vanilla.default.settings.csv.zst`
          - `potions-predicted-ap.default.settings.csv.zst`
          - `potions-predicted-caco.default.settings.csv.zst`
          - `potions-predicted-caco-ap.default.settings.csv.zst`
          - `potions-predicted-requiem.default.settings.csv.zst`
          - `potions-predicted-apothecary.default.settings.csv.zst`
      3. **Next Command**: Exit Skyrim and run `python pat-vanilla-changed.py` on disk.

---

#### Sub-Phase 7B: Changed Settings Prediction Export Suite

1. **Vanilla Mode (Changed Settings)**:
   - **Modified Settings**: Disk: CACO disabled, AP disabled. In-Game: Player Alchemy 65, Fortify 50 (Peerless gear), Alchemist 3, Physician, Benefactor, Poisoner, Seeker of Shadows, `InitMult=4.5`, `SkillFactor=1.8`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-vanilla-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat vanilla changed`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-vanilla.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-ap-changed.py` on disk.

2. **Alchemy Plus (AP) Mode (Changed Settings)**:
   - **Modified Settings**: Disk: CACO disabled, AP enabled (`magnitudeThreshold=10.0`, `magnitudeMult=2.0`, `durationThreshold=10.0`, `durationMult=2.0`, `impureCostFix=False`, overrides for `0x0003EB15`). In-Game: Player Alchemy 75, Fortify 50 (Peerless gear), Alchemist 4, Physician, Benefactor, `InitMult=4.2`, `SkillFactor=1.6`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-ap-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat ap changed`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-ap.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-caco-changed.py` on disk.

3. **CACO Mode (Changed Settings)**:
   - **Modified Settings**: Disk: CACO enabled, AP disabled. In-Game: Player Alchemy 55, Fortify 50 (Peerless gear), Alchemist 2, Physician, Poisoner, `InitMult=3.2`, `SkillFactor=2.8`, CACO 10s Durations (all index 2), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-caco-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat caco changed`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-caco.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-caco-ap-changed.py` on disk.

4. **CACO + AP Mode (Changed Settings)**:
   - **Modified Settings**: Disk: CACO enabled, AP enabled (`magnitudeThreshold=30.0`, `magnitudeMult=6.0`, `durationThreshold=20.0`, `durationMult=6.0`, `impureCostFix=True`). In-Game: Player Alchemy 85, Fortify 50 (Peerless gear), Alchemist 4, Physician, Benefactor, Poisoner, `InitMult=3.5`, `SkillFactor=2.5`, CACO Mixed Durations (RestoreHealth 5s, RestoreMagicka 10s, RestoreStamina 0s, DamageHealth 10s, DamageMagicka 5s, DamageStamina 0s), `DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-caco-ap-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat caco-ap changed`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-caco-ap.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-requiem-changed.py` on disk.

5. **Requiem Mode (Changed Settings)**:
   - **Modified Settings**: Disk: Requiem enabled, CACO disabled, AP disabled. In-Game: Player Alchemy 75, Fortify 0, Alchemical Lore 1 + 2 (effective tier 2), Improved Elixirs, Improved Poisons, `InitMult=4.0`, `SkillFactor=1.1`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-requiem-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat requiem changed`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-requiem.csv.zst`.
      6. **Next Command**: Exit Skyrim and run `python pat-apothecary-changed.py` on disk.

6. **Apothecary Mode (Changed Settings)**:
   - **Modified Settings**: Disk: Apothecary enabled, CACO disabled, AP disabled. In-Game: Player Alchemy 65, Fortify 50 (Peerless gear), Alchemist 3, `InitMult=4.5`, `SkillFactor=1.8`.
   - **Steps**:
      1. Exit Skyrim. Run `python pat-apothecary-changed.py`.
      2. Run `python reset_saves_and_start_skyrim.py`.
      3. In Skyrim console, run `pat apothecary changed`.
      4. Trigger in-game export potion prediction CSV command/hotkey.
      5. Run `python sync_potion_predictions.py` on disk -> syncs to `potions-predicted-apothecary.csv.zst`.
      6. **Next Command**: `python potion_prediction_test.py --check-confirmed-csv` on disk.

7. **Verify & Archive Changed Predictions**:
   - **Steps**:
      1. Run `python potion_prediction_test.py --check-confirmed-csv`.
      2. Run `python save_predicted_changed_settings.py` on disk to archive changed setting CSV fixtures to:
          - `potions-predicted-vanilla.changed.settings.csv.zst`
          - `potions-predicted-ap.changed.settings.csv.zst`
          - `potions-predicted-caco.changed.settings.csv.zst`
          - `potions-predicted-caco-ap.changed.settings.csv.zst`
          - `potions-predicted-requiem.changed.settings.csv.zst`
          - `potions-predicted-apothecary.changed.settings.csv.zst`
      3. **Next Step**: Suite Complete! Run `python verify_test_suite_alignment.py` to confirm 100% test suite alignment.

---

#### Sub-Phase 7C: Toggling Active Prediction Baseline Fixtures

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
     - All 60 requested observed-craft setting blocks across all 6 modes are present (10 AP, 10 Vanilla, 10 CACO, 10 CACO+AP, 10 Requiem, 10 Apothecary blocks).
     - Mode flags (`caco_enabled`, `alchemy_plus_enabled`, Requiem mode, Apothecary mode) match the block specification.
     - In-game parameters (`player_alchemy_level`, `player_fortify_alchemy`, `player_perks`, `game_settings`, `caco_settings`, `ap_settings`) match the block specification.
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
| **AP-12** | `AP-12` | `pat-ap-4.py` | `pat ap 12` | Same as AP-11 disk setup | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Seeker of Shadows (+10%) | Blisterwort+Wheat (Seeker x unrounded AP); Briar Heart+Canis Root |
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
| **Vanilla-16** | `Vanilla-16` | `pat-vanilla.py` | `pat vanilla 16` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: Full tree + Seeker | Abecean Longfin+Salt Pile+Cyrodilic Spadetail |
| **Vanilla-17** | `Vanilla-17` | `pat-vanilla.py` | `pat vanilla 17` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 15 (Level 15 baseline), Fortify 0, Perks: None | Blisterwort+Wheat (Level 15 baseline) |
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
| **CACO-15** | `CACO-15` | `pat-caco.py` | `pat caco 15` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | N/A | Skill 100, Fortify 0, Perks: None | Garlic+Mudcrab Chitin (Resist Disease aliasing) |
| **CACO-16** | `CACO-16` | `pat-caco.py` | `pat caco 16` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 10s (Index 2), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Monarch Butterfly+Nightshade (Damage Undead base cost 8.3); Creep Cluster+Giant Lichen+Rock Warbler Egg |
| **CACO-17** | `CACO-17` | `pat-caco.py` | `pat caco 17` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: Seeker of Shadows active | Blisterwort+Wheat Extract (Verify zero CACO Seeker rows) |
| **CACO-18** | `CACO-18` | `pat-caco.py` | `pat caco 18` | N/A (AP Disabled) | InitMult 3.0, SkillFactor 3.0 | All 5s (Index 1), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Wisp Wrappings+Glowing Mushroom (Etherealize); Wisp Wrappings+Watcher's Eye (Detect Life); Blind Watcher's Eye+Watcher's Eye (Light) |
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
| **CACO-AP-11**| `CACO-AP-11`| `pat-caco-ap-4.py`| `pat caco-ap 11` | mag 25/5, dur 15/5, roundedPotency.enabled=false | InitMult 3.0, SkillFactor 3.0 | All 0s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Blisterwort+Wheat Extract (CACO + unrounded AP); Canis Root+Spider Egg |
| **Requiem-1** | `Requiem-1` | `pat-requiem.py` | `pat requiem` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 | Blue Mountain Flower+Wheat (RestH); Deathbell+Nightshade (DmgH); Glowing Mushroom+Nightshade (FortDest) |
| **Requiem-2** | `Requiem-2` | `pat-requiem.py` | `pat requiem 2` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2 (tier 2) | Blue Mountain Flower+Wheat; Deathbell+Nightshade; Glowing Mushroom+Nightshade; Glowing Mushroom+Snowberries |
| **Requiem-3** | `Requiem-3` | `pat-requiem.py` | `pat requiem 3` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2, Improved Elixirs (+25% Elixirs only) | Blue Mountain Flower+Wheat (Elixir +25%); Salt Pile+Garlic (Elixir +25%); Deathbell+Nightshade (Poison 0%) |
| **Requiem-4** | `Requiem-4` | `pat-requiem.py` | `pat requiem 4` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2, Improved Poisons (+25% Poisons only) | Deathbell+Nightshade (Poison +25%); Briar Heart+Creep Cluster (Poison +25%); Blue Mountain Flower+Wheat (Elixir 0%) |
| **Requiem-5** | `Requiem-5` | `pat-requiem.py` | `pat requiem 5` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Alchemical Lore 1 + 2, Purification Process | Blue Mountain Flower+Wheat (Purified); Blue Mountain Flower+Blue Butterfly Wing (Purified); Salt Pile+Garlic |
| **Requiem-6** | `Requiem-6` | `pat-requiem.py` | `pat requiem 6` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: None (Unperked gate check) | Blue Mountain Flower+Wheat (Gate check); Deathbell+Nightshade (Gate check) |
| **Requiem-7** | `Requiem-7` | `pat-requiem.py` | `pat requiem 7` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Lore 1 + 2, Improved Elixirs (+25%), Improved Poisons (+25%) | Blue Mountain Flower+Wheat (Elixir +25%); Deathbell+Nightshade (Poison +25%); Salt Pile+Garlic (Elixir +25%) |
| **Requiem-8** | `Requiem-8` | `pat-requiem.py` | `pat requiem 8` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Lore 1 + 2, Improved Elixirs, Improved Poisons, Purification Process (Full tree) | Blue Mountain Flower+Wheat (Purified Elixir); Briar Heart+Creep Cluster (Improved Poison); Dragon's Tongue+Fly Amanita (Improved Elixir) |
| **Requiem-9** | `Requiem-9` | `pat-requiem.py` | `pat requiem 9` | AP disabled; Requiem enabled | InitMult 4.5, SkillFactor 1.8 | N/A (CACO disabled) | Skill 100, Fortify 50 (Peerless gear), Perks: Lore 1 + 2, All Requiem perks | Blue Mountain Flower+Wheat; Deathbell+Nightshade; Glowing Mushroom+Snowberries |
| **Requiem-10** | `Requiem-10` | `pat-requiem.py` | `pat requiem 10` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 50 (Level < 100), Fortify 50 (Peerless gear), Perks: Alchemical Lore 1 + 2 | Blue Mountain Flower+Wheat; Glowing Mushroom+Snowberries; Deathbell+Nightshade |
| **Requiem-11** | `Requiem-11` | `pat-requiem.py` | `pat requiem 11` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: REQ_RacialSkills_CreatePotionsUnperked active | Blue Mountain Flower+Wheat (Unperked keyword craft) |
| **Requiem-12** | `Requiem-12` | `pat-requiem.py` | `pat requiem 12` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A (CACO disabled) | Skill 100, Fortify 0, Perks: Lore 1 + 2, Improved Elixirs | Glowing Mushroom+Nightshade (Fortify Destruction x0.5 skill factor) |
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
| **Pred-Default-Vanilla** | `Vanilla-Default` | `pat-default-vanilla.py` | `pat default vanilla` | N/A (AP Disabled) | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Default-AP** | `AP-Default` | `pat-default-ap.py` | `pat default ap` | mag 25/5, dur 15/5, impureFix=True | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Default-CACO** | `CACO-Default` | `pat-default-caco.py` | `pat default caco` | N/A (AP Disabled) | InitMult 3.9, SkillFactor 1.0 | All 0s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Default-CACO+AP** | `CACO-AP-Default` | `pat-default-caco-ap.py` | `pat default caco-ap` | mag 25/5, dur 15/5, impureFix=True | InitMult 3.9, SkillFactor 1.0 | All 0s (Index 0), DisableHandling=1, ImpureProc=0 | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Default-Requiem** | `Requiem-Default` | `pat-default-requiem.py` | `pat default requiem` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A | Skill 100, Fortify 0, Perks: Alchemical Lore 1 | Full Potion Prediction Export |
| **Pred-Default-Apothecary** | `Apothecary-Default` | `pat-default-apothecary.py` | `pat default apothecary` | AP disabled; Apothecary enabled | InitMult 4.0, SkillFactor 1.5 | N/A | Skill 100, Fortify 0, Perks: None | Full Potion Prediction Export |
| **Pred-Changed-Vanilla** | `Vanilla-Changed` | `pat-vanilla-changed.py` | `pat vanilla changed` | N/A (AP Disabled) | InitMult 4.5, SkillFactor 1.8 | N/A | Skill 65, Fortify 50 (Peerless gear), Perks: Alchemist 3, Physician, Benefactor, Poisoner, Conc Poison, Seeker of Shadows | Full Potion Prediction Export |
| **Pred-Changed-AP** | `AP-Changed` | `pat-ap-changed.py` | `pat ap changed` | mag 10/2, dur 10/2, impureFix=False, overrides (0x3EB15) | InitMult 4.2, SkillFactor 1.6 | N/A | Skill 75, Fortify 50 (Peerless gear), Perks: Alchemist 4, Physician, Benefactor | Full Potion Prediction Export |
| **Pred-Changed-CACO** | `CACO-Changed` | `pat-caco-changed.py` | `pat caco changed` | N/A (AP Disabled) | InitMult 3.2, SkillFactor 2.8 | All 10s (Index 2), DisableHandling=1, ImpureProc=0 | Skill 55, Fortify 50 (Peerless gear), Perks: Alchemist 2, Physician, Poisoner | Full Potion Prediction Export |
| **Pred-Changed-CACO+AP** | `CACO-AP-Changed` | `pat-caco-ap-changed.py` | `pat caco-ap changed` | mag 30/6, dur 20/6, impureFix=True | InitMult 3.5, SkillFactor 2.5 | Mixed: RestH 5s, RestM 10s, RestS 0s, DmgH 10s, DmgM 5s, DmgS 0s, DisableHandling=1, ImpureProc=0 | Skill 85, Fortify 50 (Peerless gear), Perks: Alchemist 4, Physician, Benefactor, Poisoner | Full Potion Prediction Export |
| **Pred-Changed-Requiem** | `Requiem-Changed` | `pat-requiem-changed.py` | `pat requiem changed` | AP disabled; Requiem enabled | InitMult 4.0, SkillFactor 1.1 | N/A | Skill 75, Fortify 0, Perks: Lore 2, Improved Elixirs, Improved Poisons | Full Potion Prediction Export |
| **Pred-Changed-Apothecary** | `Apothecary-Changed` | `pat-apothecary-changed.py` | `pat apothecary changed` | AP disabled; Apothecary enabled | InitMult 4.5, SkillFactor 1.8 | N/A | Skill 65, Fortify 50 (Peerless gear), Perks: Alchemist 3 | Full Potion Prediction Export |

---

## AI Agent Reset Procedure

If other test tasks or agents modify `pa-console-tests/Source/Scripts/ProsperousAlchemistTests.psc`, `pa-console-tests/SKSE/CustomConsole/pa-tests.yaml`, or root `pat-*.py` scripts, an AI agent can restore the full minimal test suite by following these exact steps:

1. **Verify Console Definition (`pa-tests.yaml`)**:
   Ensure `pa-console-tests/SKSE/CustomConsole/pa-tests.yaml` contains subcommands for `default`, `vanilla`, `caco`, `ap`, `caco-ap`, `requiem`, `apothecary`, `vanilla-changed`, `ap-changed`, `caco-changed`, `caco-ap-changed`, `requiem-changed`, and `apothecary-changed` with optional `variant` string parameters. The help strings for `vanilla` (2-17), `caco` (2-18), `ap` (2-12), `caco-ap` (2-11), `requiem` (2-12), and `apothecary` (2-12) must cover all mode variants.
2. **Verify Papyrus Test Script (`ProsperousAlchemistTests.psc`)**:
   Ensure `pa-console-tests/Source/Scripts/ProsperousAlchemistTests.psc` implements all 82 in-game test block handlers in `ProvisionAndPrintTests` as specified in the technical matrix.
3. **Recompile Papyrus Script**:
   Execute the PowerShell build script:
   ```powershell
   cd pa-console-tests
   .\compile.ps1
   ```
4. **Verify Root Python Mode Scripts**:
   Ensure all 24 pre-launch mode scripts (`pat-ap.py`, `pat-ap-2.py`, `pat-ap-3.py`, `pat-ap-4.py`, `pat-vanilla.py`, `pat-caco.py`, `pat-caco-ap.py`, `pat-caco-ap-2.py`, `pat-caco-ap-3.py`, `pat-caco-ap-4.py`, `pat-requiem.py`, `pat-apothecary.py`, `pat-default-vanilla.py`, `pat-default-ap.py`, `pat-default-caco.py`, `pat-default-caco-ap.py`, `pat-default-requiem.py`, `pat-default-apothecary.py`, `pat-vanilla-changed.py`, `pat-ap-changed.py`, `pat-caco-changed.py`, `pat-caco-ap-changed.py`, `pat-requiem-changed.py`, `pat-apothecary-changed.py`) configure `AlchemyPlus.json` and MO2 `modlist.txt` accurately using `apply_mode_config` from `pat_config_helper.py`.
5. **Rebuild & Deploy SKSE Plugin**:
   Run `python build.py` from repository root and verify that the built and deployed DLL timestamps match.
6. **Final Verification Check**:
   Run `python verify_test_suite_alignment.py` and ensure output reports 100% PASS across all verification modules before completing work.
