#include "Ordinator.h"

#include "PluginUtils.h"

#include <RE/Skyrim.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <set>
#include <string_view>

namespace alchemist::ordinator
{
	namespace
	{
		using plugin_utils::EqualsIgnoreCase;

		constexpr std::string_view kPluginName = "Ordinator - Perks of Skyrim.esp";
		constexpr std::string_view kAdvancedLabGlobal = "ORD_Alc_AdvancedLab_Global_Type";
		// Ordinator overrides these Skyrim alchemy perks in place, retaining their
		// Skyrim.esm FormIDs and editor IDs instead of Ordinator-prefixed identities.
		constexpr std::array<RE::FormID, 2> kOverriddenAlchemyMasteryFormIDs{ 0x000BE127, 0x000C07CA };
		constexpr RE::FormID kOverriddenPhysicianFormID = 0x00058215;
		// Verified PERK records in the installed Ordinator ESP. Skyrim's BGSPerk
		// does not retain editor IDs, so these plugin-local IDs are necessary to
		// detect hidden choice perks independently of the parent dialog perk.
		constexpr std::array<RE::FormID, 3> kPhysicianChoiceFormIDs{ 0x0003F79D, 0x0003F79E, 0x0003F79F };
		constexpr RE::FormID kOverriddenPoisonerFormID = 0x00058217;
		constexpr RE::FormID kOverriddenPureMixtureFormID = 0x0005821D;

		bool ContainsIgnoreCase(std::string_view a_text, std::string_view a_search) noexcept
		{
			if (a_search.empty()) {
				return true;
			}
			if (a_search.size() > a_text.size()) {
				return false;
			}
			for (std::size_t offset = 0; offset <= a_text.size() - a_search.size(); ++offset) {
				if (EqualsIgnoreCase(a_text.substr(offset, a_search.size()), a_search)) {
					return true;
				}
			}
			return false;
		}

		bool HasIdentity(const RE::BGSPerk* a_perk, std::string_view a_identity) noexcept
		{
			if (!a_perk) {
				return false;
			}
			const auto* editorID = a_perk->GetFormEditorID();
			return editorID && ContainsIgnoreCase(editorID, "ORD_Alc") && ContainsIgnoreCase(editorID, a_identity);
		}

		bool HasPerkByLocalFormID(const RE::PlayerCharacter* a_player, RE::FormID a_localFormID) noexcept
		{
			if (!a_player) {
				return false;
			}
			auto* perk = plugin_utils::LookupFormFlexible<RE::BGSPerk>(a_localFormID, kPluginName);
			return perk && a_player->HasPerk(perk);
		}

		template <class Predicate>
		int GetActivePerkRank(const RE::PlayerCharacter* a_player, Predicate a_predicate) noexcept
		{
			if (!a_player) {
				return 0;
			}
			try {
				const auto& runtimeData = a_player->GetPlayerRuntimeData();
				int rank = 0;
				for (const auto* entry : runtimeData.addedPerks) {
					if (entry && entry->perk && entry->currentRank > 0 &&
						a_player->HasPerk(const_cast<RE::BGSPerk*>(entry->perk)) && a_predicate(entry->perk)) {
						rank = (std::max)(rank, static_cast<int>(entry->currentRank));
					}
				}
				for (const auto* perk : runtimeData.perks) {
					if (perk && a_player->HasPerk(const_cast<RE::BGSPerk*>(perk)) && a_predicate(perk)) {
						rank = (std::max)(rank, 1);
					}
				}
				return rank;
			} catch (...) {
				return 0;
			}
		}

		template <class Predicate>
		int GetActivePerkCount(const RE::PlayerCharacter* a_player, Predicate a_predicate) noexcept
		{
			if (!a_player) {
				return 0;
			}
			try {
				const auto& runtimeData = a_player->GetPlayerRuntimeData();
				std::set<const RE::BGSPerk*> active;
				for (const auto* entry : runtimeData.addedPerks) {
					if (entry && entry->perk && entry->currentRank > 0 &&
						a_player->HasPerk(const_cast<RE::BGSPerk*>(entry->perk)) && a_predicate(entry->perk)) {
						active.insert(entry->perk);
					}
				}
				for (const auto* perk : runtimeData.perks) {
					if (perk && a_player->HasPerk(const_cast<RE::BGSPerk*>(perk)) && a_predicate(perk)) {
						active.insert(perk);
					}
				}
				// Papyrus-added Ordinator choice perks are not always present in the
				// player's runtime perk arrays. Inspect loaded perk records as a fallback.
				if (auto* dataHandler = RE::TESDataHandler::GetSingleton()) {
					for (const auto* perk : dataHandler->GetFormArray<RE::BGSPerk>()) {
						if (perk && a_player->HasPerk(const_cast<RE::BGSPerk*>(perk)) && a_predicate(perk)) {
							active.insert(perk);
						}
					}
				}
				return static_cast<int>(active.size());
			} catch (...) {
				return 0;
			}
		}

		float ReadAdvancedLabType() noexcept
		{
			if (!plugin_utils::FindLoadedPlugin(kPluginName)) {
				return -1.0f;
			}
			try {
				auto* dataHandler = RE::TESDataHandler::GetSingleton();
				if (!dataHandler) {
					return -1.0f;
				}
				for (const auto* global : dataHandler->GetFormArray<RE::TESGlobal>()) {
					const auto* editorID = global ? global->GetFormEditorID() : nullptr;
					if (editorID && plugin_utils::EqualsIgnoreCase(editorID, kAdvancedLabGlobal)) {
						return global->value;
					}
				}
			} catch (...) {
			}
			return -1.0f;
		}
	}

	bool Adapter::IsActive() noexcept
	{
		return plugin_utils::FindLoadedPlugin(kPluginName) != nullptr;
	}

	int Adapter::GetAdvancedLabType() noexcept
	{
		const float value = ReadAdvancedLabType();
		return std::isfinite(value) && value > 0.0f ? static_cast<int>(value) : 0;
	}

	bool Adapter::IsAdvancedLabActive(RE::PlayerCharacter* a_player) noexcept
	{
		if (!IsActive() || !a_player) {
			return false;
		}
		try {
			// This local form ID is verified against Ordinator's installed plugin and
			// is also used by ProsperousAlchemistTests.psc to apply the proc spell.
			auto* advancedLabProc = plugin_utils::LookupFormFlexible<RE::SpellItem>(0x0003D68C, kPluginName);
			if (!advancedLabProc) {
				return false;
			}
			auto* magicTarget = a_player->GetMagicTarget();
			auto* activeEffects = magicTarget ? magicTarget->GetActiveEffectList() : nullptr;
			if (!activeEffects) {
				return false;
			}
			return std::any_of(activeEffects->begin(), activeEffects->end(), [advancedLabProc](const auto* effect) {
				if (!effect || effect->flags.any(RE::ActiveEffect::Flag::kInactive, RE::ActiveEffect::Flag::kDispelled) || !effect->spell) {
					return false;
				}
				return effect->spell == advancedLabProc;
			});
		} catch (...) {
			return false;
		}
	}

	std::string Adapter::GetPhysicianAttribute(const RE::PlayerCharacter* a_player) noexcept
	{
		const auto attributes = GetPhysicianAttributes(a_player);
		const int count = static_cast<int>(attributes[0]) + static_cast<int>(attributes[1]) + static_cast<int>(attributes[2]);
		if (count != 1) return {};
		return attributes[0] ? "Health" : attributes[1] ? "Magicka" : "Stamina";
	}

	std::array<bool, 3> Adapter::GetPhysicianAttributes(const RE::PlayerCharacter* a_player) noexcept
	{
		std::array<bool, 3> attributes{};
		if (!IsActive() || !a_player) return attributes;
		// These selected-attribute perk IDs are verified against the installed
		// Ordinator ESP. Papyrus adds these exact records; resolve them directly
		// because choice perks can be absent from the player's runtime perk arrays.
		attributes[0] = HasPerkByLocalFormID(a_player, kPhysicianChoiceFormIDs[0]) ||
			GetActivePerkCount(a_player, [](const RE::BGSPerk* a_perk) { return HasIdentity(a_perk, "Physician_Perk_20_Proc_Health"); }) > 0;
		attributes[1] = HasPerkByLocalFormID(a_player, kPhysicianChoiceFormIDs[1]) ||
			GetActivePerkCount(a_player, [](const RE::BGSPerk* a_perk) { return HasIdentity(a_perk, "Physician_Perk_20_Proc_Magicka"); }) > 0;
		attributes[2] = HasPerkByLocalFormID(a_player, kPhysicianChoiceFormIDs[2]) ||
			GetActivePerkCount(a_player, [](const RE::BGSPerk* a_perk) { return HasIdentity(a_perk, "Physician_Perk_20_Proc_Stamina"); }) > 0;
		return attributes;
	}

	bool Adapter::IsPhysicianEffect(const RE::EffectSetting* a_effect, const std::array<bool, 3>& a_attributes) noexcept
	{
		if (!a_effect) {
			return false;
		}
		return (a_attributes[0] && (a_effect->HasKeywordString("MagicAlchRestoreHealth") || a_effect->HasKeywordString("MagicAlchFortifyHealth") || a_effect->HasKeywordString("MagicAlchFortifyHealRate"))) ||
			(a_attributes[1] && (a_effect->HasKeywordString("MagicAlchRestoreMagicka") || a_effect->HasKeywordString("MagicAlchFortifyMagicka") || a_effect->HasKeywordString("MagicAlchFortifyMagickaRate"))) ||
			(a_attributes[2] && (a_effect->HasKeywordString("MagicAlchRestoreStamina") || a_effect->HasKeywordString("MagicAlchFortifyStamina") || a_effect->HasKeywordString("MagicAlchFortifyStaminaRate")));
	}

	int Adapter::GetAlchemyMasteryRank(const RE::PlayerCharacter* a_player) noexcept
	{
		if (!IsActive()) {
			return 0;
		}
		// These two Skyrim-owned records are Ordinator's Mastery ranks; the IDs
		// are required because their overridden records keep Skyrim's identities.
		return (std::min)(2, GetActivePerkCount(a_player, [](const RE::BGSPerk* a_perk) {
			return a_perk && (std::find(kOverriddenAlchemyMasteryFormIDs.begin(),
				kOverriddenAlchemyMasteryFormIDs.end(), a_perk->GetFormID()) != kOverriddenAlchemyMasteryFormIDs.end() ||
				HasIdentity(a_perk, "AlchemyMastery"));
		}));
	}

	bool Adapter::HasPhysician(const RE::PlayerCharacter* a_player) noexcept
	{
		if (!IsActive() || !a_player) return false;
		// Resolve the actual choice perks before querying the parent: a choice
		// can be granted directly, and editor-ID scans cannot find native PERKs.
		const auto attributes = GetPhysicianAttributes(a_player);
		return std::any_of(attributes.begin(), attributes.end(), [](bool a_active) { return a_active; }) ||
			GetActivePerkCount(a_player, [](const RE::BGSPerk* a_perk) {
				return a_perk && (a_perk->GetFormID() == kOverriddenPhysicianFormID || HasIdentity(a_perk, "Physician"));
			}) > 0;
	}

	bool Adapter::HasPoisoner(const RE::PlayerCharacter* a_player) noexcept
	{
		return IsActive() && GetActivePerkRank(a_player, [](const RE::BGSPerk* a_perk) {
			return a_perk && (a_perk->GetFormID() == kOverriddenPoisonerFormID || HasIdentity(a_perk, "Poisoner"));
		}) > 0;
	}

	bool Adapter::HasPureMixture(const RE::PlayerCharacter* a_player) noexcept
	{
		return IsActive() && GetActivePerkRank(a_player, [](const RE::BGSPerk* a_perk) {
			return a_perk && (a_perk->GetFormID() == kOverriddenPureMixtureFormID || HasIdentity(a_perk, "PureMixture"));
		}) > 0;
	}

	bool Adapter::HasMagnumOpus(const RE::PlayerCharacter* a_player) noexcept
	{
		return IsActive() && GetActivePerkRank(a_player, [](const RE::BGSPerk* a_perk) {
			return HasIdentity(a_perk, "ThatWhichDoesNotKillYou");
		}) > 0;
	}

	float Adapter::GetMagnumOpusMultiplier(const RE::PlayerCharacter* a_player) noexcept
	{
		// The capstone perk grants an ability, not an effectiveness entry point.
		// ORD_PurifyTheFlesh_Script awards AlchemyPowerMod after survival; the
		// actor value is captured separately, including bonuses without this perk.
		(void)a_player;
		return 1.0f;
	}

	bool Adapter::IsPoisonerPerk(const RE::BGSPerk* a_perk) noexcept
	{
		return IsActive() && a_perk &&
			(a_perk->GetFormID() == kOverriddenPoisonerFormID || HasIdentity(a_perk, "Poisoner"));
	}

	bool Adapter::IsHandledEffectivenessPerk(const RE::BGSPerk* a_perk) noexcept
	{
		if (!IsActive() || !a_perk) return false;
		// The analytic Ordinator path applies these bonuses from captured state.
		// Replaying their native entry points as well would multiply them twice.
		const bool physicianChoice = std::any_of(kPhysicianChoiceFormIDs.begin(), kPhysicianChoiceFormIDs.end(),
			[a_perk](RE::FormID a_localFormID) {
				return a_perk == plugin_utils::LookupFormFlexible<RE::BGSPerk>(a_localFormID, kPluginName);
			});
		return physicianChoice || a_perk->GetFormID() == kOverriddenPhysicianFormID ||
			IsPoisonerPerk(a_perk) ||
			HasIdentity(a_perk, "Physician") ||
			HasIdentity(a_perk, "AdvancedLab") ||
			HasIdentity(a_perk, "ThatWhichDoesNotKillYou");
	}

	float Adapter::GetPoisonerMultiplier(const RE::PlayerCharacter* a_player, float a_alchemyLevel) noexcept
	{
		if (!HasPoisoner(a_player) || !std::isfinite(a_alchemyLevel)) {
			return 1.0f;
		}
		// Ordinator's documented Poisoner bonus is one percent per Alchemy level.
		return (std::max)(1.0f, 1.0f + a_alchemyLevel * 0.01f);
	}

	float Adapter::GetAdvancedLabPotionMultiplier(RE::PlayerCharacter* a_player) noexcept
	{
		// The upgrade global identifies the chosen station; Ordinator grants its 25%
		// bonus only while the Advanced Lab proc spell is active at that station.
		return IsAdvancedLabActive(a_player) ? 1.25f : 1.0f;
	}
}
