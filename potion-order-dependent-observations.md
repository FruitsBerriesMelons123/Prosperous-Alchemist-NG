# CACO Order-Dependent Potion Observations

## [2026-09-15T20:35:52-06:00] Complete baseline matrix passes the order-aware confirmed check (historical snapshot)

The current `links/alchemist.potions-confirmed.csv` contains 12 authoritative CACO rows: all six native selection permutations for each Roobrush form (`0xFE004819` and `0x0833A4D0`). Every row has the required crafted-effect, potion FormID, CACO settings, and native selection-order metadata. The focused `potion_prediction_test.py --check-confirmed-csv` now evaluates the exported selection order and later equal-cost shared-effect candidate, and reports `checked=12 passed=12 failed=0` for this historical snapshot. The live plugin's current confirmation format begins with `mode,ingredients,actual_value` and includes the selection-order field; diagnostic observations are kept in the separate plugin-generated observation CSV.

This observed-craft tie behavior is opt-in to the confirmed-row gate; the general predictor and broad historical predicted-CSV suite were not changed. No additional default CACO captures are needed. The former next validation changed one CACO setting at a time and has since been completed; current duration-family work is documented in `potion-prediction-default-settings.md`.

## [2026-09-15T19:19:15-06:00] Earlier confirmed-fixture baseline (superseded)

At that time, `links/alchemist.potions-confirmed.csv` contained 15 authoritative CACO rows with crafted effects, potion FormIDs, and native ingredient-selection order. All six selection permutations were represented for Roobrush form `0xFE004819`; form `0x0833A4D0` had four unique permutations plus duplicate captures, with `L>S>R` and `R>L>S` still missing. The focused Python checker then reported 7/15, with every failure being an expected 234 versus predicted 249 mismatch. The complete 12-row fixture and order-aware gate now supersede that partial baseline.

## [2026-09-15T18:45:00-06:00] Four additional confirmations narrow the next capture set

The current `links/alchemist.potions-confirmed.csv` contains eight authoritative CACO rows for `Large Antlers, Roobrush, Slaughterfish Egg`, four for each Roobrush form, with `DisableAllPotionHandling=1` and `ImpurePotionProcessing=0`. Across the captured rows, `Lingering Damage Health` has magnitude 2 and value 234 when Slaughterfish Egg is selected after Roobrush, and magnitude 3 and value 249 when Roobrush is selected after Slaughterfish Egg. The two captured relative orders are present for both forms, and Large Antlers does not provide that effect.

This was enough to form a hypothesis that the later-selected candidate wins this shared effect, but it was not a complete permutation matrix and the recipe also contained other shared effects. At that time, no predictor exception or replacement of the unordered evaluation was made. The remaining captures listed below were subsequently supplied and are included in the complete matrix above:

- Roobrush form `0x0833A4D0`: `Large Antlers, Slaughterfish Egg, Roobrush` and `Roobrush, Large Antlers, Slaughterfish Egg`.
- Roobrush form `0xFE004819`: `Roobrush, Slaughterfish Egg, Large Antlers` and `Slaughterfish Egg, Large Antlers, Roobrush`.

Use the same CACO-only settings block as the confirmed rows, retain exact native selection order, and leave the alchemy menu open while crafting. No AP or Vanilla recaptures are required for this follow-up.

## [2026-09-15T18:27:59-06:00] Supported-scope confirmed rows expose two native states

The updated `links/alchemist.potions-confirmed.csv` adds four CACO confirmations captured with CACO potion handling disabled (`DisableAllPotionHandling=1`, `ImpurePotionProcessing=0`). The rows preserve exact native selection order for both Roobrush forms (`0xFE004819` and `0x0833A4D0`). Roobrush-first captures produce Lingering Damage Health magnitude 2 and value 234; Roobrush-last captures produce magnitude 3 and value 249. The generated effects and values are otherwise identical across each state.

The current predictor check is 39/41: both Roobrush-first rows are predicted as 249 instead of 234, while the two Roobrush-last rows pass. This proves the order-sensitive behavior exists inside the supported no-potion-handling scope, but four rows cover only two of six permutations per form. Do not encode a first/last exception until the four missing permutations for each form have been captured.

## [2026-09-15T17:44:28.241-06:00] Native selection-order capture added

The deployed diagnostic build now exports `ingredient_selection_order` in both future confirmation rows and `alchemist.potion-observations.csv`. The value is read from the native `AlchemyMenu::selectedIndexes` sequence and includes each selection position, FormID, and localized name; delayed post-menu events report it as unavailable. The supplied four-row observation CSV predates this field and therefore remains runtime evidence of inventory events only.

## [2026-09-15T15:57:56-06:00] Diagnostic record created

The eight rows in `potion-order-dependent-observations.csv` preserve the user's Large Antlers, Roobrush, and Slaughterfish Egg observations. They are deliberately separate from `alchemist.potions-confirmed.csv` because the observations do not identify one stable value for one recipe:

- With CACO `ImpurePotionProcessing=1`, SkyUI showed 234 when Roobrush was selected first and 249 when Roobrush was selected last, while the later inventory value was 1 in both cases.
- The result occurred with both Roobrush forms (`0xFE004819` and `0x0833A4D0`).
- With `ImpurePotionProcessing=0`, the later inventory value matched the menu value: 234 for the Roobrush-first captures and 249 for the Roobrush-last captures.
- The captured crafted effects also differ: the Roobrush-first captures have Lingering Damage Health magnitude 2, while the Roobrush-last captures have magnitude 3.

Every CSV row has `authoritative=false` and `prediction_treatment=diagnostic-only`. `potion_prediction_test.py` loads and reports these rows during a confirmed-fixture check, but excludes them from expected-value scoring. They must not be copied into `alchemist.potions-confirmed.csv` or converted into a recipe-specific predictor exception.

## Current interpretation

The reviewed CACO path provides a plausible timing explanation. After Skyrim creates the potion, `CACO_CreatePotionPlayerScript` queues `CACO_AdjustPotionThread`. That thread removes and later re-adds the potion. When impurity processing is enabled, CACO's `ImpurePotion` sets the gold value to 20 percent and scales each effect's duration or magnitude to 20 percent before the adjusted potion is returned. A menu/recorder observation can therefore precede the later inventory state.

The CACO Papyrus source reviewed so far does not store ingredient click order or use it in its potion adjustment formula. The remaining order-dependent difference may be caused by Skyrim's native alchemy state, an interaction with SkyUI, or the timing of asynchronous CACO mutation. The supplied evidence is not enough to select among those explanations.

## Handling rule

Treat all CACO and CACO+Alchemy Plus confirmations as observations of a particular runtime stage until a synchronized recraft records the menu value, post-adjustment inventory value, crafted effects, potion FormID, and exact ingredient selection order. Preserve distinct rows when settings, forms, values, or synchronized crafted state differ. Do not use a 1-value fallback and do not globally disable CACO impurity processing in the predictor: either would encode an unproven observation stage rather than model the game.
