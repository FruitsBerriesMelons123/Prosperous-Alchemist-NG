#pragma once

#include <RE/Skyrim.h>

#include "PluginUtils.h"

#include <string_view>

namespace alchemist::seeker
{
	inline constexpr std::string_view kDragonborn = "Dragonborn.esm";
	inline constexpr RE::FormID kSpellLocalFormID = 0x034838;
	inline constexpr RE::FormID kPerkLocalFormID = 0x03399F;
	inline constexpr RE::FormID kRewardGlobalLocalFormID = 0x020E9A;
	inline constexpr float kShadowsRewardValue = 3.0f;

	inline RE::SpellItem* GetSpell()
	{
		return plugin_utils::LookupFormFlexible<RE::SpellItem>(kSpellLocalFormID, kDragonborn);
	}

	inline RE::BGSPerk* GetPerk()
	{
		return plugin_utils::LookupFormFlexible<RE::BGSPerk>(kPerkLocalFormID, kDragonborn);
	}

	inline RE::TESGlobal* GetRewardGlobal()
	{
		return plugin_utils::LookupFormFlexible<RE::TESGlobal>(kRewardGlobalLocalFormID, kDragonborn);
	}
}