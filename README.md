# Prosperous Alchemist NG

Prosperous Alchemist NG is an SKSE plugin for Skyrim Special Edition, Anniversary Edition, and Skyrim VR. It looks at the ingredients in the player's inventory and shows the most valuable potions and poisons they can craft, in an overlay next to Skyrim's native alchemy menu.

![Prosperous Alchemist preview](Prosperous-Alchemist-NG.jfif)

This README is for developers who want to build, test, and change the plugin. Players should read the [user guide](docs/USER_README.md) and download the mod from [Nexus Mods](https://www.nexusmods.com/skyrimspecialedition/mods/33059).

- Source: [FruitsBerriesMelons123/Prosperous-Alchemist-NG](https://github.com/FruitsBerriesMelons123/Prosperous-Alchemist-NG)
- Original Skyrim LE mod: [Prosperous Alchemist](https://www.nexusmods.com/skyrim/mods/38634)
- Changelog: [docs/CHANGELOG.md](docs/CHANGELOG.md)

## Contents

- [Project overview](#project-overview)
- [Repository layout](#repository-layout)
- [Development environment setup](#development-environment-setup)
- [Build, deploy, and package](#build-deploy-and-package)
- [Test environment setup](#test-environment-setup)
- [Test workflow](#test-workflow)
- [Offline validation](#offline-validation)
- [Working with an AI coding agent](#working-with-an-ai-coding-agent)
- [Configuration, profiles, and developer mode](#configuration-profiles-and-developer-mode)
- [Troubleshooting](#troubleshooting)
- [Related projects](#related-projects)
- [License and credits](#license-and-credits)

## Project overview

### Runtime model

- The plugin is a native C++ SKSE plugin built with [CommonLibSSE-NG](https://github.com/alandtse/CommonLibSSE-NG). One DLL supports SE, AE, and VR through the Address Library. Players still need a matching [SKSE](https://skse.silverlock.org/) and [Address Library for SKSE Plugins](https://www.nexusmods.com/skyrimspecialedition/mods/32444) (or [VR Address Library](https://www.nexusmods.com/skyrimspecialedition/mods/58101)).
- The overlay is drawn with [Dear ImGui](https://github.com/ocornut/imgui) through a D3D11 render hook. It needs Skyrim's native alchemy menu. [SkyUI](https://www.nexusmods.com/skyrimspecialedition/mods/12604) is supported but not required. The mod has no ESP/ESL and no replacement Scaleform files.
- On Skyrim VR the overlay renders to the desktop mirror window.
- Release builds link their third-party C++ dependencies statically, so the plugin does not need `fmt.dll`, `spdlog.dll`, or a zstd DLL next to it.

### How the plugin works

When the native alchemy submenu opens, the plugin takes a snapshot of the loaded ingredient forms, inventory counts, player state (Alchemy skill, perks, Fortify Alchemy), and the settings of any supported overhaul. It then evaluates eligible ingredient pairs and trios on background threads, applies the protection rules and the active compatibility calculation, and caches the result in memory. It never crafts items, consumes ingredients, edits game records, or writes to the save file.

### Compatibility modes

The active mode depends on the mods and settings that are actually loaded. Having a mod installed does not always turn on its adapter. For example, Alchemy Plus needs its DLL and a readable `AlchemyPlus.json`.

| Mode | Adapter source | Notes |
| --- | --- | --- |
| Vanilla | `alchemist/Vanilla/` | Loaded Skyrim ingredient and effect records with the vanilla alchemy formula. |
| [Alchemy Plus](https://www.nexusmods.com/skyrimspecialedition/mods/80882) (AP) | `alchemist/AlchemyPlus/` | Applies magnitude and duration rounding (thresholds, multiples, and per-effect overrides) and the impure-cost fix from `SKSE/Plugins/AlchemyPlus.json` when `AlchemyPlus.dll` is loaded. |
| [CACO](https://www.nexusmods.com/skyrimspecialedition/mods/19924) | `alchemist/CACO/` | Loaded CACO records and live MCM globals, including duration-variant resolution. See [caco.md](caco.md). |
| CACO + AP | CACO and AP adapters | The only supported mixed-overhaul combination. CACO calculates the effects and AP adjusts the value. |
| [Requiem](https://www.nexusmods.com/skyrimspecialedition/mods/60888) | `alchemist/Requiem/` | Requiem records, alchemy effectiveness, Alchemical Lore ranks, and perk/keyword gates. Must not be combined with CACO or AP. |
| [Apothecary](https://www.nexusmods.com/skyrimspecialedition/mods/52130) | `alchemist/Apothecary/` | Loaded Apothecary records and keyword-based effectiveness scaling. AP behavior is not applied. |

The predictions model each mod's mechanics from loaded records and supported settings. They do not run each mod's scripted post-craft changes. CACO potion handling is not supported for automated capture: `CACO_OptionDisableAllPotionHandling` must stay `1` and `CACO_OptionImpurePotions` must stay `0` during testing.

## Repository layout

| Path | Purpose |
| --- | --- |
| `alchemist/` | CMake project for the plugin: `src/`, `include/`, the per-mode adapters (`Vanilla/`, `AlchemyPlus/`, `CACO/`, `Requiem/`, `Apothecary/`), `version.rc`, and `CMakeLists.txt`. |
| `cmake/imgui-reusable/` | CMake wrapper that builds and installs Dear ImGui as a static, reusable package. |
| `locales/` | Bundled translation JSON files and the locale schema ([locales/README.md](locales/README.md)). |
| `fonts/` | Instructions for optional multilingual fonts ([fonts/README.md](fonts/README.md)). |
| `docs/` | [USER_README.md](docs/USER_README.md), the player guide that becomes the Nexus description, and [CHANGELOG.md](docs/CHANGELOG.md). |
| `licenses/`, `COPYING`, `EXCEPTIONS.md` | Project license, exceptions, and third-party notices. |
| `build.py` | The supported entry point for building, deploying, and packaging. |
| `config.example.py`, `user-paths.example.md`, `pa-console-tests/compile-paths.example.ps1` | Templates for the git-ignored, machine-specific `config.py`, `user-paths.md`, and `pa-console-tests/compile-paths.ps1`. |
| `potion_prediction_test.py`, `potion_prediction_baseline.json` | Offline prediction harness and the baseline of passing rows used for regression checks. |
| `ingredients-*.csv` | Ingredient and effect snapshots for Vanilla, CACO, Requiem, and Apothecary, used by the harness and by recipe validation. |
| `db/`, `build_ingredient_db.py` | Canonical ingredient database generated from game plugins and the snapshots. |
| `pat-*.py`, `pat_config_helper.py` | Pre-launch scripts that set up the MO2 mod list, `plugins.txt`, and `AlchemyPlus.json` for each test mode. |
| `pa-console-tests/` | Papyrus source and CustomConsole YAML for the in-game `pat` command, plus `compile.ps1` and `compile-paths.example.ps1`. |
| `sync_potion_predictions.py`, `save_predicted_*_settings.py`, `toggle-predicted-settings.py`, `tail_predicted.py` | Helpers for prediction-export fixtures (`potions-predicted-*.csv.zst`). |
| `reset_saves_and_start_skyrim.py` | Clears the test profile's saves and launches SKSE through MO2. |
| `verify_*.py` | Consistency checks between the test scripts, compiled commands, and `test-suite.md`. |
| `test-suite.md`, `potion-prediction-default-settings.md`, `potion-order-dependent-observations.md`, `skyrim-console.md`, `caco.md` | Test specifications, capture defaults, and research notes. |
| `AGENTS.md` | Project rules for AI coding agents. |
| `build-alchemist/`, `dist/` | Generated build tree and release archives. Not source-controlled. |

## Development environment setup

The build runs on Windows only.

### 1. Install the toolchain

| Tool | Notes |
| --- | --- |
| [Visual Studio](https://visualstudio.microsoft.com/downloads/) or Build Tools | The "Desktop development with C++" workload (MSVC x64) and a Windows 10/11 SDK. `build.py` finds MSVC through `vswhere` and sets up the x64 environment itself. |
| [Python](https://www.python.org/downloads/) 3.10+ | Runs the build and test scripts. Run `pip install zstandard` so the harness can read `.csv.zst` prediction exports. |
| [CMake](https://cmake.org/download/) 3.21+ | |
| [Ninja](https://github.com/ninja-build/ninja/releases) | The generator used for every CMake build. |
| [Git](https://git-scm.com/) | |
| [vcpkg](https://github.com/microsoft/vcpkg) | Supplies the static C++ dependencies. |
| [md2nexus](https://github.com/ceejbot/md2nexus/releases/latest) | Optional. Converts the user guide to Nexus BBCode when packaging. |

### 2. Get the external source dependencies

Keep all of these outside this repository.

**CommonLibSSE-NG.** Clone [alandtse/CommonLibSSE-NG](https://github.com/alandtse/CommonLibSSE-NG) with its submodules:

```bash
git clone --recurse-submodules https://github.com/alandtse/CommonLibSSE-NG.git
```

`build.py` configures, builds, and installs it into the source, build, and install directories you set in `config.py` (SE, AE, and VR enabled, static MSVC runtime, tests off).

**Dear ImGui.** Check out the version the project uses (v1.91.9b):

```bash
git clone --branch v1.91.9b --depth 1 https://github.com/ocornut/imgui.git
```

`build.py` builds it with the wrapper in `cmake/imgui-reusable/` and installs it to `IMGUI_INSTALL_DIR`.

**vcpkg packages.** Install CommonLibSSE-NG's manifest dependencies (directxmath, directxtk, fmt, nlohmann-json, rapidcsv, simpleini, spdlog, toml11, xbyak) for the `x64-windows-static` triplet into a project-specific install root under your vcpkg tool root. Then add `zstd` to the same root. It is not in CommonLibSSE-NG's manifest, but the plugin links against it.

```bash
vcpkg install --x-manifest-root=<CommonLibSSE-NG checkout> --x-install-root=<vcpkg root>/installed/prosperous-alchemist-commonlib --triplet x64-windows-static
```

```bash
vcpkg install zstd:x64-windows-static --classic --x-install-root=<vcpkg root>/installed/prosperous-alchemist-commonlib
```

Install zstd after the manifest install, because a manifest install removes packages that the manifest does not list. The static prefix (`.../prosperous-alchemist-commonlib/x64-windows-static`) must sit under the vcpkg tool root and outside this repository; `build.py` checks both.

### 3. Create the local configuration

Copy the templates to their git-ignored local names and replace every path with one from your machine:

```bash
cp config.example.py config.py
```

```bash
cp user-paths.example.md user-paths.md
```

```bash
cp pa-console-tests/compile-paths.example.ps1 pa-console-tests/compile-paths.ps1
```

`config.py` feeds the Python scripts. `user-paths.md` is the human- and agent-readable version of the same locations. `compile-paths.ps1` feeds `pa-console-tests/compile.ps1` for compiling test scripts. Keep them in sync with your machine paths and never commit local configuration files. The settings that matter most:

| Setting | Used for |
| --- | --- |
| `CMAKE_DIR`, `NINJA_DIR` | Tool locations. `NINJA_DIR` is added to `PATH` during the build. |
| `COMMONLIBSSE_SOURCE`, `COMMONLIBSSE_BUILD_DIR`, `COMMONLIBSSE_INSTALL_DIR` | CommonLibSSE-NG checkout, build tree, and install prefix. |
| `IMGUI_SOURCE_DIR`, `IMGUI_BUILD_DIR`, `IMGUI_INSTALL_DIR` | Dear ImGui checkout, build tree, and install prefix. |
| `VCPKG_ROOT`, `VCPKG_STATIC_INSTALL_ROOT`, `VCPKG_STATIC_DIR` | vcpkg tool root and the project's static package prefix. The download and binary caches default to folders under `VCPKG_ROOT`. |
| `DLL_DEPLOY` | Where `alchemist.dll` goes, normally `<MO2 instance>/mods/Prosperous Alchemist NG/SKSE/Plugins/alchemist.dll`. |
| `MD2NEXUS` | md2nexus executable, used for packaging. |
| `MO2_PROFILE`, `MO2_EXECUTABLE`, `MO2_SKSE_SHORTCUT`, `MO2_SAVES_DIR` | MO2 instance used by the test scripts. |
| `*_MOD_DIR`, `CACO_SETTINGS` | MO2 mod folders for each supported overhaul and the live `AlchemyPlus.json`, which the `pat-*.py` scripts switch between. |
| `BACKUP_LOADORDER`, `BACKUP_LOCKEDORDER`, `BACKUP_PLUGINS` | Backed-up MO2 load-order files used to restore the test profile. |
| `SKYRIM`, `SKYRIM_LOGS` | Game install and the `Documents/My Games/Skyrim Special Edition/SKSE` log directory. |
| `CAPRICA_DIR`, `CREATION_KIT_DIR` | Papyrus compiler and the extracted vanilla script sources used for the test scripts. |
| `*_SOURCE` | Optional reference checkouts (see [Related projects](#related-projects)). |

## Build, deploy, and package

Build and deploy with:

```powershell
python build.py
```

Each run:

1. Configures, builds, and installs Dear ImGui and CommonLibSSE-NG (Release, Ninja). These are incremental and are not rebuilt unless they change.
2. Configures `alchemist/` in `build-alchemist/` and removes only the plugin outputs. The CommonLibSSE-NG artifacts are never cleaned.
3. Builds `build-alchemist/alchemist.dll` and `alchemist.pdb` and checks that both are newer than the build start time.
4. Copies the DLL, PDB, and `locales/` to the folder containing `DLL_DEPLOY`, then checks that the deployed files match the built ones.

Progress is written, and flushed as it goes, to `build.log`. If Skyrim is running, deployment fails because the DLL is locked; close Skyrim and run the build again.

Create a release archive:

```powershell
python build.py --package
```

This builds, deploys, converts `docs/USER_README.md` to Nexus BBCode in `dist/`, and writes `dist/Prosperous-Alchemist-NG-v<version>.zip`. The archive contains the DLL, PDB, default `alchemist.ini`, locale and font READMEs, locale files, the license files, and the user guide. To regenerate only the BBCode description:

```powershell
python build.py --md2nexus
```

### Versioning

The version comes from `alchemist/include/version.h` (the `MYFP_VERSION_*` macros) and from both `VERSION` arguments in `alchemist/CMakeLists.txt`. `version.rc`, the generated CMake files, the DLL metadata, and the archive name are all derived from those. Change the two source files together and rebuild; never edit the generated outputs by hand.

## Test environment setup

The in-game tests run in a dedicated Mod Organizer 2 instance so test changes never touch a normal playthrough.

### Mods

Install and enable these in the MO2 test profile:

| Mod | Why it is needed |
| --- | --- |
| [SKSE64](https://www.nexusmods.com/skyrimspecialedition/mods/30379) ([skse.silverlock.org](https://skse.silverlock.org/)) with its Papyrus scripts | Loads the plugin. The script sources are imported when compiling the tests. |
| [Address Library for SKSE Plugins](https://www.nexusmods.com/skyrimspecialedition/mods/32444) | Runtime offsets. |
| [ConsoleUtil Extended](https://www.nexusmods.com/skyrimspecialedition/mods/133569) ([GitHub](https://github.com/KrisV-777/ConsoleUtil-Extended)) | Custom console commands via Papyrus and CustomConsole YAML. Provides `pat`. |
| [Extended Console](https://www.nexusmods.com/skyrimspecialedition/mods/133570) ([GitHub](https://github.com/KrisV-777/Extended-Console)) | Reference and companion CustomConsole commands. |
| [powerofthree's Papyrus Extender](https://www.nexusmods.com/skyrimspecialedition/mods/22854) ([GitHub](https://github.com/powerof3/PapyrusExtenderSSE)) | Inventory sweeps and perk functions used by the test script. |
| Prosperous Alchemist NG | The folder `DLL_DEPLOY` points into. `compile.ps1` also puts the test script and YAML here. |
| [Alchemy Plus](https://www.nexusmods.com/skyrimspecialedition/mods/80882) | AP and CACO+AP modes. |
| [Complete Alchemy & Cooking Overhaul](https://www.nexusmods.com/skyrimspecialedition/mods/19924) | CACO and CACO+AP modes. |
| [kryptopyr's Patch Hub](https://www.nexusmods.com/skyrimspecialedition/mods/19518) (Automated Patches) | Standardizes Creation Club Rare Curios ingredients with CACO. |
| [Requiem](https://www.nexusmods.com/skyrimspecialedition/mods/60888) | Requiem mode. |
| [Apothecary](https://www.nexusmods.com/skyrimspecialedition/mods/52130) | Apothecary mode. |

[SkyUI](https://www.nexusmods.com/skyrimspecialedition/mods/12604) is optional but helps with CACO's MCM. The `pat-*.py` scripts switch the overhaul mods on and off, so a test run only has the intended mode's mods active.

```text
<MO2 instance>/
  mods/
    Prosperous Alchemist NG/
      SKSE/Plugins/alchemist.dll          (build.py)
      SKSE/Plugins/locales/               (build.py)
      SKSE/CustomConsole/pa-tests.yaml    (compile.ps1)
      Scripts/ProsperousAlchemistTests.pex (compile.ps1)
    ConsoleUtil-Extended/
    Extended-Console/
    Papyrus Extender/
    Alchemy Plus/
    Complete Alchemy & Cooking Overhaul/
    kryptopyr's Automated Patches/
    Requiem - The Roleplaying Overhaul/
    Apothecary - An Alchemy Overhaul/
  profiles/<test profile>/
```

Folder names can differ; the scripts use whatever paths `config.py` gives them.

### Compile the `pat` console command

`pa-console-tests/` holds the Papyrus source (`Source/Scripts/ProsperousAlchemistTests.psc`) and the command definition (`SKSE/CustomConsole/pa-tests.yaml`). Compile and deploy them with [Caprica](https://github.com/Orvid/Caprica):

```powershell
pwsh pa-console-tests/compile.ps1
```

`compile.ps1` loads its machine-specific paths from `pa-console-tests/compile-paths.ps1` (git-ignored). Copy `pa-console-tests/compile-paths.example.ps1` to `pa-console-tests/compile-paths.ps1` and update your machine paths before compiling (the Caprica executable, `TESV_Papyrus_Flags.flg`, the SKSE, vanilla, Papyrus Extender, and ConsoleUtil Extended script imports, and the output mod folder). The vanilla script sources and the flags file come from the Creation Kit's `Scripts.zip`. See [skyrim-console.md](skyrim-console.md) for how the command works.

### Developer mode

Set `developer = 1` in the active profile's section of the deployed `alchemist.ini` to turn on the Developer Test Hub and the capture of confirmed potions. When crafting in that mode, the plugin logs each crafted item to `alchemist.potions-confirmed.csv` (next to the DLL) along with the full player, perk, GameSetting, and mod-setting state. Developer actions can change the live character, so use them only on a test character.

## Test workflow

[test-suite.md](test-suite.md) is the full test plan, with 156 in-game blocks across all modes plus a prediction-export phase. It has two tiers:

1. **Pre-launch disk setup (Skyrim closed).** Run the mode's script, for example `python pat-vanilla.py`, `python pat-ap-2.py`, or `python pat-caco-ap.py`. It enables only that mode's mods in the MO2 profile, syncs `plugins.txt`, and writes `AlchemyPlus.json`. Modes with no settings on disk use a single script; AP and CACO+AP use one script per JSON configuration.
2. **In-game blocks (one Skyrim session).** Launch SKSE through MO2 (or run `python reset_saves_and_start_skyrim.py`), open the console, and run `pat <mode> [n]`, for example `pat vanilla`, `pat caco 3`, or `pat requiem 5`. Each command clears ingredients, perks, Fortify Alchemy gear, GameSettings, and mod globals, applies the block's state, gives 99 of each required ingredient, and prints the recipes to craft and the next command. If the alchemy menu is already open, press **F** to refresh the ingredient list.

The supported modes are `vanilla`, `ap`, `caco`, `caco-ap`, `requiem`, and `apothecary`. The final phase uses `pat-default-<mode>.py` and `pat-<mode>-changed.py` to export full prediction files (`potions-predicted-*.csv.zst`). Afterwards, `sync_potion_predictions.py`, `save_predicted_default_settings.py`, `save_predicted_changed_settings.py`, and `toggle-predicted-settings.py` copy those exports into the repository fixtures and switch between them.

Before designing new test recipes, check them with `validate_ingredient_combination` in `pat_config_helper.py` against both the target mode's snapshot and `ingredients-vanilla.csv`. Resolve every FormID from the real plugins or snapshots, and use `Game.GetFormFromFile` in Papyrus. [potion-prediction-default-settings.md](potion-prediction-default-settings.md) lists the baseline settings for each mode.

Files the game produces (`alchemist.potions-confirmed*.csv`, `alchemist.potion-observations.csv`, `potions-predicted-*`) count as evidence. You can back them up or move them, but never edit or rewrite them; regenerate them in game instead.

## Offline validation

`potion_prediction_test.py` runs the same analytical model as the plugin, using the ingredient snapshots, and compares it with in-game observations.

```powershell
python potion_prediction_test.py --check-confirmed-csv --check-baseline
```

That command checks every confirmed craft row and reports a regression if a row listed in `potion_prediction_baseline.json` no longer passes. After you validate new rows or change the model on purpose, record a new baseline:

```powershell
python potion_prediction_test.py --check-confirmed-csv --record-baseline
```

Other useful modes: `--check-confirmed-row <N>` checks a single row, `--check-predicted-csv` checks a prediction export, and passing two or three ingredient names with flags such as `--caco-enabled`, `--purity`, or `--ap-magnitude-threshold` predicts one recipe. Run `python potion_prediction_test.py --help` for the full list.

When the C++ prediction code changes, rebuild, deploy, and re-export predictions in game before checking prediction files. Otherwise you are validating stale exports.

## Working with an AI coding agent

Open the repository root as the agent's workspace. [AGENTS.md](AGENTS.md) holds the project rules: no git commits, no manual edits to game-generated files, explicit permission before any version bump, and the test and FormID verification rules. It points the agent to `user-paths.md` for every machine-specific location. Give the agent file-system access to the MO2 instance, the reference checkouts, and Caprica.

The agent can edit sources, build and deploy, compile the `pat` scripts, and run the `pat-*.py` and validation scripts. It cannot play the game: you launch Skyrim through MO2, run the `pat` commands it gives you, craft, and then ask it to validate the new rows. `failed-commands.md` records shell commands that failed before in this environment so they are not retried.

## Configuration, profiles, and developer mode

The plugin creates `Data/SKSE/Plugins/alchemist.ini` on first run. All settings live in named profiles in that file, never in the save. `[Profiles]` maps each Skyrim Character ID to the profile it used last. The player-facing settings are listed in the [user guide](docs/USER_README.md). Settings only relevant to development:

| Key | Default | Meaning |
| --- | --- | --- |
| `developer` | `0` | Enables the Developer Test Hub, confirmed-potion capture, inventory observation, and quest-scan diagnostics. |
| `singleprofile` | `0` | Forces the lowest-numbered profile with this flag set onto every character. |
| `autoprovision` | empty | Obsolete; the `pat` commands handle provisioning now. |
| `Player`, `CACO`, `AlchemyPlus`, `Requiem` | managed | Snapshots the plugin refreshes from live data. They are not prediction overrides. |

Restart Skyrim after editing the INI by hand.

## Troubleshooting

- **Build: missing `config.py`.** Copy `config.example.py` to `config.py` and fill in real paths.
- **Compile: missing `compile-paths.ps1`.** Copy `pa-console-tests/compile-paths.example.ps1` to `pa-console-tests/compile-paths.ps1` and set your machine paths.
- **Build: invalid vcpkg or ImGui layout.** The static prefix must be under `VCPKG_ROOT` and outside the repository, and the ImGui build and install folders must not sit inside the ImGui source tree.
- **Build: `zstd` or `nlohmann_json` package not found.** Install the missing package into the same `x64-windows-static` prefix (see step 2).
- **Build: deployment failed.** Skyrim is holding the DLL. Close it and build again.
- **Plugin does not load.** Check the newest `alchemist.log` and `skse64.log` in `SKYRIM_LOGS`, confirm that SKSE and Address Library match the game runtime, and confirm MO2 is running the right profile with the mod enabled.
- **Stale behavior in game.** Compare the timestamp and hash of `build-alchemist/alchemist.dll` with the DLL that MO2 actually loads.
- **`pat` is an unknown command.** Make sure ConsoleUtil Extended and Papyrus Extender are enabled and that `pa-tests.yaml` and `ProsperousAlchemistTests.pex` are in the enabled mod folder. Then run `compile.ps1` again.
- **Harness cannot read `.zst` files.** Run `pip install zstandard`.

## Related projects

| Project | Links | Role |
| --- | --- | --- |
| Prosperous Alchemist (LE original) | [Nexus](https://www.nexusmods.com/skyrim/mods/38634) | The Skyrim LE mod this plugin rewrites. |
| Prosperous Alchemist NG | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/33059) · [GitHub](https://github.com/FruitsBerriesMelons123/Prosperous-Alchemist-NG) | This project. |
| SKSE64 | [Website](https://skse.silverlock.org/) · [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/30379) | Script extender runtime. |
| Address Library for SKSE Plugins | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/32444) · [VR](https://www.nexusmods.com/skyrimspecialedition/mods/58101) | Runtime address database. |
| CommonLibSSE-NG | [GitHub (alandtse)](https://github.com/alandtse/CommonLibSSE-NG) · [GitHub (CharmedBaryon)](https://github.com/CharmedBaryon/CommonLibSSE-NG) | Reverse-engineered game library. |
| Dear ImGui | [GitHub](https://github.com/ocornut/imgui) | Overlay UI. |
| nlohmann/json | [GitHub](https://github.com/nlohmann/json) | JSON parsing. |
| Zstandard | [GitHub](https://github.com/facebook/zstd) | Compressed prediction exports. |
| spdlog | [GitHub](https://github.com/gabime/spdlog) | Logging, through CommonLibSSE-NG. |
| DirectXTK | [GitHub](https://github.com/microsoft/DirectXTK) | D3D helpers, through CommonLibSSE-NG. |
| vcpkg | [GitHub](https://github.com/microsoft/vcpkg) | C++ package manager. |
| md2nexus | [GitHub](https://github.com/ceejbot/md2nexus) | Markdown to Nexus BBCode. |
| Mod Organizer 2 | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/6194) · [GitHub](https://github.com/ModOrganizer2/modorganizer) | Test environment. |
| SSEEdit (xEdit) | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/164) · [GitHub](https://github.com/TES5Edit/TES5Edit) | Inspecting records and FormIDs. |
| Caprica | [GitHub](https://github.com/Orvid/Caprica) | Papyrus compiler. |
| ConsoleUtil Extended | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/133569) · [GitHub](https://github.com/KrisV-777/ConsoleUtil-Extended) | Custom console commands. |
| Extended Console | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/133570) · [GitHub](https://github.com/KrisV-777/Extended-Console) | CustomConsole YAML examples. |
| powerofthree's Papyrus Extender | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/22854) · [GitHub](https://github.com/powerof3/PapyrusExtenderSSE) | Papyrus functions used by the tests. |
| powerofthree's Tweaks | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/51073) · [GitHub](https://github.com/powerof3/po3-Tweaks) | Reference for engine hooks. |
| SkyUI | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/12604) · [GitHub (community)](https://github.com/doodlum/SkyUI-Community) | Optional UI framework. |
| Alchemy Plus | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/80882) · [GitHub](https://github.com/Exit-9B/AlchemyPlus) | Supported overhaul. |
| Complete Alchemy & Cooking Overhaul | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/19924) | Supported overhaul. |
| CACO Potion Builder | [GitHub](https://github.com/dhildebr/caco-potion-builder) | Reference for CACO potion mechanics. |
| kryptopyr's Patch Hub | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/19518) | CACO and Rare Curios patches. |
| Requiem | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/60888) · [GitHub](https://github.com/ProbablyManuel/requiem) | Supported overhaul. |
| Apothecary – An Alchemy Overhaul | [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/52130) | Supported overhaul. |
| Quest Tracker NG | [GitHub](https://github.com/wtarking-cell/QuestTrackerNG) | Reference for quest-related code. |

## License and credits

Prosperous Alchemist is licensed under the [GNU General Public License version 3 or later](COPYING), with the [Modding Exception and GPL-3.0 Linking Exception](EXCEPTIONS.md). Third-party notices are in [licenses/](licenses/README.md).

Credits go to the SKSE team, the CommonLibSSE-NG contributors, Dear ImGui, nlohmann/json, and Zstandard; to the authors of the supported overhauls and the testing tools listed above; and to the contributors and translators credited in the project and resource notices.
