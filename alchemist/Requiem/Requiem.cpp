#include "Requiem.h"

#include "PluginUtils.h"

#include <RE/A/Actor.h>
#include <RE/B/BGSKeyword.h>
#include <RE/B/BGSPerk.h>
#include <RE/E/EffectSetting.h>
#include <RE/G/GameSettingCollection.h>
#include <RE/P/PlayerCharacter.h>
#include <RE/T/TESDataHandler.h>
#include <RE/T/TESFile.h>
#include <RE/T/TESNPC.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <string_view>

namespace alchemist::requiem
{
	namespace
	{
		constexpr std::string_view kRequiemPlugin = "Requiem.esp";
		constexpr std::string_view kRequiemPluginEsm = "Requiem.esm";
		constexpr std::string_view kRequiemPluginEsl = "Requiem.esl";
		constexpr std::array<std::string_view, 3> kRequiemPlugins{ kRequiemPlugin, kRequiemPluginEsm, kRequiemPluginEsl };

		constexpr RE::FormID kBeneficialKeywordFormID = 0x000F8A4E;
		constexpr RE::FormID kHarmfulKeywordFormID = 0x00042509;
		constexpr RE::FormID kRestoreHealthKeywordFormID = 0x00042503;
		constexpr RE::FormID kRestoreMagickaKeywordFormID = 0x00042508;
		constexpr RE::FormID kRestoreStaminaKeywordFormID = 0x00042504;

		constexpr std::array<RE::FormID, 12> kFortifySkillKeywordFormIDs{
			0x00065A1D, // Alteration
			0x00065A1E, // Block
			0x00065A2A, // Conjuration
			0x00065A2B, // Destruction
			0x00065A2E, // Enchanting
			0x00065A21, // Marksman
			0x00065A2C, // Illusion
			0x00065A1F, // OneHanded
			0x00065A2D, // Restoration
			0x00065A27, // Sneak
			0x00065A29, // Barter
			0x00065A20  // TwoHanded
		};

		constexpr RE::FormID kUnperkedCraftingKeywordLocalID = 0x00AD3A3B;

		struct State
		{
			bool initialized = false;
			bool detected = false;
			bool active = false;
			std::string pluginName;
			float alchemyIngredientInitMultiplier = 4.0f;
			float alchemySkillFactor = 1.1f;

			RE::BGSKeyword* beneficialKeyword = nullptr;
			RE::BGSKeyword* harmfulKeyword = nullptr;
			RE::BGSKeyword* restoreHealthKeyword = nullptr;
			RE::BGSKeyword* restoreMagickaKeyword = nullptr;
			RE::BGSKeyword* restoreStaminaKeyword = nullptr;
			RE::BGSKeyword* unperkedCraftingKeyword = nullptr;
			std::array<RE::BGSKeyword*, 12> fortifySkillKeywords{};
		};

		State g_state;

		RE::BGSKeyword* ResolveKeyword(RE::FormID a_formID) noexcept
		{
			auto* form = RE::TESForm::LookupByID(a_formID);
			return form ? form->As<RE::BGSKeyword>() : nullptr;
		}

		RE::BGSKeyword* ResolvePluginKeyword(std::string_view a_plugin, RE::FormID a_localFormID) noexcept
		{
			return plugin_utils::LookupFormFlexible<RE::BGSKeyword>(a_localFormID, a_plugin);
		}

		template <typename T>
		T* ResolveEditorID(std::string_view a_editorID) noexcept
		{
			auto* form = RE::TESForm::LookupByEditorID(a_editorID);
			return form ? form->As<T>() : nullptr;
		}

		bool HasEffectKeyword(const RE::EffectSetting* a_effect, const RE::BGSKeyword* a_keyword, RE::FormID a_fallbackFormID) noexcept
		{
			if (!a_effect) {
				return false;
			}
			if (a_keyword && a_effect->HasKeyword(a_keyword)) {
				return true;
			}
			if (a_fallbackFormID != 0) {
				for (std::uint32_t i = 0; i < a_effect->numKeywords; ++i) {
					if (a_effect->keywords[i] && a_effect->keywords[i]->GetFormID() == a_fallbackFormID) {
						return true;
					}
				}
			}
			return false;
		}
	}

	void Adapter::Initialize() noexcept
	{
		g_state = State{};
		g_state.initialized = true;

		if (const auto* file = plugin_utils::FindLoadedPlugin("Requiem")) {
			const auto filename = file->GetFilename();
			g_state.pluginName.assign(filename.data(), filename.size());
			g_state.detected = true;
		}

		if (!g_state.detected) {
			return;
		}

		Refresh();
		g_state.active = true;
	}

	void Adapter::Refresh() noexcept
	{
		if (!g_state.detected) {
			return;
		}

		auto* gmstCollection = RE::GameSettingCollection::GetSingleton();
		if (gmstCollection) {
			auto* initSetting = gmstCollection->GetSetting("fAlchemyIngredientInitMult");
			if (initSetting && std::isfinite(initSetting->GetFloat()) && initSetting->GetFloat() > 0.0f) {
				g_state.alchemyIngredientInitMultiplier = initSetting->GetFloat();
			}
			auto* skillSetting = gmstCollection->GetSetting("fAlchemySkillFactor");
			if (skillSetting && std::isfinite(skillSetting->GetFloat()) && skillSetting->GetFloat() > 0.0f) {
				g_state.alchemySkillFactor = skillSetting->GetFloat();
			}
		}

		g_state.beneficialKeyword = ResolveKeyword(kBeneficialKeywordFormID);
		g_state.harmfulKeyword = ResolveKeyword(kHarmfulKeywordFormID);
		g_state.restoreHealthKeyword = ResolveKeyword(kRestoreHealthKeywordFormID);
		g_state.restoreMagickaKeyword = ResolveKeyword(kRestoreMagickaKeywordFormID);
		g_state.restoreStaminaKeyword = ResolveKeyword(kRestoreStaminaKeywordFormID);

		for (std::size_t i = 0; i < kFortifySkillKeywordFormIDs.size(); ++i) {
			g_state.fortifySkillKeywords[i] = ResolveKeyword(kFortifySkillKeywordFormIDs[i]);
		}

		g_state.unperkedCraftingKeyword = ResolvePluginKeyword(g_state.pluginName, kUnperkedCraftingKeywordLocalID);
		if (!g_state.unperkedCraftingKeyword) {
			for (const auto plugin : kRequiemPlugins) {
				if (auto* kw = ResolvePluginKeyword(plugin, kUnperkedCraftingKeywordLocalID)) {
					g_state.unperkedCraftingKeyword = kw;
					break;
				}
			}
		}
		// EditorID fallback: handles Requiem versions where the FormID has shifted.
		if (!g_state.unperkedCraftingKeyword) {
			g_state.unperkedCraftingKeyword = ResolveEditorID<RE::BGSKeyword>("REQ_RacialSkills_CreatePotionsUnperked");
		}
		if (!g_state.unperkedCraftingKeyword) {
			g_state.unperkedCraftingKeyword = ResolveEditorID<RE::BGSKeyword>("REQ_Keyword_Crafting_Unperked");
		}
		if (!g_state.unperkedCraftingKeyword) {
			g_state.unperkedCraftingKeyword = ResolveEditorID<RE::BGSKeyword>("REQ_Crafting_Unperked");
		}
	}

	bool Adapter::IsDetected() noexcept
	{
		return g_state.detected;
	}

	bool Adapter::IsActive() noexcept
	{
		return g_state.detected && g_state.active;
	}

	float Adapter::GetAlchemySkillFactor() noexcept
	{
		return g_state.alchemySkillFactor;
	}

	float Adapter::GetAlchemyIngredientInitMultiplier() noexcept
	{
		return g_state.alchemyIngredientInitMultiplier;
	}

	void Adapter::SetGameSettings(float a_initMult, float a_skillFactor) noexcept
	{
		if (std::isfinite(a_initMult) && a_initMult > 0.0f) {
			g_state.alchemyIngredientInitMultiplier = a_initMult;
		}
		if (std::isfinite(a_skillFactor) && a_skillFactor > 0.0f) {
			g_state.alchemySkillFactor = a_skillFactor;
		}
	}

	bool Adapter::TryGetSettings(Settings& a_settings) noexcept
	{
		if (!IsActive()) {
			return false;
		}
		a_settings.alchemyIngredientInitMultiplier = g_state.alchemyIngredientInitMultiplier;
		a_settings.alchemySkillFactor = g_state.alchemySkillFactor;
		return true;
	}

	bool Adapter::HasBeneficialKeyword(const RE::EffectSetting* a_effect) noexcept
	{
		if (!a_effect) {
			return false;
		}
		if (HasEffectKeyword(a_effect, g_state.beneficialKeyword, kBeneficialKeywordFormID)) {
			return true;
		}
		return !HasHarmfulKeyword(a_effect) && !a_effect->IsHostile();
	}

	bool Adapter::HasHarmfulKeyword(const RE::EffectSetting* a_effect) noexcept
	{
		if (!a_effect) {
			return false;
		}
		if (HasEffectKeyword(a_effect, g_state.harmfulKeyword, kHarmfulKeywordFormID)) {
			return true;
		}
		return a_effect->IsHostile() || a_effect->data.flags.all(RE::EffectSetting::EffectSettingData::Flag::kDetrimental);
	}

	bool Adapter::HasRestoreAttributeKeyword(const RE::EffectSetting* a_effect) noexcept
	{
		if (!a_effect) {
			return false;
		}
		return HasEffectKeyword(a_effect, g_state.restoreHealthKeyword, kRestoreHealthKeywordFormID) ||
			HasEffectKeyword(a_effect, g_state.restoreMagickaKeyword, kRestoreMagickaKeywordFormID) ||
			HasEffectKeyword(a_effect, g_state.restoreStaminaKeyword, kRestoreStaminaKeywordFormID) ||
			(a_effect->HasKeywordString("MagicAlchRestoreHealth") ||
			 a_effect->HasKeywordString("MagicAlchRestoreMagicka") ||
			 a_effect->HasKeywordString("MagicAlchRestoreStamina"));
	}

	bool Adapter::HasFortifySkillPenaltyKeyword(const RE::EffectSetting* a_effect) noexcept
	{
		if (!a_effect) {
			return false;
		}
		for (std::size_t i = 0; i < kFortifySkillKeywordFormIDs.size(); ++i) {
			if (HasEffectKeyword(a_effect, g_state.fortifySkillKeywords[i], kFortifySkillKeywordFormIDs[i])) {
				return true;
			}
		}
		return false;
	}

	bool Adapter::HasUnperkedCraftingKeyword(const RE::Actor* a_actor) noexcept
	{
		if (!a_actor) {
			return false;
		}
		if (g_state.unperkedCraftingKeyword && a_actor->HasKeyword(g_state.unperkedCraftingKeyword)) {
			return true;
		}
		const auto* race = a_actor->GetRace();
		if (race) {
			if (g_state.unperkedCraftingKeyword && race->HasKeyword(g_state.unperkedCraftingKeyword)) {
				return true;
			}
			const auto fid = race->GetFormID();
			if (fid == 0x00013740 || fid == 0x00013741 || fid == 0x00013742 ||
				fid == 0x00013743 || fid == 0x00013749 ||
				fid == 0x0008883A || fid == 0x0008883C || fid == 0x0008883D ||
				fid == 0x00088840 || fid == 0x00088884) {
				return true;
			}
		}
		return false;
	}

	bool Adapter::TryGetAlchemyEffectivenessMultipliers(
		const RE::EffectSetting* a_effect,
		float a_alchemyLevel,
		float a_fallbackAlchemistMultiplier,
		bool a_potion,
		bool a_includeTypePerks,
		const EvaluationContext& a_context,
		float& a_magnitudeMultiplier,
		float& a_durationMultiplier) noexcept
	{
		if (!IsActive()) {
			return false;
		}
		if (!std::isfinite(a_alchemyLevel) || a_alchemyLevel < 0.0f) {
			return false;
		}

		const float baseEffectiveness = algorithm::CalculateRequiemEffectiveness(
			a_alchemyLevel, 1.0f, g_state.alchemyIngredientInitMultiplier, g_state.alchemySkillFactor);
		if (!std::isfinite(baseEffectiveness) || baseEffectiveness < 0.0f) {
			return false;
		}

		float perkMultiplier = 1.0f;
		if (a_context.captured) {
			if (a_context.hasAlchemicalLore2 || a_context.alchemicalLoreRank >= 2) {
				perkMultiplier = 1.50f;
			} else if (a_context.hasAlchemicalLore1 || a_context.alchemicalLoreRank == 1) {
				perkMultiplier = 1.25f;
			} else if (a_context.hasUnperkedKeyword) {
				perkMultiplier = 1.0f;
			} else {
				perkMultiplier = 0.0f;
			}
		} else {
			perkMultiplier = (std::isfinite(a_fallbackAlchemistMultiplier) && a_fallbackAlchemistMultiplier >= 0.0f) ?
				a_fallbackAlchemistMultiplier : 1.0f;
		}

		float effectMultiplier = 1.0f;
		if (HasFortifySkillPenaltyKeyword(a_effect)) {
			effectMultiplier *= 0.5f;
		}

		if (a_includeTypePerks && a_context.captured) {
			const bool isBeneficial = HasBeneficialKeyword(a_effect);
			const bool isHarmful = HasHarmfulKeyword(a_effect);
			const bool isRestore = HasRestoreAttributeKeyword(a_effect);

			if (a_context.hasImprovedElixirs && a_potion && isBeneficial) {
				effectMultiplier *= 1.25f;
				if (isRestore) {
					effectMultiplier *= 1.25f;
				}
			}
			if (a_context.hasImprovedPoisons && !a_potion && isHarmful) {
				effectMultiplier *= 1.25f;
			}
			if (a_context.hasPurificationProcess) {
				effectMultiplier *= 1.20f;
				if (a_potion && isBeneficial) {
					effectMultiplier *= 1.50f;
				} else if (!a_potion && isHarmful) {
					effectMultiplier *= 1.50f;
				}
				if (isRestore) {
					effectMultiplier *= 1.50f;
				}
			}
		}

		const float finalMultiplier = baseEffectiveness * perkMultiplier * effectMultiplier;
		a_magnitudeMultiplier = finalMultiplier;
		a_durationMultiplier = finalMultiplier;
		return true;
	}
}
