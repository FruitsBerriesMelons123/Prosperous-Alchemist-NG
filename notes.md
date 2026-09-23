# Notes

## Verify and Fix

Run `python potion_prediction_test.py --check-confirmed-csv --diagnose` to audit confirmed craft rows, identify any failing rows in the Python harness or C++ plugin source (`alchemist/`), and update the code so both Python and C++ achieve 100% PASS and parity against empirical in-game crafts.

## Prompt

Give me instructions to fix `potion_prediction_test.py` so it predicts this row correctly without causing regressions:

### alchemist.potions-confirmed.csv
```csv
mode,ingredients,actual_value,alchemy_level,fortify_alchemy_level,alchemist_rank,physician,benefactor,poisoner,purity,seeker_of_shadows,mod_settings,alchemist_perk_multiplier,ingredient_details,potion_form_id,potion_cost_override,crafted_effects,ingredient_selection_order
Requiem,"Ash Creep Cluster, Flame Stalk, Frost Salts",709,100,0,1,0,0,0,0,0,"{""AlchemicalLoreRank"":""1"",""AlchemyIngredientInitMultiplier"":4.0,""AlchemySkillFactor"":1.100000023841858,""HasImprovedElixirs"":""0"",""HasImprovedPoisons"":""0"",""HasPurificationProcess"":""0"",""HasUnperkedCraftingKeyword"":""0""}",1.25,"Ash Creep Cluster [form=0x0401CD74, count=1]; Flame Stalk [form=0xFE00482A, count=1]; Frost Salts [form=0x0003AD5F, count=1]",0xFF00092E,0,index=0|form_id=0x0003EAEB|magnitude=33|duration=300|area=0|base_cost=0.25|flags=0x00201002;index=1|form_id=0x0003EB3D|magnitude=0|duration=33|area=0|base_cost=50|flags=0x00401C02;index=2|form_id=0x00073F2D|magnitude=22|duration=30|area=0|base_cost=0.300000012|flags=0x00201007,selection=1|form_id=0x0401CD74|name=A;selection=2|form_id=0xFE00482A|name=F;selection=3|form_id=0x0003AD5F|name=F
```

### python potion_prediction_test.py --confirmed-row <number>
```powershell
PS E:\Projects\games\skyrim\prosperous-alchemist\pa-ng> python potion_prediction_test.py --confirmed-row 310             
Row 310 settings read from E:\Projects\games\skyrim\prosperous-alchemist\pa-ng\links\alchemist.potions-confirmed.csv:
  Mode: Requiem (caco_enabled=False, alchemy_plus_enabled=False)
  Recipe Ingredients: Ash Creep Cluster, Flame Stalk, Frost Salts
  Selection Order Recipe: Ash Creep Cluster@0x401CD74, Flame Stalk@0xFE00482A, Frost Salts@0x3AD5F
  Confirmed In-Game Observed Value (from CSV): 709
  Player Settings:
    alchemy_level: 100.0
    fortify_alchemy_level: 0.0
    alchemist_rank: 1
    alchemist_perk_multiplier: 1.25
    physician: False
    benefactor: False
    poisoner: False
    purity: False
    seeker_of_shadows: False

CSV Data Source: E:\Projects\games\skyrim\prosperous-alchemist\pa-ng\ingredients-requiem.csv
Mode: requiem
Ingredients: Ash Creep Cluster@0x401CD74, Flame Stalk@0xFE00482A, Frost Salts@0x3AD5F
Type: Potion
Effects: 3
  Resist Frost [0x3EAEB] magnitude=33 duration=300 cost=493.331359 (Python script calculated effect cost) order=493.331359 (Python script candidate order cost)
  Invisibility [0x3EB3D] magnitude=0 duration=33 cost=185.92395 (Python script calculated effect cost) order=185.92395 (Python script candidate order cost)
  Weakness to Fire [0x73F2D] magnitude=17 duration=60 cost=48.593867 (Python script calculated effect cost) order=48.593867 (Python script candidate order cost)
Beneficial: True
Harmful: True
Pre-adjustment gold (Python script floor): 727
Predicted float value (Python script calculation): 727.849182
Displayed integer value (Python script floor prediction): 727
Alchemy Plus impure adjustment: False
CACO impure adjustment: False

Confirmed Row 310 Test: Expected (In-Game Observed Craft from CSV) = 709, Predicted (Python Test Harness Script) = 727, Status = FAIL
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
