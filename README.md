# Prosperous Alchemist NG

Prosperous Alchemist NG is an SKSE plugin for Skyrim Special Edition, Anniversary Edition, and Skyrim VR. It analyzes the ingredients in the player's inventory and recommends valuable craftable potions and poisons in an overlay beside Skyrim's native alchemy menu.

![Prosperous Alchemist preview](Prosperous-Alchemist-NG.jfif)

For player-facing installation, configuration, and usage, see the [user guide](docs/USER_README.md).

## Project status and requirements

- The project builds a native C++ SKSE plugin with CommonLibSSE-NG and Address Library support. A matching SKSE installation and Address Library runtime file are still required; runtime independence does not mean Address Library is optional.
- Skyrim's native alchemy menu and D3D11 renderer are required. SkyUI is supported but optional. No ESP/ESL or replacement Scaleform files are required.
- Skyrim VR is supported. The overlay renders to the desktop mirror window; view it in-headset through SteamVR Desktop View or a compatible desktop overlay.
- Release builds statically link their third-party C++ dependencies; separate `fmt.dll` or `spdlog.dll` files are not required beside the plugin.
- A source checkout is not an installer and does not include a tracked compiled plugin DLL. The build script can create and deploy the DLL and package a release archive.

## Features

- Searches ingredient pairs and trios, then sorts and displays valid recommendations by estimated item value.
- Uses the actual loaded ingredient forms, inventory, player Alchemy state, relevant perks, and Fortify Alchemy equipment unless **Ignore player state** is enabled.
- Distinguishes potions from poisons and displays effect names and calculated magnitude/duration where available.
- Provides recipe search, four sort modes, pagination, an optional Effects column, and a filter based on ingredients selected in the native alchemy menu.
- Offers optional ingredient protection and tracking for custom reservations, ingredient effects, detected craftable-item requirements, quest requirements, and Atronach Forge recipes.
- Uses an in-memory recipe cache and background evaluation by default, with configurable recalculation behavior and a single-threaded option.
- Includes localized interface resources and profile-specific preferences.

Recommendations are analytical estimates. The plugin does not automatically craft items, consume ingredients, modify game records, change perks, or write profile data to Skyrim save files.

## Compatibility

The plugin uses the compatibility adapters available in the active game. A mod's presence alone does not always activate an adapter: Alchemy Plus, for example, requires its plugin DLL and a readable configuration with supported settings enabled.

| Mode | Behavior and support notes |
| --- | --- |
| Vanilla Skyrim | Uses the loaded Skyrim ingredient/effect records and vanilla alchemy calculation. |
| Alchemy Plus (AP) | Applies supported potency rounding and impure-cost settings from `SKSE/Plugins/AlchemyPlus.json` when `AlchemyPlus.dll` is loaded. |
| CACO | Uses loaded CACO records and supported live settings, including effect/duration variants and relevant post-processing behavior. |
| CACO + AP | Supported combined path. CACO calculation and Alchemy Plus value adjustments are composed in the prediction pipeline. |
| Requiem | Separate compatibility path using Requiem records, effectiveness, perk rules, and Fortify Skill behavior. Keep CACO and Alchemy Plus disabled when using Requiem. |
| Apothecary | Separate compatibility path for Apothecary's loaded records and keyword-based effectiveness scaling. Alchemy Plus behavior is not applied in this path. |

Compatibility predictions use data available from loaded records and supported settings; they do not execute every mod's in-game potion construction or scripted post-craft changes. Mixed-overhaul combinations other than the documented CACO + AP path should not be assumed supported. See [`test-suite.md`](test-suite.md) for the current compatibility and capture matrix.

## How the plugin works

When Skyrim's native alchemy submenu opens, the plugin takes a snapshot of the available ingredient forms, inventory counts, player state, and applicable mod settings. It evaluates eligible pairs and trios, applies protection rules and the selected compatibility calculation, and displays the resulting list. The calculation and cache are in memory; they are not saved to disk.

The browser searches recipe names, ingredient names, and effect descriptions. Multiple terms are combined with AND; standalone `OR` separates alternatives, double quotes match a phrase, and a trailing `~` allows a small spelling variation. The default selected-ingredient filter affects only which rows are shown, not the underlying calculations.

## Repository layout

- `alchemist/` — C++ plugin, UI, calculation engine, and compatibility adapters.
- `locales/` — bundled translation resources and the locale-file schema.
- `docs/USER_README.md` — player-facing guide included with release materials.
- `build.py` — supported plugin build, deployment, and packaging entry point.
- `config.example.py` and `user-paths.example.md` — templates for local machine-specific paths. Their local counterparts are ignored and should not contain paths committed to the repository.
- `potion_prediction_test.py` — Python prediction and confirmed-observation validation harness.
- `ingredients-vanilla.csv`, `ingredients-caco.csv`, `ingredients-requiem.csv`, and `ingredients-apothecary.csv` — ingredient/effect snapshots used by the offline prediction harness.
- `pat-*.py` and `pa-console-tests/` — pre-launch configuration and in-game test support.
- `test-suite.md`, `potion-prediction-default-settings.md`, and `potion-order-dependent-observations.md` — test specifications, capture defaults, and observation notes.
- `build-alchemist/` — generated plugin build tree; created by the build process and not source-controlled.

## Build and package

The plugin build is supported on Windows with:

- Visual Studio C++ Build Tools (MSVC x64) and a Windows SDK.
- Python 3.10 or later, CMake 3.21 or later, and Ninja.
- An external CommonLibSSE-NG checkout with its nested dependencies initialized.
- The CommonLibSSE-NG manifest dependencies installed for the static `x64-windows-static` vcpkg triplet.
- For packaging, the configured `md2nexus` executable.

Copy `config.example.py` to the ignored local `config.py` and `user-paths.example.md` to the ignored local `user-paths.md`, then set the machine-specific paths required by the build. Keep the CommonLibSSE-NG source, build, and install locations separate from this repository. The vcpkg tool root is not the installed package prefix; use the static, manifest-specific package directory configured for this project.

Build and deploy the plugin with the repository's supported entry point:

```powershell
python build.py
```

The wrapper configures and builds the Release plugin and deploys the DLL and bundled locale resources to the configured destination. It records build output in `build.log` and verifies the generated and deployed DLLs. The resulting plugin is `build-alchemist/alchemist.dll`.

Create a release archive after configuring the packaging path:

```powershell
python build.py --package
```

Packaging creates a version-named archive under `dist/` and converts `docs/USER_README.md` into a Nexus-ready description. The package includes the plugin, PDB, applicable locale, font, license, and user-guide resources, plus `alchemist.ini` when present. The PDB is included in the archive but is optional at runtime; font resources and the INI are also optional.

To run only the Nexus BBCode description conversion without building the plugin:

```powershell
python build.py --md2nexus
```

Do not edit generated version metadata, build outputs, deployed artifacts, or release archives by hand. A release version change must be applied consistently to the authoritative project version sources before rebuilding and packaging.

## Validation and test references

The offline prediction harness evaluates the analytical prediction model against its ingredient snapshots and captured in-game observations. The confirmed-row accuracy and regression check is:

```powershell
python potion_prediction_test.py --check-confirmed-csv --check-baseline
```

Use [`potion-prediction-default-settings.md`](potion-prediction-default-settings.md) for mode baselines and [`test-suite.md`](test-suite.md) for the in-game craft and prediction-export test plan. Test captures and plugin-generated observation files are evidence: never patch or rewrite them manually. Generate updated observations in game. The in-game `pat` tests use the supported modes `vanilla`, `caco`, `ap`, `caco-ap`, `requiem`, and `apothecary`; Requiem is tested independently from CACO and AP.

The optional Developer Test Hub is hidden unless `developer=1` is enabled for the active profile. Its diagnostic operations can change the live player's state or inventory; use a dedicated test character/profile rather than normal gameplay.

## In-game `pat` command setup

The detailed test blocks and command behavior are documented in [`test-suite.md`](test-suite.md) and [`skyrim-console.md`](skyrim-console.md). They assume the test environment is already installed; the setup below describes the MO2 layout and local configuration needed to make the commands available.

Install and enable the runtime command bridge in the MO2 profile used for testing: SKSE, ConsoleUtil-Extended, Extended-Console (the `CustomConsole` YAML command loader), and PapyrusExtenderSSE. Install the Prosperous Alchemist NG mod in that profile as well. The compiled test script and command definition must be deployed into that mod's virtual file tree alongside the plugin:

```text
<MO2 instance>/
  mods/
	Prosperous Alchemist NG/
	  SKSE/
		Plugins/alchemist.dll
		CustomConsole/pa-tests.yaml
	  Scripts/ProsperousAlchemistTests.pex
	ConsoleUtil-Extended/
	Extended-Console/
	Papyrus Extender/
	Alchemy Plus/                         (when testing AP or CACO+AP)
	Complete Alchemy & Cooking Overhaul/ (when testing CACO or CACO+AP)
	Requiem - The Roleplaying Overhaul/   (when testing Requiem)
	Apothecary - An Alchemy Overhaul/     (when testing Apothecary)
  profiles/
	<test profile>/
```

These are MO2 virtual mod directories; the names may differ with a user's installation. `pa-console-tests/` in this repository contains the YAML and Papyrus source, not the installed runtime files. `pa-console-tests/compile.ps1` compiles and deploys the command files, while `build.py` builds/deploys the plugin DLL. The compile script currently contains machine-specific paths for Caprica, script imports, and the destination mod directory; adjust them for the local installation before compiling. Keep test mods enabled only in the intended MO2 profile. Requiem is tested independently and must not be combined with CACO or AP. For CACO captures, keep `CACO_OptionDisableAllPotionHandling = 1` and `CACO_OptionImpurePotions = 0`.

### Configure an AI agent for local test setup

To let an AI coding agent prepare or update this environment, open the repository root as its workspace and provide access to the local MO2 instance and the compiler/source directories it needs. Copy `config.example.py` to the ignored local `config.py` and `user-paths.example.md` to the ignored local `user-paths.md`; replace their example paths with the real MO2 instance/profile, mod directories, deployed plugin path, Papyrus compiler, and required script-source locations. Keep these machine-specific files local and do not commit them. The repository's `AGENTS.md` tell the agent how to use `user-paths.md` and the project test rules.

With those paths and filesystem access in place, the agent can update the test sources, run the Papyrus compile/deploy step, and prepare the pre-launch mode scripts. The agent cannot perform the in-game portion: launch Skyrim through MO2 yourself, run the requested `pat` commands in the console, and return the resulting observations to the agent for validation. Never grant access to or ask an agent to edit generated in-game observation files; they must be produced by the game.

## Configuration and profiles

The plugin creates `Data/SKSE/Plugins/alchemist.ini` with defaults when it is missing. Settings and preferences are stored in named profiles in that INI, not in the Skyrim save. Profiles can be bound to a character, created blank or from another profile, renamed, and managed from the overlay's Settings page.

Most player settings are editable in the overlay. The INI is intended for advanced configuration and troubleshooting; restart Skyrim after manually editing it. Compatibility snapshots are managed from live mod settings and are not intended as user-authored prediction overrides. The player-facing configuration details are documented in the [user guide](docs/USER_README.md).

## Troubleshooting

- Launch Skyrim through the SKSE loader and confirm that SKSE and Address Library match the installed game runtime.
- In Mod Organizer 2, confirm that the intended profile is active and that the plugin is enabled in that profile.
- Confirm `alchemist.dll` is visible at `SKSE/Plugins/alchemist.dll` in the effective game data directory. The plugin does not require SkyUI, but the native alchemy menu must be open for the overlay to appear.
- Check the current user's Skyrim `SKSE` log directory for plugin load errors. If reporting a crash, include the newest SKSE log entries and the crash report when available.
- If no recipes appear, verify that at least two available, unprotected ingredients share an effect and that protection settings are not reserving them.
- Restart Skyrim after manual INI changes. For a suspected stale deployment, compare the built DLL with the DLL supplied by the active mod-manager profile.

## License and credits

Prosperous Alchemist is licensed under the [GNU General Public License version 3 or later](COPYING), with the [Modding Exception and GPL-3.0 Linking Exception](EXCEPTIONS.md). See those files and the notices in `licenses/` for applicable third-party terms.

Credits include the SKSE Team, CommonLibSSE-NG, Dear ImGui, and the contributors and translators acknowledged in the project and resource notices.

