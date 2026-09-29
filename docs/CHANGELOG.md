# Changelog

## 1.6.0
Added standalone Ordinator compatibility, including its Alchemy Mastery ranks, selected Physician attribute, Poisoner, Pure Mixture, Advanced Lab, and permanent AlchemyPowerMod effects on potion predictions.

## 1.5.0
Added automatic compatibility for Alchemy Potions and Food Adjustments (APAFA), including its ingredient and effect records and potion-related MCM settings.

## 1.4.1
Unified the shared alchemy calculations across Vanilla, Alchemy Plus, CACO, Requiem, and Apothecary, improving effect magnitude, duration, and potion value predictions, including Fortify Alchemy and perk interactions.
Refined CACO and Apothecary compatibility.

## 1.4.0
Added automatic Requiem compatibility, including Requiem ingredient records, alchemy effectiveness, Alchemical Lore ranks, and supported perk and keyword effects.
Added automatic Apothecary compatibility using loaded ingredient records and Apothecary's alchemy-effectiveness rules.
Updated CACO predictions to use active duration settings and adjusted potion-value weighting so harmful-only effects are handled correctly.
Improved mod-record lookup across plugin filename and extension variants, including light plugins, so supported ingredient and effect records are resolved more reliably.
Settings now allows selecting an existing profile or creating a blank profile when Skyrim has not yet provided the character's identity data.

## 1.3.2
The recipe browser now shows the number of protected ingredients when ingredient protection is enabled.
Ingredient protection requirements refresh automatically when the alchemy menu opens.
CACO potion and poison quality prefixes and effect separators now use localized text.
Ingredient tracking labels, quest grouping options, profile gender labels, and protected-recipe count text now have localization entries for supported languages.
Developer-only potion confirmation capture, inventory observation, quest scanning, and Developer Test Hub actions remain inactive unless developer mode is enabled.
The recipe search field is skipped by keyboard tab navigation so navigation moves directly through actionable controls.

## 1.2.0
Add localization.

## 1.1.0
Expanded the recipe browser with pagination, four sorting modes, an optional Effects column, selectable recipes, and improved loading/completion feedback.
Added filtering by all ingredients currently selected in Skyrim’s alchemy menu; enabled by default and configurable in Settings.
Improved recalculation performance with persistent caching, incremental updates, background processing, debouncing, cancellation, and stale-list/manual recalculation handling.
Improved CACO and combined Alchemy Plus/CACO prediction compatibility, including duration-based effects, mixed potions, partial/legacy records, and safer fallbacks.
Fixed duplicate-name ingredient handling by tracking actual ingredient forms for recipes and ingredient-protection rules.

## 1.0.2
Made the main window more compact.

## 1.0.1
Fixed "Potion of" / "Poison of" setting.
Removed obsolete settings.

## 1.0.0
Updated to use CommonLibSSE-NG.
Updated to be compatible with Complete Alchemy and Cooking Overhaul.
Updated to be compatible with Alchemy Plus.
