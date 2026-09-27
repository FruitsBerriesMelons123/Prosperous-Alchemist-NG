Scriptname ProsperousAlchemistTests Hidden

Function ClearAllAlchemyPerks(Actor player) global
    player.RemovePerk(Game.GetFormFromFile(0x000BE127, "Skyrim.esm") as Perk)
    player.RemovePerk(Game.GetFormFromFile(0x000C07CA, "Skyrim.esm") as Perk)
    player.RemovePerk(Game.GetFormFromFile(0x000C07CB, "Skyrim.esm") as Perk)
    player.RemovePerk(Game.GetFormFromFile(0x000C07CC, "Skyrim.esm") as Perk)
    player.RemovePerk(Game.GetFormFromFile(0x000C07CD, "Skyrim.esm") as Perk)
    
    player.RemovePerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk) ; Physician
    player.RemovePerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk) ; Benefactor / Improved Elixirs
    player.RemovePerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk) ; Poisoner / Improved Poisons
    player.RemovePerk(Game.GetFormFromFile(0x00058218, "Skyrim.esm") as Perk) ; Experimenter 1
    player.RemovePerk(Game.GetFormFromFile(0x00105F2A, "Skyrim.esm") as Perk) ; Experimenter 2
    player.RemovePerk(Game.GetFormFromFile(0x00105F2B, "Skyrim.esm") as Perk) ; Experimenter 3
    player.RemovePerk(Game.GetFormFromFile(0x00105F2C, "Skyrim.esm") as Perk) ; Snakeblood
    player.RemovePerk(Game.GetFormFromFile(0x00105F2E, "Skyrim.esm") as Perk) ; Green Thumb
    player.RemovePerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk) ; Purity / Purification Process
    
    ClearSeekerOfShadows(player)
EndFunction

Function SetAlchemistRank(Actor player, int rank) global
    player.RemovePerk(Game.GetFormFromFile(0x000BE127, "Skyrim.esm") as Perk)
    player.RemovePerk(Game.GetFormFromFile(0x000C07CA, "Skyrim.esm") as Perk)
    player.RemovePerk(Game.GetFormFromFile(0x000C07CB, "Skyrim.esm") as Perk)
    player.RemovePerk(Game.GetFormFromFile(0x000C07CC, "Skyrim.esm") as Perk)
    player.RemovePerk(Game.GetFormFromFile(0x000C07CD, "Skyrim.esm") as Perk)
    
    if rank == 1
        player.AddPerk(Game.GetFormFromFile(0x000BE127, "Skyrim.esm") as Perk)
    elseif rank == 2
        player.AddPerk(Game.GetFormFromFile(0x000C07CA, "Skyrim.esm") as Perk)
    elseif rank == 3
        player.AddPerk(Game.GetFormFromFile(0x000C07CB, "Skyrim.esm") as Perk)
    elseif rank == 4
        player.AddPerk(Game.GetFormFromFile(0x000C07CC, "Skyrim.esm") as Perk)
    elseif rank == 5
        player.AddPerk(Game.GetFormFromFile(0x000C07CD, "Skyrim.esm") as Perk)
    endif
EndFunction

Function SetRequiemLoreRank(Actor player, int rank) global
    if rank >= 1
        player.AddPerk(Game.GetFormFromFile(0x000BE127, "Skyrim.esm") as Perk) ; Requiem Alchemical Lore 1
    endif
    if rank >= 2
        player.AddPerk(Game.GetFormFromFile(0x000C07CA, "Skyrim.esm") as Perk) ; Requiem Alchemical Lore 2
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

; Values are CACO duration INDICES (0 = 1 sec, 1 = 5 sec, 2 = 10 sec), not seconds.
; CACO_AlchDurationModifier only divides magnitude when a global is exactly 1 or 2, so
; any other value (e.g. 5 or 10) silently behaves like the 1-second option.
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 5: Physician) ---")
    elseif variant == "6"
        modeTag = "vanilla-6"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 1)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 6: Benefactor) ---")
    elseif variant == "7"
        modeTag = "vanilla-7"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 1)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 7: Poisoner) ---")
    elseif variant == "8"
        modeTag = "vanilla-8"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 8: Purity & Full Perks) ---")
    elseif variant == "9"
        modeTag = "vanilla-9"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 10: Skill 50 Non-100) ---")
    elseif variant == "11"
        modeTag = "vanilla-11"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk) ; Benefactor only
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 11: Benefactor Only Isolate) ---")
    elseif variant == "12"
        modeTag = "vanilla-12"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk) ; Physician only
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 12: Physician Non-Restore Isolate) ---")
    elseif variant == "13"
        modeTag = "vanilla-13"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk) ; Poisoner only
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk) ; Physician
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk) ; Benefactor
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk) ; Poisoner
        player.AddPerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk) ; Purity
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
    elseif variant == "18"
        modeTag = "vanilla-18"
        player.SetActorValue("Alchemy", 40)
        player.ForceActorValue("Alchemy", 40)
        SetAlchemistRank(player, 1)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Vanilla State Applied (Block 18: Skill 40 Rank 1 Intermediate Bracket) ---")
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 5: Poisoner) ---")
    elseif variant == "6"
        modeTag = "ap-6"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 6: Purity) ---")
    elseif variant == "7"
        modeTag = "ap-7"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 5)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.5")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.8")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 9: Gear & Perks) ---")
    elseif variant == "10"
        modeTag = "ap-10"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 2)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
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
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 12: Full Combo x AP Rounding) ---")
    elseif variant == "13"
        modeTag = "ap-13"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] AP State Applied (Block 13: Mid-skill & AP checks) ---")
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

string Function SetupCACO(string variant = "1") global
    Actor player = Game.GetPlayer()
    ResetPlayerState(player)
    ; Reset CACO duration indices so blocks that do not set their own never inherit a previous block's values.
    SetAllCacoDurations(0, 0, 0, 0, 0, 0)
    SetCacoGlobal(0x00AAB031, 1.0) ; DisableAllPotionHandling = 1 (required default)
    SetCacoGlobal(0x00AAB030, 0.0) ; ImpurePotions = 0 (required default)
    
    string modeTag = "caco"
    if variant == "changed"
        modeTag = "caco-changed"
        player.SetActorValue("Alchemy", 55)
        player.ForceActorValue("Alchemy", 55)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 2)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00105F2E, "Skyrim.esm") as Perk) ; Green Thumb
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(1, 1, 1, 1, 1, 1)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO State Applied (Block 18: Record Flags Isolates) ---")
    elseif variant == "19"
        modeTag = "caco-19"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 1, 1, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "20"
        modeTag = "caco-20"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 1, 0, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "21"
        modeTag = "caco-21"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "22"
        modeTag = "caco-22"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 0, 0, 1, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "23"
        modeTag = "caco-23"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 0, 0, 2, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "24"
        modeTag = "caco-24"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "25"
        modeTag = "caco-25"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(1, 0, 0, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "26"
        modeTag = "caco-26"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 2, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "27"
        modeTag = "caco-27"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 0, 2, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
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

string Function SetupCACOAP(string variant = "1") global
    Actor player = Game.GetPlayer()
    ResetPlayerState(player)
    ; Reset CACO duration indices so blocks that do not set their own never inherit a previous block's values.
    SetAllCacoDurations(0, 0, 0, 0, 0, 0)
    SetCacoGlobal(0x00AAB031, 1.0) ; DisableAllPotionHandling = 1 (required default)
    SetCacoGlobal(0x00AAB030, 0.0) ; ImpurePotions = 0 (required default)
    
    string modeTag = "caco-ap"
    if variant == "changed"
        modeTag = "caco-ap-changed"
        player.SetActorValue("Alchemy", 85)
        player.ForceActorValue("Alchemy", 85)
        ApplyFortifyAlchemyGear(player)
        SetAlchemistRank(player, 4)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00105F2E, "Skyrim.esm") as Perk) ; Green Thumb
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        SetCacoGlobal(0x00AAB031, 1.0)
        SetCacoGlobal(0x00AAB030, 0.0)
        ConsoleUtil.PrintMessage("--- [PAT] CACO+AP State Applied (Block 11: Rounding OFF) ---")
    elseif variant == "12"
        modeTag = "caco-ap-12"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 2, 1, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "13"
        modeTag = "caco-ap-13"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 2, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "14"
        modeTag = "caco-ap-14"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "15"
        modeTag = "caco-ap-15"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 0, 0, 1, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "16"
        modeTag = "caco-ap-16"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 0, 0, 2, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "17"
        modeTag = "caco-ap-17"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "18"
        modeTag = "caco-ap-18"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "19"
        modeTag = "caco-ap-19"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 1)
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "20"
        modeTag = "caco-ap-20"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 3)
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "21"
        modeTag = "caco-ap-21"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(1, 0, 0, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "22"
        modeTag = "caco-ap-22"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 0, 0, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
    elseif variant == "23"
        modeTag = "caco-ap-23"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAllCacoDurations(0, 1, 0, 0, 0, 0)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 3.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 3.0")
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

string Function SetupRequiem(string variant = "1") global
    Actor player = Game.GetPlayer()
    ResetPlayerState(player)
    
    string modeTag = "requiem"
    if variant == "changed"
        modeTag = "requiem-changed"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 3: Improved Elixirs Only) ---")
    elseif variant == "4"
        modeTag = "requiem-4"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 4: Improved Poisons Only) ---")
    elseif variant == "5"
        modeTag = "requiem-5"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 7: Improved Elixirs + Improved Poisons) ---")
    elseif variant == "8"
        modeTag = "requiem-8"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 8: Full Tree) ---")
    elseif variant == "9"
        modeTag = "requiem-9"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ApplyFortifyAlchemyGear(player)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x0005821D, "Skyrim.esm") as Perk)
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
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
        ConsoleUtil.PrintMessage("--- [PAT] Requiem State Applied (Block 12: Improved Elixirs Fortify Skill) ---")
    elseif variant == "13"
        modeTag = "requiem-13"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
    elseif variant == "14"
        modeTag = "requiem-14"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
    elseif variant == "15"
        modeTag = "requiem-15"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetFormFromFile(0x00105F2E, "Skyrim.esm") as Perk) ; Green Thumb (REQ_NULL_GreenThumb in Requiem: no-effect check)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
    elseif variant == "16"
        modeTag = "requiem-16"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        SetRequiemLoreRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
    elseif variant == "17"
        modeTag = "requiem-17"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk) ; Physician (REQ_NULL_Physician in Requiem: no-effect check)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
    elseif variant == "18"
        modeTag = "requiem-18"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetRequiemLoreRank(player, 2)
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.1")
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

string Function SetupApothecary(string variant = "1") global
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
    elseif variant == "13"
        modeTag = "apothecary-13"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 13: Resist-Family at Skill 100) ---")
    elseif variant == "14"
        modeTag = "apothecary-14"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 14: Reflect Damage at Skill 50) ---")
    elseif variant == "15"
        modeTag = "apothecary-15"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 15: Reflect Damage at Skill 100) ---")
    elseif variant == "16"
        modeTag = "apothecary-16"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 16: Damage Health Rank 0 Baseline) ---")
    elseif variant == "17"
        modeTag = "apothecary-17"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 1)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 17: Damage Health Rank 1 Bracket) ---")
    elseif variant == "18"
        modeTag = "apothecary-18"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 18: Damage Health Rank 2 Bracket) ---")
    elseif variant == "19"
        modeTag = "apothecary-19"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 4)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 19: Damage Health Rank 4 Bracket) ---")
    elseif variant == "28"
        modeTag = "apothecary-28"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 5)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 28: Damage Health Rank 5 Ceiling) ---")
    elseif variant == "29"
        modeTag = "apothecary-29"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "30"
        modeTag = "apothecary-30"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "36"
        modeTag = "apothecary-36"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 36: Damage Slope Pinning - Skill 100 Rank 2) ---")
    elseif variant == "37"
        modeTag = "apothecary-37"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 4)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 37: Damage Slope Pinning - Skill 100 Rank 4) ---")
    elseif variant == "38"
        modeTag = "apothecary-38"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        SetAlchemistRank(player, 5)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 38: Damage Slope Pinning - Skill 100 Rank 5) ---")
    elseif variant == "41"
        modeTag = "apothecary-41"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "42"
        modeTag = "apothecary-42"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "43"
        modeTag = "apothecary-43"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "44"
        modeTag = "apothecary-44"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "45"
        modeTag = "apothecary-45"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "46"
        modeTag = "apothecary-46"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "47"
        modeTag = "apothecary-47"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "48"
        modeTag = "apothecary-48"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "20"
        modeTag = "apothecary-20"
        player.SetActorValue("Alchemy", 15)
        player.ForceActorValue("Alchemy", 15)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "31"
        modeTag = "apothecary-31"
        player.SetActorValue("Alchemy", 15)
        player.ForceActorValue("Alchemy", 15)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "39"
        modeTag = "apothecary-39"
        player.SetActorValue("Alchemy", 15)
        player.ForceActorValue("Alchemy", 15)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "21"
        modeTag = "apothecary-21"
        player.SetActorValue("Alchemy", 25)
        player.ForceActorValue("Alchemy", 25)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "55"
        modeTag = "apothecary-55"
        player.SetActorValue("Alchemy", 25)
        player.ForceActorValue("Alchemy", 25)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "22"
        modeTag = "apothecary-22"
        player.SetActorValue("Alchemy", 40)
        player.ForceActorValue("Alchemy", 40)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "23"
        modeTag = "apothecary-23"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "32"
        modeTag = "apothecary-32"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "40"
        modeTag = "apothecary-40"
        player.SetActorValue("Alchemy", 50)
        player.ForceActorValue("Alchemy", 50)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "24"
        modeTag = "apothecary-24"
        player.SetActorValue("Alchemy", 60)
        player.ForceActorValue("Alchemy", 60)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "56"
        modeTag = "apothecary-56"
        player.SetActorValue("Alchemy", 60)
        player.ForceActorValue("Alchemy", 60)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "25"
        modeTag = "apothecary-25"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "26"
        modeTag = "apothecary-26"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        SetAlchemistRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 26: Skill 75 Rank 2 Restore Magicka & Stamina) ---")
    elseif variant == "33"
        modeTag = "apothecary-33"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        SetAlchemistRank(player, 3)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 33: Damage Slope Pinning - Skill 75 Rank 3) ---")
    elseif variant == "34"
        modeTag = "apothecary-34"
        player.SetActorValue("Alchemy", 75)
        player.ForceActorValue("Alchemy", 75)
        SetAlchemistRank(player, 4)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 34: Damage Slope Pinning - Skill 75 Rank 4) ---")
    elseif variant == "27"
        modeTag = "apothecary-27"
        player.SetActorValue("Alchemy", 90)
        player.ForceActorValue("Alchemy", 90)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "52"
        modeTag = "apothecary-52"
        player.SetActorValue("Alchemy", 90)
        player.ForceActorValue("Alchemy", 90)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "57"
        modeTag = "apothecary-57"
        player.SetActorValue("Alchemy", 90)
        player.ForceActorValue("Alchemy", 90)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "35"
        modeTag = "apothecary-35"
        player.SetActorValue("Alchemy", 85)
        player.ForceActorValue("Alchemy", 85)
        SetAlchemistRank(player, 2)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
        ConsoleUtil.PrintMessage("--- [PAT] Apothecary State Applied (Block 35: Damage Slope Pinning - Skill 85 Rank 2) ---")
    elseif variant == "54"
        modeTag = "apothecary-54"
        player.SetActorValue("Alchemy", 85)
        player.ForceActorValue("Alchemy", 85)
        if variant == "54"
            SetAlchemistRank(player, 1)
        endif
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "49"
        modeTag = "apothecary-49"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetFormFromFile(0x00105F2E, "Skyrim.esm") as Perk) ; Green Thumb
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "50"
        modeTag = "apothecary-50"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        ApplySeekerOfShadows(player)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "51"
        modeTag = "apothecary-51"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        player.AddPerk(Game.GetFormFromFile(0x00058215, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058216, "Skyrim.esm") as Perk)
        player.AddPerk(Game.GetFormFromFile(0x00058217, "Skyrim.esm") as Perk)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    elseif variant == "53"
        modeTag = "apothecary-53"
        player.SetActorValue("Alchemy", 65)
        player.ForceActorValue("Alchemy", 65)
        SetAlchemistRank(player, 1)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
    else
        modeTag = "apothecary-1"
        player.SetActorValue("Alchemy", 100)
        player.ForceActorValue("Alchemy", 100)
        ConsoleUtil.ExecuteCommand("setgs fAlchemyIngredientInitMult 4.0")
        ConsoleUtil.ExecuteCommand("setgs fAlchemySkillFactor 1.5")
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
    string nextStep = "python pat-default-ap.py"
    if mode == "ap"
        nextStep = "python pat-default-caco.py"
    elseif mode == "caco"
        nextStep = "python pat-default-caco-ap.py"
    elseif mode == "caco-ap"
        nextStep = "python pat-default-requiem.py"
    elseif mode == "requiem"
        nextStep = "python pat-default-apothecary.py"
    elseif mode == "apothecary"
        nextStep = "python potion_prediction_test.py --check-confirmed-csv"
    endif
    ConsoleUtil.PrintMessage("Next: In the Developer Test Hub press 'Export potion predictions to CSV', then run 'python sync_potion_predictions.py'")
    if mode == "apothecary"
        ConsoleUtil.PrintMessage("Then: " + nextStep + ", then 'python save_predicted_default_settings.py', then exit Skyrim and run python pat-vanilla-changed.py")
    else
        ConsoleUtil.PrintMessage("Then: Exit Skyrim and run " + nextStep)
    endif
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
    if !f && (primaryFormID == 0x00A100AD || secondaryFormID == 0x000000D0)
        f = Game.GetFormFromFile(0x000000D0, "_ResourcePack.esl")
    endif
    if f
        player.AddItem(f, count, true)
    endif
EndFunction

Function ProvisionAndPrintTests(Actor player, string modeTag, string variant) global
	ClearPlayerIngredients(player)
	if modeTag == "ap-1"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
		ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
		ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
		ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Bear Claws + Bee")
		ConsoleUtil.PrintMessage("3. Craft: Luna Moth Wing + Vampire Dust")
		ConsoleUtil.PrintMessage("Next: pat ap 2")
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
		ConsoleUtil.PrintMessage("Next: pat ap 3")
	elseif modeTag == "ap-3"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Giant's Toe + Wheat")
		ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-ap-2.py")
	elseif modeTag == "ap-4"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
		ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + River Betty")
		ConsoleUtil.PrintMessage("2. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("3. Craft: Chaurus Eggs + Luna Moth Wing")
		ConsoleUtil.PrintMessage("Next: pat ap 5")
	elseif modeTag == "ap-5"
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x0004DA23, "Skyrim.esm") ; Imp Stool
		ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
		ConsoleUtil.PrintMessage("1. Craft: Canis Root + Imp Stool")
		ConsoleUtil.PrintMessage("2. Craft: Glowing Mushroom + Nightshade")
		ConsoleUtil.PrintMessage("3. Craft: Deathbell + River Betty")
		ConsoleUtil.PrintMessage("Next: pat ap 6")
	elseif modeTag == "ap-6"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("3. Craft: Briar Heart + Canis Root")
		ConsoleUtil.PrintMessage("Next: pat ap 7")
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
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-ap-3.py")
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
		ConsoleUtil.PrintMessage("Next: pat ap 9")
	elseif modeTag == "ap-9"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("3. Craft: Giant's Toe + Wheat")
		ConsoleUtil.PrintMessage("Next: pat ap 10")
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
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-ap-4.py")
	elseif modeTag == "ap-11"
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ConsoleUtil.PrintMessage("1. Craft: Briar Heart + Canis Root")
		ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("Next: pat ap 12")
	elseif modeTag == "ap-12"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ProvisionForm(player, 0x00106E1B, "Skyrim.esm") ; Abecean Longfin
		ProvisionForm(player, 0x0004DA20, "Skyrim.esm") ; Bleeding Crown
		ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
		ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Ambrosia")
		ConsoleUtil.PrintMessage("2. Craft: Abecean Longfin + Bleeding Crown")
		ConsoleUtil.PrintMessage("3. Craft: Luna Moth Wing + Ash Creep Cluster")
		ConsoleUtil.PrintMessage("Next: pat ap 13")
	elseif modeTag == "ap-13"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ProvisionForm(player, 0x00106E1B, "Skyrim.esm") ; Abecean Longfin
		ProvisionForm(player, 0x0004DA20, "Skyrim.esm") ; Bleeding Crown
		ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
		ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Ambrosia")
		ConsoleUtil.PrintMessage("2. Craft: Abecean Longfin + Bleeding Crown")
		ConsoleUtil.PrintMessage("3. Craft: Luna Moth Wing + Ash Creep Cluster")
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-vanilla.py")
	elseif modeTag == "vanilla-1"
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
		ConsoleUtil.PrintMessage("Next: pat vanilla 2")
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
		ConsoleUtil.PrintMessage("Next: pat vanilla 3")
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
		ConsoleUtil.PrintMessage("Next: pat vanilla 4")
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
		ConsoleUtil.PrintMessage("Next: pat vanilla 5")
	elseif modeTag == "vanilla-5"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
		ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
		ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Ectoplasm")
		ConsoleUtil.PrintMessage("3. Craft: Bear Claws + Bee")
		ConsoleUtil.PrintMessage("Next: pat vanilla 6")
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
		ConsoleUtil.PrintMessage("Next: pat vanilla 7")
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
		ConsoleUtil.PrintMessage("Next: pat vanilla 8")
	elseif modeTag == "vanilla-8"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("3. Craft: Briar Heart + Canis Root")
		ConsoleUtil.PrintMessage("Next: pat vanilla 9")
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
		ConsoleUtil.PrintMessage("Next: pat vanilla 10")
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
		ConsoleUtil.PrintMessage("Next: pat vanilla 11")
	elseif modeTag == "vanilla-11"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Blue Butterfly Wing")
		ConsoleUtil.PrintMessage("Next: pat vanilla 12")
	elseif modeTag == "vanilla-12"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Blue Butterfly Wing")
		ConsoleUtil.PrintMessage("Next: pat vanilla 13")
	elseif modeTag == "vanilla-13"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("Next: pat vanilla 14")
	elseif modeTag == "vanilla-14"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("Next: pat vanilla 15")
	elseif modeTag == "vanilla-15"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("Next: pat vanilla 16")
	elseif modeTag == "vanilla-16"
		ProvisionForm(player, 0x00106E1B, "Skyrim.esm") ; Abecean Longfin
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00106E19, "Skyrim.esm") ; Cyrodilic Spadetail
		ConsoleUtil.PrintMessage("1. Craft: Abecean Longfin + Salt Pile + Cyrodilic Spadetail")
		ConsoleUtil.PrintMessage("Next: pat vanilla 17")
	elseif modeTag == "vanilla-17"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("Next: pat vanilla 18")
	elseif modeTag == "vanilla-18"
		ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
		ProvisionForm(player, 0x00034D31, "Skyrim.esm") ; Elves Ear
		ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
		ConsoleUtil.PrintMessage("1. Craft: Dragon's Tongue + Elves Ear + Fly Amanita")
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-caco.py")
	elseif modeTag == "caco-1"
		ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
		ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
		ConsoleUtil.PrintMessage("1. Craft: Boar Tusk + Briar Heart")
		ConsoleUtil.PrintMessage("2. Craft: Creep Cluster + Giant's Toe")
		ConsoleUtil.PrintMessage("3. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("4. Craft: Canis Root + Spider Egg")
		ConsoleUtil.PrintMessage("Next: pat caco 2")
	elseif modeTag == "caco-2"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
		ProvisionForm(player, 0x000059BA, "Dawnguard.esm") ; Ancestor Moth
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
		ConsoleUtil.PrintMessage("2. Craft: Deathbell + River Betty")
		ConsoleUtil.PrintMessage("3. Craft: Ancestor Moth + Blue Mountain Flower")
		ConsoleUtil.PrintMessage("4. Craft: Briar Heart + Ectoplasm")
		ConsoleUtil.PrintMessage("Next: pat caco 3")
	elseif modeTag == "caco-3"


		ConsoleUtil.PrintMessage("Next: pat caco 4")
	elseif modeTag == "caco-4"
		ProvisionForm(player, 0x00000819, "ccbgssse037-curios.esl") ; Roobrush
		ProvisionForm(player, 0x0006BC0A, "Skyrim.esm") ; Large Antlers
		ProvisionForm(player, 0x0007E8C5, "Skyrim.esm") ; Slaughterfish Egg
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x0003AD5B, "Skyrim.esm") ; Daedra Heart
		ConsoleUtil.PrintMessage("1. Craft: Roobrush -> Large Antlers -> Slaughterfish Egg")
		ConsoleUtil.PrintMessage("2. Craft: Slaughterfish Egg -> Large Antlers -> Roobrush")
		ConsoleUtil.PrintMessage("3. Craft: Aloe Vera + Daedra Heart")
		ConsoleUtil.PrintMessage("Next: pat caco 5")
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
		ConsoleUtil.PrintMessage("Next: pat caco 6")
	elseif modeTag == "caco-6"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
		ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
		ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
		ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Ectoplasm")
		ConsoleUtil.PrintMessage("3. Craft: Chaurus Eggs + Vampire Dust")
		ConsoleUtil.PrintMessage("Next: pat caco 7")
	elseif modeTag == "caco-7"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
		ProvisionForm(player, 0x0007E8B7, "Skyrim.esm") ; Swamp Fungal Pod
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + River Betty")
		ConsoleUtil.PrintMessage("2. Craft: Canis Root + Spider Egg")
		ConsoleUtil.PrintMessage("3. Craft: Swamp Fungal Pod + Wheat Extract")
		ConsoleUtil.PrintMessage("Next: pat caco 8")
	elseif modeTag == "caco-8"
		ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
		ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
		ProvisionForm(player, 0x000059BA, "Dawnguard.esm") ; Ancestor Moth
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ConsoleUtil.PrintMessage("1. Craft: Dragon's Tongue + Fly Amanita")
		ConsoleUtil.PrintMessage("2. Craft: Ancestor Moth + Blue Mountain Flower")
		ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("Next: pat caco 9")
	elseif modeTag == "caco-9"
		ProvisionForm(player, 0x00077E1D, "Skyrim.esm") ; Red Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
		ConsoleUtil.PrintMessage("1. Craft: Red Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Boar Tusk + Briar Heart")
		ConsoleUtil.PrintMessage("3. Craft: Deathbell + River Betty")
		ConsoleUtil.PrintMessage("Next: pat caco 10")
	elseif modeTag == "caco-10"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ProvisionForm(player, 0x0006BC00, "Skyrim.esm") ; Mudcrab Chitin
		ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
		ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
		ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
		ConsoleUtil.PrintMessage("2. Craft: Mudcrab Chitin + Vampire Dust")
		ConsoleUtil.PrintMessage("3. Craft: Dragon's Tongue + Fly Amanita")
		ConsoleUtil.PrintMessage("Next: pat caco 11")
	elseif modeTag == "caco-11"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
		ConsoleUtil.PrintMessage("Next: pat caco 12")
	elseif modeTag == "caco-12"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
		ConsoleUtil.PrintMessage("Next: pat caco 13")
	elseif modeTag == "caco-13"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
		ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
		ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + River Betty")
		ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Ectoplasm")
		ConsoleUtil.PrintMessage("3. Craft: Bear Claws + Bee")
		ConsoleUtil.PrintMessage("Next: pat caco 14")
	elseif modeTag == "caco-14"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
		ConsoleUtil.PrintMessage("Next: pat caco 15")
	elseif modeTag == "caco-15"
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ProvisionForm(player, 0x0006BC00, "Skyrim.esm") ; Mudcrab Chitin
		ConsoleUtil.PrintMessage("1. Craft: Garlic + Mudcrab Chitin")
		ConsoleUtil.PrintMessage("Next: pat caco 16")
	elseif modeTag == "caco-16"
		ProvisionForm(player, 0x000727E0, "Skyrim.esm") ; Monarch Butterfly
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
		ProvisionForm(player, 0x0007E8C1, "Skyrim.esm") ; Giant Lichen
		ProvisionForm(player, 0x0007E8C8, "Skyrim.esm") ; Rock Warbler Egg
		ConsoleUtil.PrintMessage("1. Craft: Monarch Butterfly + Nightshade")
		ConsoleUtil.PrintMessage("2. Craft: Creep Cluster + Giant Lichen + Rock Warbler Egg")
		ConsoleUtil.PrintMessage("Next: pat caco 17")
	elseif modeTag == "caco-17"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
		ConsoleUtil.PrintMessage("Next: pat caco 18")
	elseif modeTag == "caco-18"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat caco 19")
	elseif modeTag == "caco-19"
		ProvisionForm(player, 0x00316D7D, "Complete Alchemy & Cooking Overhaul.esp") ; Alkanet Flower
		ProvisionFormFallback(player, 0x0597B010, "Complete Alchemy & Cooking Overhaul.esp", 0x0097B010, "Complete Alchemy & Cooking Overhaul.esp") ; Barley
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x00326096, "Complete Alchemy & Cooking Overhaul.esp") ; Cecropia Moth
		ConsoleUtil.PrintMessage("1. Craft: Alkanet Flower + Barley")
		ConsoleUtil.PrintMessage("2. Craft: Aloe Vera + Bear Claws")
		ConsoleUtil.PrintMessage("3. Craft: Blue Mountain Flower + Cecropia Moth")
		ConsoleUtil.PrintMessage("Next: pat caco 20")
	elseif modeTag == "caco-20"
		ProvisionForm(player, 0x00316D7D, "Complete Alchemy & Cooking Overhaul.esp") ; Alkanet Flower
		ProvisionFormFallback(player, 0x0597B010, "Complete Alchemy & Cooking Overhaul.esp", 0x0097B010, "Complete Alchemy & Cooking Overhaul.esp") ; Barley
		ConsoleUtil.PrintMessage("1. Craft: Alkanet Flower + Barley")
		ConsoleUtil.PrintMessage("Next: pat caco 21")
	elseif modeTag == "caco-21"
		ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
		ProvisionFormFallback(player, 0x05A10059, "Complete Alchemy & Cooking Overhaul.esp", 0x00A10059, "Complete Alchemy & Cooking Overhaul.esp") ; Clouded Funnel Cap
		ConsoleUtil.PrintMessage("1. Craft: Chaurus Eggs + Clouded Funnel Cap")
		ConsoleUtil.PrintMessage("Next: pat caco 22")
	elseif modeTag == "caco-22"
		ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
		ProvisionFormFallback(player, 0x05A10059, "Complete Alchemy & Cooking Overhaul.esp", 0x00A10059, "Complete Alchemy & Cooking Overhaul.esp") ; Clouded Funnel Cap
		ConsoleUtil.PrintMessage("1. Craft: Chaurus Eggs + Clouded Funnel Cap")
		ConsoleUtil.PrintMessage("Next: pat caco 23")
	elseif modeTag == "caco-23"
		ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
		ProvisionFormFallback(player, 0x05A10059, "Complete Alchemy & Cooking Overhaul.esp", 0x00A10059, "Complete Alchemy & Cooking Overhaul.esp") ; Clouded Funnel Cap
		ConsoleUtil.PrintMessage("1. Craft: Chaurus Eggs + Clouded Funnel Cap")
		ConsoleUtil.PrintMessage("Next: pat caco 24")
	elseif modeTag == "caco-24"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ProvisionForm(player, 0x00660004, "Complete Alchemy & Cooking Overhaul.esp") ; Banded Pennant
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Ambrosia")
		ConsoleUtil.PrintMessage("2. Craft: Aloe Vera + Banded Pennant")
		ConsoleUtil.PrintMessage("Next: pat caco 25")
	elseif modeTag == "caco-25"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat caco 26")
	elseif modeTag == "caco-26"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Bear Claws")
		ConsoleUtil.PrintMessage("Next: pat caco 27")
	elseif modeTag == "caco-27"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x00326096, "Complete Alchemy & Cooking Overhaul.esp") ; Cecropia Moth
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Cecropia Moth")
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-caco-ap.py")
	elseif modeTag == "caco-ap-1"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
		ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
		ProvisionForm(player, 0x00000806, "ccbgssse037-curios.esl") ; Comberry
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x0003AD5B, "Skyrim.esm") ; Daedra Heart
		ProvisionForm(player, 0x0006BC0A, "Skyrim.esm") ; Large Antlers
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
		ConsoleUtil.PrintMessage("2. Craft: Deathbell + River Betty")
		ConsoleUtil.PrintMessage("3. Craft: Ash Creep Cluster + Comberry")
		ConsoleUtil.PrintMessage("4. Craft: Aloe Vera + Daedra Heart + Large Antlers")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 2")
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
		ConsoleUtil.PrintMessage("Next: pat caco-ap 3")
	elseif modeTag == "caco-ap-3"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat Extract")
		ConsoleUtil.PrintMessage("2. Craft: Boar Tusk + Briar Heart")
		ConsoleUtil.PrintMessage("3. Craft: Briar Heart + Ectoplasm")
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-caco-ap-2.py")
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
		ConsoleUtil.PrintMessage("Next: pat caco-ap 5")
	elseif modeTag == "caco-ap-5"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
		ProvisionForm(player, 0x0007E8B7, "Skyrim.esm") ; Swamp Fungal Pod
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + River Betty")
		ConsoleUtil.PrintMessage("2. Craft: Canis Root + Spider Egg")
		ConsoleUtil.PrintMessage("3. Craft: Swamp Fungal Pod + Wheat Extract")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 6")
	elseif modeTag == "caco-ap-6"
		ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
		ProvisionForm(player, 0x00000806, "ccbgssse037-curios.esl") ; Comberry
		ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
		ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ConsoleUtil.PrintMessage("1. Craft: Ash Creep Cluster + Comberry")
		ConsoleUtil.PrintMessage("2. Craft: Dragon's Tongue + Fly Amanita")
		ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 7")
	elseif modeTag == "caco-ap-7"
		ProvisionForm(player, 0x00077E1D, "Skyrim.esm") ; Red Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x005A46B8, "Complete Alchemy & Cooking Overhaul.esp") ; Wheat Extract
		ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ConsoleUtil.PrintMessage("1. Craft: Red Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat Extract")
		ConsoleUtil.PrintMessage("3. Craft: Boar Tusk + Briar Heart")
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-caco-ap-3.py")
	elseif modeTag == "caco-ap-8"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x0003AD5B, "Skyrim.esm") ; Daedra Heart
		ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
		ProvisionForm(player, 0x0006F950, "Skyrim.esm") ; Scaly Pholiota
		ProvisionForm(player, 0x000059BA, "Dawnguard.esm") ; Ancestor Moth
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Daedra Heart")
		ConsoleUtil.PrintMessage("2. Craft: Creep Cluster + Scaly Pholiota")
		ConsoleUtil.PrintMessage("3. Craft: Ancestor Moth + Blue Mountain Flower")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 9")
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
		ConsoleUtil.PrintMessage("Next: pat caco-ap 10")
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
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-caco-ap-4.py")
	elseif modeTag == "caco-ap-11"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 12")
	elseif modeTag == "caco-ap-12"
		ProvisionForm(player, 0x00316D7D, "Complete Alchemy & Cooking Overhaul.esp") ; Alkanet Flower
		ProvisionFormFallback(player, 0x0597B010, "Complete Alchemy & Cooking Overhaul.esp", 0x0097B010, "Complete Alchemy & Cooking Overhaul.esp") ; Barley
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
		ConsoleUtil.PrintMessage("1. Craft: Alkanet Flower + Barley")
		ConsoleUtil.PrintMessage("2. Craft: Aloe Vera + Bear Claws")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 13")
	elseif modeTag == "caco-ap-13"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Bear Claws")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 14")
	elseif modeTag == "caco-ap-14"
		ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
		ProvisionFormFallback(player, 0x05A10059, "Complete Alchemy & Cooking Overhaul.esp", 0x00A10059, "Complete Alchemy & Cooking Overhaul.esp") ; Clouded Funnel Cap
		ConsoleUtil.PrintMessage("1. Craft: Chaurus Eggs + Clouded Funnel Cap")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 15")
	elseif modeTag == "caco-ap-15"
		ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
		ProvisionFormFallback(player, 0x05A10059, "Complete Alchemy & Cooking Overhaul.esp", 0x00A10059, "Complete Alchemy & Cooking Overhaul.esp") ; Clouded Funnel Cap
		ConsoleUtil.PrintMessage("1. Craft: Chaurus Eggs + Clouded Funnel Cap")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 16")
	elseif modeTag == "caco-ap-16"
		ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
		ProvisionFormFallback(player, 0x05A10059, "Complete Alchemy & Cooking Overhaul.esp", 0x00A10059, "Complete Alchemy & Cooking Overhaul.esp") ; Clouded Funnel Cap
		ConsoleUtil.PrintMessage("1. Craft: Chaurus Eggs + Clouded Funnel Cap")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 17")
	elseif modeTag == "caco-ap-17"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ProvisionForm(player, 0x00660004, "Complete Alchemy & Cooking Overhaul.esp") ; Banded Pennant
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Ambrosia")
		ConsoleUtil.PrintMessage("2. Craft: Aloe Vera + Banded Pennant")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 18")
	elseif modeTag == "caco-ap-18"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ProvisionForm(player, 0x00CC0635, "Update.esm") ; Black Pearl (CACO_PearlBlack, injected into Update.esm range)
		ProvisionFormFallback(player, 0x0033F5E0, "Complete Alchemy & Cooking Overhaul.esp", 0x0833F5E0, "Complete Alchemy & Cooking Overhaul.esp") ; Blue Clipper Butterfly
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Ambrosia")
		ConsoleUtil.PrintMessage("2. Craft: Black Pearl + Blue Clipper Butterfly")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 19")
	elseif modeTag == "caco-ap-19"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 20")
	elseif modeTag == "caco-ap-20"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 21")
	elseif modeTag == "caco-ap-21"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 22")
	elseif modeTag == "caco-ap-22"
		ProvisionForm(player, 0x00316D7D, "Complete Alchemy & Cooking Overhaul.esp") ; Alkanet Flower
		ProvisionFormFallback(player, 0x0597B010, "Complete Alchemy & Cooking Overhaul.esp", 0x0097B010, "Complete Alchemy & Cooking Overhaul.esp") ; Barley
		ConsoleUtil.PrintMessage("1. Craft: Alkanet Flower + Barley")
		ConsoleUtil.PrintMessage("Next: pat caco-ap 23")
	elseif modeTag == "caco-ap-23"
		ProvisionForm(player, 0x00316D7D, "Complete Alchemy & Cooking Overhaul.esp") ; Alkanet Flower
		ProvisionFormFallback(player, 0x0597B010, "Complete Alchemy & Cooking Overhaul.esp", 0x0097B010, "Complete Alchemy & Cooking Overhaul.esp") ; Barley
		ConsoleUtil.PrintMessage("1. Craft: Alkanet Flower + Barley")
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-requiem.py")
	elseif modeTag == "requiem-1"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("3. Craft: Glowing Mushroom + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat requiem 2")
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
		ConsoleUtil.PrintMessage("Next: pat requiem 3")
	elseif modeTag == "requiem-3"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt (Requiem renames Salt Pile)
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Salt + Garlic")
		ConsoleUtil.PrintMessage("3. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat requiem 4")
	elseif modeTag == "requiem-4"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Creep Cluster")
		ConsoleUtil.PrintMessage("3. Craft: Blue Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("Next: pat requiem 5")
	elseif modeTag == "requiem-5"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt (Requiem renames Salt Pile)
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Blue Mountain Flower + Blue Butterfly Wing")
		ConsoleUtil.PrintMessage("3. Craft: Salt + Garlic")
		ConsoleUtil.PrintMessage("Next: pat requiem 6")
	elseif modeTag == "requiem-6"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat requiem 7")
	elseif modeTag == "requiem-7"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt (Requiem renames Salt Pile)
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("3. Craft: Salt + Garlic")
		ConsoleUtil.PrintMessage("Next: pat requiem 8")
	elseif modeTag == "requiem-8"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
		ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
		ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Creep Cluster")
		ConsoleUtil.PrintMessage("3. Craft: Dragon's Tongue + Fly Amanita")
		ConsoleUtil.PrintMessage("Next: pat requiem 9")
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
		ConsoleUtil.PrintMessage("Next: pat requiem 10")
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
		ConsoleUtil.PrintMessage("Next: pat requiem 11")
	elseif modeTag == "requiem-11"
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ConsoleUtil.PrintMessage("1. Craft: Blue Mountain Flower + Wheat")
		ConsoleUtil.PrintMessage("Next: pat requiem 12")
	elseif modeTag == "requiem-12"
		ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Glowing Mushroom + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat requiem 13")
	elseif modeTag == "requiem-13"
		ProvisionForm(player, 0x00000822, "ccbgssse037-curios.esl") ; Blind Watcher's Eye
		ProvisionForm(player, 0x0001CD6E, "Dragonborn.esm") ; Burnt Spriggan Wood
		ProvisionForm(player, 0x000727E0, "Skyrim.esm") ; Butterfly Wing
		ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
		ProvisionForm(player, 0x00000D66, "ccbgssse037-curios.esl") ; Aster Bloom Core
		ProvisionForm(player, 0x0001CD6F, "Dragonborn.esm") ; Boar Tusk
		ProvisionForm(player, 0x000059BA, "Dawnguard.esm") ; Ancestor Moth Wing
		ProvisionForm(player, 0x00000807, "ccbgssse037-curios.esl") ; Congealed Putrescence
		ConsoleUtil.PrintMessage("1. Craft: Blind Watcher's Eye + Burnt Spriggan Wood")
		ConsoleUtil.PrintMessage("2. Craft: Butterfly Wing + Dragon's Tongue")
		ConsoleUtil.PrintMessage("3. Craft: Aster Bloom Core + Boar Tusk")
		ConsoleUtil.PrintMessage("4. Craft: Ancestor Moth Wing + Congealed Putrescence")
		ConsoleUtil.PrintMessage("Next: pat requiem 14")
	elseif modeTag == "requiem-14"
		ProvisionForm(player, 0x00000827, "ccbgssse037-curios.esl") ; Dreugh Wax
		ProvisionForm(player, 0x0000081F, "ccbgssse037-curios.esl") ; Stoneflower Petals
		ProvisionForm(player, 0x00059155, "ccbgssse025-advdsgs.esm") ; Bliss Bug Thorax
		ProvisionForm(player, 0x000F11C0, "Skyrim.esm") ; Dwarven Oil
		ProvisionForm(player, 0x000008EB, "ccbgssse001-fish.esm") ; Angelfish
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x00057F91, "Skyrim.esm") ; Hanging Moss
		ConsoleUtil.PrintMessage("1. Craft: Dreugh Wax + Stoneflower Petals")
		ConsoleUtil.PrintMessage("2. Craft: Bliss Bug Thorax + Dwarven Oil")
		ConsoleUtil.PrintMessage("3. Craft: Angelfish + Canis Root")
		ConsoleUtil.PrintMessage("4. Craft: Canis Root + Hanging Moss")
		ConsoleUtil.PrintMessage("Next: pat requiem 15")
	elseif modeTag == "requiem-15"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera Leaves + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat requiem 16")
	elseif modeTag == "requiem-16"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera Leaves + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat requiem 17")
	elseif modeTag == "requiem-17"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera Leaves + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat requiem 18")
	elseif modeTag == "requiem-18"
		ProvisionFormFallback(player, 0x00A100AD, "Complete Alchemy & Cooking Overhaul.esp", 0x000000D0, "_ResourcePack.esl")
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Aloe Vera Leaves + Ambrosia")
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-apothecary.py")
	elseif modeTag == "apothecary-1"
		ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
		ConsoleUtil.PrintMessage("1. Craft: Blue Butterfly Wing + Blue Mountain Flower")
		ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("4. Craft: Canis Root + Spider Egg")
		ConsoleUtil.PrintMessage("Next: pat apothecary 2")
	elseif modeTag == "apothecary-2"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Blue Butterfly Wing + Blue Mountain Flower")
		ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("Next: pat apothecary 3")
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
		ConsoleUtil.PrintMessage("Next: pat apothecary 4")
	elseif modeTag == "apothecary-4"
		ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
		ConsoleUtil.PrintMessage("1. Craft: Blue Butterfly Wing + Blue Mountain Flower")
		ConsoleUtil.PrintMessage("2. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("4. Craft: Canis Root + Spider Egg")
		ConsoleUtil.PrintMessage("Next: pat apothecary 5")
	elseif modeTag == "apothecary-5"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Blue Butterfly Wing + Blue Mountain Flower")
		ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("Next: pat apothecary 6")
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
		ConsoleUtil.PrintMessage("Next: pat apothecary 7")
	elseif modeTag == "apothecary-7"
		ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x000889A2, "Skyrim.esm") ; Dragon's Tongue
		ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ProvisionForm(player, 0x000727DF, "Skyrim.esm") ; Luna Moth Wing
		ProvisionForm(player, 0x0003AD76, "Skyrim.esm") ; Vampire Dust
		ConsoleUtil.PrintMessage("1. Craft: Blue Butterfly Wing + Blue Mountain Flower")
		ConsoleUtil.PrintMessage("2. Craft: Dragon's Tongue + Fly Amanita")
		ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("4. Craft: Luna Moth Wing + Vampire Dust")
		ConsoleUtil.PrintMessage("Next: pat apothecary 8")
	elseif modeTag == "apothecary-8"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x0003AD63, "Skyrim.esm") ; Ectoplasm
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Briar Heart + Ectoplasm")
		ConsoleUtil.PrintMessage("3. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("4. Craft: Canis Root + Spider Egg")
		ConsoleUtil.PrintMessage("Next: pat apothecary 9")
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
		ConsoleUtil.PrintMessage("Next: pat apothecary 10")
	elseif modeTag == "apothecary-10"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x00034CDF, "Skyrim.esm") ; Salt Pile
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Blue Butterfly Wing + Blue Mountain Flower")
		ConsoleUtil.PrintMessage("3. Craft: Salt Pile + Garlic")
		ConsoleUtil.PrintMessage("4. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat apothecary 11")
	elseif modeTag == "apothecary-11"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x000727DE, "Skyrim.esm") ; Blue Butterfly Wing
		ProvisionForm(player, 0x00077E1C, "Skyrim.esm") ; Blue Mountain Flower
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Blue Butterfly Wing + Blue Mountain Flower")
		ConsoleUtil.PrintMessage("3. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat apothecary 12")
	elseif modeTag == "apothecary-12"
		ProvisionForm(player, 0x0004DA73, "Skyrim.esm") ; Torchbug Thorax
		ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
		ConsoleUtil.PrintMessage("1. Craft: Torchbug Thorax + Chaurus Eggs")
		ConsoleUtil.PrintMessage("Next: pat apothecary 13")
	elseif modeTag == "apothecary-13"
		ProvisionForm(player, 0x0004DA00, "Skyrim.esm") ; Fly Amanita
		ProvisionForm(player, 0x0001B3BD, "Skyrim.esm") ; Snowberries
		ProvisionForm(player, 0x00034D32, "Skyrim.esm") ; Frost Mirriam
		ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
		ProvisionForm(player, 0x000A9191, "Skyrim.esm") ; Beehive Husk
		ProvisionForm(player, 0x000134AA, "Skyrim.esm") ; Thistle Branch
		ConsoleUtil.PrintMessage("1. Craft: Fly Amanita + Snowberries")
		ConsoleUtil.PrintMessage("2. Craft: Frost Mirriam + Snowberries")
		ConsoleUtil.PrintMessage("3. Craft: Glowing Mushroom + Snowberries")
		ConsoleUtil.PrintMessage("4. Craft: Beehive Husk + Thistle Branch")
		ConsoleUtil.PrintMessage("Next: pat apothecary 14")
	elseif modeTag == "apothecary-14"
		ProvisionForm(player, 0x0003AD5B, "Skyrim.esm") ; Daedra Heart
		ProvisionForm(player, 0x0006BC07, "Skyrim.esm") ; Eye of Sabre Cat
		ConsoleUtil.PrintMessage("1. Craft: Daedra Heart + Eye of Sabre Cat")
		ConsoleUtil.PrintMessage("Next: pat apothecary 15")
	elseif modeTag == "apothecary-15"
		ProvisionForm(player, 0x0003AD5B, "Skyrim.esm") ; Daedra Heart
		ProvisionForm(player, 0x0006BC07, "Skyrim.esm") ; Eye of Sabre Cat
		ConsoleUtil.PrintMessage("1. Craft: Daedra Heart + Eye of Sabre Cat")
		ConsoleUtil.PrintMessage("Next: pat apothecary 16")
	elseif modeTag == "apothecary-16"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ProvisionForm(player, 0x00023D77, "Skyrim.esm") ; Chicken's Egg
		ProvisionForm(player, 0x0003F7F8, "Skyrim.esm") ; Tundra Cotton
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("2. Craft: Chicken's Egg + Tundra Cotton")
		ConsoleUtil.PrintMessage("Next: pat apothecary 17")
	elseif modeTag == "apothecary-17"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat apothecary 18")
	elseif modeTag == "apothecary-18"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat apothecary 19")
	elseif modeTag == "apothecary-19"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat apothecary 20")
	elseif modeTag == "apothecary-20"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0004B0BA, "Skyrim.esm") ; Wheat
		ProvisionForm(player, 0x00077E1D, "Skyrim.esm") ; Red Mountain Flower
		ProvisionForm(player, 0x0003F7F8, "Skyrim.esm") ; Tundra Cotton
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Wheat")
		ConsoleUtil.PrintMessage("2. Craft: Red Mountain Flower + Tundra Cotton")
		ConsoleUtil.PrintMessage("Next: pat apothecary 21")
	elseif modeTag == "apothecary-21"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat apothecary 22")
	elseif modeTag == "apothecary-22"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ProvisionForm(player, 0x00077E1D, "Skyrim.esm") ; Red Mountain Flower
		ProvisionForm(player, 0x000EC870, "Skyrim.esm") ; Mora Tapinella
		ProvisionForm(player, 0x00077E1E, "Skyrim.esm") ; Purple Mountain Flower
		ProvisionForm(player, 0x0006BC04, "Skyrim.esm") ; Sabre Cat Tooth
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("2. Craft: Red Mountain Flower + Mora Tapinella")
		ConsoleUtil.PrintMessage("3. Craft: Purple Mountain Flower + Sabre Cat Tooth")
		ConsoleUtil.PrintMessage("Next: pat apothecary 23")
	elseif modeTag == "apothecary-23"
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
		ProvisionForm(player, 0x000F11C0, "Skyrim.esm") ; Dwarven Oil
		ProvisionForm(player, 0x0006F950, "Skyrim.esm") ; Scaly Pholiota
		ProvisionForm(player, 0x00023D77, "Skyrim.esm") ; Chicken's Egg
		ProvisionForm(player, 0x0003F7F8, "Skyrim.esm") ; Tundra Cotton
		ConsoleUtil.PrintMessage("1. Craft: Canis Root + Spider Egg")
		ConsoleUtil.PrintMessage("2. Craft: Dwarven Oil + Scaly Pholiota")
		ConsoleUtil.PrintMessage("3. Craft: Chicken's Egg + Tundra Cotton")
		ConsoleUtil.PrintMessage("Next: pat apothecary 24")
	elseif modeTag == "apothecary-24"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat apothecary 25")
	elseif modeTag == "apothecary-25"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x0009151B, "Skyrim.esm") ; Spider Egg
		ProvisionForm(player, 0x000F11C0, "Skyrim.esm") ; Dwarven Oil
		ProvisionForm(player, 0x0006F950, "Skyrim.esm") ; Scaly Pholiota
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("2. Craft: Canis Root + Spider Egg")
		ConsoleUtil.PrintMessage("3. Craft: Dwarven Oil + Scaly Pholiota")
		ConsoleUtil.PrintMessage("Next: pat apothecary 26")
	elseif modeTag == "apothecary-26"
		ProvisionForm(player, 0x00077E1D, "Skyrim.esm") ; Red Mountain Flower
		ProvisionForm(player, 0x000EC870, "Skyrim.esm") ; Mora Tapinella
		ProvisionForm(player, 0x00077E1E, "Skyrim.esm") ; Purple Mountain Flower
		ProvisionForm(player, 0x0006BC04, "Skyrim.esm") ; Sabre Cat Tooth
		ConsoleUtil.PrintMessage("1. Craft: Red Mountain Flower + Mora Tapinella")
		ConsoleUtil.PrintMessage("2. Craft: Purple Mountain Flower + Sabre Cat Tooth")
		ConsoleUtil.PrintMessage("Next: pat apothecary 27")
	elseif modeTag == "apothecary-27"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat apothecary 28")
	elseif modeTag == "apothecary-28"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0002F44C, "Skyrim.esm") ; Nightshade
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Nightshade")
		ConsoleUtil.PrintMessage("Next: pat apothecary 29")
	elseif modeTag == "apothecary-29"
		ProvisionForm(player, 0x0004DA20, "Skyrim.esm") ; Bleeding Crown
		ProvisionForm(player, 0x00059155, "ccbgssse025-advdsgs.esm") ; Bliss Bug Thorax
		ProvisionForm(player, 0x000E4F0C, "Skyrim.esm") ; Blue Dartwing
		ProvisionForm(player, 0x00000D6C, "ccbgssse037-curios.esl") ; Bog Beacon
		ProvisionForm(player, 0x00000805, "ccbgssse037-curios.esl") ; Coda Flower
		ProvisionForm(player, 0x000B2183, "Skyrim.esm") ; Creep Cluster
		ProvisionForm(player, 0x000059BA, "Dawnguard.esm") ; Ancestor Moth Wing
		ProvisionForm(player, 0x0001CD6E, "Dragonborn.esm") ; Burnt Spriggan Wood
		ConsoleUtil.PrintMessage("1. Craft: Bleeding Crown + Bliss Bug Thorax")
		ConsoleUtil.PrintMessage("2. Craft: Blue Dartwing + Bog Beacon")
		ConsoleUtil.PrintMessage("3. Craft: Coda Flower + Creep Cluster")
		ConsoleUtil.PrintMessage("4. Craft: Ancestor Moth Wing + Burnt Spriggan Wood")
		ConsoleUtil.PrintMessage("Next: pat apothecary 30")
	elseif modeTag == "apothecary-30"
		ProvisionForm(player, 0x0004DA23, "Skyrim.esm") ; Imp Stool
		ProvisionForm(player, 0x000BB956, "Skyrim.esm") ; Orange Dartwing
		ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
		ProvisionForm(player, 0x0006F950, "Skyrim.esm") ; Scaly Pholiota
		ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
		ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Imp Stool + Orange Dartwing")
		ConsoleUtil.PrintMessage("2. Craft: Bee + Scaly Pholiota")
		ConsoleUtil.PrintMessage("3. Craft: Bear Claws + Giant's Toe")
		ConsoleUtil.PrintMessage("4. Craft: Deathbell + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 31")
	elseif modeTag == "apothecary-31"
		ProvisionForm(player, 0x0004DA20, "Skyrim.esm") ; Bleeding Crown
		ProvisionForm(player, 0x00059155, "ccbgssse025-advdsgs.esm") ; Bliss Bug Thorax
		ConsoleUtil.PrintMessage("1. Craft: Bleeding Crown + Bliss Bug Thorax")
		ConsoleUtil.PrintMessage("Next: pat apothecary 32")
	elseif modeTag == "apothecary-32"
		ProvisionForm(player, 0x0004DA20, "Skyrim.esm") ; Bleeding Crown
		ProvisionForm(player, 0x00059155, "ccbgssse025-advdsgs.esm") ; Bliss Bug Thorax
		ConsoleUtil.PrintMessage("1. Craft: Bleeding Crown + Bliss Bug Thorax")
		ConsoleUtil.PrintMessage("Next: pat apothecary 33")
	elseif modeTag == "apothecary-33"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 34")
	elseif modeTag == "apothecary-34"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 35")
	elseif modeTag == "apothecary-35"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 36")
	elseif modeTag == "apothecary-36"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 37")
	elseif modeTag == "apothecary-37"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 38")
	elseif modeTag == "apothecary-38"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 39")
	elseif modeTag == "apothecary-39"
		ProvisionForm(player, 0x000E4F0C, "Skyrim.esm") ; Blue Dartwing
		ProvisionForm(player, 0x00106E19, "Skyrim.esm") ; Cyrodilic Spadetail
		ConsoleUtil.PrintMessage("1. Craft: Blue Dartwing + Cyrodilic Spadetail")
		ConsoleUtil.PrintMessage("Next: pat apothecary 40")
	elseif modeTag == "apothecary-40"
		ProvisionForm(player, 0x000E4F0C, "Skyrim.esm") ; Blue Dartwing
		ProvisionForm(player, 0x00106E19, "Skyrim.esm") ; Cyrodilic Spadetail
		ConsoleUtil.PrintMessage("1. Craft: Blue Dartwing + Cyrodilic Spadetail")
		ConsoleUtil.PrintMessage("Next: pat apothecary 41")
	elseif modeTag == "apothecary-41"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0003AD5D, "Skyrim.esm") ; Falmer Ear
		ProvisionForm(player, 0x00106E1B, "Skyrim.esm") ; Abecean Longfin
		ProvisionForm(player, 0x00034D31, "Skyrim.esm") ; Elves Ear
		ProvisionForm(player, 0x00016E26, "Dragonborn.esm") ; Ashen Grass Pod
		ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
		ProvisionForm(player, 0x0003AD56, "Skyrim.esm") ; Chaurus Eggs
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Falmer Ear")
		ConsoleUtil.PrintMessage("2. Craft: Abecean Longfin + Elves Ear")
		ConsoleUtil.PrintMessage("3. Craft: Ashen Grass Pod + Bee")
		ConsoleUtil.PrintMessage("4. Craft: Chaurus Eggs + Deathbell")
		ConsoleUtil.PrintMessage("Next: pat apothecary 42")
	elseif modeTag == "apothecary-42"
		ProvisionForm(player, 0x00106E1B, "Skyrim.esm") ; Abecean Longfin
		ProvisionForm(player, 0x000A9191, "Skyrim.esm") ; Beehive Husk
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x0007EE01, "Skyrim.esm") ; Glowing Mushroom
		ProvisionForm(player, 0x00016E26, "Dragonborn.esm") ; Ashen Grass Pod
		ProvisionForm(player, 0x0003AD5D, "Skyrim.esm") ; Falmer Ear
		ConsoleUtil.PrintMessage("1. Craft: Abecean Longfin + Beehive Husk")
		ConsoleUtil.PrintMessage("2. Craft: Abecean Longfin + Deathbell")
		ConsoleUtil.PrintMessage("3. Craft: Blisterwort + Glowing Mushroom")
		ConsoleUtil.PrintMessage("4. Craft: Ashen Grass Pod + Falmer Ear")
		ConsoleUtil.PrintMessage("Next: pat apothecary 43")
	elseif modeTag == "apothecary-43"
		ProvisionForm(player, 0x000E4F0C, "Skyrim.esm") ; Blue Dartwing
		ProvisionForm(player, 0x000BB956, "Skyrim.esm") ; Orange Dartwing
		ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
		ProvisionForm(player, 0x0003AD73, "Skyrim.esm") ; Glow Dust
		ProvisionForm(player, 0x000727E0, "Skyrim.esm") ; Butterfly Wing
		ProvisionForm(player, 0x00023D77, "Skyrim.esm") ; Chicken's Egg
		ProvisionForm(player, 0x0006B689, "Skyrim.esm") ; Hagraven Claw
		ProvisionForm(player, 0x00077E1E, "Skyrim.esm") ; Purple Mountain Flower
		ConsoleUtil.PrintMessage("1. Craft: Blue Dartwing + Orange Dartwing")
		ConsoleUtil.PrintMessage("2. Craft: Bear Claws + Glow Dust")
		ConsoleUtil.PrintMessage("3. Craft: Butterfly Wing + Chicken's Egg")
		ConsoleUtil.PrintMessage("4. Craft: Hagraven Claw + Purple Mountain Flower")
		ConsoleUtil.PrintMessage("Next: pat apothecary 44")
	elseif modeTag == "apothecary-44"
		ProvisionForm(player, 0x0004DA23, "Skyrim.esm") ; Imp Stool
		ProvisionForm(player, 0x000BB956, "Skyrim.esm") ; Orange Dartwing
		ProvisionForm(player, 0x00083E64, "Skyrim.esm") ; Grass Pod
		ProvisionForm(player, 0x00106E1A, "Skyrim.esm") ; River Betty
		ProvisionForm(player, 0x0003AD61, "Skyrim.esm") ; Briar Heart
		ProvisionForm(player, 0x000B08C5, "Skyrim.esm") ; Honeycomb
		ProvisionForm(player, 0x0006BC02, "Skyrim.esm") ; Bear Claws
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ConsoleUtil.PrintMessage("1. Craft: Imp Stool + Orange Dartwing")
		ConsoleUtil.PrintMessage("2. Craft: Grass Pod + River Betty")
		ConsoleUtil.PrintMessage("3. Craft: Briar Heart + Honeycomb")
		ConsoleUtil.PrintMessage("4. Craft: Bear Claws + Canis Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 45")
	elseif modeTag == "apothecary-45"
		ProvisionForm(player, 0x00034CDD, "Skyrim.esm") ; Bone Meal
		ProvisionForm(player, 0x0003AD64, "Skyrim.esm") ; Giant's Toe
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ProvisionForm(player, 0x00000D68, "ccbgssse037-curios.esl") ; Bittergreen Petals
		ProvisionForm(player, 0x00000D6A, "ccbgssse037-curios.esl") ; Blister Pod Cap
		ProvisionForm(player, 0x00000810, "ccbgssse037-curios.esl") ; Kagouti Hide
		ProvisionForm(player, 0x0003AD5D, "Skyrim.esm") ; Falmer Ear
		ProvisionForm(player, 0x0003AD6F, "Skyrim.esm") ; Skeever Tail
		ConsoleUtil.PrintMessage("1. Craft: Bone Meal + Giant's Toe")
		ConsoleUtil.PrintMessage("2. Craft: Ambrosia + Bittergreen Petals")
		ConsoleUtil.PrintMessage("3. Craft: Blister Pod Cap + Kagouti Hide")
		ConsoleUtil.PrintMessage("4. Craft: Falmer Ear + Skeever Tail")
		ConsoleUtil.PrintMessage("Next: pat apothecary 46")
	elseif modeTag == "apothecary-46"
		ProvisionForm(player, 0x00000D62, "ccbgssse037-curios.esl") ; Alocasia Fruit
		ProvisionForm(player, 0x00000822, "ccbgssse037-curios.esl") ; Blind Watcher's Eye
		ProvisionForm(player, 0x000008EB, "ccbgssse001-fish.esm") ; Angelfish
		ProvisionForm(player, 0x000008F0, "ccbgssse001-fish.esm") ; Angler Larvae
		ProvisionForm(player, 0x00034CDD, "Skyrim.esm") ; Bone Meal
		ProvisionForm(player, 0x00000802, "ccbgssse037-curios.esl") ; Bungler's Bane
		ProvisionForm(player, 0x000A9195, "Skyrim.esm") ; Bee
		ProvisionForm(player, 0x000705B7, "Skyrim.esm") ; Berit's Ashes
		ConsoleUtil.PrintMessage("1. Craft: Alocasia Fruit + Blind Watcher's Eye")
		ConsoleUtil.PrintMessage("2. Craft: Angelfish + Angler Larvae")
		ConsoleUtil.PrintMessage("3. Craft: Bone Meal + Bungler's Bane")
		ConsoleUtil.PrintMessage("4. Craft: Bee + Berit's Ashes")
		ConsoleUtil.PrintMessage("Next: pat apothecary 47")
	elseif modeTag == "apothecary-47"
		ProvisionForm(player, 0x00000D66, "ccbgssse037-curios.esl") ; Aster Bloom Core
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x00034D32, "Skyrim.esm") ; Frost Mirriam
		ProvisionForm(player, 0x00083E64, "Skyrim.esm") ; Grass Pod
		ProvisionForm(player, 0x00052695, "Skyrim.esm") ; Charred Skeever Hide
		ProvisionForm(player, 0x000E7ED0, "Skyrim.esm") ; Hawk Feathers
		ProvisionForm(player, 0x000727E0, "Skyrim.esm") ; Butterfly Wing
		ProvisionForm(player, 0x0000080F, "ccbgssse037-curios.esl") ; Imp Gall
		ConsoleUtil.PrintMessage("1. Craft: Aster Bloom Core + Canis Root")
		ConsoleUtil.PrintMessage("2. Craft: Frost Mirriam + Grass Pod")
		ConsoleUtil.PrintMessage("3. Craft: Charred Skeever Hide + Hawk Feathers")
		ConsoleUtil.PrintMessage("4. Craft: Butterfly Wing + Imp Gall")
		ConsoleUtil.PrintMessage("Next: pat apothecary 48")
	elseif modeTag == "apothecary-48"
		ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
		ProvisionForm(player, 0x000A9191, "Skyrim.esm") ; Beehive Husk
		ProvisionForm(player, 0x0001CD71, "Dragonborn.esm") ; Ash Hopper Jelly
		ProvisionForm(player, 0x00059155, "ccbgssse025-advdsgs.esm") ; Bliss Bug Thorax
		ProvisionForm(player, 0x00000D6C, "ccbgssse037-curios.esl") ; Bog Beacon
		ProvisionForm(player, 0x000059BA, "Dawnguard.esm") ; Ancestor Moth Wing
		ProvisionForm(player, 0x0006B689, "Skyrim.esm") ; Hagraven Claw
		ConsoleUtil.PrintMessage("1. Craft: Ash Creep Cluster + Beehive Husk")
		ConsoleUtil.PrintMessage("2. Craft: Ash Hopper Jelly + Beehive Husk")
		ConsoleUtil.PrintMessage("3. Craft: Bliss Bug Thorax + Bog Beacon")
		ConsoleUtil.PrintMessage("4. Craft: Ancestor Moth Wing + Hagraven Claw")
		ConsoleUtil.PrintMessage("Next: pat apothecary 49")
	elseif modeTag == "apothecary-49"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat apothecary 50")
	elseif modeTag == "apothecary-50"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ProvisionForm(player, 0x000008EB, "ccbgssse001-fish.esm") ; Angelfish
		ProvisionForm(player, 0x0006ABCB, "Skyrim.esm") ; Canis Root
		ProvisionForm(player, 0x00000805, "ccbgssse037-curios.esl") ; Coda Flower
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Ambrosia")
		ConsoleUtil.PrintMessage("2. Craft: Angelfish + Canis Root")
		ConsoleUtil.PrintMessage("3. Craft: Coda Flower + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 51")
	elseif modeTag == "apothecary-51"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat apothecary 52")
	elseif modeTag == "apothecary-52"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 53")
	elseif modeTag == "apothecary-53"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 54")
	elseif modeTag == "apothecary-54"
		ProvisionForm(player, 0x000516C8, "Skyrim.esm") ; Deathbell
		ProvisionForm(player, 0x0001BCBC, "Skyrim.esm") ; Jarrin Root
		ConsoleUtil.PrintMessage("1. Craft: Deathbell + Jarrin Root")
		ConsoleUtil.PrintMessage("Next: pat apothecary 55")
	elseif modeTag == "apothecary-55"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ProvisionForm(player, 0x000F11C0, "Skyrim.esm") ; Dwarven Oil
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Ambrosia")
		ConsoleUtil.PrintMessage("2. Craft: Dwarven Oil + Garlic")
		ConsoleUtil.PrintMessage("Next: pat apothecary 56")
	elseif modeTag == "apothecary-56"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Ambrosia")
		ConsoleUtil.PrintMessage("Next: pat apothecary 57")
	elseif modeTag == "apothecary-57"
		ProvisionForm(player, 0x0004DA25, "Skyrim.esm") ; Blisterwort
		ProvisionForm(player, 0x00000836, "ccbgssse037-curios.esl") ; Ambrosia
		ProvisionForm(player, 0x000F11C0, "Skyrim.esm") ; Dwarven Oil
		ProvisionForm(player, 0x00034D22, "Skyrim.esm") ; Garlic
		ProvisionForm(player, 0x000008EB, "ccbgssse001-fish.esm") ; Angelfish
		ProvisionForm(player, 0x0001CD74, "Dragonborn.esm") ; Ash Creep Cluster
		ConsoleUtil.PrintMessage("1. Craft: Blisterwort + Ambrosia")
		ConsoleUtil.PrintMessage("2. Craft: Dwarven Oil + Garlic")
		ConsoleUtil.PrintMessage("3. Craft: Angelfish + Ash Creep Cluster")
		ConsoleUtil.PrintMessage("Next: Exit Skyrim and run python pat-default-vanilla.py")
	elseif modeTag == "vanilla-changed"
		ConsoleUtil.PrintMessage("Export-only block: no crafting required.")
		ConsoleUtil.PrintMessage("Next: In the Developer Test Hub press 'Export potion predictions to CSV', then run 'python sync_potion_predictions.py'")
		ConsoleUtil.PrintMessage("Then: Exit Skyrim and run python pat-ap-changed.py")
	elseif modeTag == "ap-changed"
		ConsoleUtil.PrintMessage("Export-only block: no crafting required.")
		ConsoleUtil.PrintMessage("Next: In the Developer Test Hub press 'Export potion predictions to CSV', then run 'python sync_potion_predictions.py'")
		ConsoleUtil.PrintMessage("Then: Exit Skyrim and run python pat-caco-changed.py")
	elseif modeTag == "caco-changed"
		ConsoleUtil.PrintMessage("Export-only block: no crafting required.")
		ConsoleUtil.PrintMessage("Next: In the Developer Test Hub press 'Export potion predictions to CSV', then run 'python sync_potion_predictions.py'")
		ConsoleUtil.PrintMessage("Then: Exit Skyrim and run python pat-caco-ap-changed.py")
	elseif modeTag == "caco-ap-changed"
		ConsoleUtil.PrintMessage("Export-only block: no crafting required.")
		ConsoleUtil.PrintMessage("Next: In the Developer Test Hub press 'Export potion predictions to CSV', then run 'python sync_potion_predictions.py'")
		ConsoleUtil.PrintMessage("Then: Exit Skyrim and run python pat-requiem-changed.py")
	elseif modeTag == "requiem-changed"
		ConsoleUtil.PrintMessage("Export-only block: no crafting required.")
		ConsoleUtil.PrintMessage("Next: In the Developer Test Hub press 'Export potion predictions to CSV', then run 'python sync_potion_predictions.py'")
		ConsoleUtil.PrintMessage("Then: Exit Skyrim and run python pat-apothecary-changed.py")
	elseif modeTag == "apothecary-changed"
		ConsoleUtil.PrintMessage("Export-only block: no crafting required.")
		ConsoleUtil.PrintMessage("Next: In the Developer Test Hub press 'Export potion predictions to CSV', then run 'python sync_potion_predictions.py'")
		ConsoleUtil.PrintMessage("Then: python potion_prediction_test.py --check-confirmed-csv, then python save_predicted_changed_settings.py")
	else
		ConsoleUtil.PrintMessage("Unknown mode tag: " + modeTag)
	endif
EndFunction