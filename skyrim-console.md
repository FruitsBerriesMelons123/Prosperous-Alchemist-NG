# Skyrim Console Operations

## Batch Files (`bat`) Limitations
Skyrim's native `bat` command parser is notoriously fragile:
1. It struggles with sequentially rapid commands, large batches of `player.removeperk`/`player.addperk`, or complex syntax without crashing or throwing unrecognized command errors.
2. It fails when scripts are saved with Windows `\r\n` line endings instead of Unix `\n` line endings.
3. It cannot dynamically resolve load order form IDs (e.g., if CACO is loaded at `02` or `04`), making hardcoded `player.addperk 02xxxxxx` commands break whenever the load order changes.

## New Testing Methodology: `ConsoleUtil-Extended` + `PapyrusExtenderSSE`
To provide stable test execution, we utilize a custom Papyrus script bundled with a `ConsoleUtil-Extended` YAML configuration:
- **Test Suite Documentation & Plan**: See **test-suite.md** for full step-by-step instructions, chained console commands, and the AI agent reset procedure.
- **Papyrus Scripts**: Located in `pa-console-tests/Source/Scripts/ProsperousAlchemistTests.psc`. This script uses `PO3_SKSEFunctions` to safely manage perks and dynamically resolves load orders using `Game.GetFormFromFile`.
- **YAML Config**: Located in `pa-console-tests/SKSE/CustomConsole/pa-tests.yaml`. It registers the `pat` (Prosperous Alchemist Tests) root command in the console.

### Commands & Exact State Applied
Once compiled and deployed, you can use the following stable console commands to set up testing states:
- `pat vanilla [1..10, changed]` (or `pat v [1..10, changed]`):
  - **Block 1 (`pat vanilla`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 2 (`pat vanilla 2`):** Skill 100 | Fortify 0 | Perks: Alchemist 1 | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 3 (`pat vanilla 3`):** Skill 100 | Fortify 0 | Perks: Alchemist 3 | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 4 (`pat vanilla 4`):** Skill 100 | Fortify 0 | Perks: Alchemist 5 | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 5 (`pat vanilla 5`):** Skill 100 | Fortify 0 | Perks: Physician | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 6 (`pat vanilla 6`):** Skill 100 | Fortify 0 | Perks: Benefactor | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 7 (`pat vanilla 7`):** Skill 100 | Fortify 0 | Perks: Poisoner | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 8 (`pat vanilla 8`):** Skill 100 | Fortify 0 | Perks: Purity & Full Perks | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 9 (`pat vanilla 9`):** Skill 100 | Fortify 50 | Perks: Seeker of Shadows & Gear | `InitMult = 5.0`, `SkillFactor = 2.0`
  - **Block 10 (`pat vanilla 10`):** Skill 50 | Fortify 50 | Perks: Alchemist 2, Physician | `InitMult = 4.0`, `SkillFactor = 1.5`
- `pat ap [1..10, changed]` (or `pat a [1..10, changed]`):
  - **Block 1 (`pat ap`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 4.0`, `SkillFactor = 1.5` | AP Custom Rounding 10/2
  - **Block 2 (`pat ap 2`):** Skill 100 | Fortify 0 | Perks: Alchemist 3 | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 3 (`pat ap 3`):** Skill 100 | Fortify 0 | Perks: Physician, Benefactor | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 4 (`pat ap 4`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 4.0`, `SkillFactor = 1.5` | AP Default Rounding, ImpureFix=True
  - **Block 5 (`pat ap 5`):** Skill 100 | Fortify 0 | Perks: Poisoner | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 6 (`pat ap 6`):** Skill 100 | Fortify 0 | Perks: Purity | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 7 (`pat ap 7`):** Skill 100 | Fortify 0 | Perks: Full Tree | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 8 (`pat ap 8`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 5.0`, `SkillFactor = 2.0` | High Rounding 30/6
  - **Block 9 (`pat ap 9`):** Skill 100 | Fortify 50 | Perks: Gear & Perks | `InitMult = 4.5`, `SkillFactor = 1.8`
  - **Block 10 (`pat ap 10`):** Skill 50 | Fortify 50 | Perks: Skill 50 Non-100 | `InitMult = 4.0`, `SkillFactor = 1.5`
- `pat caco [1..10, changed]` (or `pat c [1..10, changed]`):
  - **Block 1 (`pat caco`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 5s (index 1)
  - **Block 2 (`pat caco 2`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 10s (index 2)
  - **Block 3 (`pat caco 3`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 5.0`, `SkillFactor = 2.0` | Durations = 0s (index 0)
  - **Block 4 (`pat caco 4`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 0s (index 0)
  - **Block 5 (`pat caco 5`):** Skill 100 | Fortify 0 | Perks: Alchemist 2 | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 5s (index 1)
  - **Block 6 (`pat caco 6`):** Skill 100 | Fortify 0 | Perks: Physician | `InitMult = 3.0`, `SkillFactor = 3.0` | Mixed Durations
  - **Block 7 (`pat caco 7`):** Skill 100 | Fortify 0 | Perks: Poisoner | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 10s (index 2)
  - **Block 8 (`pat caco 8`):** Skill 100 | Fortify 0 | Perks: Benefactor | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 5s (index 1)
  - **Block 9 (`pat caco 9`):** Skill 100 | Fortify 50 | Perks: Purity Gear | `InitMult = 3.0`, `SkillFactor = 3.0` | Mixed Durations
  - **Block 10 (`pat caco 10`):** Skill 50 | Fortify 50 | Perks: Skill 50 Non-100 | `InitMult = 3.0`, `SkillFactor = 3.0`
- `pat caco-ap [1..10, changed]` (or `pat ca [1..10, changed]`):
  - **Block 1 (`pat caco-ap`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 0s (index 0) | AP Default Rounding 25/5
  - **Block 2 (`pat caco-ap 2`):** Skill 100 | Fortify 0 | Perks: Alchemist 4 | `InitMult = 4.0`, `SkillFactor = 1.5` | Durations = 0s (index 0)
  - **Block 3 (`pat caco-ap 3`):** Skill 100 | Fortify 0 | Perks: Physician | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 5s (index 1)
  - **Block 4 (`pat caco-ap 4`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 5s (index 1) | AP Low Rounding 10/2
  - **Block 5 (`pat caco-ap 5`):** Skill 100 | Fortify 0 | Perks: Poisoner | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 10s (index 2)
  - **Block 6 (`pat caco-ap 6`):** Skill 100 | Fortify 0 | Perks: Benefactor | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 10s (index 2)
  - **Block 7 (`pat caco-ap 7`):** Skill 100 | Fortify 0 | Perks: Purity | `InitMult = 3.0`, `SkillFactor = 3.0` | Mixed Durations
  - **Block 8 (`pat caco-ap 8`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 5.0`, `SkillFactor = 2.0` | Durations = 10s (index 2) | High Rounding 30/6
  - **Block 9 (`pat caco-ap 9`):** Skill 100 | Fortify 50 | Perks: Full Tree | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 5s (index 1)
  - **Block 10 (`pat caco-ap 10`):** Skill 50 | Fortify 50 | Perks: Skill 50 Non-100 | `InitMult = 3.0`, `SkillFactor = 3.0` | Durations = 10s (index 2)
- `pat requiem [1..10, changed]` (or `pat r [1..10, changed]`):
  - **Block 1 (`pat requiem`):** Skill 100 | Fortify 0 | Perks: Alchemical Lore 1 | `InitMult = 4.0`, `SkillFactor = 1.1`
  - **Block 2 (`pat requiem 2`):** Skill 100 | Fortify 0 | Perks: Lore 1 + 2 | `InitMult = 4.0`, `SkillFactor = 1.1`
  - **Block 3 (`pat requiem 3`):** Skill 100 | Fortify 0 | Perks: Improved Elixirs Only | `InitMult = 4.0`, `SkillFactor = 1.1`
  - **Block 4 (`pat requiem 4`):** Skill 100 | Fortify 0 | Perks: Improved Poisons Only | `InitMult = 4.0`, `SkillFactor = 1.1`
  - **Block 5 (`pat requiem 5`):** Skill 100 | Fortify 0 | Perks: Purification Process Only | `InitMult = 4.0`, `SkillFactor = 1.1`
  - **Block 6 (`pat requiem 6`):** Skill 100 | Fortify 0 | Perks: No Lore Unperked Gate Check | `InitMult = 4.0`, `SkillFactor = 1.1`
  - **Block 7 (`pat requiem 7`):** Skill 100 | Fortify 0 | Perks: Improved Elixirs + Improved Poisons | `InitMult = 4.0`, `SkillFactor = 1.1`
  - **Block 8 (`pat requiem 8`):** Skill 100 | Fortify 0 | Perks: Full Tree | `InitMult = 4.0`, `SkillFactor = 1.1`
  - **Block 9 (`pat requiem 9`):** Skill 100 | Fortify 50 | Perks: Gear & Changed GameSettings | `InitMult = 4.5`, `SkillFactor = 1.8`
  - **Block 10 (`pat requiem 10`):** Skill 50 | Fortify 50 | Perks: Skill 50 Non-100 | `InitMult = 4.0`, `SkillFactor = 1.1`
- `pat apothecary [1..10, changed]` (or `pat apot [1..10, changed]`):
  - **Block 1 (`pat apothecary`):** Skill 100 | Fortify 0 | Perks: None | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 2 (`pat apothecary 2`):** Skill 100 | Fortify 0 | Perks: Alchemist 1 | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 3 (`pat apothecary 3`):** Skill 100 | Fortify 0 | Perks: Alchemist 3 | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 4 (`pat apothecary 4`):** Skill 100 | Fortify 0 | Perks: Alchemist 5 | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 5 (`pat apothecary 5`):** Skill 100 | Fortify 50 | Perks: Peerless Gear | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 6 (`pat apothecary 6`):** Skill 100 | Fortify 0 | Perks: Changed GameSettings | `InitMult = 4.5`, `SkillFactor = 1.8`
  - **Block 7 (`pat apothecary 7`):** Skill 100 | Fortify 0 | Perks: Fortify Skill & Regen Rate Branches | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 8 (`pat apothecary 8`):** Skill 100 | Fortify 0 | Perks: Restore Attribute & Generic Branches | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 9 (`pat apothecary 9`):** Skill 100 | Fortify 0 | Perks: Alchemist 2 Mixed | `InitMult = 4.0`, `SkillFactor = 1.5`
  - **Block 10 (`pat apothecary 10`):** Skill 50 | Fortify 50 | Perks: Skill 50 Non-100 | `InitMult = 4.0`, `SkillFactor = 1.5`
- `pat default <mode>` (or `pat d <mode>`):
  - Subcommand alias to apply canonical default state (Skill 100, Fortify 0, no perks) for any given mode (`vanilla`, `caco`, `ap`, `caco-ap`, `requiem`, `apothecary`). The Requiem default includes Alchemical Lore 1 so potions appear in the potion list.

---

## Critical Rules for Agents

### 1. Runtime State vs. External Configuration Files
- In-game console commands (and Papyrus scripts) **ONLY modify runtime engine state**:
  - Actor values (`player.SetActorValue`)
  - Perks (`player.AddPerk`, `player.RemovePerk`)
  - Spells / Active Effects (`player.AddSpell`, `player.RemoveSpell`)
  - Engine GameSettings (mutated via `ConsoleUtil.ExecuteCommand("setgs <Setting> <Value>")` in Papyrus test scripts; interactive `setgs` in console for manual human testing)
  - TESGlobal variables (mutated via native Papyrus `Game.GetFormFromFile(FormID, "Plugin.esp") as GlobalVariable` and `.SetValue(val)` in Papyrus test scripts)
- In-game console commands **CANNOT edit JSON/INI files on disk**:
  - `Alchemy Plus` reads its settings from `SKSE\Plugins\AlchemyPlus.json` on disk (e.g. `roundedPotency`, `magnitudeThreshold`, `overrides`). Running `pat ap` **does NOT and cannot alter this file**.
  - To configure external on-disk files (`AlchemyPlus.json`), MO2 enabled mods (`modlist.txt`), and backed up load order files (`plugins.txt`, `loadorder.txt`, `lockedorder.txt` from backups) for each mode before launching Skyrim, dedicated Python scripts are located in the repository root:
    - `python pat-vanilla.py`
    - `python pat-caco.py`
    - `python pat-ap.py`
    - `python pat-caco-ap.py`
    - `python pat-requiem.py` for Requiem blocks 1 and 2
    - `python pat-requiem-2.py` for Requiem blocks 3 and 4
  - Pre-launch Python scripts configure MO2 enabled plugins (`modlist.txt`), `AlchemyPlus.json`, and Requiem's enabled state on disk. Requiem scripts enable Requiem and disable CACO and Alchemy Plus. Every in-game `pat <mode> [variant]` command automatically handles 100% of state resetting and inventory cleanup at the beginning of the setup function in Papyrus (clearing all player ingredients, stripping all 14 alchemy perks & Seeker of Shadows, unequipping Fortify Alchemy gear & resetting actor values to 0, and resetting engine GameSettings & mod option globals) BEFORE provisioning 99 count of each required test ingredient for that block and logging test recipes line-by-line in the console. Running `pat <mode> [variant]` is completely self-contained with zero manual overhead for the user. If a `pat` command is executed while already inside the Alchemy Lab UI, press **F** while the Alchemy Lab menu is focused to refresh and display the newly provisioned ingredient list without exiting the lab.
  - Instruct the user to run the appropriate Python script on disk before starting Skyrim for each test mode.

### 2. Alchemy Plus Has No ESP Plugin
- `Alchemy Plus` is a pure SKSE DLL plugin (`AlchemyPlus.dll`). There is **NO `AlchemyPlus.esp`**.

### 3. Return Values in CustomConsole
- `ConsoleUtil-Extended` prints the return value of any Papyrus function called from a console command.
- All `pat` functions return a descriptive `string`.

### 4. Mod Global Variables vs. Engine GameSettings in Papyrus Test Scripts
- **Mod Global Variables (`TESGlobal`): NEVER use `ConsoleUtil.ExecuteCommand("set <Global_EditorID> to <val>")`.**
- **Engine GameSettings (`GMST`): Use `ConsoleUtil.ExecuteCommand("setgs <Setting> <val>")`.** This is the pattern used by `ProsperousAlchemistTests.psc`; do not replace it with the nonexistent Papyrus API `Utility.SetGameSettingFloat`.

### 5. Mandatory Recipe Craftability Validation (`validate_ingredient_combination`)
- Always validate candidate ingredient pairs/trios using `validate_ingredient_combination(ingredients, caco_enabled, requiem_enabled)` in `pat_config_helper.py` before adding them to `ProsperousAlchemistTests.psc` or presenting test plans to the user.
- Use `ingredients-requiem.csv` when `requiem_enabled=True`, `ingredients-caco.csv` when CACO is enabled, and `ingredients-vanilla.csv` otherwise.
- Ensure every ingredient pair shares at least one alchemy effect and produces a valid craftable potion/poison in Skyrim. Never guess ingredient combinations.

---

## FormID Reference Guide for Alchemy

Always use these verified FormIDs in Papyrus scripts and tests:

| Form Name | Type | FormID | Source Plugin | Notes |
|---|---|---|---|---|
| **Alchemist Rank 1 / Alchemical Lore 1** | Perk | `0x000BE127` | `Skyrim.esm` | Vanilla rank 1 or Requiem Alchemical Lore 1 |
| **Alchemist Rank 2 / Alchemical Lore 2** | Perk | `0x000C07CA` | `Skyrim.esm` | Vanilla rank 2 or Requiem Alchemical Lore 2 |
| **Alchemist Rank 3** | Perk | `0x000C07CB` | `Skyrim.esm` | +60% potion/poison strength |
| **Alchemist Rank 4** | Perk | `0x000C07CC` | `Skyrim.esm` | +80% potion/poison strength |
| **Alchemist Rank 5** | Perk | `0x000C07CD` | `Skyrim.esm` | +100% potion/poison strength |
| **Physician** | Perk | `0x00058215` | `Skyrim.esm` | +25% restore health/magicka/stamina |
| **Benefactor** | Perk | `0x00058216` | `Skyrim.esm` | +25% beneficial potion strength |
| **Poisoner** | Perk | `0x00058217` | `Skyrim.esm` | +25% poison strength/duration |
| **Purification Process / Purity** | Perk | `0x0005821D` | `Skyrim.esm` | Requiem purification and vanilla purity behavior |

---

### Automated Compilation
Agents MUST update `ProsperousAlchemistTests.psc` and automatically recompile via `compile.ps1` BEFORE presenting test prompts or instructions to the user whenever new test blocks, ingredient sets, or console output recipes are requested.
A PowerShell build script `compile.ps1` is provided in the `pa-console-tests/` directory:
```powershell
cd pa-console-tests
.\compile.ps1
```
