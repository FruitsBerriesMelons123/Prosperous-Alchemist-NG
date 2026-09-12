Scriptname ProsperousAlchemistTests Hidden

Function ClearAllAlchemyPerks(Actor player) global
    player.RemovePerk(Game.GetForm(0x000BE127) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CA) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CB) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CC) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CD) as Perk)
    
    player.RemovePerk(Game.GetForm(0x00058215) as Perk) ; Physician
    player.RemovePerk(Game.GetForm(0x00058216) as Perk) ; Benefactor
    player.RemovePerk(Game.GetForm(0x00058217) as Perk) ; Poisoner
    player.RemovePerk(Game.GetForm(0x00105F2F) as Perk) ; Concentrated Poison
    player.RemovePerk(Game.GetForm(0x00058218) as Perk) ; Experimenter 1
    player.RemovePerk(Game.GetForm(0x00105F2A) as Perk) ; Experimenter 2
    player.RemovePerk(Game.GetForm(0x00105F2B) as Perk) ; Experimenter 3
    player.RemovePerk(Game.GetForm(0x00105F2C) as Perk) ; Snakeblood
    player.RemovePerk(Game.GetForm(0x00105F2E) as Perk) ; Green Thumb
    player.RemovePerk(Game.GetForm(0x0005821D) as Perk) ; Purity
    
    ClearSeekerOfShadows(player)
EndFunction

Function RemoveAllAlchemyPerks(Actor player) global
    ClearAllAlchemyPerks(player)
EndFunction

Function SetAlchemistRank(Actor player, int rank) global
    player.RemovePerk(Game.GetForm(0x000BE127) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CA) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CB) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CC) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CD) as Perk)
    
    if rank == 1
        player.AddPerk(Game.GetForm(0x000BE127) as Perk)
    elseif rank == 2
        player.AddPerk(Game.GetForm(0x000C07CA) as Perk)
    elseif rank == 3
        player.AddPerk(Game.GetForm(0x000C07CB) as Perk)
    elseif rank == 4
        player.AddPerk(Game.GetForm(0x000C07CC) as Perk)
    elseif rank == 5
        player.AddPerk(Game.GetForm(0x000C07CD) as Perk)
    endif
EndFunction

Function ApplySeekerOfShadows(Actor player) global
    Spell seekerSpell = Game.GetFormFromFile(0x034838, "Dragonborn.esm") as Spell
    Perk seekerPerk = Game.GetFormFromFile(0x03399F, "Dragonborn.esm") as Perk
    GlobalVariable seekerGlobal = Game.GetFormFromFile(0x020E9A, "Dragonborn.esm") as GlobalVariable
    
    if seekerSpell
        player.AddSpell(seekerSpell, false)
    endif
    if seekerPerk
        player.AddPerk(seekerPerk)
    endif
    if seekerGlobal
        seekerGlobal.SetValue(3.0)
    endif
EndFunction

Function ClearSeekerOfShadows(Actor player) global
    Spell seekerSpell = Game.GetFormFromFile(0x034838, "Dragonborn.esm") as Spell
    Perk seekerPerk = Game.GetFormFromFile(0x03399F, "Dragonborn.esm") as Perk
    GlobalVariable seekerGlobal = Game.GetFormFromFile(0x020E9A, "Dragonborn.esm") as GlobalVariable
    
    if seekerSpell
        player.RemoveSpell(seekerSpell)
    endif
    if seekerPerk
        player.RemovePerk(seekerPerk)
    endif
    if seekerGlobal
        seekerGlobal.SetValue(0.0)
    endif
EndFunction

Function SetCacoGlobal(int aiFormID, float afVal) global
    GlobalVariable gv = Game.GetFormFromFile(aiFormID, "Complete Alchemy & Cooking Overhaul.esp") as GlobalVariable
    if !gv
        gv = Game.GetFormFromFile(aiFormID, "Complete Alchemy & Cooking Overhaul.esm") as GlobalVariable
    endif
    if !gv
        gv = Game.GetFormFromFile(aiFormID, "Update.esm") as GlobalVariable
    endif
    if !gv
        gv = Game.GetFormFromFile(aiFormID, "Skyrim.esm") as GlobalVariable
    endif
    if !gv
        int altFormID = aiFormID
        if (aiFormID < 0x01000000)
            altFormID = aiFormID + 0x01000000
        endif
        gv = Game.GetFormFromFile(altFormID, "Update.esm") as GlobalVariable
        if !gv
            gv = Game.GetFormFromFile(altFormID, "Skyrim.esm") as GlobalVariable
        endif
        if !gv
            gv = Game.GetFormFromFile(altFormID, "Complete Alchemy & Cooking Overhaul.esp") as GlobalVariable
        endif
    endif
    if gv
        gv.SetValue(afVal)
    endif
EndFunction

string Function SetupVanilla(string variant = "") global
    Actor player = Game.GetPlayer()
    ClearAllAlchemyPerks(player)
    
    string modeTag = "vanilla"
    if variant == "changed"
        modeTag = "vanilla-changed"
        player.SetActorValue("Alchemy", 65)
        player.SetActorValue("FortifyAlchemy", 35)
        SetAlchemistRank(player, 3)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician
        player.AddPerk(Game.GetForm(0x00058216) as Perk) ; Benefactor
        player.AddPerk(Game.GetForm(0x00058217) as Perk) ; Poisoner
        player.AddPerk(Game.GetForm(0x00105F2F) as Perk) ; Concentrated Poison
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.5")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.8")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla Changed State Applied (Skill 65, Fortify 35, Alchemist 3, Perks, InitMult 4.5, SkillFactor 1.8) ---")
    elseif variant == "2"
        modeTag = "vanilla-2"
        player.SetActorValue("Alchemy", 50)
        player.SetActorValue("FortifyAlchemy", 50)
        SetAlchemistRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 2: Skill 50, Fortify 50, Alchemist 2, Physician) ---")
    elseif variant == "3"
        modeTag = "vanilla-3"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician
        player.AddPerk(Game.GetForm(0x00058216) as Perk) ; Benefactor
        player.AddPerk(Game.GetForm(0x00058217) as Perk) ; Poisoner
        player.AddPerk(Game.GetForm(0x0005821D) as Perk) ; Purity
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 3: Purity & Full Perks) ---")
    elseif variant == "4"
        modeTag = "vanilla-4"
        player.SetActorValue("Alchemy", 15)
        player.SetActorValue("FortifyAlchemy", 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 4: Starter Skill 15, No Perks) ---")
    else
        modeTag = "vanilla-1"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 5.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.0")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 1: InitMult 5.0, SkillFactor 2.0) ---")
    endif
    ProvisionAndPrintTests(player, modeTag, variant)
    return "Vanilla test state applied successfully."
EndFunction

string Function SetupCACO(string variant = "") global
    Actor player = Game.GetPlayer()
    ClearAllAlchemyPerks(player)
    
    string modeTag = "caco"
    if variant == "changed"
        modeTag = "caco-changed"
        player.SetActorValue("Alchemy", 55)
        player.SetActorValue("FortifyAlchemy", 45)
        SetAlchemistRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician
        player.AddPerk(Game.GetForm(0x00058217) as Perk) ; Poisoner
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.2")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.8")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2) ; 10s durations for all families
        SetCacoGlobal(0x00AAB031, 1.0) ; DisableAllPotionHandling = 1
        SetCacoGlobal(0x00AAB030, 0.0) ; ImpurePotionProcessing = 0
        ConsoleUtil.PrintMessage("--- [PAT] CACO Changed State Applied (Skill 55, Fortify 45, Alchemist 2, Physician, Poisoner, 10s Durations) ---")
    elseif variant == "2"
        modeTag = "caco-2"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2) ; 10s durations for all families
        SetCacoGlobal(0x00AAB031, 1.0) ; DisableAllPotionHandling = 1
        SetCacoGlobal(0x00AAB030, 0.0) ; ImpurePotionProcessing = 0
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 2: 10s Durations) ---")
    elseif variant == "3"
        modeTag = "caco-3"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 5.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.0")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0) ; 0s durations
        SetCacoGlobal(0x00AAB031, 1.0) ; DisableAllPotionHandling = 1
        SetCacoGlobal(0x00AAB030, 0.0) ; ImpurePotionProcessing = 0
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 3: 0s Durations, Selection Order Test) ---")
    elseif variant == "4"
        modeTag = "caco-4"
        player.SetActorValue("Alchemy", 50)
        player.SetActorValue("FortifyAlchemy", 30)
        SetAlchemistRank(player, 3)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 2, 0, 0, 0, 0) ; Mixed durations (RestoreHealth 5s, RestoreMagicka 10s, DamageHealth 0s)
        SetCacoGlobal(0x00AAB031, 1.0) ; DisableAllPotionHandling = 1
        SetCacoGlobal(0x00AAB030, 0.0) ; ImpurePotionProcessing = 0
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 4: Skill 50, Fortify 30, Perks, Mixed Durations) ---")
    else ; Block 1 (default variant "")
        modeTag = "caco-1"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1) ; 5s durations for all families
        SetCacoGlobal(0x00AAB031, 1.0) ; DisableAllPotionHandling = 1
        SetCacoGlobal(0x00AAB030, 0.0) ; ImpurePotionProcessing = 0
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 1: 5s Durations) ---")
    endif
    ProvisionAndPrintTests(player, modeTag, variant)
    return "CACO test state applied successfully."
EndFunction

string Function SetupAP(string variant = "") global
    Actor player = Game.GetPlayer()
    ClearAllAlchemyPerks(player)
    
    string modeTag = "ap"
    if variant == "changed"
        modeTag = "ap-changed"
        player.SetActorValue("Alchemy", 75)
        player.SetActorValue("FortifyAlchemy", 40)
        SetAlchemistRank(player, 4)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician
        player.AddPerk(Game.GetForm(0x00058216) as Perk) ; Benefactor
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.2")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.6")
        ConsoleUtil.PrintMessage("--- [PAT] AP Changed State Applied (Skill 75, Fortify 40, Alchemist 4, Physician, Benefactor, InitMult 4.2, SkillFactor 1.6) ---")
    elseif variant == "2"
        modeTag = "ap-2"
        player.SetActorValue("Alchemy", 50)
        player.SetActorValue("FortifyAlchemy", 25)
        SetAlchemistRank(player, 3)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 5.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.0")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 2: Skill 50, Fortify 25, Alchemist 3, InitMult 5.0) ---")
    elseif variant == "3"
        modeTag = "ap-3"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 3: Default Rounding 25/5, ImpureFix=True) ---")
    elseif variant == "4"
        modeTag = "ap-4"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician
        player.AddPerk(Game.GetForm(0x00058216) as Perk) ; Benefactor
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 4: High Rounding 50/10, Perks Applied) ---")
    else
        modeTag = "ap-1"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 1: Custom Rounding 10/2, ImpureFix=False) ---")
    endif
    ProvisionAndPrintTests(player, modeTag, variant)
    return "AP test state applied successfully."
EndFunction

string Function SetupCACOAP(string variant = "") global
    Actor player = Game.GetPlayer()
    ClearAllAlchemyPerks(player)
    
    string modeTag = "caco-ap"
    if variant == "changed"
        modeTag = "caco-ap-changed"
        player.SetActorValue("Alchemy", 85)
        player.SetActorValue("FortifyAlchemy", 15)
        SetAlchemistRank(player, 4)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician
        player.AddPerk(Game.GetForm(0x00058216) as Perk) ; Benefactor
        player.AddPerk(Game.GetForm(0x00058217) as Perk) ; Poisoner
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.5")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.5")
        SetAllCacoDurations(1, 2, 0, 2, 1, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP Changed State Applied (Skill 85, Fortify 15, Alchemist 4, Physician, Benefactor, Poisoner, InitMult 3.5, SkillFactor 2.5, Mixed CACO Durations) ---")
    elseif variant == "2"
        modeTag = "caco-ap-2"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        SetAlchemistRank(player, 4)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 2: Alchemist 4, InitMult 4.0) ---")
    elseif variant == "3"
        modeTag = "caco-ap-3"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1) ; All 5s
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 3: 5s Durations, AP Custom Rounding 10/2) ---")
    elseif variant == "4"
        modeTag = "caco-ap-4"
        player.SetActorValue("Alchemy", 50)
        player.SetActorValue("FortifyAlchemy", 20)
        SetAlchemistRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician
        player.AddPerk(Game.GetForm(0x00058216) as Perk) ; Benefactor
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2) ; All 10s
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 4: Skill 50, Fortify 20, Perks, 10s Durations) ---")
    else ; Block 1 (default)
        modeTag = "caco-ap-1"
        player.SetActorValue("Alchemy", 100)
        player.SetActorValue("FortifyAlchemy", 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0) ; All 0s
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 1: 0s Durations, AP Default Rounding) ---")
    endif
    ProvisionAndPrintTests(player, modeTag, variant)
    return "CACO+AP test state applied successfully."
EndFunction

string Function SetupVanillaPurity() global
    return SetupVanilla("3")
EndFunction

string Function SetupVanillaChanged() global
    return SetupVanilla("changed")
EndFunction

string Function SetupAPChanged() global
    return SetupAP("changed")
EndFunction

string Function SetupCACOAPChanged() global
    return SetupCACOAP("changed")
EndFunction

string Function SetupCACOChanged() global
    return SetupCACO("changed")
EndFunction

string Function SetupVanillaDefault() global
    return SetupDefault("vanilla")
EndFunction

string Function SetupAPDefault() global
    return SetupDefault("ap")
EndFunction

string Function SetupCACOAPDefault() global
    return SetupDefault("caco-ap")
EndFunction

string Function SetupCACODefault() global
    return SetupDefault("caco")
EndFunction

string Function SetupDefault(string mode = "vanilla") global
    Actor player = Game.GetPlayer()
    ClearAllAlchemyPerks(player)
    player.SetActorValue("Alchemy", 100)
    player.SetActorValue("FortifyAlchemy", 0)
    
    if mode == "caco" || mode == "c"
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.9")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.0")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] Default CACO State Applied (Skill 100, Fortify 0, No Perks, InitMult 3.9, SkillFactor 1.0, 0s Durations) ---")
        ProvisionAndPrintTests(player, "caco-default", "")
        return "Default CACO test state applied successfully."
    elseif mode == "ap" || mode == "a"
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Default AP State Applied (Skill 100, Fortify 0, No Perks, InitMult 4.0, SkillFactor 1.5) ---")
        ProvisionAndPrintTests(player, "ap-default", "")
        return "Default AP test state applied successfully."
    elseif mode == "caco-ap" || mode == "ca" || mode == "caco+ap"
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.9")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.0")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] Default CACO+AP State Applied (Skill 100, Fortify 0, No Perks, InitMult 3.9, SkillFactor 1.0, 0s Durations) ---")
        ProvisionAndPrintTests(player, "caco-ap-default", "")
        return "Default CACO+AP test state applied successfully."
    else
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Default Vanilla State Applied (Skill 100, Fortify 0, No Perks, InitMult 4.0, SkillFactor 1.5) ---")
        ProvisionAndPrintTests(player, "vanilla-default", "")
        return "Default Vanilla test state applied successfully."
    endif
EndFunction

Function ClearPlayerIngredients(Actor player) global
    Form[] ingredients = PO3_SKSEFunctions.AddItemsOfTypeToArray(player, 30, false, false, false)
    if ingredients
        int i = 0
        while i < ingredients.Length
            Form ing = ingredients[i]
            if ing
                int count = player.GetItemCount(ing)
                if count > 0
                    player.RemoveItem(ing, count, true)
                endif
            endif
            i += 1
        endWhile
    endif
EndFunction

Function ProvisionForm(Actor player, int aiFormID, string plugin1, string plugin2 = "", string plugin3 = "") global
    Form ing = Game.GetFormFromFile(aiFormID, plugin1)
    if !ing && plugin2 != ""
        ing = Game.GetFormFromFile(aiFormID, plugin2)
    endif
    if !ing && plugin3 != ""
        ing = Game.GetFormFromFile(aiFormID, plugin3)
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "ccbgssse037-curios.esl")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "ccbgssse025-advdsgs.esm")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "ccbgssse001-fish.esm")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "ccbgssse067-daedinv.esm")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "ccbgssse003-zombies.esl")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "ccbgssse040-advobgg.esl")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "ccasvsse001-almsivi.esm")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "ccvsvsse004-beaskpeg.esl")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "Complete Alchemy & Cooking Overhaul.esp")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "Complete Alchemy & Cooking Overhaul.esm")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "Skyrim.esm")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "Update.esm")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "Dragonborn.esm")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "Dawnguard.esm")
    endif
    if !ing
        ing = Game.GetFormFromFile(aiFormID, "HearthFires.esm")
    endif
    if ing
        player.AddItem(ing, 99, true)
    endif
EndFunction

Function ProvisionAndPrintTests(Actor player, string mode, string variant) global
    ClearPlayerIngredients(player)
    ConsoleUtil.PrintMessage("Cleared previous ingredients from player inventory.")
    
    if mode == "ap-1" || mode == "ap" && (variant == "" || variant == "1")
        ProvisionForm(player, 0x6BC02, "Skyrim.esm") ; Bear Claws
        ProvisionForm(player, 0xA9195, "Skyrim.esm") ; Bee
        ProvisionForm(player, 0x705B7, "Skyrim.esm") ; Berit's Ashes
        ProvisionForm(player, 0x34CDD, "Skyrim.esm") ; Bone Meal
        ProvisionForm(player, 0x727DF, "Skyrim.esm") ; Luna Moth Wing
        ProvisionForm(player, 0x3AD76, "Skyrim.esm") ; Vampire Dust
        ProvisionForm(player, 0x4DA25, "Skyrim.esm") ; Blisterwort
        if player.GetItemCount(Game.GetFormFromFile(0x4DA25, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x04DA20, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x4B0BA, "Skyrim.esm") ; Wheat
        ConsoleUtil.PrintMessage("Provisioned 99x of 8 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Bear Claws + Bee")
        ConsoleUtil.PrintMessage("Craft: Berit's Ashes + Bone Meal")
        ConsoleUtil.PrintMessage("Craft: Luna Moth Wing + Vampire Dust")
        ConsoleUtil.PrintMessage("Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next command: run 'pat ap 2'")
    elseif mode == "ap-2"
        ProvisionForm(player, 0x3AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x6ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x77E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x4DA23, "Skyrim.esm") ; Imp Stool
        ProvisionForm(player, 0x889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x4DA00, "Skyrim.esm") ; Fly Amanita
        ConsoleUtil.PrintMessage("Provisioned 99x of 7 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Briar Heart + Canis Root")
        ConsoleUtil.PrintMessage("Craft: Blue Butterfly Wing + Blue Mountain Flower")
        ConsoleUtil.PrintMessage("Craft: Canis Root + Imp Stool")
        ConsoleUtil.PrintMessage("Craft: Dragon's Tongue + Fly Amanita")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-ap-2.py'")
    elseif mode == "ap-3"
        ProvisionForm(player, 0x4DA25, "Skyrim.esm") ; Blisterwort
        if player.GetItemCount(Game.GetFormFromFile(0x4DA25, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x04DA20, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x4B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x106E1A, "Skyrim.esm") ; River Betty
        if player.GetItemCount(Game.GetFormFromFile(0x106E1A, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x63B5D, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x34CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x34D22, "Skyrim.esm") ; Garlic
        ProvisionForm(player, 0x3AD56, "Skyrim.esm") ; Chaurus Eggs
        ProvisionForm(player, 0x727DF, "Skyrim.esm") ; Luna Moth Wing
        ConsoleUtil.PrintMessage("Provisioned 99x of 8 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("Craft: Chaurus Eggs + Luna Moth Wing")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next command: run 'pat ap 4'")
    elseif mode == "ap-4"
        ProvisionForm(player, 0x7EE01, "Skyrim.esm") ; Glowing Mushroom
        ProvisionForm(player, 0x2F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0xB2183, "Skyrim.esm", "Update.esm") ; Creep Cluster
        if player.GetItemCount(Game.GetFormFromFile(0xB2183, "Skyrim.esm")) == 0
            ProvisionForm(player, 0xB18CD, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x6F950, "Skyrim.esm") ; Scaly Pholiota
        ProvisionForm(player, 0xEC870, "Skyrim.esm") ; Mora Tapinella
        ProvisionForm(player, 0x3AD64, "Skyrim.esm") ; Giant's Toe
        if player.GetItemCount(Game.GetFormFromFile(0x3AD64, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x3AD5F, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x4B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x106E1B, "Skyrim.esm") ; Abecean Longfin
        ProvisionForm(player, 0x106E19, "Skyrim.esm") ; Cyrodilic Spadetail
        ProvisionForm(player, 0x34CDF, "Skyrim.esm") ; Salt Pile
        ConsoleUtil.PrintMessage("Provisioned 99x of 10 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Glowing Mushroom + Nightshade")
        ConsoleUtil.PrintMessage("Craft: Creep Cluster + Scaly Pholiota + Mora Tapinella")
        ConsoleUtil.PrintMessage("Craft: Giant's Toe + Wheat")
        ConsoleUtil.PrintMessage("Craft: Abecean Longfin + Cyrodilic Spadetail + Salt Pile")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-vanilla.py'")
    elseif mode == "vanilla-1" || mode == "vanilla" && (variant == "" || variant == "1")
        ProvisionForm(player, 0x4DA25, "Skyrim.esm") ; Blisterwort
        if player.GetItemCount(Game.GetFormFromFile(0x4DA25, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x04DA20, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x4B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x106E1A, "Skyrim.esm") ; River Betty
        if player.GetItemCount(Game.GetFormFromFile(0x106E1A, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x63B5D, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x77E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x34CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x34D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("Provisioned 99x of 8 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("Craft: Blue Mountain Flower + Blue Butterfly Wing")
        ConsoleUtil.PrintMessage("Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 2'")
    elseif mode == "vanilla-2"
        ProvisionForm(player, 0x6BC02, "Skyrim.esm") ; Bear Claws
        ProvisionForm(player, 0xA9195, "Skyrim.esm") ; Bee
        ProvisionForm(player, 0x705B7, "Skyrim.esm") ; Berit's Ashes
        ProvisionForm(player, 0x34CDD, "Skyrim.esm") ; Bone Meal
        ProvisionForm(player, 0x3AD66, "Skyrim.esm") ; Hagraven Feathers
        ProvisionForm(player, 0xB18CD, "Skyrim.esm", "Update.esm") ; Human Heart
        ProvisionForm(player, 0x727DF, "Skyrim.esm") ; Luna Moth Wing
        ProvisionForm(player, 0x3AD76, "Skyrim.esm") ; Vampire Dust
        ConsoleUtil.PrintMessage("Provisioned 99x of 8 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Bear Claws + Bee")
        ConsoleUtil.PrintMessage("Craft: Berit's Ashes + Bone Meal")
        ConsoleUtil.PrintMessage("Craft: Hagraven Feathers + Human Heart")
        ConsoleUtil.PrintMessage("Craft: Luna Moth Wing + Vampire Dust")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-vanilla-2.py'")
    elseif mode == "vanilla-3"
        ProvisionForm(player, 0x77E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x4B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x4DA25, "Skyrim.esm") ; Blisterwort
        if player.GetItemCount(Game.GetFormFromFile(0x4DA25, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x04DA20, "Skyrim.esm")
        endif
        ProvisionForm(player, 0xB2183, "Skyrim.esm", "Update.esm") ; Creep Cluster
        if player.GetItemCount(Game.GetFormFromFile(0xB2183, "Skyrim.esm")) == 0
            ProvisionForm(player, 0xB18CD, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x3AD64, "Skyrim.esm") ; Giant's Toe
        if player.GetItemCount(Game.GetFormFromFile(0x3AD64, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x3AD5F, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x3AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x6ABCB, "Skyrim.esm") ; Canis Root
        ConsoleUtil.PrintMessage("Provisioned 99x of 7 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Blue Mountain Flower + Wheat")
        ConsoleUtil.PrintMessage("Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("Craft: Creep Cluster + Giant's Toe + Wheat")
        ConsoleUtil.PrintMessage("Craft: Briar Heart + Canis Root")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 4'")
    elseif mode == "vanilla-4"
        ProvisionForm(player, 0x4DA25, "Skyrim.esm") ; Blisterwort
        if player.GetItemCount(Game.GetFormFromFile(0x4DA25, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x04DA20, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x4B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x106E1A, "Skyrim.esm") ; River Betty
        if player.GetItemCount(Game.GetFormFromFile(0x106E1A, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x63B5D, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x77E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ConsoleUtil.PrintMessage("Provisioned 99x of 6 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("Craft: Blue Mountain Flower + Blue Butterfly Wing")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-caco.py'")
    elseif mode == "caco-1" || mode == "caco" && (variant == "" || variant == "1")
        ProvisionForm(player, 0x01CD6F, "Dragonborn.esm", "Skyrim.esm") ; Boar Tusk
        if player.GetItemCount(Game.GetFormFromFile(0x01CD6F, "Dragonborn.esm")) == 0
            ProvisionForm(player, 0x01F8AA, "Dragonborn.esm")
        endif
        ProvisionForm(player, 0x3AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0xB2183, "Skyrim.esm", "Update.esm") ; Creep Cluster
        if player.GetItemCount(Game.GetFormFromFile(0xB2183, "Skyrim.esm")) == 0
            ProvisionForm(player, 0xB18CD, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x3AD64, "Skyrim.esm") ; Giant's Toe
        if player.GetItemCount(Game.GetFormFromFile(0x3AD64, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x3AD5F, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x4DA25, "Skyrim.esm") ; Blisterwort
        if player.GetItemCount(Game.GetFormFromFile(0x4DA25, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x04DA20, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x4B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x6ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x9151B, "Skyrim.esm") ; Spider Egg
        ConsoleUtil.PrintMessage("Provisioned 99x of 8 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Boar Tusk + Briar Heart")
        ConsoleUtil.PrintMessage("Craft: Creep Cluster + Giant's Toe")
        ConsoleUtil.PrintMessage("Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("Craft: Canis Root + Spider Egg")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 2'")
    elseif mode == "caco-2"
        ProvisionForm(player, 0x4DA25, "Skyrim.esm") ; Blisterwort
        if player.GetItemCount(Game.GetFormFromFile(0x4DA25, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x04DA20, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x5A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x106E1A, "Skyrim.esm") ; River Betty
        if player.GetItemCount(Game.GetFormFromFile(0x106E1A, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x63B5D, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x0059BA, "Dawnguard.esm", "Skyrim.esm") ; Ancestor Moth
        ProvisionForm(player, 0x77E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x3AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x3AD63, "Skyrim.esm") ; Ectoplasm
        ConsoleUtil.PrintMessage("Provisioned 99x of 8 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Blisterwort + Wheat Extract")
        ConsoleUtil.PrintMessage("Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("Craft: Ancestor Moth + Blue Mountain Flower")
        ConsoleUtil.PrintMessage("Craft: Briar Heart + Ectoplasm")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-caco-2.py'")
    elseif mode == "caco-3"
        ProvisionForm(player, 0x33A4D0, "Complete Alchemy & Cooking Overhaul.esp", "ccbgssse037-curios.esl") ; Roobrush
        if player.GetItemCount(Game.GetFormFromFile(0x33A4D0, "Complete Alchemy & Cooking Overhaul.esp")) == 0
            ProvisionForm(player, 0x004819, "ccbgssse037-curios.esl")
        endif
        ProvisionForm(player, 0x7E8C5, "Skyrim.esm") ; Slaughterfish Egg
        ProvisionForm(player, 0x6BC0A, "Skyrim.esm") ; Large Antlers
        if player.GetItemCount(Game.GetFormFromFile(0x6BC0A, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x6BC04, "Skyrim.esm")
        endif
        ConsoleUtil.PrintMessage("Provisioned 99x of 3 test ingredients (Order Selection Test).")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft Order 1: Roobrush -> Slaughterfish Egg -> Large Antlers")
        ConsoleUtil.PrintMessage("Craft Order 2: Slaughterfish Egg -> Roobrush -> Large Antlers")
        ConsoleUtil.PrintMessage("Craft Order 3: Large Antlers -> Roobrush -> Slaughterfish Egg")
        ConsoleUtil.PrintMessage("Craft Order 4: Large Antlers -> Slaughterfish Egg -> Roobrush")
        ConsoleUtil.PrintMessage("Craft Order 5: Roobrush -> Large Antlers -> Slaughterfish Egg")
        ConsoleUtil.PrintMessage("Craft Order 6: Slaughterfish Egg -> Large Antlers -> Roobrush")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 4'")
    elseif mode == "caco-4"
        ProvisionForm(player, 0x7E8B7, "Skyrim.esm") ; Swamp Fungal Pod
        ProvisionForm(player, 0x5A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x6BC00, "Skyrim.esm") ; Mudcrab Chitin
        ProvisionForm(player, 0x3AD76, "Skyrim.esm") ; Vampire Dust
        ProvisionForm(player, 0x3AD56, "Skyrim.esm") ; Chaurus Eggs
        ProvisionForm(player, 0x889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x4DA00, "Skyrim.esm") ; Fly Amanita
        ConsoleUtil.PrintMessage("Provisioned 99x of 7 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Swamp Fungal Pod + Wheat Extract")
        ConsoleUtil.PrintMessage("Craft: Mudcrab Chitin + Vampire Dust")
        ConsoleUtil.PrintMessage("Craft: Chaurus Eggs + Vampire Dust")
        ConsoleUtil.PrintMessage("Craft: Dragon's Tongue + Fly Amanita")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-caco-ap.py'")
    elseif mode == "caco-ap-1" || mode == "caco-ap" && (variant == "" || variant == "1")
        ProvisionForm(player, 0x4DA25, "Skyrim.esm") ; Blisterwort
        if player.GetItemCount(Game.GetFormFromFile(0x4DA25, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x04DA20, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x5A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x106E1A, "Skyrim.esm") ; River Betty
        if player.GetItemCount(Game.GetFormFromFile(0x106E1A, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x63B5D, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x01CD74, "Dragonborn.esm", "Skyrim.esm") ; Ash Creep Cluster
        ProvisionForm(player, 0x004806, "ccbgssse037-curios.esl", "Complete Alchemy & Cooking Overhaul.esp") ; Comberry
        ProvisionForm(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", "ccbgssse037-curios.esl") ; Aloe Vera / Aloe Vera Leaves
        if player.GetItemCount(Game.GetFormFromFile(0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp")) == 0
            ProvisionForm(player, 0x0060D0, "ccbgssse037-curios.esl")
        endif
        ProvisionForm(player, 0x3AD5B, "Skyrim.esm") ; Daedra Heart
        ProvisionForm(player, 0x6BC0A, "Skyrim.esm") ; Large Antlers
        if player.GetItemCount(Game.GetFormFromFile(0x6BC0A, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x6BC04, "Skyrim.esm")
        endif
        ConsoleUtil.PrintMessage("Provisioned 99x of 9 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Blisterwort + Wheat Extract")
        ConsoleUtil.PrintMessage("Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("Craft: Ash Creep Cluster + Comberry")
        ConsoleUtil.PrintMessage("Craft: Aloe Vera + Daedra Heart + Large Antlers")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco-ap 2'")
    elseif mode == "caco-ap-2"
        ProvisionForm(player, 0x77E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x004D6C, "ccbgssse037-curios.esl", "Complete Alchemy & Cooking Overhaul.esp") ; Bog Beacon
        ProvisionForm(player, 0x1BCBC, "Skyrim.esm") ; Jarrin Root
        ProvisionForm(player, 0x01CD74, "Dragonborn.esm", "Skyrim.esm") ; Ash Creep Cluster
        ProvisionForm(player, 0xB701A, "Skyrim.esm") ; Crimson Nirnroot
        ProvisionForm(player, 0x6ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x9151B, "Skyrim.esm") ; Spider Egg
        ProvisionForm(player, 0x889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x4DA00, "Skyrim.esm") ; Fly Amanita
        ConsoleUtil.PrintMessage("Provisioned 99x of 9 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Blue Mountain Flower + Bog Beacon + Jarrin Root")
        ConsoleUtil.PrintMessage("Craft: Ash Creep Cluster + Crimson Nirnroot")
        ConsoleUtil.PrintMessage("Craft: Canis Root + Spider Egg")
        ConsoleUtil.PrintMessage("Craft: Dragon's Tongue + Fly Amanita")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-caco-ap-2.py'")
    elseif mode == "caco-ap-3"
        ProvisionForm(player, 0x01CD6F, "Dragonborn.esm", "Skyrim.esm") ; Boar Tusk
        if player.GetItemCount(Game.GetFormFromFile(0x01CD6F, "Dragonborn.esm")) == 0
            ProvisionForm(player, 0x01F8AA, "Dragonborn.esm")
        endif
        ProvisionForm(player, 0x3AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0xB2183, "Skyrim.esm", "Update.esm") ; Creep Cluster
        if player.GetItemCount(Game.GetFormFromFile(0xB2183, "Skyrim.esm")) == 0
            ProvisionForm(player, 0xB18CD, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x3AD64, "Skyrim.esm") ; Giant's Toe
        if player.GetItemCount(Game.GetFormFromFile(0x3AD64, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x3AD5F, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x77E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x004D6C, "ccbgssse037-curios.esl", "Complete Alchemy & Cooking Overhaul.esp") ; Bog Beacon
        ProvisionForm(player, 0x1BCBC, "Skyrim.esm") ; Jarrin Root
        ProvisionForm(player, 0x01CD74, "Dragonborn.esm", "Skyrim.esm") ; Ash Creep Cluster
        ProvisionForm(player, 0xB701A, "Skyrim.esm") ; Crimson Nirnroot
        ConsoleUtil.PrintMessage("Provisioned 99x of 9 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Boar Tusk + Briar Heart")
        ConsoleUtil.PrintMessage("Craft: Creep Cluster + Giant's Toe")
        ConsoleUtil.PrintMessage("Craft: Blue Mountain Flower + Bog Beacon + Jarrin Root")
        ConsoleUtil.PrintMessage("Craft: Ash Creep Cluster + Crimson Nirnroot")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco-ap 4'")
    elseif mode == "caco-ap-4"
        ProvisionForm(player, 0x4DA25, "Skyrim.esm") ; Blisterwort
        if player.GetItemCount(Game.GetFormFromFile(0x4DA25, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x04DA20, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x5A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x106E1A, "Skyrim.esm") ; River Betty
        if player.GetItemCount(Game.GetFormFromFile(0x106E1A, "Skyrim.esm")) == 0
            ProvisionForm(player, 0x63B5D, "Skyrim.esm")
        endif
        ProvisionForm(player, 0x01CD74, "Dragonborn.esm", "Skyrim.esm") ; Ash Creep Cluster
        ProvisionForm(player, 0x004806, "ccbgssse037-curios.esl", "Complete Alchemy & Cooking Overhaul.esp") ; Comberry
        ConsoleUtil.PrintMessage("Provisioned 99x of 6 test ingredients.")
        ConsoleUtil.PrintMessage("--- Next Tests To Perform ---")
        ConsoleUtil.PrintMessage("Craft: Blisterwort + Wheat Extract")
        ConsoleUtil.PrintMessage("Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("Craft: Ash Creep Cluster + Comberry")
        ConsoleUtil.PrintMessage("Press F in alchemy menu to refresh inventory.")
        ConsoleUtil.PrintMessage("--- MINIMAL BUT FULLY COMPREHENSIVE TEST SUITE EXECUTION COMPLETE ---")
        ConsoleUtil.PrintMessage("Exit Skyrim now.")
    elseif mode == "vanilla-changed" || mode == "ap-changed" || mode == "caco-ap-changed" || mode == "caco-changed" || mode == "vanilla-default" || mode == "ap-default" || mode == "caco-ap-default" || mode == "caco-default"
        ConsoleUtil.PrintMessage("--- Next Action ---")
        ConsoleUtil.PrintMessage("Run in-game 'export potion prediction csv' command/hotkey.")
        ConsoleUtil.PrintMessage("Then exit Skyrim and run 'python sync_potion_predictions.py'")
    endif
EndFunction

Function ApplyCacoDurationFamily(int aiGlobalFormID, int aiDurationIndex, \
                                 int aiList1, int aiList2, int aiList3, int aiList4, \
                                 int aiEff1, int aiEff5, int aiEff10, \
                                 int aiAltEff1 = 0, int aiAltEff5 = 0, int aiAltEff10 = 0) global
    SetCacoGlobal(aiGlobalFormID, aiDurationIndex as float)
    
    int targetSecs = 1
    if aiDurationIndex == 1
        targetSecs = 5
    elseif aiDurationIndex == 2
        targetSecs = 10
    endif
    
    UpdateCacoIngredientList(aiList1, 0, targetSecs)
    UpdateCacoIngredientList(aiList2, 1, targetSecs)
    UpdateCacoIngredientList(aiList3, 2, targetSecs)
    UpdateCacoIngredientList(aiList4, 3, targetSecs)
    
    string cacoPlugin = "Complete Alchemy & Cooking Overhaul.esp"
    Form testForm = Game.GetFormFromFile(aiEff1, cacoPlugin)
    if !testForm
        cacoPlugin = "Complete Alchemy & Cooking Overhaul.esm"
    endif
    MagicEffect m1 = Game.GetFormFromFile(aiEff1, cacoPlugin) as MagicEffect
    MagicEffect m5 = Game.GetFormFromFile(aiEff5, cacoPlugin) as MagicEffect
    MagicEffect m10 = Game.GetFormFromFile(aiEff10, cacoPlugin) as MagicEffect
    
    MagicEffect alt1 = None
    MagicEffect alt5 = None
    MagicEffect alt10 = None
    if aiAltEff1 != 0
        alt1 = Game.GetFormFromFile(aiAltEff1, cacoPlugin) as MagicEffect
        alt5 = Game.GetFormFromFile(aiAltEff5, cacoPlugin) as MagicEffect
        alt10 = Game.GetFormFromFile(aiAltEff10, cacoPlugin) as MagicEffect
    endif
    
    if aiDurationIndex == 0
        if m1
            m1.ClearEffectFlag(0x8000)
        endif
        if m5
            m5.SetEffectFlag(0x8000)
        endif
        if m10
            m10.SetEffectFlag(0x8000)
        endif
        if alt1
            alt1.ClearEffectFlag(0x8000)
        endif
        if alt5
            alt5.SetEffectFlag(0x8000)
        endif
        if alt10
            alt10.SetEffectFlag(0x8000)
        endif
    elseif aiDurationIndex == 1
        if m1
            m1.SetEffectFlag(0x8000)
        endif
        if m5
            m5.ClearEffectFlag(0x8000)
        endif
        if m10
            m10.SetEffectFlag(0x8000)
        endif
        if alt1
            alt1.SetEffectFlag(0x8000)
        endif
        if alt5
            alt5.ClearEffectFlag(0x8000)
        endif
        if alt10
            alt10.SetEffectFlag(0x8000)
        endif
    else ; index 2
        if m1
            m1.SetEffectFlag(0x8000)
        endif
        if m5
            m5.SetEffectFlag(0x8000)
        endif
        if m10
            m10.ClearEffectFlag(0x8000)
        endif
        if alt1
            alt1.SetEffectFlag(0x8000)
        endif
        if alt5
            alt5.SetEffectFlag(0x8000)
        endif
        if alt10
            alt10.ClearEffectFlag(0x8000)
        endif
    endif
EndFunction

Function UpdateCacoIngredientList(int aiFormListID, int aiEffectPos, int aiTargetSecs) global
    string cacoPlugin = "Complete Alchemy & Cooking Overhaul.esp"
    FormList list = Game.GetFormFromFile(aiFormListID, cacoPlugin) as FormList
    if !list
        cacoPlugin = "Complete Alchemy & Cooking Overhaul.esm"
        list = Game.GetFormFromFile(aiFormListID, cacoPlugin) as FormList
    endif
    if !list
        return
    endif
    int count = list.GetSize()
    while count > 0
        count -= 1
        Ingredient ing = list.GetAt(count) as Ingredient
        if ing
            ing.SetNthEffectDuration(aiEffectPos, aiTargetSecs)
        endif
    endWhile
EndFunction

Function SetAllCacoDurations(int restH, int restM, int restS, int dmgH, int dmgM, int dmgS) global
    ; Restore Health
    ApplyCacoDurationFamily(0x00CCA010, restH, \
                           0x000D03ED, 0x000D03EE, 0x000D03EF, 0x000D03F0, \
                           0x001AA0B6, 0x001AA0B7, 0x001AA0B8, \
                           0x005BDD37, 0x005BDD39, 0x005BDD3A)
    ; Restore Magicka
    ApplyCacoDurationFamily(0x00CCA011, restM, \
                           0x000D03F1, 0x000D03F2, 0x000D03F3, 0x000D03F4, \
                           0x001B42BE, 0x001B42BF, 0x001B42C0)
    ; Restore Stamina
    ApplyCacoDurationFamily(0x00CCA012, restS, \
                           0x000D03F5, 0x000D03F6, 0x000D03F7, 0x000D03F8, \
                           0x001B42BB, 0x001B42BC, 0x001B42BD)
    ; Damage Health
    ApplyCacoDurationFamily(0x00CCA013, dmgH, \
                           0x001B93CB, 0x001B93CC, 0x001B93CD, 0x001B93CE, \
                           0x001B93C8, 0x001B93C9, 0x001B93CA, \
                           0x00316D85, 0x00316D86, 0x00316D7F)
    ; Damage Magicka
    ApplyCacoDurationFamily(0x00CCA014, dmgM, \
                           0x001B93CF, 0x001B93D0, 0x001B93D1, 0x001B93D2, \
                           0x001B93C5, 0x001B93C6, 0x001B93C7)
    ; Damage Stamina
    ApplyCacoDurationFamily(0x00CCA015, dmgS, \
                           0x001B93D3, 0x001B93D4, 0x001B93D5, 0x001B93D6, \
                           0x001B93C2, 0x001B93C3, 0x001B93C4)
EndFunction
