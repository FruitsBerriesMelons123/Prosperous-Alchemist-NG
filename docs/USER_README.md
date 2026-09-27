# Prosperous Alchemist NG

Prosperous Alchemist NG looks at the ingredients you are carrying and shows the most valuable potions and poisons you can craft with them. The list appears in an overlay next to Skyrim's alchemy menu.

It only recommends recipes. It never crafts anything, uses up ingredients, changes your perks or game records, or touches your save file. You can install or remove it at any point in a playthrough.

This is a from-scratch rewrite of the original [Prosperous Alchemist](https://www.nexusmods.com/skyrim/mods/38634) for Skyrim LE. The source code is on [GitHub](https://github.com/FruitsBerriesMelons123/Prosperous-Alchemist-NG).

## Features

- Checks every ingredient pair and trio you can make and sorts the recipes by estimated value.
- Takes your Alchemy skill, alchemy perks, and any Fortify Alchemy gear you are wearing into account. You can turn this off.
- Handles Vanilla Skyrim, Alchemy Plus, Complete Alchemy & Cooking Overhaul (CACO), CACO with Alchemy Plus, Requiem, and Apothecary automatically.
- Search by recipe name, ingredient, or effect, with support for AND, OR, exact phrases, and near matches.
- Sort by value or by name, page through long lists, and optionally show each recipe's effects.
- Narrow the list to recipes that use the ingredients you have already picked in the alchemy menu.
- Optionally hold back ingredients you want to keep: quest items, crafting materials, Atronach Forge ingredients, favorite effects, or your own list.
- Separate settings profiles for each character.
- Translated into more than 35 languages.
- Works on Skyrim Special Edition, Anniversary Edition, and Skyrim VR. No ESP, so it takes no plugin slot.

## Requirements

- Skyrim Special Edition, Anniversary Edition, or Skyrim VR on Windows.
- [SKSE64](https://skse.silverlock.org/) ([Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/30379)) for your game version, or SKSEVR for Skyrim VR.
- [Address Library for SKSE Plugins](https://www.nexusmods.com/skyrimspecialedition/mods/32444) for SE/AE, or [VR Address Library for SKSEVR](https://www.nexusmods.com/skyrimspecialedition/mods/58101) for VR. Get the file that matches your game version.

Optional:

- [SkyUI](https://www.nexusmods.com/skyrimspecialedition/mods/12604) is supported but not needed. The overlay works with Skyrim's normal alchemy menu.

### Skyrim VR

The overlay shows up on the desktop mirror window. To see it in your headset, use SteamVR Desktop View or a similar desktop overlay.

## Installation

1. Install the archive with [Mod Organizer 2](https://www.nexusmods.com/skyrimspecialedition/mods/6194), [Vortex](https://www.nexusmods.com/about/vortex/), or another mod manager, and enable it.
2. Start the game through SKSE (in Mod Organizer 2, pick the SKSE executable).

When installed, the plugin sits at `Data/SKSE/Plugins/alchemist.dll`. The archive also includes translations, a default `alchemist.ini`, and an `alchemist.pdb` file. The PDB only helps with crash reports and is not needed to play. If you install by hand, copy the `SKSE` folder from the archive into your `Data` folder.

**Upgrading from an older Prosperous Alchemist release:** uninstall the old version first, including any ESP or menu files it came with. This version needs neither.

**Uninstalling:** remove the mod at any time. Nothing is stored in your save.

## Using the overlay

1. Start Skyrim through SKSE.
2. Use an Alchemy Lab. The overlay opens next to the alchemy menu.
3. Search, sort, and page through the recipes. Clicking a row only highlights it; it does not select or craft anything in Skyrim.
4. Craft the recipe you want in the alchemy menu as usual. The list updates after each craft.

Each row shows the potion or poison name, estimated value, ingredients (in alphabetical order), and optionally its effects. The values are estimates based on your game data and settings. In most setups they match the game exactly, but other mods that change ingredients or potion creation can cause small differences.

### Search

- Several words must all match: `restore health`
- Put **OR** between alternatives: `restore OR damage`
- Put quotes around an exact phrase: `"fortify health"`
- End a word with `~` to allow a small typo: `restor~`

`AND` and `OR` only count as operators when you type them as separate words. Case does not matter.

### Sorting, pages, and effects

You can sort by value (high to low or low to high) or by name (A–Z or Z–A). Long lists are split into pages. Turn on **Effects** to see each recipe's magnitudes and durations.

### Filter by selected ingredients

By default, when you select ingredients in the alchemy menu, the overlay only shows recipes that use all of them. With nothing selected, you see every recipe. You can turn this off with **Filter potions by selected ingredients** in Settings. The filter only changes what is shown; it does not change any values.

### Recalculation

Results are kept in memory for a while so the list comes back instantly when you reopen the alchemy menu. The list updates when your ingredients or Alchemy stats change. If an update takes a while, the old list stays up, marked as outdated, and a **Recalculate** button appears so you can refresh it immediately.

## Settings and profiles

Click **Settings** in the overlay. Changes save immediately to `Data/SKSE/Plugins/alchemist.ini`, never to your save, and take effect without restarting the game.

Profiles are tied to your characters. Each character gets the profile it used last, and a new character gets a fresh one. In Settings you can rename the current profile, create a blank profile, copy another profile, switch profiles for the current character, or delete a profile you are not using. A copied profile keeps preferences such as language and calculation options, but starts with its own ingredient protection list.

### Options

* **Ignore player state** (`IgnorePlayer`): *Default Off*
Ignores your Alchemy skill, perks, and Fortify Alchemy gear when estimating values. Only your inventory is used.
* **Protect ingredients** (`ProtectIngredients`): *Default Off*
Leaves protected ingredients out of the recommendations.
* **Use only manual/custom protection** (`ManualProtectionOnly`): *Default Off*
Protects only the ingredients and effects you choose yourself, and skips automatic quest, crafting, and Atronach Forge detection.
* **Filter potions by selected ingredients** (`FilterPotionsBySelectedIngredients`): *Default On*
Shows only recipes that use every ingredient selected in the alchemy menu.
* **Use single-threaded calculation** (`Singlethreaded`): *Default Off*
Runs the calculation on one thread. Only useful for troubleshooting.
* **Cache duration** (`CacheDurationSeconds`): *Default 180 seconds*
How long results are kept after you close the alchemy menu. `0` discards them immediately.
* **Stale recalculation threshold** (`StaleRecalculateThresholdMs`): *Default 500 ms*
If an update takes longer than this, the old list stays visible and **Recalculate** appears. `0` turns this off.
* **Craft debounce** (`CraftDebounceMs`): *Default 400 ms*
Waits this long after quick crafts or inventory changes before updating, so the list is not recalculated after every single craft.
* **Language** (`Language`): *Default Automatic*
Pick a language, or leave it on Automatic to follow your Windows language.

**Reset all settings** puts the current profile back to its defaults.

### Editing the INI file

You shouldn't need to edit the INI; everything is in Settings. If you do edit it, close Skyrim first, and make sure you are editing the copy your mod manager actually uses. One setting is only available in the INI:

* **Single profile** (`singleprofile`): *Default 0*
Set it to `1` in a profile's section to make every character use that profile.

## Ingredient protection

Protection is off by default. Open **Track** to turn it on and choose what to keep. Protected ingredients can come from:

- Your own list of ingredients, with an optional quantity for each.
- Chosen effects. Fortify Enchanting and Fortify Smithing are selected by default.
- Ingredients needed for craftable items in your load order and for Atronach Forge recipes.
- Ingredients mentioned in active quest objectives, plus requirements you add yourself.

Click an ingredient to see why it is protected and change the quantity. Effect protection can keep every copy of an ingredient or only a set number. Ingredients for finished quests are released automatically. Ingredients that share a name are tracked separately.

**Refresh detection** scans your load order and quest objectives again. Quest text is written for players, not for mods, so detection can miss something or flag an ingredient a quest doesn't actually need. Check the results and adjust them by hand if needed.

To add ingredients to your own list, use the ingredient name, editor ID, or hex FormID, separated by commas. Add `|count` to keep that many; leave it off to keep all of them. Example: `Daedra Heart|3,Blue Butterfly Wing`.

## Compatibility

The plugin detects which mods are installed and adjusts its calculations to match. No patches or settings are needed.

- **Vanilla Skyrim**, including the official DLCs and Creation Club ingredients.
- **[Alchemy Plus](https://www.nexusmods.com/skyrimspecialedition/mods/80882):** follows your Alchemy Plus settings for magnitude and duration rounding (including per-effect rounding overrides) and the impure-cost fix.
- **[Complete Alchemy & Cooking Overhaul (CACO)](https://www.nexusmods.com/skyrimspecialedition/mods/19924):** uses CACO's ingredients and your CACO MCM settings, including the Restore Health/Magicka/Stamina duration options. CACO's optional scripted potion handling can change a potion after you craft it, so if that option is on, the final item may not match the estimate.
- **CACO + Alchemy Plus:** supported together.
- **[Requiem](https://www.nexusmods.com/skyrimspecialedition/mods/60888):** uses Requiem's ingredients, alchemy effectiveness, Alchemical Lore ranks, and perks. Use Requiem without CACO or Alchemy Plus.
- **[Apothecary – An Alchemy Overhaul](https://www.nexusmods.com/skyrimspecialedition/mods/52130):** uses Apothecary's ingredients and effect scaling. Not combined with Alchemy Plus.
- **[kryptopyr's Patch Hub](https://www.nexusmods.com/skyrimspecialedition/mods/19518):** the CACO Rare Curios patch is supported.

Other mods that add ingredients work too, since the plugin reads ingredients straight from your load order. Mods that change how potions are built or priced, and overhaul combinations not listed here, may make the estimates less accurate.

## Languages

The overlay uses your Windows language unless you pick one in Settings. Included languages: Arabic, Bulgarian, Chinese (Simplified, Traditional, and Hong Kong), Croatian, Czech, Danish, Dutch, English, Finnish, French (France and Canada), German, Greek, Hebrew, Hindi, Hungarian, Indonesian, Italian, Japanese, Korean, Malay, Norwegian Bokmål, Polish, Portuguese (Brazil and Portugal), Romanian, Russian, Slovak, Spanish (Spain, Latin America, and Mexico), Swedish, Tagalog, Thai, Turkish, Ukrainian, and Vietnamese.

**Your own translation:** add a file named `alchemist.<language>.json` to `SKSE/Plugins/locales/`, for example `alchemist.fr.json` or `alchemist.es-419.json`. Anything missing falls back to English. `SKSE/Plugins/locales/README.md` in the download explains the format.

**Fonts:** if some characters show up as boxes, your Windows fonts may not cover that language. Put a suitable font (such as [Noto Sans](https://fonts.google.com/noto)) in `SKSE/Plugins/fonts/` and follow `SKSE/Plugins/fonts/README.md` in the download.

## Troubleshooting

### The overlay does not appear

- Make sure the mod is enabled in your mod manager and that you started the game through SKSE.
- Make sure your SKSE and Address Library versions match your game version.
- Use an Alchemy Lab; the overlay only appears in the alchemy menu.
- Check `Documents/My Games/Skyrim Special Edition/SKSE/alchemist.log` for errors.

### No recipes are listed

- You need at least two ingredients that share an effect.
- If ingredient protection is on, it may be holding back those ingredients.
- If the selected-ingredient filter is on, clear your selection in the alchemy menu or turn the filter off in Settings.

### A setting did not change

Changes made in Settings save automatically. If you edited `alchemist.ini` by hand, restart Skyrim and make sure you edited the copy your mod manager uses.

### Text shows up as boxes

Pick another language in Settings, or add a font as described under **Languages**.

### Reporting a problem

Post in the Nexus comments or open an issue on [GitHub](https://github.com/FruitsBerriesMelons123/Prosperous-Alchemist-NG/issues). Include your game version, the overhaul mods you use, `alchemist.log`, and a crash log if the game crashed.

## Credits

- Built with [CommonLibSSE-NG](https://github.com/alandtse/CommonLibSSE-NG), [Dear ImGui](https://github.com/ocornut/imgui), [nlohmann/json](https://github.com/nlohmann/json), and [Zstandard](https://github.com/facebook/zstd).
- Thanks to the [SKSE team](https://skse.silverlock.org/), the Address Library author, and the authors of Alchemy Plus, CACO, Requiem, and Apothecary.
- Thanks to all translators and contributors.

## License

Prosperous Alchemist is licensed under the [GNU General Public License version 3 or later](https://github.com/FruitsBerriesMelons123/Prosperous-Alchemist-NG/blob/main/COPYING), with the [Modding Exception and GPL-3.0 Linking Exception](https://github.com/FruitsBerriesMelons123/Prosperous-Alchemist-NG/blob/main/EXCEPTIONS.md). Third-party notices are included in the download.
