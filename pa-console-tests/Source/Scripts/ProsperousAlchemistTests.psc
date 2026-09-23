Scriptname ProsperousAlchemistTests Hidden

Function ClearAllAlchemyPerks(Actor player) global
    player.RemovePerk(Game.GetForm(0x000BE127) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CA) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CB) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CC) as Perk)
    player.RemovePerk(Game.GetForm(0x000C07CD) as Perk)
    
    player.RemovePerk(Game.GetForm(0x00058215) as Perk) ; Physician
    player.RemovePerk(Game.GetForm(0x00058216) as Perk) ; Benefactor / Improved Elixirs
    player.RemovePerk(Game.GetForm(0x00058217) as Perk) ; Poisoner / Improved Poisons
    player.RemovePerk(Game.GetForm(0x00058218) as Perk) ; Experimenter 1
    player.RemovePerk(Game.GetForm(0x00105F2A) as Perk) ; Experimenter 2
    player.RemovePerk(Game.GetForm(0x00105F2B) as Perk) ; Experimenter 3
    player.RemovePerk(Game.GetForm(0x00105F2C) as Perk) ; Snakeblood
    player.RemovePerk(Game.GetForm(0x00105F2E) as Perk) ; Green Thumb
    player.RemovePerk(Game.GetForm(0x0005821D) as Perk) ; Purity / Purification Process
    
    ClearSeekerOfShadows(player)
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

Function SetRequiemLoreRank(Actor player, int rank) global
    if rank >= 1
        player.AddPerk(Game.GetForm(0x000BE127) as Perk) ; Requiem Alchemical Lore 1
    endif
    if rank >= 2
        player.AddPerk(Game.GetForm(0x000C07CA) as Perk) ; Requiem Alchemical Lore 2
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
        gv = Game.GetFormFromFile(aiFormID, "CACO.esp") as GlobalVariable
    endif
    if !gv
        gv = Game.GetFormFromFile(aiFormID, "CACO.esm") as GlobalVariable
    endif
    if !gv
        gv = Game.GetFormFromFile(aiFormID, "CACO.esl") as GlobalVariable
    endif
    if !gv
        gv = Game.GetFormFromFile(aiFormID, "Update.esm") as GlobalVariable
    endif
    if !gv
        gv = Game.GetFormFromFile(aiFormID, "Skyrim.esm") as GlobalVariable
    endif
    if gv
        gv.SetValue(afVal)
    endif
EndFunction

Function SetCacoDurationGlobal(int aiFormID, int aiVal) global
    SetCacoGlobal(aiFormID, aiVal as float)
EndFunction

Function SetAllCacoDurations(int valH, int valM, int valS, int valDH, int valDM, int valDS) global
    SetCacoDurationGlobal(0x00CCA010, valH)
    SetCacoDurationGlobal(0x00CCA011, valM)
    SetCacoDurationGlobal(0x00CCA012, valS)
    SetCacoDurationGlobal(0x00CCA013, valDH)
    SetCacoDurationGlobal(0x00CCA014, valDM)
    SetCacoDurationGlobal(0x00CCA015, valDS)
    ConsoleUtil.PrintMessage("CACO Durations Set: RestH=" + valH + ", RestM=" + valM + ", RestS=" + valS + ", DmgH=" + valDH + ", DmgM=" + valDM + ", DmgS=" + valDS)
EndFunction

Function ClearFortifyAlchemyState(Actor player) global
    if !player
        return
    endif
    Form circlet = Game.GetFormFromFile(0x000FC005, "Skyrim.esm") ; Circlet of Peerless Alchemy (+25%)
    if circlet
        if player.IsEquipped(circlet)
            player.UnequipItem(circlet, false, true)
        endif
        if player.GetItemCount(circlet) > 0
            player.RemoveItem(circlet, player.GetItemCount(circlet), true)
        endif
    endif
    Form necklace = Game.GetFormFromFile(0x0010DF4A, "Skyrim.esm") ; Necklace of Peerless Alchemy (+25%)
    if necklace
        if player.IsEquipped(necklace)
            player.UnequipItem(necklace, false, true)
        endif
        if player.GetItemCount(necklace) > 0
            player.RemoveItem(necklace, player.GetItemCount(necklace), true)
        endif
    endif
    Form item3 = Game.GetFormFromFile(0x000CF8A1, "Skyrim.esm")
    if item3
        if player.IsEquipped(item3)
            player.UnequipItem(item3, false, true)
        endif
        if player.GetItemCount(item3) > 0
            player.RemoveItem(item3, player.GetItemCount(item3), true)
        endif
    endif
    Form item4 = Game.GetFormFromFile(0x000CF889, "Skyrim.esm")
    if item4
        if player.IsEquipped(item4)
            player.UnequipItem(item4, false, true)
        endif
        if player.GetItemCount(item4) > 0
            player.RemoveItem(item4, player.GetItemCount(item4), true)
        endif
    endif
    player.SetActorValue("FortifyAlchemy", 0)
EndFunction

Function ResetAlchemyXP(Actor player) global
    ActorValueInfo avi = ActorValueInfo.GetActorValueInfoByName("Alchemy")
    if avi
        avi.SetSkillExperience(0.0)
    endif
    player.SetActorValue("AlchemySkillAdvance", 0)
EndFunction

Function ResetPlayerState(Actor player) global
    ClearPlayerIngredients(player)
    ClearAllAlchemyPerks(player)
    ClearFortifyAlchemyState(player)
    ResetAlchemyXP(player)
    player.SetActorValue("Alchemy", 100)
    player.ForceActorValue("Alchemy", 100)
EndFunction

Function ApplyFortifyAlchemyGear(Actor player) global
    if !player
        return
    endif
    Form circlet = Game.GetFormFromFile(0x000FC005, "Skyrim.esm") ; Circlet of Peerless Alchemy (+25%)
    Form necklace = Game.GetFormFromFile(0x0010DF4A, "Skyrim.esm") ; Necklace of Peerless Alchemy (+25%)
    if circlet
        player.AddItem(circlet, 1, true)
        player.EquipItem(circlet, true, true)
    endif
    if necklace
        player.AddItem(necklace, 1, true)
        player.EquipItem(necklace, true, true)
    endif
EndFunction

string Function SetupVanilla(string variant = "") global
    Actor player = Game.GetPlayer()
    ResetPlayerState(player)
    
    string modeTag = "vanilla"
    if variant == "changed"
        modeTag = "vanilla-changed"
        player.SetActorValue("Alchemy", 65)
        player.ForceActorValue("Alchemy", 65)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 3)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        player.AddPerk(Game.GetForm(0x00105F2F) as Perk)
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.5")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.8")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla Changed State Applied ---")
    elseif variant == "2"
        modeTag = "vanilla-2"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 1)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 2: Alchemist 1) ---")
    elseif variant == "3"
        modeTag = "vanilla-3"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 3)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 3: Alchemist 3) ---")
    elseif variant == "4"
        modeTag = "vanilla-4"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 5)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 4: Alchemist 5) ---")
    elseif variant == "5"
        modeTag = "vanilla-5"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 1)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 5: Physician) ---")
    elseif variant == "6"
        modeTag = "vanilla-6"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 1)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 6: Benefactor) ---")
    elseif variant == "7"
        modeTag = "vanilla-7"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 1)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 7: Poisoner) ---")
    elseif variant == "8"
        modeTag = "vanilla-8"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        player.AddPerk(Game.GetForm(0x0005821D) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 8: Purity & Full Perks) ---")
    elseif variant == "9"
        modeTag = "vanilla-9"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        player.AddPerk(Game.GetForm(0x0005821D) as Perk)
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 5.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.0")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 9: Seeker of Shadows & Gear) ---")
    elseif variant == "10"
        modeTag = "vanilla-10"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 10: Skill 50 Non-100) ---")
    elseif variant == "11"
        modeTag = "vanilla-11"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x00058216) as Perk) ; Benefactor only
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 11: Benefactor Only Isolate) ---")
    elseif variant == "12"
        modeTag = "vanilla-12"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician only
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 12: Physician Non-Restore Isolate) ---")
    elseif variant == "13"
        modeTag = "vanilla-13"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x00058217) as Perk) ; Poisoner only
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 13: Poisoner Potion Isolate) ---")
    elseif variant == "14"
        modeTag = "vanilla-14"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplySeekerOfShadows(player) ; Seeker only
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 14: Seeker Only Isolate) ---")
    elseif variant == "15"
        modeTag = "vanilla-15"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 4) ; Rank 4 only
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 15: Rank 4 Unperked Isolate) ---")
    elseif variant == "16"
        modeTag = "vanilla-16"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetForm(0x00058215) as Perk) ; Physician
        player.AddPerk(Game.GetForm(0x00058216) as Perk) ; Benefactor
        player.AddPerk(Game.GetForm(0x00058217) as Perk) ; Poisoner
        player.AddPerk(Game.GetForm(0x0005821D) as Perk) ; Purity
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 16: Full Perk Tree + Seeker) ---")
    elseif variant == "17"
        modeTag = "vanilla-17"
        player.SetActorValue("Alchemy", 15)
        player.ForceActorValue("Alchemy", 15)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 17: Skill 15 Low Level Baseline) ---")
    else
        modeTag = "vanilla-1"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 1: Skill 100 Baseline) ---")
    endif
    ProvisionAndPrintTests(player, modeTag, variant)
    return "Vanilla test state applied successfully."
EndFunction

string Function SetupAP(string variant = "") global
    Actor player = Game.GetPlayer()
    ResetPlayerState(player)
    
    string modeTag = "ap"
    if variant == "changed"
        modeTag = "ap-changed"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 4)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.2")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.6")
        ConsoleUtil.PrintMessage("--- [PAT] AP Changed State Applied ---")
    elseif variant == "2"
        modeTag = "ap-2"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 3)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 2: Alchemist 3) ---")
    elseif variant == "3"
        modeTag = "ap-3"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 3: Physician + Benefactor) ---")
    elseif variant == "4"
        modeTag = "ap-4"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 4: Default Rounding, ImpureFix=True) ---")
    elseif variant == "5"
        modeTag = "ap-5"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 5: Poisoner) ---")
    elseif variant == "6"
        modeTag = "ap-6"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x0005821D) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 6: Purity) ---")
    elseif variant == "7"
        modeTag = "ap-7"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        player.AddPerk(Game.GetForm(0x0005821D) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 7: Full Tree) ---")
    elseif variant == "8"
        modeTag = "ap-8"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 5.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.0")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 8: High Rounding 30/6) ---")
    elseif variant == "9"
        modeTag = "ap-9"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 4)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.5")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.8")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 9: Gear & Perks) ---")
    elseif variant == "10"
        modeTag = "ap-10"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 10: Skill 50 Non-100) ---")
    elseif variant == "11"
        modeTag = "ap-11"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 11: Rounding OFF) ---")
    elseif variant == "12"
        modeTag = "ap-12"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 12: Seeker x AP Rounding) ---")
    else
        modeTag = "ap-1"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 1: Custom Rounding 10/2) ---")
    endif
    ProvisionAndPrintTests(player, modeTag, variant)
    return "AP test state applied successfully."
EndFunction

string Function SetupCACO(string variant = "") global
    Actor player = Game.GetPlayer()
    ResetPlayerState(player)
    
    string modeTag = "caco"
    if variant == "changed"
        modeTag = "caco-changed"
        player.SetActorValue("Alchemy", 55)
        player.ForceActorValue("Alchemy", 55)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.2")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.8")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO Changed State Applied ---")
    elseif variant == "2"
        modeTag = "caco-2"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 2: 10s Durations) ---")
    elseif variant == "3"
        modeTag = "caco-3"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 5.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.0")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 3: 0s Durations Order Matrix 1-4) ---")
    elseif variant == "4"
        modeTag = "caco-4"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 4: Order Matrix 5-6 & Aloe Vera) ---")
    elseif variant == "5"
        modeTag = "caco-5"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 5: Alchemist 2) ---")
    elseif variant == "6"
        modeTag = "caco-6"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 2, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 6: Physician Mixed Durations) ---")
    elseif variant == "7"
        modeTag = "caco-7"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 7: Poisoner 10s Durations) ---")
    elseif variant == "8"
        modeTag = "caco-8"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 8: Benefactor 5s Durations) ---")
    elseif variant == "9"
        modeTag = "caco-9"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        player.AddPerk(Game.GetForm(0x0005821D) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 2, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 9: Purity Gear Mixed Durations) ---")
    elseif variant == "10"
        modeTag = "caco-10"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 3)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 10: Skill 50 Non-100) ---")
    elseif variant == "11"
        modeTag = "caco-11"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 0, 0, 0, 0, 0) ; RestoreHealthDuration = Index 1 (5s), others 0s
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 11: Restore Health 5s MCM Slider) ---")
    elseif variant == "12"
        modeTag = "caco-12"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(2, 0, 0, 0, 0, 0) ; RestoreHealthDuration = Index 2 (10s), others 0s
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 12: Restore Health 10s MCM Slider) ---")
    elseif variant == "13"
        modeTag = "caco-13"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(0, 2, 2, 2, 0, 0) ; DmgH 10s, RestM 10s, RestS 10s Sliders
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 13: DmgH 10s, RestM 10s, RestS 10s Sliders) ---")
    elseif variant == "14"
        modeTag = "caco-14"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(2, 0, 0, 0, 0, 0) ; RestoreHealthDuration = 10s, others 0s
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 14: Base Cost 54g Effect Duration Isolate) ---")
    elseif variant == "15"
        modeTag = "caco-15"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 15: Restore Health 5s Duration) ---")
    elseif variant == "16"
        modeTag = "caco-16"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 16: All 10s Durations) ---")
    elseif variant == "17"
        modeTag = "caco-17"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 17: Seeker of Shadows Zero Rows Check) ---")
    elseif variant == "18"
        modeTag = "caco-18"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 18: Record Flags Isolates) ---")
    else
        modeTag = "caco-1"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 1: 5s Durations Baseline) ---")
    endif
    ProvisionAndPrintTests(player, modeTag, variant)
    return "CACO test state applied successfully."
EndFunction

string Function SetupCACOAP(string variant = "") global
    Actor player = Game.GetPlayer()
    ResetPlayerState(player)
    
    string modeTag = "caco-ap"
    if variant == "changed"
        modeTag = "caco-ap-changed"
        player.SetActorValue("Alchemy", 85)
        player.ForceActorValue("Alchemy", 85)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 4)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.5")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.5")
        SetAllCacoDurations(1, 2, 0, 2, 1, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP Changed State Applied ---")
    elseif variant == "2"
        modeTag = "caco-ap-2"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 4)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 2: Alchemist 4) ---")
    elseif variant == "3"
        modeTag = "caco-ap-3"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 3: Physician 5s) ---")
    elseif variant == "4"
        modeTag = "caco-ap-4"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 4: Low Rounding 10/2) ---")
    elseif variant == "5"
        modeTag = "caco-ap-5"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 5: Poisoner 10s) ---")
    elseif variant == "6"
        modeTag = "caco-ap-6"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 6: Benefactor 10s) ---")
    elseif variant == "7"
        modeTag = "caco-ap-7"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetForm(0x0005821D) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 2, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 7: Purity Mixed Durations) ---")
    elseif variant == "8"
        modeTag = "caco-ap-8"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 5.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 2.0")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 8: High Rounding 30/6) ---")
    elseif variant == "9"
        modeTag = "caco-ap-9"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 9: Gear & Full Perks) ---")
    elseif variant == "10"
        modeTag = "caco-ap-10"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058215) as Perk)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(2, 2, 2, 2, 2, 2)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 10: Skill 50 Non-100) ---")
    elseif variant == "11"
        modeTag = "caco-ap-11"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 11: Rounding OFF) ---")
    else
        modeTag = "caco-ap-1"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 1: Default AP Rounding) ---")
    endif
    ProvisionAndPrintTests(player, modeTag, variant)
    return "CACO+AP test state applied successfully."
EndFunction

string Function SetupRequiem(string variant = "") global
    Actor player = Game.GetPlayer()
    ResetPlayerState(player)
    
    string modeTag = "requiem"
    if variant == "changed"
        modeTag = "requiem-changed"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem Changed State Applied ---")
    elseif variant == "2"
        modeTag = "requiem-2"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 2: Lore 1 + 2) ---")
    elseif variant == "3"
        modeTag = "requiem-3"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 3: Improved Elixirs Only) ---")
    elseif variant == "4"
        modeTag = "requiem-4"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 4: Improved Poisons Only) ---")
    elseif variant == "5"
        modeTag = "requiem-5"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetForm(0x0005821D) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 5: Purification Process Only) ---")
    elseif variant == "6"
        modeTag = "requiem-6"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 6: No Lore Unperked Gate Check) ---")
    elseif variant == "7"
        modeTag = "requiem-7"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 7: Improved Elixirs + Improved Poisons) ---")
    elseif variant == "8"
        modeTag = "requiem-8"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        player.AddPerk(Game.GetForm(0x0005821D) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 8: Full Tree) ---")
    elseif variant == "9"
        modeTag = "requiem-9"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplyFortifyAlchemyGear(player)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        player.AddPerk(Game.GetForm(0x00058217) as Perk)
        player.AddPerk(Game.GetForm(0x0005821D) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.5")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.8")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 9: Gear & Changed GameSettings) ---")
    elseif variant == "10"
        modeTag = "requiem-10"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ApplyFortifyAlchemyGear(player)
        SetRequiemLoreRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 10: Skill 50 Non-100) ---")
    elseif variant == "11"
        modeTag = "requiem-11"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        Keyword reqUnperked = Game.GetFormFromFile(0x00AD3A3B, "Requiem.esp") as Keyword
        if reqUnperked
            PO3_SKSEFunctions.AddKeywordToForm(player, reqUnperked)
            PO3_SKSEFunctions.AddKeywordToForm(player.GetBaseObject(), reqUnperked)
            PO3_SKSEFunctions.AddKeywordToForm(player.GetRace(), reqUnperked)
        endif
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 11: Lore 0 Unperked Keyword) ---")
    elseif variant == "12"
        modeTag = "requiem-12"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetForm(0x00058216) as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 12: Improved Elixirs Fortify Skill) ---")
    else
        modeTag = "requiem-1"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 1)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 1: Lore 1 Baseline) ---")
    endif
    ProvisionAndPrintTests(player, modeTag, variant)
    return "Requiem test state applied successfully."
EndFunction

string Function SetupApothecary(string variant = "") global
    Actor player = Game.GetPlayer()
    ResetPlayerState(player)
    
    Perk magScaling = Game.GetFormFromFile(0x000CB06C, "Apothecary.esp") as Perk
    if magScaling && !player.HasPerk(magScaling)
        player.AddPerk(magScaling)
    endif
    
    string modeTag = "apothecary"
    if variant == "changed"
        modeTag = "apothecary-changed"
        player.SetActorValue("Alchemy", 65)
        player.ForceActorValue("Alchemy", 65)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 3)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.5")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.8")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary Changed State Applied ---")
    elseif variant == "2"
        modeTag = "apothecary-2"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 1)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 2: Alchemist 1) ---")
    elseif variant == "3"
        modeTag = "apothecary-3"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 3)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 3: Alchemist 3) ---")
    elseif variant == "4"
        modeTag = "apothecary-4"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 5)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 4: Alchemist 5 All Categories) ---")
    elseif variant == "5"
        modeTag = "apothecary-5"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 3)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 5: Peerless Gear) ---")
    elseif variant == "6"
        modeTag = "apothecary-6"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 4)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.5")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.8")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 6: Changed GameSettings) ---")
    elseif variant == "7"
        modeTag = "apothecary-7"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 7: Fortify Skill & Regen Rate Branches) ---")
    elseif variant == "8"
        modeTag = "apothecary-8"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 8: Restore Attribute & Generic Branches) ---")
    elseif variant == "9"
        modeTag = "apothecary-9"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 9: Alchemist 2 Mixed) ---")
    elseif variant == "10"
        modeTag = "apothecary-10"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 3)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 10: Skill 50 Non-100) ---")
    elseif variant == "11"
        modeTag = "apothecary-11"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 11: Skill 75 & Level 60 Stepped Check) ---")
    elseif variant == "12"
        modeTag = "apothecary-12"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 12: Fortify Stamina 2.5 Category) ---")
    else
        modeTag = "apothecary-1"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 1: Baseline All 4 Categories) ---")
    endif
    ProvisionAndPrintTests(player, modeTag, variant)
    return "Apothecary test state applied successfully."
EndFunction

string Function SetupDefault(string mode = "vanilla") global
    Actor player = Game.GetPlayer()
    ResetPlayerState(player)
    player.SetActorValue("Alchemy", 100)
    player.ForceActorValue("Alchemy", 100)
    
    if mode == "caco" || mode == "caco-ap"
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.9")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.0")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
    elseif mode == "requiem"
        SetRequiemLoreRank(player, 1)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
    else
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    endif
    
    ConsoleUtil.PrintMessage("--- [PAT] Default State Applied for mode '" + mode + "' (Skill 100, Fortify 0, Default Perks & GameSettings) ---")
    ConsoleUtil.PrintMessage("Next step: Trigger in-game export prediction command/hotkey, then run 'python sync_potion_predictions.py'")
    return "Default test state applied successfully."
EndFunction

Function ClearPlayerIngredients(Actor player) global
    if !player
        return
    endif
    Form[] ings = PO3_SKSEFunctions.AddItemsOfTypeToArray(player, 30)
    if ings
        int i = 0
        int count = ings.Length
        while i < count
            Form f = ings[i]
            if f
                int amt = player.GetItemCount(f)
                if amt > 0
                    player.RemoveItem(f, amt, true)
                endif
            endif
            i += 1
        endwhile
    endif
    Form[] kwIngs = PO3_SKSEFunctions.AddItemsWithKeywordStringToArray(player, "VendorItemIngredient")
    if kwIngs
        int j = 0
        int kwCount = kwIngs.Length
        while j < kwCount
            Form f2 = kwIngs[j]
            if f2
                int amt2 = player.GetItemCount(f2)
                if amt2 > 0
                    player.RemoveItem(f2, amt2, true)
                endif
            endif
            j += 1
        endwhile
    endif
EndFunction

string Function ClearIngredients() global
    Actor player = Game.GetPlayer()
    ClearPlayerIngredients(player)
    ConsoleUtil.PrintMessage("--- [PAT] All player ingredients removed ---")
    return "Player ingredients cleared successfully."
EndFunction

Function ProvisionForm(Actor player, int formID, string pluginName, int count = 99) global
    Form f = Game.GetFormFromFile(formID, pluginName)
    if f
        player.AddItem(f, count, true)
    endif
EndFunction

Function ProvisionFormFallback(Actor player, int primaryFormID, string primaryPlugin, int secondaryFormID, string secondaryPlugin, int count = 99) global
    Form f = Game.GetFormFromFile(primaryFormID, primaryPlugin)
    if !f
        f = Game.GetFormFromFile(secondaryFormID, secondaryPlugin)
    endif
    if f
        player.AddItem(f, count, true)
    endif
EndFunction

Function ProvisionAndPrintTests(Actor player, string modeTag, string variant) global
    ClearPlayerIngredients(player)
    
    ConsoleUtil.PrintMessage("--- Target Test Crafts for " + modeTag + " ---")
    
    if modeTag == "vanilla-1"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("4. Craft: Blue Mountain Flower + Blue Butterfly Wing")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 2'")
    elseif modeTag == "vanilla-2"
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
        ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
        ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ConsoleUtil.PrintMessage("1. Craft: Briar Heart + Canis Root")
        ConsoleUtil.PrintMessage("2. Craft: Bear Claws + Bee")
        ConsoleUtil.PrintMessage("3. Craft: Glowing Mushroom + Nightshade")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 3'")
    elseif modeTag == "vanilla-3"
        ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
        ProvisionForm(player, 0x0006F950, "Skyrim.esm") ; Scaly Pholiota
        ProvisionForm(player, 0x000EC870, "Skyrim.esm") ; Mora Tapinella
        ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
        ConsoleUtil.PrintMessage("1. Craft: Creep Cluster + Scaly Pholiota + Mora Tapinella")
        ConsoleUtil.PrintMessage("2. Craft: Giant's Toe + Wheat")
        ConsoleUtil.PrintMessage("3. Craft: Dragon's Tongue + Fly Amanita")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 4'")
    elseif modeTag == "vanilla-4"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 5'")
    elseif modeTag == "vanilla-5"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
        ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
        ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (Restore Health)")
        ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Ectoplasm (Restore Magicka)")
        ConsoleUtil.PrintMessage("3. Craft: Bear Claws + Bee (Restore Stamina)")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 6'")
    elseif modeTag == "vanilla-6"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Blue Butterfly Wing")
        ConsoleUtil.PrintMessage("2. Craft: Dragon's Tongue + Fly Amanita")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 7'")
    elseif modeTag == "vanilla-7"
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0004DA23, "Skyrim.esm") ; Imp Stool
        ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ConsoleUtil.PrintMessage("1. Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("2. Craft: Canis Root + Imp Stool")
        ConsoleUtil.PrintMessage("3. Craft: Glowing Mushroom + Nightshade")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 8'")
    elseif modeTag == "vanilla-8"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat (Purity strip DmgM)")
        ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat (Purity strip DmgS)")
        ConsoleUtil.PrintMessage("3. Craft: Briar Heart + Canis Root (Purity strip Paralyze)")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 9'")
    elseif modeTag == "vanilla-9"
        ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("1. Craft: Giant's Toe + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Blue Mountain Flower + Blue Butterfly Wing")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 10'")
    elseif modeTag == "vanilla-10"
        ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
        ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
        ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
        ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
        ProvisionForm(player, 0x000705B7, "Skyrim.esm") ; Berit's Ashes
        ProvisionForm(player, 0x00034CDD, "Skyrim.esm") ; Bone Meal
        ConsoleUtil.PrintMessage("1. Craft: Bear Claws + Bee")
        ConsoleUtil.PrintMessage("2. Craft: Luna Moth Wing + Vampire Dust")
        ConsoleUtil.PrintMessage("3. Craft: Berit's Ashes + Bone Meal")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 11'")
    elseif modeTag == "vanilla-11"
ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Blue Butterfly Wing (Benefactor isolate)")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 12'")
    elseif modeTag == "vanilla-12"
ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Blue Butterfly Wing (Physician 0% check)")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 13'")
    elseif modeTag == "vanilla-13"
ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (Poisoner 0% check)")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 14'")
    elseif modeTag == "vanilla-14"
ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (Seeker isolate)")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 15'")
    elseif modeTag == "vanilla-15"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (Rank 4 unperked isolate)")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 16'")
    elseif modeTag == "vanilla-16"
ProvisionForm(player, 0x00106E1B, "Skyrim.esm") ; Abecean Longfin
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00106E19, "Skyrim.esm") ; Cyrodilic Spadetail
        ConsoleUtil.PrintMessage("1. Craft: Abecean Longfin + Salt Pile + Cyrodilic Spadetail")
        ConsoleUtil.PrintMessage("Next command: run 'pat vanilla 17'")
    elseif modeTag == "vanilla-17"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (Skill 15 baseline)")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-caco.py'")
    
    ; AP Modes
    elseif modeTag == "ap-1"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
        ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
        ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
        ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (Restore Health override 0x3EB15)")
        ConsoleUtil.PrintMessage("2. Craft: Bear Claws + Bee (Restore Stamina override 0x3EB3D)")
        ConsoleUtil.PrintMessage("3. Craft: Luna Moth Wing + Vampire Dust")
        ConsoleUtil.PrintMessage("Next command: run 'pat ap 2'")
    elseif modeTag == "ap-2"
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ConsoleUtil.PrintMessage("1. Craft: Briar Heart + Canis Root")
        ConsoleUtil.PrintMessage("2. Craft: Blue Butterfly Wing + Blue Mountain Flower")
        ConsoleUtil.PrintMessage("3. Craft: Glowing Mushroom + Nightshade")
        ConsoleUtil.PrintMessage("Next command: run 'pat ap 3'")
    elseif modeTag == "ap-3"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (Physician + Benefactor)")
        ConsoleUtil.PrintMessage("2. Craft: Giant's Toe + Wheat (Benefactor)")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic (Benefactor)")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-ap-2.py'")
    elseif modeTag == "ap-4"
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
        ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
        ConsoleUtil.PrintMessage("1. Craft: Deathbell + River Betty (impureCostFix=True)")
        ConsoleUtil.PrintMessage("2. Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("3. Craft: Chaurus Eggs + Luna Moth Wing")
        ConsoleUtil.PrintMessage("Next command: run 'pat ap 5'")
    elseif modeTag == "ap-5"
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0004DA23, "Skyrim.esm") ; Imp Stool
        ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ConsoleUtil.PrintMessage("1. Craft: Canis Root + Imp Stool (Poisoner)")
        ConsoleUtil.PrintMessage("2. Craft: Glowing Mushroom + Nightshade (Poisoner)")
        ConsoleUtil.PrintMessage("3. Craft: Deathbell + River Betty (Poisoner)")
        ConsoleUtil.PrintMessage("Next command: run 'pat ap 6'")
    elseif modeTag == "ap-6"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat (Purity AP strip)")
        ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat (Purity AP strip)")
        ConsoleUtil.PrintMessage("3. Craft: Briar Heart + Canis Root")
        ConsoleUtil.PrintMessage("Next command: run 'pat ap 7'")
    elseif modeTag == "ap-7"
        ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
        ProvisionForm(player, 0x0006F950, "Skyrim.esm") ; Scaly Pholiota
        ProvisionForm(player, 0x000EC870, "Skyrim.esm") ; Mora Tapinella
        ProvisionForm(player, 0x00106E1B, "Skyrim.esm") ; Abecean Longfin
        ProvisionForm(player, 0x00106E19, "Skyrim.esm") ; Cyrodilic Spadetail
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ConsoleUtil.PrintMessage("1. Craft: Creep Cluster + Scaly Pholiota + Mora Tapinella")
        ConsoleUtil.PrintMessage("2. Craft: Abecean Longfin + Cyrodilic Spadetail + Salt Pile")
        ConsoleUtil.PrintMessage("3. Craft: Giant's Toe + Wheat")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-ap-3.py'")
    elseif modeTag == "ap-8"
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ConsoleUtil.PrintMessage("1. Craft: Briar Heart + Canis Root")
        ConsoleUtil.PrintMessage("2. Craft: Dragon's Tongue + Fly Amanita")
        ConsoleUtil.PrintMessage("3. Craft: Blue Butterfly Wing + Blue Mountain Flower")
        ConsoleUtil.PrintMessage("Next command: run 'pat ap 9'")
    elseif modeTag == "ap-9"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("3. Craft: Giant's Toe + Wheat")
        ConsoleUtil.PrintMessage("Next command: run 'pat ap 10'")
    elseif modeTag == "ap-10"
        ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
        ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
        ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
        ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
        ProvisionForm(player, 0x000705B7, "Skyrim.esm") ; Berit's Ashes
        ProvisionForm(player, 0x00034CDD, "Skyrim.esm") ; Bone Meal
        ConsoleUtil.PrintMessage("1. Craft: Bear Claws + Bee")
        ConsoleUtil.PrintMessage("2. Craft: Luna Moth Wing + Vampire Dust")
        ConsoleUtil.PrintMessage("3. Craft: Berit's Ashes + Bone Meal")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-ap-4.py'")
    elseif modeTag == "ap-11"
ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ConsoleUtil.PrintMessage("1. Craft: Briar Heart + Canis Root (unrounded AP)")
        ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat (unrounded AP)")
        ConsoleUtil.PrintMessage("Next command: run 'pat ap 12'")
    elseif modeTag == "ap-12"
ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (Seeker x unrounded AP)")
        ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Canis Root")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-vanilla.py'")
    elseif modeTag == "caco-1"
        ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
        ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
        ConsoleUtil.PrintMessage("1. Craft: Boar Tusk + Briar Heart (FortH 5s)")
        ConsoleUtil.PrintMessage("2. Craft: Creep Cluster + Giant's Toe (DmgS 5s)")
        ConsoleUtil.PrintMessage("3. Craft: Blisterwort + Wheat (RestH 5s)")
        ConsoleUtil.PrintMessage("4. Craft: Canis Root + Spider Egg (DmgS 5s)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 2'")
    elseif modeTag == "caco-2"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ProvisionForm(player, 0x000059BA, "Dawnguard.esm") ; Ancestor Moth
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract (RestH 10s CACO Extract)")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + River Betty (DmgH 10s)")
        ConsoleUtil.PrintMessage("3. Craft: Ancestor Moth + Blue Mountain Flower (FortConj 10s)")
        ConsoleUtil.PrintMessage("4. Craft: Briar Heart + Ectoplasm (RestM 10s)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 3'")
    elseif modeTag == "caco-3"
        ProvisionFormFallback(player, 0x0033A4D0, "Complete Alchemy & Cooking Overhaul.esp", 0x00000819, "ccbgssse037-curios.esl") ; Roobrush
        ProvisionForm(player, 0x0007E8C5, "Skyrim.esm") ; Slaughterfish Egg
        ProvisionForm(player, 0x0006BC0A, "Skyrim.esm") ; Large Antlers
        ConsoleUtil.PrintMessage("Craft Click Selection Order Matrix 1-4:")
        ConsoleUtil.PrintMessage("1. Roobrush -> Slaughterfish Egg -> Large Antlers")
        ConsoleUtil.PrintMessage("2. Slaughterfish Egg -> Roobrush -> Large Antlers")
        ConsoleUtil.PrintMessage("3. Large Antlers -> Roobrush -> Slaughterfish Egg")
        ConsoleUtil.PrintMessage("4. Large Antlers -> Slaughterfish Egg -> Roobrush")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 4'")
    elseif modeTag == "caco-4"
        ProvisionForm(player, 0x0033A4D0, "Complete Alchemy & Cooking Overhaul.esp") ; Roobrush
        ProvisionForm(player, 0x0006BC0A, "Skyrim.esm") ; Large Antlers
        ProvisionForm(player, 0x0007E8C5, "Skyrim.esm") ; Slaughterfish Egg
        ProvisionForm(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp") ; Aloe Vera
        ProvisionForm(player, 0x0003AD5B, "Skyrim.esm") ; Daedra Heart
        ConsoleUtil.PrintMessage("1. Order 5: Roobrush -> Large Antlers -> Slaughterfish Egg")
        ConsoleUtil.PrintMessage("2. Order 6: Slaughterfish Egg -> Large Antlers -> Roobrush")
        ConsoleUtil.PrintMessage("3. Craft: Aloe Vera + Daedra Heart (CACO Aloe Vera)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 5'")
    elseif modeTag == "caco-5"
        ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ConsoleUtil.PrintMessage("1. Craft: Boar Tusk + Briar Heart")
        ConsoleUtil.PrintMessage("2. Craft: Canis Root + Spider Egg")
        ConsoleUtil.PrintMessage("3. Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 6'")
    elseif modeTag == "caco-6"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
        ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
        ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract (RestH 5s Physician)")
        ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Ectoplasm (RestM 10s Physician)")
        ConsoleUtil.PrintMessage("3. Craft: Chaurus Eggs + Vampire Dust (DmgH 0s)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 7'")
    elseif modeTag == "caco-7"
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
        ProvisionForm(player, 0x0007E8B7, "Skyrim.esm") ; Swamp Fungal Pod
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ConsoleUtil.PrintMessage("1. Craft: Deathbell + River Betty (DmgH 10s Poisoner)")
        ConsoleUtil.PrintMessage("2. Craft: Canis Root + Spider Egg (DmgS 10s Poisoner)")
        ConsoleUtil.PrintMessage("3. Craft: Swamp Fungal Pod + Wheat Extract (DmgM 10s Poisoner)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 8'")
    elseif modeTag == "caco-8"
        ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
        ProvisionForm(player, 0x000059BA, "Dawnguard.esm") ; Ancestor Moth
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("1. Craft: Dragon's Tongue + Fly Amanita (Benefactor)")
        ConsoleUtil.PrintMessage("2. Craft: Ancestor Moth + Blue Mountain Flower (Benefactor)")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic (Benefactor)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 9'")
    elseif modeTag == "caco-9"
        ProvisionForm(player, 0x00077E1D, "Skyrim.esm") ; Red Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ConsoleUtil.PrintMessage("1. Craft: Red Mountain Flower + Wheat (Purity CACO strip)")
        ConsoleUtil.PrintMessage("2. Craft: Boar Tusk + Briar Heart")
        ConsoleUtil.PrintMessage("3. Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 10'")
    elseif modeTag == "caco-10"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x0006BC00, "Skyrim.esm") ; Mudcrab Chitin
        ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
        ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract (RestH 5s)")
        ConsoleUtil.PrintMessage("2. Craft: Mudcrab Chitin + Vampire Dust")
        ConsoleUtil.PrintMessage("3. Craft: Dragon's Tongue + Fly Amanita")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 11'")
    elseif modeTag == "caco-11"
ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract (RestH 5s MCM slider)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 12'")
    elseif modeTag == "caco-12"
ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract (RestH 10s MCM slider)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 13'")
    elseif modeTag == "caco-13"
ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
        ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
        ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
        ConsoleUtil.PrintMessage("1. Craft: Deathbell + River Betty (DmgH 10s)")
        ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Ectoplasm (RestM 10s)")
        ConsoleUtil.PrintMessage("3. Craft: Bear Claws + Bee (RestS 10s)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 14'")
    elseif modeTag == "caco-14"
ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract (54g base cost duration isolate)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 15'")
    elseif modeTag == "caco-15"
ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ProvisionForm(player, 0x0006BC00, "Skyrim.esm") ; Mudcrab Chitin
        ConsoleUtil.PrintMessage("1. Craft: Garlic + Mudcrab Chitin (Resist Disease aliasing)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 16'")
    elseif modeTag == "caco-16"
        ProvisionForm(player, 0x000727E0, "Skyrim.esm") ; Monarch Butterfly
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
        ProvisionForm(player, 0x0007E8C1, "Skyrim.esm") ; Giant Lichen
        ProvisionForm(player, 0x0007E8C8, "Skyrim.esm") ; Rock Warbler Egg
        ConsoleUtil.PrintMessage("1. Craft: Monarch Butterfly + Nightshade (Damage Undead base cost 8.3)")
        ConsoleUtil.PrintMessage("2. Craft: Creep Cluster + Giant Lichen + Rock Warbler Egg")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 17'")
    elseif modeTag == "caco-17"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract (Verify zero CACO Seeker rows)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco 18'")
    elseif modeTag == "caco-18"
        ProvisionForm(player, 0x0006BC0E, "Skyrim.esm") ; Wisp Wrappings
        ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
        ProvisionForm(player, 0x00000821, "ccbgssse037-curios.esl") ; Watcher's Eye
        ProvisionForm(player, 0x00000822, "ccbgssse037-curios.esl") ; Blind Watcher's Eye
        ConsoleUtil.PrintMessage("1. Craft: Wisp Wrappings + Glowing Mushroom (Etherealize)")
        ConsoleUtil.PrintMessage("2. Craft: Wisp Wrappings + Watcher's Eye (Detect Life)")
        ConsoleUtil.PrintMessage("3. Craft: Blind Watcher's Eye + Watcher's Eye (Light)")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-caco-ap.py'")
    elseif modeTag == "caco-ap-1"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
        ProvisionForm(player, 0x00000806, "ccbgssse037-curios.esl") ; Comberry
        ProvisionForm(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp") ; Aloe Vera
        ProvisionForm(player, 0x0003AD5B, "Skyrim.esm") ; Daedra Heart
        ProvisionForm(player, 0x0006BC0A, "Skyrim.esm") ; Large Antlers
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("3. Craft: Ash Creep Cluster + Comberry")
        ConsoleUtil.PrintMessage("4. Craft: Aloe Vera + Daedra Heart + Large Antlers")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco-ap 2'")
    elseif modeTag == "caco-ap-2"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x00000D6C, "ccbgssse037-curios.esl") ; Bog Beacon
        ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
        ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
        ProvisionForm(player, 0x000B701A, "Skyrim.esm") ; Crimson Nirnroot
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
        ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Bog Beacon + Jarrin Root")
        ConsoleUtil.PrintMessage("2. Craft: Ash Creep Cluster + Crimson Nirnroot")
        ConsoleUtil.PrintMessage("3. Craft: Canis Root + Spider Egg")
        ConsoleUtil.PrintMessage("4. Craft: Dragon's Tongue + Fly Amanita")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco-ap 3'")
    elseif modeTag == "caco-ap-3"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract (RestH 5s Physician)")
        ConsoleUtil.PrintMessage("2. Craft: Boar Tusk + Briar Heart (FortH 5s Physician)")
        ConsoleUtil.PrintMessage("3. Craft: Briar Heart + Ectoplasm (RestM 5s Physician)")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-caco-ap-2.py'")
    elseif modeTag == "caco-ap-4"
        ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
        ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x00000D6C, "ccbgssse037-curios.esl") ; Bog Beacon
        ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
        ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
        ProvisionForm(player, 0x000B701A, "Skyrim.esm") ; Crimson Nirnroot
        ConsoleUtil.PrintMessage("1. Craft: Boar Tusk + Briar Heart")
        ConsoleUtil.PrintMessage("2. Craft: Creep Cluster + Giant's Toe")
        ConsoleUtil.PrintMessage("3. Craft: Blue Mountain Flower + Bog Beacon + Jarrin Root")
        ConsoleUtil.PrintMessage("4. Craft: Ash Creep Cluster + Crimson Nirnroot")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco-ap 5'")
    elseif modeTag == "caco-ap-5"
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
        ProvisionForm(player, 0x0007E8B7, "Skyrim.esm") ; Swamp Fungal Pod
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ConsoleUtil.PrintMessage("1. Craft: Deathbell + River Betty (DmgH 10s Poisoner)")
        ConsoleUtil.PrintMessage("2. Craft: Canis Root + Spider Egg (DmgS 10s Poisoner)")
        ConsoleUtil.PrintMessage("3. Craft: Swamp Fungal Pod + Wheat Extract (DmgM 10s Poisoner)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco-ap 6'")
    elseif modeTag == "caco-ap-6"
        ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
        ProvisionForm(player, 0x00000806, "ccbgssse037-curios.esl") ; Comberry
        ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
        ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("1. Craft: Ash Creep Cluster + Comberry (FortDest 10s Benefactor)")
        ConsoleUtil.PrintMessage("2. Craft: Dragon's Tongue + Fly Amanita (Benefactor)")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic (Benefactor)")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco-ap 7'")
    elseif modeTag == "caco-ap-7"
        ProvisionForm(player, 0x00077E1D, "Skyrim.esm") ; Red Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ConsoleUtil.PrintMessage("1. Craft: Red Mountain Flower + Wheat (Purity CACO+AP strip)")
        ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat Extract")
        ConsoleUtil.PrintMessage("3. Craft: Boar Tusk + Briar Heart")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-caco-ap-3.py'")
    elseif modeTag == "caco-ap-8"
        ProvisionForm(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp") ; Aloe Vera
        ProvisionForm(player, 0x0003AD5B, "Skyrim.esm") ; Daedra Heart
        ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
        ProvisionForm(player, 0x0006F950, "Skyrim.esm") ; Scaly Pholiota
        ProvisionForm(player, 0x000059BA, "Dawnguard.esm") ; Ancestor Moth
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Daedra Heart")
        ConsoleUtil.PrintMessage("2. Craft: Creep Cluster + Scaly Pholiota")
        ConsoleUtil.PrintMessage("3. Craft: Ancestor Moth + Blue Mountain Flower")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco-ap 9'")
    elseif modeTag == "caco-ap-9"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
        ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
        ProvisionForm(player, 0x00000806, "ccbgssse037-curios.esl") ; Comberry
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + River Betty")
        ConsoleUtil.PrintMessage("3. Craft: Ash Creep Cluster + Comberry")
        ConsoleUtil.PrintMessage("Next command: run 'pat caco-ap 10'")
    elseif modeTag == "caco-ap-10"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
        ProvisionForm(player, 0x00000806, "ccbgssse037-curios.esl") ; Comberry
        ProvisionForm(player, 0x0006BC00, "Skyrim.esm") ; Mudcrab Chitin
        ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
        ConsoleUtil.PrintMessage("2. Craft: Ash Creep Cluster + Comberry")
        ConsoleUtil.PrintMessage("3. Craft: Mudcrab Chitin + Vampire Dust")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-caco-ap-4.py'")
    elseif modeTag == "caco-ap-11"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract (CACO + unrounded AP)")
        ConsoleUtil.PrintMessage("2. Craft: Canis Root + Spider Egg")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-requiem.py'")
    elseif modeTag == "requiem-1"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + Nightshade")
        ConsoleUtil.PrintMessage("3. Craft: Glowing Mushroom + Nightshade")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 2'")
    elseif modeTag == "requiem-2"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
        ProvisionForm(player, 0x0001B3BD, "Skyrim.esm") ; Snowberries
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + Nightshade")
        ConsoleUtil.PrintMessage("3. Craft: Glowing Mushroom + Nightshade")
        ConsoleUtil.PrintMessage("4. Craft: Glowing Mushroom + Snowberries")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 3'")
    elseif modeTag == "requiem-3"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x00074A19, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat (Elixir +25%)")
        ConsoleUtil.PrintMessage("2. Craft: Salt Pile + Garlic (Elixir +25%)")
        ConsoleUtil.PrintMessage("3. Craft: Deathbell + Nightshade (Poison 0%)")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 4'")
    elseif modeTag == "requiem-4"
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade (Poison +25%)")
        ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Creep Cluster (Poison +25%)")
        ConsoleUtil.PrintMessage("3. Craft: Blue Mountain Flower + Wheat (Elixir 0%)")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 5'")
    elseif modeTag == "requiem-5"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00074A19, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat (Purified)")
        ConsoleUtil.PrintMessage("2. Craft: Blue Mountain Flower + Blue Butterfly Wing (Purified)")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 6'")
    elseif modeTag == "requiem-6"
ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat (Gate check)")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + Nightshade (Gate check)")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 7'")
    elseif modeTag == "requiem-7"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0x00074A19, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat (Elixir +25%)")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + Nightshade (Poison +25%)")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic (Elixir +25%)")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 8'")
    elseif modeTag == "requiem-8"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
        ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat (Purified Elixir)")
        ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Creep Cluster (Improved Poison)")
        ConsoleUtil.PrintMessage("3. Craft: Dragon's Tongue + Fly Amanita (Improved Elixir)")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 9'")
    elseif modeTag == "requiem-9"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
        ProvisionForm(player, 0x0001B3BD, "Skyrim.esm") ; Snowberries
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + Nightshade")
        ConsoleUtil.PrintMessage("3. Craft: Glowing Mushroom + Snowberries")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 10'")
    elseif modeTag == "requiem-10"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
        ProvisionForm(player, 0x0001B3BD, "Skyrim.esm") ; Snowberries
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Glowing Mushroom + Snowberries")
        ConsoleUtil.PrintMessage("3. Craft: Deathbell + Nightshade")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 11'")
    elseif modeTag == "requiem-11"
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat (Requiem Lore 0 Unperked Keyword)")
        ConsoleUtil.PrintMessage("Next command: run 'pat requiem 12'")
    elseif modeTag == "requiem-12"
        ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ConsoleUtil.PrintMessage("1. Craft: Glowing Mushroom + Nightshade (Improved Elixirs Fortify Skill x0.5)")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-apothecary.py'")
    
    ; Apothecary Modes
    elseif modeTag == "apothecary-1"
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x00074A19, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
        ConsoleUtil.PrintMessage("1. Craft: Blue Butterfly Wing + Blue Mountain Flower (FortSkill +1.5%/lvl)")
        ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat (RestAttr +0.667%/lvl)")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic (RegenRate +0.52%/lvl)")
        ConsoleUtil.PrintMessage("4. Craft: Canis Root + Spider Egg (Generic +1.25%/lvl)")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 2'")
    elseif modeTag == "apothecary-2"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x00074A19, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Blue Butterfly Wing + Blue Mountain Flower")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 3'")
    elseif modeTag == "apothecary-3"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
        ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + Nightshade")
        ConsoleUtil.PrintMessage("3. Craft: Luna Moth Wing + Vampire Dust")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 4'")
    elseif modeTag == "apothecary-4"
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x00074A19, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
        ConsoleUtil.PrintMessage("1. Craft: Blue Butterfly Wing + Blue Mountain Flower")
        ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("4. Craft: Canis Root + Spider Egg")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 5'")
    elseif modeTag == "apothecary-5"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x00074A19, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Blue Butterfly Wing + Blue Mountain Flower")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 6'")
    elseif modeTag == "apothecary-6"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
        ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Deathbell + Nightshade")
        ConsoleUtil.PrintMessage("3. Craft: Luna Moth Wing + Vampire Dust")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 7'")
    elseif modeTag == "apothecary-7"
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
        ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
        ProvisionForm(player, 0x00074A19, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
        ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
        ConsoleUtil.PrintMessage("1. Craft: Blue Butterfly Wing + Blue Mountain Flower (FortSkill +1.5%/lvl)")
        ConsoleUtil.PrintMessage("2. Craft: Dragon's Tongue + Fly Amanita (FortSkill +1.5%/lvl)")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic (RegenRate +0.52%/lvl)")
        ConsoleUtil.PrintMessage("4. Craft: Luna Moth Wing + Vampire Dust (RegenRate +0.52%/lvl)")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 8'")
    elseif modeTag == "apothecary-8"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
        ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
        ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (RestAttr +0.667%/lvl)")
        ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Ectoplasm (RestAttr +0.667%/lvl)")
        ConsoleUtil.PrintMessage("3. Craft: Deathbell + Nightshade (Generic +1.25%/lvl)")
        ConsoleUtil.PrintMessage("4. Craft: Canis Root + Spider Egg (Generic +1.25%/lvl)")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 9'")
    elseif modeTag == "apothecary-9"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
        ConsoleUtil.PrintMessage("2. Craft: Blue Butterfly Wing + Blue Mountain Flower")
        ConsoleUtil.PrintMessage("3. Craft: Deathbell + Nightshade")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 10'")
    elseif modeTag == "apothecary-10"
        ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x00074A19, "Skyrim.esm") ; Salt Pile
        ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (RestAttr x 35)")
        ConsoleUtil.PrintMessage("2. Craft: Blue Butterfly Wing + Blue Mountain Flower (FortSkill x 35)")
        ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic (RegenRate x 35)")
        ConsoleUtil.PrintMessage("4. Craft: Deathbell + Nightshade (Generic x 35)")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 11'")
    elseif modeTag == "apothecary-11"
ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
        ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
        ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
        ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
        ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
        ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
        ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat (RestAttr x 60)")
        ConsoleUtil.PrintMessage("2. Craft: Blue Butterfly Wing + Blue Mountain Flower (FortSkill x 60)")
        ConsoleUtil.PrintMessage("3. Craft: Deathbell + Nightshade (Generic x 60)")
        ConsoleUtil.PrintMessage("Next command: run 'pat apothecary 12'")
    elseif modeTag == "apothecary-12"
        ProvisionForm(player, 0x0004DA73, "Skyrim.esm") ; Torchbug Thorax
        ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
        ConsoleUtil.PrintMessage("1. Craft: Torchbug Thorax + Chaurus Eggs")
        ConsoleUtil.PrintMessage("Next step: Exit Skyrim, run 'python pat-default-vanilla.py'")
    endif
EndFunction