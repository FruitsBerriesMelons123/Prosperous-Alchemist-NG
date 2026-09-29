# Notes

## Verify and Fix

Run `python potion_prediction_test.py --check-confirmed-csv --diagnose` to audit confirmed craft rows, identify any failing rows in the Python harness or C++ plugin source (`alchemist/`), and update the code so both Python and C++ achieve 100% PASS and parity against empirical in-game crafts. If you detect anything that would be appropriate to fix, go ahead and fix it appropriately.

## Prompt

Give me instructions to fix `potion_prediction_test.py` so it predicts this row correctly without causing regressions:

### alchemist.potions-confirmed.csv
```csv
mode,ingredients,actual_value,alchemy_level,fortify_alchemy_level,alchemist_rank,physician,benefactor,poisoner,purity,seeker_of_shadows,mod_settings,alchemist_perk_multiplier,ingredient_details,potion_form_id,potion_cost_override,crafted_effects,ingredient_selection_order

```

### python potion_prediction_test.py --confirmed-row <number>
```powershell

```

### python potion_prediction_test.py --check-confirmed-csv
```powershell

```

### python potion_prediction_test.py --check-predicted-csvs
```powershell

```

### python potion_prediction_test.py --check-predicted-csv
```powershell

```

## Debug
Help me appropriately add logging to the code to provide you with the information you need to be able to help me fix the code to accurately predict this potion.

## Fix
Help me appropriately fix the code so it accurately predicts this potion.
