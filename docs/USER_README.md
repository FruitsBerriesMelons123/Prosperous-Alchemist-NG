# Prosperous Alchemist

This project is a from-scratch rewrite of the original Skyrim Legendary Edition SKSE plugin. The source code is available on [GitHub](https://github.com/FruitsBerriesMelons123/Prosperous-Alchemist-NG).

Prosperous Alchemist recommends the most valuable potion or poison that can be made from the ingredients currently available to the player. It considers ingredient effects and, when enabled, the player's Alchemy skill, perks, and Fortify Alchemy equipment.

*Note: Prosperous Alchemist only recommends recipes. It does not automatically craft potions, consume ingredients, alter game records, or change perks.*

## Features

- **Real-Time Calculations:** Evaluates available ingredients using a long-lived in-memory cache and incremental updates to find the highest-value recipe.
- **Smart Filtering and Protection:** Exclude rare ingredients such as Jarrin Root or Daedra Hearts, reserve specific quantities, or filter recipes by ingredients currently selected in Skyrim's native menu.
- **Modern UI:** Renders a Dear ImGui overlay that works alongside Skyrim's native crafting interface.
- **Broad Compatibility:** Supports Special Edition, Anniversary Edition, and Skyrim VR through the matching SKSE and Address Library runtime files.

## Requirements

- Skyrim Special Edition, Anniversary Edition, or VR on Windows (see the VR note below).
- [**SKSE64**](https://skse.silverlock.org/) matching the installed Skyrim runtime.
- [**Address Library for SKSE Plugins**](https://www.nexusmods.com/skyrimspecialedition/mods/32444) for SE and AE, or [**VR Address Library for SKSE Plugins**](https://www.nexusmods.com/skyrimspecialedition/mods/58101) for Skyrim VR.
- Skyrim's native alchemy/crafting menu; SkyUI is optional and fully supported.
- The game must be launched through SKSE.

### Skyrim VR support

In Skyrim VR, the Dear ImGui overlay renders to Skyrim's desktop companion/mirror window. To view the overlay inside the VR headset, use SteamVR Desktop View or overlay utilities like Desktop+.

### UI compatibility

Prosperous Alchemist NG hooks Skyrim's native crafting engine (`RE::CraftingMenu` / `RE::CraftingSubMenus::AlchemyMenu`). It does not require or modify Scaleform SWF assets and works seamlessly with either vanilla UI or SkyUI.

The same plugin can support compatible runtimes through Address Library. Install the Address Library version file that matches your game runtime.

## Installation

### Mod Organizer 2 or Vortex

Install the archive through Mod Organizer 2 or Vortex as normal. Ensure the deployed plugin is located at `SKSE/Plugins/alchemist.dll` in the active profile or deployment.

### Mod Organizer 2 details

Install the mod with this structure:

```text
Prosperous Alchemist NG/
└── SKSE/
	└── Plugins/
		├── alchemist.dll
		├── alchemist.pdb (development symbols, optional for gameplay)
		├── alchemist.ini
		├── locales/
		│	└── alchemist.en.json
		└── fonts/
```

If you received only `alchemist.dll`, create or select a mod in MO2 and place it at:

```text
SKSE/Plugins/alchemist.dll
```

The optional `locales` and `fonts` directories go beside the DLL. The release archive includes example locale files and font instructions; font binaries are intentionally optional because system and third-party font licenses vary.

Enable the mod and launch Skyrim through SKSE. Make sure the intended MO2 profile is active.

The deployed `alchemist.ini` records the live player and supported CACO/Alchemy Plus values used by the latest potion-list calculation. The repository prediction script reads this deployed snapshot beside `alchemist.dll`; it does not use the repository template or another profile INI automatically. If the deployed snapshot is unavailable, provide every required prediction setting with the script's command-line flags. Release archives include `alchemist.pdb` beside the DLL for optional diagnostics; it is not required to run the mod.

### Direct installation

Copy `alchemist.dll` to:

```text
<Skyrim installation>/Data/SKSE/Plugins/alchemist.dll
```

Launch the game through SKSE after copying the file.

Prosperous Alchemist does not require an ESP or ESL or ship a replacement Scaleform SWF. It functions with Skyrim's native alchemy menu and SkyUI, rendering its separate overlay window with Dear ImGui.

## Using the plugin

1. Launch Skyrim through SKSE.
2. Open an Alchemy Table.
3. Review the automatically opened Prosperous Alchemist overlay.
4. Search the recipe name, ingredients, or effects, choose a sort mode, and optionally enable the **Effects** column.
5. Select a recipe by clicking its row. Use the pagination controls when the filtered list spans multiple pages.
6. Close the ImGui window or the alchemy crafting menu when finished.

Recipe search accepts multiple terms as an implicit **AND**. Use **OR** between alternatives, double quotes for an exact phrase, and a trailing `~` for a small spelling mistake: `restore health`, `restore OR damage`, `"fortify health"`, or `restor~`. `AND` and `OR` are case-insensitive and only act as operators when entered as standalone words; incomplete operators and unmatched quotes are handled safely.

A typical result looks like this:

```text
Potion of Fortify Something: effect description(s)
 Value: 123
Ingredient A, Ingredient B, Ingredient C
```

Ingredient names are displayed alphabetically. Each recipe also retains the actual Skyrim ingredient forms behind its display names, so ingredients that share a name are not treated as interchangeable. The result is calculated from available, unprotected ingredient forms.

By default, the browser filters the displayed recipes to those containing every ingredient currently selected in Skyrim's native alchemy menu. With no ingredients selected, all calculated recipes are shown. Disable **Filter potions by selected ingredients** in Settings to show the complete calculated list regardless of the native menu selection. The filter only changes the browser view; it does not change calculations or consume ingredients.

Recipe calculations use a long-lived in-memory cache and update incrementally when new ingredient forms become available. Player-state changes can reevaluate cached recipes, and repeated changes are coalesced before background processing begins. Superseded work is cancelled. The cache is not saved to disk and is retained after closing the menu only for the configured cache duration.

During a calculation, the overlay shows the current phase and progress. A completion message is shown briefly when the list is ready. If a previous calculation was slow, the existing list may be marked as outdated while the plugin waits for a stable request; select **Recalculate** to request an immediate update.




## Configuration

The plugin reads:

```text
Data/SKSE/Plugins/alchemist.ini
```

If the file does not exist, it is created with default settings when the plugin starts. The top-level `[Profiles]` section is always serialized first and maps each unique nonzero native Skyrim Character ID to the last-used `[Profile N]`, for example `123456 = Profile 1`. Each profile-specific setting, including the player-editable `ProfileName`, native Skyrim `CharacterID`, visible character identity, developer mode, calculation, tracking, language, window, and managed external-mod snapshots, is stored in its `[Profile N]` section. Unmanaged keys in recognized profile sections are retained when the plugin saves the file. Restart the game after editing the file.

When SKSE reports a new game or begins loading a save, the plugin waits for a usable native Character ID and visible identity before selecting a profile. An exact Character ID mapping is restored automatically, including the last-used profile when several profiles belong to the same character. If the Character ID has no mapping, the plugin automatically creates and binds a new blank profile for that character. Profiles bound to another Character ID cannot be selected for the current character unless they have `singleprofile=1`. All profile data is stored in `alchemist.ini` and never in the Skyrim save.

Skyrim's native `BGSSaveLoadManager::currentCharacterID` is the persistent character key used for profile matching. After a save load, an exact nonzero Character ID mapping is selected automatically. If there is only one unbound profile, the plugin silently binds it to the first usable character; any other unmapped character receives a new blank profile automatically. Profile names are separate from character names, must be non-empty, and must be unique case-insensitively. The Settings window always shows the profile controls, including when only one profile exists, and lets the player switch directly between profiles already bound to the current Character ID, rename the active profile, create a blank profile, open a scrollable **Create from profile** chooser, and delete a non-active profile after confirmation. The chooser shows each profile's name and index, character identity, completed and marked tracking requirements, protected effects, and custom protected ingredients before the player confirms a source. A clone keeps preferences such as developer mode, calculation, language, and window layout, receives a new unique default profile name, and resets identity, protected ingredients/effects/counts, tracking requirements, and managed snapshots for the new character. Older recognized formats are migrated only when valid; legacy `Current`/`NewGame` metadata and old `[Profiles]` metadata are converted to the Character ID mapping and removed on the next successful save. Unknown sections, invalid typed values, invalid JSON, duplicate profile indices or names, or other structural problems cause the original file to be backed up to the first unused `alchemist.backup.ini`, `alchemist.backup2.ini`, and so on before a clean profile-only file is written. Normal profile saves use a temporary replacement so a failed write does not replace the last valid INI. Blank profiles use immutable application defaults rather than values currently loaded from another profile, so settings such as `developer` do not leak into new profiles.

**Key settings:**

- **`ProfileName`:** Player-editable display name for the profile. It is separate from the Skyrim character `Name`, must not be blank, and must be unique without regard to letter case. Change it from **Settings**; the plugin rejects duplicates without changing profile data.
- **`singleprofile` (`0` / `1`):** Set to `1` to force this profile for every character, ignoring Character ID matching. If more than one profile is flagged, the lowest numeric profile index wins regardless of INI section order, and manual selection or creation of another active profile is rejected.
- **`IgnorePlayer` (`0` / `1`):** Uses the player's Alchemy skill, perks, and worn Fortify Alchemy equipment. Set to `1` to ignore player alchemy state.
- **`ProtectIngredients` (`0` / `1`):** Enables the unified ingredient protection and tracking system. It defaults to `0`; set it to `1` to protect the configured list, enough ingredients for one of every loaded ingredient-bearing craftable item and reachable Atronach Forge ingredient reference, selected ingredient effects, and unfinished tracking requirements.
- **`ManualProtectionOnly` (`0` / `1`):** Set to `1` to disable automatic quest and craftable reservations and use only manual/custom reservations plus selected protected effects. The automatic sources remain stored and return when this is set back to `0`.
- **`Singlethreaded` (`0` / `1`):** At `0`, recipe evaluation uses worker threads; at `1`, calculation runs single-threaded on the main thread.
- **`FilterPotionsBySelectedIngredients` (`0` / `1`):** Set to `1` to show only recipes containing every ingredient currently selected in Skyrim's native alchemy menu. With no ingredients selected, all calculated recipes are shown.
- **`CacheDurationSeconds`:** Keep the in-memory master recipe cache after closing the alchemy menu for this many seconds (default: `180`). Set to `0` to expire it immediately; no cache file is written.
- **`StaleRecalculateThresholdMs`:** Keep the current list visible as potentially outdated after a calculation longer than this threshold and show a manual **Recalculate** button (default: `500`). Set to `0` to disable this guard.
- **`CraftDebounceMs`:** Delay non-forced background recalculation after rapid crafting or inventory changes so repeated requests are coalesced (default: `400`).
- **`ProtectedIngredients`:** Comma-separated ingredient names, editor IDs, or hexadecimal FormIDs. The default is empty. Use `Name|Count` to reserve a specific quantity, such as `Daedra Heart|3`. An entry without a count protects all copies. The in-game picker saves resolved records as canonical `formid:0x...` entries, so a localized display name remains usable after changing Skyrim's language and two records with the same name remain separate. Existing name-based entries continue to work as a compatibility fallback.
- **`ProtectedEffects`:** Comma-separated loaded ingredient effects to protect. The defaults are the stable editor IDs `MagicAlchFortifyEnchanting` and `MagicAlchFortifySmithing`, so they work across localizations. Localized effect names and FormID keys remain accepted for compatibility; the Track page dynamically lists every available effect.
- **`ProtectedEffectCounts`:** Automatically maintained finite quantity defaults for selected effects. Use the Track page to choose protect-all or a quantity per ingredient; individual ingredient details can override a specific detected source.
- **`Language`:** Select a BCP 47 locale such as `en`, `es`, `zh-CN`, `hi`, `ar`, `pt-BR`, `fr`, `ru`, `ja`, or `de`. Empty or `auto` follows the Windows user interface locale.

The `[Profiles]` section is collection-wide metadata, not a profile. It is always written before the profile sections. Each nonzero Character ID appears once as a key, and its value is the last-used profile section. Do not add duplicate Character ID keys or map an ID to a profile whose `[Profile N]` section stores a different `CharacterID`.

Example:

```ini
[Profiles]
123456=Profile 1
789012=Profile 3

[Profile 1]
ProfileName=Profile 1
Name=
Race=
RaceID=
Gender=
singleprofile=0
IgnorePlayer=0
ProtectIngredients=0
Singlethreaded=0
FilterPotionsBySelectedIngredients=1
CacheDurationSeconds=180
StaleRecalculateThresholdMs=500
CraftDebounceMs=400
ProtectedIngredients=Jarrin Root,Daedra Heart|3,Blue Butterfly Wing|10
ManualProtectionOnly=0
ProtectedEffects=MagicAlchFortifyEnchanting,MagicAlchFortifySmithing
ProtectedEffectCounts=
Requirements={"nextManualId":1,"manual":[],"overrides":[]}
Language=
PositionX=-1
PositionY=-1
Width=-1
Height=-1
Player={}
CACO=
AlchemyPlus=
```

### In-game settings

Open the alchemy overlay and select **Settings** to change calculation options without editing the INI manually. Select **Track** to manage the single protection/tracking setting, which is disabled by default, the **Use only manual/custom protection** mode, dynamic effect selections, per-effect protect-all or quantity controls, ordinary craftable and Atronach Forge reservations, and manual or detected requirements. When manual/custom mode is enabled, automatic quest, ordinary craftable, and Atronach Forge protection rows are hidden and no longer reserve ingredients; selected protected effects remain visible and active. The protected-ingredient comparison shows numeric **Custom**, **Quest**, **Craftable**, and **Effect** protection columns; click an ingredient name to inspect and edit its complete breakdown. **Use single-threaded calculation** uses multithreaded worker-thread evaluation by default; selecting it runs recipe evaluation on the main thread. **Reset all settings** restores the declared defaults and removes tracker overrides. Changes are saved automatically.

### Ingredient tracking

Select **Track** beside **Settings** in the recipe toolbar to open the unified protection and tracking page. The page dynamically scans all loaded ingredient-bearing constructible records and reserves the quantities needed for one craft of every detected item. Vanilla Atronach Forge recipes are resolved from their nested form lists, including every reachable alternative and repeated IngredientItem reference; the parallel game-record result lists supply the localized item name shown as `Atronach Forge: <item>` for each recipe. Non-Ingredient Forge forms such as weapons, armor, books, gems, ore, meat, and pelts are ignored because only alchemical IngredientItem leaves can be protected. It also discovers every effect on loaded ingredients; selected effects reserve all matching copies by default, with Fortify Enchanting and Fortify Smithing selected by default when available, and each selected effect can instead use a finite quantity per ingredient. Each summary ingredient is keyed by its loaded IngredientItem FormID, displayed with the current localized name, and shown with an identity suffix so duplicate names remain independently selectable. Each summary ingredient is clickable and opens all craft, Forge, effect, quest, and manual detections with independent finite-quantity, protect-all, completed, and manual-remove controls. The comparison columns show the active protected quantity by category: **Custom** is the saved protected-ingredient list, while **Quest**, **Craftable**, and **Effect** are automatic detection categories. The picker and details popup scrollbars can be clicked and dragged with the custom cursor; the details popup closes with its title-bar X.

The **Refresh detection** action scans every quest record currently loaded by Skyrim, including inactive future quests, and lists each quest's FormID, editor ID, status, and every objective's full display text. It also scans those objective texts for localized ingredient display names, but each resulting requirement retains the matched IngredientItem FormID rather than using the translated name as its identity. Detected rows show the quest name, quest FormID, objective index and text, editor ID when available, matched ingredient, inferred quantity, completion state, and a detected label. Informational quest rows do not protect ingredients by themselves; only detected ingredient matches and manual requirements do. The quantity detector recognizes simple numbers before an ingredient or `x` quantities after it; otherwise it reserves one. Objective text is not structured requirement data, so false positives and missed requirements are possible. Editing an automatic row or marking it completed creates a clearly labeled **Manual override**; use **Clear manual overrides** beside **Add protected ingredient** to restore automatic quest, craftable, and effect values without deleting manually added requirements or custom protected ingredients. **Reset to detected** remains the broader action that removes both manual rows and all detection overrides. The list covers records available through Skyrim's runtime form data; a plugin that is not loaded cannot be inspected until Skyrim loads it.

The detector also retains quest-objective matching and Atronach Forge guidance. Ordinary loaded `BGSConstructibleObject` records are scanned separately from the vanilla Forge form-list roots `AtrFrgAtronachForgeRecipeList` and `AtrFrgSigilStoneRecipeList`; their index-aligned result roots `AtrFrgAtronachForgeResultList` and `AtrFrgSigilStoneResultList` provide the actual output form name at scan time. Forge rows identify the output item, root, nested recipe path, selected IngredientItem, and FormID; every reachable alternative remains represented, while non-Ingredient leaves are skipped. If a loaded override has no matching result entry, the row uses the generic `Atronach Forge` source instead of displaying an incorrect root name. **Detect requirements** is collapsed by default, appears only when `developer=1`, and contains the detailed detected/manual editor, quest browser, quest debugging controls, and Atronach Forge guidance. **Reset to detected** removes manual rows and all detection overrides, then restores the current automatic scan result.

### Localization and fonts

The overlay uses UTF-8 resources and supports the major Latin, Cyrillic, Greek, Hebrew, Arabic, Indic, Southeast Asian, Chinese, Japanese, and Korean writing systems when a matching font is available. The release includes Arabic, Bulgarian, Chinese Hong Kong, Simplified and Traditional Chinese, Croatian, Czech, Danish, Dutch, English, Finnish, French and Canadian French, German, Greek, Hebrew, Hindi, Hungarian, Indonesian, Italian, Japanese, Korean, Malay, Norwegian Bokmål, Polish, Portuguese Brazil and Europe, Romanian, Russian, Slovak, Spanish, Latin American Spanish, Mexican Spanish, Swedish, Tagalog, Thai, Turkish, Ukrainian, and Vietnamese translations. The plugin first uses the Windows user interface locale, unless `[Localization] Language` in `alchemist.ini` specifies a BCP 47 tag such as `fr`, `fr-CA`, `es-419`, `es-MX`, `vi`, `th`, `he`, `zh-HK`, `zh-CN`, `zh-TW`, `ja`, or `ko`.

Custom translations are loaded at startup from `SKSE/Plugins/locales/alchemist.<tag>.json`. The exact tag is tried after its base language, with English and built-in English strings as the final fallback. Files must be UTF-8 JSON and may contain only the strings being changed. See `locales/README.md` in the release archive for the schema and named formatting placeholders.

Dear ImGui merges locale-declared font files from `SKSE/Plugins/fonts` with available Windows fonts. If a language's glyphs display as boxes, install a legally redistributable font such as the appropriate Noto family, copy it below `fonts`, and list its filename in the selected locale JSON. Missing resources are skipped gracefully and do not disable the overlay or its mouse cursor.

`ProtectedIngredients` uses commas as a separator. Do not place commas inside an individual ingredient entry. Ingredient names and editor IDs are matched case-insensitively; protected entries may also use hexadecimal FormIDs. The Track-page picker stores a resolved record as `formid:0x...` and uses that exact identity, while older names and ordinary hexadecimal entries remain supported. Entries are managed through `ProtectedIngredients` or the in-game Settings page.

### Optional compatibility mods

- **[Complete Alchemy & Cooking Overhaul (CACO)](https://www.nexusmods.com/skyrimspecialedition/mods/19924):** The plugin automatically detects CACO's loaded records and duration settings at `kDataLoaded`. When a calculation source and the live Skyrim alchemy settings are available, it uses CACO effect variants, mixed-effect handling, optional impure processing, Crucible exemplars, custom naming, and reweighting in its prediction. Missing optional lists, settings, or duration variants disable only the dependent behavior; a missing duration variant falls back to the source ingredient effect, while a missing active calculation source leaves the non-CACO path unchanged. CACO potion handling remains controlled by CACO's own options, but repository-supported automated captures keep potion handling disabled (`CACO_OptionDisableAllPotionHandling=1`, `CACO_OptionImpurePotions=0`) because CACO's scripted post-craft adjustment is not reliable for automated value capture.
- **[Alchemy Plus](https://www.nexusmods.com/skyrimspecialedition/mods/80882):** When `AlchemyPlus.dll` and a readable `SKSE/Plugins/AlchemyPlus.json` are present, the plugin automatically applies enabled potency-rounding and impure-cost settings to its prediction. The adapter does not install Alchemy Plus hooks or change game records.
- **SkyUI / vanilla UI:** The plugin is fully compatible with both without requiring an ESP/ESL plugin or modified SWF files.
- The two adapters are independent. When both are active, Automatic mode composes CACO's live calculation with Alchemy Plus's supported rounding and impure-cost behavior.

## Troubleshooting

### The overlay or recommendation does not appear

- Confirm `alchemist.dll` is in the active profile's `SKSE/Plugins` directory.
- Confirm Skyrim's native alchemy crafting submenu is available. If SkyUI is installed, confirm it is enabled in the active profile and that no other UI mod overrides its crafting-menu assets.
- Confirm Skyrim was launched through SKSE.
- Confirm Address Library is installed and contains the version file for the installed runtime.
- Confirm at least two available, unprotected ingredients share an effect.
- Restart the game after changing `alchemist.ini`.

If the window remains hidden, reopen the native alchemy menu and verify that its active alchemy submenu is available. The plugin intentionally fails closed when the native crafting menu or active alchemy submenu cannot be identified; it does not depend on localization resources or patch SkyUI files.

### The INI file is missing or changes do not apply

The file is created under the game's effective `Data/SKSE/Plugins` directory when the plugin starts. Exit Skyrim completely, verify the active MO2 profile, edit the file, and launch through SKSE again.

### The deployed DLL may be outdated

When using a mod manager, verify that the active profile contains the intended DLL. The plugin build output and the deployed file should have matching file hashes if you have access to both files.

### External diagnostics

SKSE and an installed Crash Logger are normally under:

```text
%USERPROFILE%\Documents\My Games\Skyrim Special Edition\SKSE\
```

Relevant files include:

```text
skse64_loader.log
skse64.log
crash-*.log
```

Prosperous Alchemist does not create a runtime or Developer Test Hub log. For a load problem, confirm that `skse64.log` reports `alchemist.dll` loaded correctly. If the game crashes, reproduce the problem once and include the newest SKSE entries and the Crash Logger SSE AE VR report when requesting help.

## Compatibility and limitations

- The plugin depends on SKSE, Address Library, Skyrim's native crafting menu and D3D11 renderer, Dear ImGui linked into the plugin, and a supported game runtime. SkyUI is optional.
- The calculation is an estimate based on Skyrim effect data and the configured player bonuses; it is not a guarantee for every modded effect or game setup.
- Protection names use configured strings and display prefixes use built-in strings; protected ingredients also accept editor IDs and hexadecimal FormIDs. Menu detection uses the runtime-matched native crafting submenu and is not controlled by display text.
- Inventory quantity changes alone may not invalidate the recommendation cache when the native ingredient forms and protected-ingredient result remain unchanged; player-state changes and CACO option revisions do invalidate it. The cache is in memory only and expires according to `CacheDurationSeconds`.
- The recipe browser's selected-ingredient filter compares native ingredient FormIDs, not display names, so duplicate-name ingredients remain distinct. If the native menu cannot expose its selected entries, the filter has no selected forms to apply and the complete calculated list remains visible.
- Values are estimates based on the available record data. CACO and Alchemy Plus compatibility improves prediction inputs and post-processing, but Skyrim's private potion-construction path is not invoked to preview every hypothetical recipe.
- The Developer Test Hub is hidden unless the active profile has `developer=1`; it is a diagnostic tool that deliberately changes player state and inventory without automatically restoring them, and should not be enabled in a normal gameplay profile. Its comparison records remain in memory only.
- There is no automatic crafting or ingredient consumption.

## Credits and license

Prosperous Alchemist is licensed under the [GNU General Public License version 3 or later](https://github.com/FruitsBerriesMelons123/Prosperous-Alchemist-NG/blob/main/COPYING), with the [Modding Exception and GPL-3.0 Linking Exception](https://github.com/FruitsBerriesMelons123/Prosperous-Alchemist-NG/blob/main/EXCEPTIONS.md). Third-party notices remain applicable to the files and libraries they cover.

Credits:

- [SKSE Team](https://skse.silverlock.org)
- [CommonLibSSE-NG](https://github.com/alandtse/CommonLibSSE-NG)
- [axxonite](https://www.nexusmods.com/skyrim/mods/38634)
