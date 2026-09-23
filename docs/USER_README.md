# Prosperous Alchemist NG
This project is a from-scratch rewrite of the original Skyrim Legendary Edition SKSE plugin. The source code is available on [GitHub](https://github.com/FruitsBerriesMelons123/Prosperous-Alchemist-NG)

Prosperous Alchemist recommends valuable potion and poison recipes from the ingredients currently in your inventory. It displays its recommendations in an overlay while Skyrim's native alchemy menu is open.

The plugin recommends recipes only. It does not automatically craft items, consume ingredients, change perks, alter game records, or store profile settings in your Skyrim save.

## Features

- Compares ingredient pairs and trios and sorts valid recipes by estimated value.
- Uses available ingredient forms and, by default, your Alchemy skill, relevant perks, and worn Fortify Alchemy equipment.
- Searches by recipe name, ingredient name, and effect description.
- Sorts by value or name, displays pages of results, and optionally shows effects in the recipe list.
- Can filter the visible list to recipes containing ingredients currently selected in Skyrim's alchemy menu.
- Includes optional ingredient protection and tracking tools.
- Supports multiple settings profiles and a localized interface.

## Requirements

- Skyrim Special Edition, Anniversary Edition, or Skyrim VR on Windows.
- SKSE matching the installed Skyrim runtime.
- Address Library for SKSE Plugins for Special Edition/Anniversary Edition, or VR Address Library for Skyrim VR. Install the version that matches your game runtime.
- Launch the game through SKSE.

The native Skyrim alchemy menu is required. SkyUI is optional and supported. No ESP/ESL or replacement menu files are required.

### Skyrim VR

The overlay appears on Skyrim's desktop mirror window. To see it in the headset, use SteamVR Desktop View or a compatible desktop overlay.

## Installation

Install the release archive with Mod Organizer 2, Vortex, or another mod manager. The plugin must be available in the active game's data directory at:

```text
SKSE/Plugins/alchemist.dll
```

The release archive includes locale resources and a PDB file; the PDB is not needed for gameplay. Optional fonts and an INI may also be included. If installing only the DLL, place it in the same `SKSE/Plugins` location. Enable the mod in your mod manager and launch the intended profile through SKSE.

The plugin creates `alchemist.ini` with default settings when it first starts. Do not install an ESP/ESL for Prosperous Alchemist; it does not use one.

## Using the overlay

1. Launch Skyrim through SKSE.
2. Open an Alchemy Table and the native alchemy menu.
3. Review the Prosperous Alchemist recipe list.
4. Search, sort, and page through recommendations. Selecting a row in the overlay does not select or craft that recipe in Skyrim.
5. Close the overlay or the alchemy menu when finished.

The list shows a potion or poison name, effect descriptions, estimated value, and ingredients. Ingredient names are displayed alphabetically. Values are predictions from the available game data and settings; they are not a guarantee of the final value for every mod or effect.

### Search and list controls

Search supports multiple terms as an implicit **AND**. Use standalone **OR** between alternatives, double quotes around an exact phrase, and a trailing `~` for a small spelling variation. Examples: `restore health`, `restore OR damage`, `"fortify health"`, and `restor~`. The words `AND` and `OR` are case-insensitive operators only when entered as separate words.

The sort choices are value descending, value ascending, name ascending, and name descending. Enable **Effects** to show calculated effect descriptions in the table. Large lists are divided into pages.

By default, the list shows recipes containing every distinct ingredient currently selected in Skyrim's alchemy menu. With no ingredients selected, all calculated recipes are shown. Disable **Filter potions by selected ingredients** in Settings to ignore the native menu selection. This filter only changes the displayed list; it does not change calculations or consume ingredients.

### Recalculation

The plugin keeps a temporary in-memory recipe cache to avoid repeating work unnecessarily. It updates recommendations as relevant ingredients or player state change. If a recalculation takes longer than the configured threshold, the existing list may remain visible as outdated while a **Recalculate** action is offered. Select it to request an immediate update. Cache contents are not saved to disk.

## Settings and profiles

Open **Settings** in the overlay to change the active profile's preferences. Changes are saved automatically in `Data/SKSE/Plugins/alchemist.ini`. Settings are not written to the Skyrim save; the game does not need to be restarted after changes made in the overlay.

Profiles are associated with Skyrim characters. The plugin restores the profile last used for a character and creates a blank profile for a character without one. From Settings, you can rename the active profile, create a blank profile, create a profile from another profile, switch between profiles for the current character, or delete a non-active profile after confirmation. A copied profile keeps preferences such as language and calculation options, but starts with separate character-specific protection and tracking data.

Most players can use the in-game Settings page rather than editing the INI file. If you edit the INI manually, exit Skyrim first and restart it for changes to take effect. Keep the INI in the active profile's effective `Data/SKSE/Plugins` directory.

### Common options

| Option | Default | Description |
| --- | --- | --- |
| **Ignore player state** (`IgnorePlayer`) | Off | Ignore Alchemy skill, perks, and worn Fortify Alchemy gear when estimating values. Ingredient availability is still based on inventory. |
| **Protect ingredients** (`ProtectIngredients`) | Off | Enable configured protection and tracking so reserved ingredients are excluded from recommendations. |
| **Use only manual/custom protection** (`ManualProtectionOnly`) | Off | Use manual/custom reservations and selected protected effects instead of automatic quest, craftable-item, and Atronach Forge reservations. |
| **Filter potions by selected ingredients** (`FilterPotionsBySelectedIngredients`) | On | Show only recipes containing all ingredients selected in the native alchemy menu. |
| **Use single-threaded calculation** (`Singlethreaded`) | Off | Run recipe evaluation on the main thread instead of using worker threads. |
| **Cache duration** (`CacheDurationSeconds`) | 180 seconds | How long the in-memory recipe cache is retained after closing the alchemy menu. Set to `0` to expire it immediately. |
| **Stale recalculation threshold** (`StaleRecalculateThresholdMs`) | 500 ms | When a calculation exceeds this time, keep the existing list visible and offer **Recalculate**. Set to `0` to disable this behavior. |
| **Craft debounce** (`CraftDebounceMs`) | 400 ms | Coalesce repeated recalculation requests after rapid crafting or inventory changes. |
| **Language** (`Language`) | Automatic | Select a language or follow the Windows user interface language. |

**Reset all settings** restores the declared defaults for the active profile and removes tracking overrides.

## Ingredient protection and tracking

Protection is off by default. Open **Track** in the overlay to enable protection and manage reservations. When enabled, the plugin can reserve ingredients from:

- Custom protected ingredients and quantities.
- Selected ingredient effects, including Fortify Enchanting and Fortify Smithing by default when available.
- Ingredients needed for loaded craftable items and reachable vanilla Atronach Forge recipes.
- Detected quest requirements and manual tracking requirements.

The tracking view groups records by ingredient identity, so ingredients with the same displayed name remain separate. Click an ingredient to inspect its detected sources and adjust quantities. Effects can protect all matching copies or a specified quantity per ingredient. Completed quest requirements are excluded from active reservations.

**Refresh detection** scans currently loaded game records and quest objective text for possible ingredient requirements. Quest objectives are written as player-facing text rather than structured ingredient requirements, so detection can miss requirements or identify a name that is not actually required. Review detected entries and use manual controls when needed.

Custom protected ingredients can be entered by displayed name, editor ID, or hexadecimal FormID. Separate entries with commas; an optional `|count` reserves that quantity, while an entry without a count protects all copies. For example: `Daedra Heart|3,Blue Butterfly Wing`.

## Compatibility

Compatibility is selected from the mods and settings loaded by the game. Keep overhauls configured as intended by their authors; combinations not listed below should not be assumed supported.

- **Vanilla Skyrim:** Uses the game's loaded ingredient and effect records.
- **Alchemy Plus:** When `AlchemyPlus.dll` and its `SKSE/Plugins/AlchemyPlus.json` configuration are available, supported potency-rounding and impure-cost settings are applied to predictions. A JSON file alone does not activate the integration.
- **Complete Alchemy & Cooking Overhaul (CACO):** Uses loaded CACO records and supported live settings, including ingredient-effect duration choices. Some CACO post-craft handling can change a potion after its initial creation, so the final in-inventory item may differ from a prediction.
- **CACO + Alchemy Plus:** Supported combined path; both integrations contribute their supported prediction behavior.
- **Requiem:** Supported as a separate compatibility path using Requiem records, alchemy effectiveness, and perk behavior. Use Requiem without CACO or Alchemy Plus.
- **Apothecary – An Alchemy Overhaul:** Automatically detects Apothecary and models its effect scaling using loaded records and relevant Skyrim alchemy settings. It is a separate compatibility path; Alchemy Plus behavior is not combined with it.

Compatibility improves estimates for supported records and settings, but the plugin does not invoke Skyrim's private potion-construction process to preview every possible recipe. Other mods that change ingredient effects or potion creation may affect the final result.

## Localization

The interface follows the Windows user interface language unless a language is selected in Settings. Bundled translations are available for Arabic, Bulgarian, Chinese (Hong Kong, Simplified, and Traditional), Croatian, Czech, Danish, Dutch, English, Finnish, French (including Canadian French), German, Greek, Hebrew, Hindi, Hungarian, Indonesian, Italian, Japanese, Korean, Malay, Norwegian Bokmål, Polish, Portuguese (Brazil and Europe), Romanian, Russian, Slovak, Spanish (including Latin American and Mexican Spanish), Swedish, Tagalog, Thai, Turkish, Ukrainian, and Vietnamese.

Custom translations can be placed beside the plugin in `SKSE/Plugins/locales/` as `alchemist.<language-tag>.json`. The language tag may be a BCP 47 tag such as `fr`, `fr-CA`, `es-419`, or `zh-CN`. Missing or invalid translations fall back to English. See `SKSE/Plugins/locales/README.md` in the release archive for the custom translation format.

Optional font files can be placed in `SKSE/Plugins/fonts/` and referenced by the selected locale resource. Fonts are only needed if the available system fonts do not contain the characters for your language. Use fonts that you are permitted to redistribute or install.

## Troubleshooting

### The overlay does not appear

- Confirm the plugin is enabled in the active mod-manager profile and is located at `SKSE/Plugins/alchemist.dll` in the effective game data directory.
- Confirm SKSE and Address Library match the installed Skyrim runtime, and launch the game through SKSE.
- Open Skyrim's native alchemy menu. SkyUI is optional; the native menu is required.
- Reopen the alchemy menu after changing profiles or enabling the plugin.

### No recipes are listed

- Confirm at least two available ingredients share an effect.
- Check whether ingredient protection is enabled and reserving those ingredients.
- If the selected-ingredient filter is enabled, select the ingredients in Skyrim's native menu or disable the filter in Settings.

### A setting change did not take effect

Changes made in the overlay are saved automatically. After editing `alchemist.ini` manually, exit Skyrim and restart it, and make sure you edited the INI used by the active mod-manager profile.

### Text is missing or appears as boxes

Choose another language in Settings or use the Windows locale. If only some characters are missing, install a suitable font for those characters and follow the locale resource instructions.

## License

Prosperous Alchemist is licensed under the [GNU General Public License version 3 or later](../COPYING), with the [Modding Exception and GPL-3.0 Linking Exception](../EXCEPTIONS.md). Third-party notices are included with the release.
