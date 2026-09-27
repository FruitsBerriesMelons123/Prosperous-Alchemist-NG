#include "CACO.h"

#include "AlchemyMath.h"
#include "Localization.h"
#include "PluginUtils.h"

#include <RE/A/AlchemyItem.h>
#include <RE/B/BGSKeyword.h>
#include <RE/B/BGSListForm.h>
#include <RE/B/BGSPerk.h>
#include <RE/B/BGSEntryPointFunctionDataOneValue.h>
#include <RE/B/BGSEntryPointPerkEntry.h>
#include <RE/E/Effect.h>
#include <RE/E/EffectSetting.h>
#include <RE/G/GameSettingCollection.h>
#include <RE/I/IngredientItem.h>
#include <RE/P/PlayerCharacter.h>
#include <RE/T/TESDataHandler.h>
#include <RE/T/TESFile.h>
#include <RE/T/TESGlobal.h>
#include <RE/T/TESCondition.h>

#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <exception>
#include <limits>
#include <set>
#include <string>
#include <string_view>

namespace alchemist::caco
{
	namespace
	{
		constexpr std::string_view kCacoPlugin = "Complete Alchemy & Cooking Overhaul.esp";
		constexpr std::string_view kCacoPluginEsm = "Complete Alchemy & Cooking Overhaul.esm";
		constexpr std::string_view kCacoPluginEsl = "Complete Alchemy & Cooking Overhaul.esl";
		constexpr std::string_view kCacoShortPlugin = "CACO.esp";
		constexpr std::string_view kCacoShortPluginEsm = "CACO.esm";
		constexpr std::string_view kCacoShortPluginEsl = "CACO.esl";
		constexpr std::string_view kLegacyPlugin = "Update.esm";
		constexpr std::array<std::string_view, 6> kCacoPlugins{
			kCacoPlugin, kCacoPluginEsm, kCacoPluginEsl,
			kCacoShortPlugin, kCacoShortPluginEsm, kCacoShortPluginEsl
		};
		constexpr RE::FormID kAlchemyEffectsListFormID = 0x0022DD8F;
		constexpr RE::FormID kAlchemyAllPotionListFormID = 0x0022DD90;
		constexpr RE::FormID kDisablePotionHandlingFormID = 0x00AAB031;
		constexpr RE::FormID kImpurePotionsFormID = 0x00AAB030;
		constexpr RE::FormID kReweightPotionsFormID = 0x00AAB02F;
		constexpr RE::FormID kRenamePotionsFormID = 0x0039A855;
		constexpr std::string_view kDurationModifierPerk = "CACO_AlchDurationModifier";
		constexpr std::string_view kCureDiseaseKeyword = "MagicAlchCureDisease_CACO";
		constexpr std::string_view kCurePoisonKeyword = "MagicAlchCurePoison_CACO";
		constexpr std::string_view kBloodKeyword = "MagicAlchBloodEffect_CACO";

		struct FamilyDefinition
		{
			std::string_view keyword;
			std::string_view editorPrefix;
			std::string_view alternateEditorPrefix;
			std::string_view durationGlobal;
			RE::FormID durationGlobalFormID;
			std::array<std::string_view, 4> ingredientLists;
			std::array<RE::FormID, 4> ingredientListFormIDs;
			std::array<std::string_view, 3> durationEffects;
			std::array<RE::FormID, 3> durationEffectFormIDs;
			std::array<std::string_view, 3> alternateDurationEffects;
			std::array<RE::FormID, 3> alternateDurationEffectFormIDs;
		};

		constexpr std::array<FamilyDefinition, 6> kFamilies{
			{
				{
					"MagicAlchRestoreHealth",
					"AlchRestoreHealth",
					"AlchRestoreHealthBlood",
					"CACO_RestoreHealthDuration",
					0x00CCA010,
					{ "CACO_RestoreIngH1st", "CACO_RestoreIngH2nd", "CACO_RestoreIngH3rd", "CACO_RestoreIngH4th" },
					{ 0x000D03ED, 0x000D03EE, 0x000D03EF, 0x000D03F0 },
					{ "AlchRestoreHealth_1sec", "AlchRestoreHealth_5sec", "AlchRestoreHealth_10sec" },
					{ 0x001AA0B6, 0x001AA0B7, 0x001AA0B8 },
					{ "AlchRestoreHealthBlood_1sec", "AlchRestoreHealthBlood_5sec", "AlchRestoreHealthBlood_10sec" },
					{ 0x005BDD37, 0x005BDD39, 0x005BDD3A }
				},
				{
					"MagicAlchRestoreMagicka",
					"AlchRestoreMagicka",
					"",
					"CACO_RestoreMagickaDuration",
					0x00CCA011,
					{ "CACO_RestoreIngM1st", "CACO_RestoreIngM2nd", "CACO_RestoreIngM3rd", "CACO_RestoreIngM4th" },
					{ 0x000D03F1, 0x000D03F2, 0x000D03F3, 0x000D03F4 },
					{ "AlchRestoreMagicka_1sec", "AlchRestoreMagicka_5sec", "AlchRestoreMagicka_10sec" },
					{ 0x001B42BE, 0x001B42BF, 0x001B42C0 },
					{ "", "", "" },
					{ 0, 0, 0 }
				},
				{
					"MagicAlchRestoreStamina",
					"AlchRestoreStamina",
					"",
					"CACO_RestoreStaminaDuration",
					0x00CCA012,
					{ "CACO_RestoreIngS1st", "CACO_RestoreIngS2nd", "CACO_RestoreIngS3rd", "CACO_RestoreIngS4th" },
					{ 0x000D03F5, 0x000D03F6, 0x000D03F7, 0x000D03F8 },
					{ "AlchRestoreStamina_1sec", "AlchRestoreStamina_5sec", "AlchRestoreStamina_10sec" },
					{ 0x001B42BB, 0x001B42BC, 0x001B42BD },
					{ "", "", "" },
					{ 0, 0, 0 }
				},
				{
					"MagicAlchDamageHealth",
					"AlchDamageHealth",
					"AlchDamageUndeadHealth",
					"CACO_DamageHealthDuration",
					0x00CCA013,
					{ "CACO_DamageIngH1st", "CACO_DamageIngH2nd", "CACO_DamageIngH3rd", "CACO_DamageIngH4th" },
					{ 0x001B93CB, 0x001B93CC, 0x001B93CD, 0x001B93CE },
					{ "AlchDamageHealth_1sec", "AlchDamageHealth_5sec", "AlchDamageHealth_10sec" },
					{ 0x001B93C8, 0x001B93C9, 0x001B93CA },
					{ "AlchDamageUndead_1sec", "AlchDamageUndead_5sec", "AlchDamageUndead_10sec" },
					{ 0x00316D85, 0x00316D86, 0x00316D7F }
				},
				{
					"MagicAlchDamageMagicka",
					"AlchDamageMagicka",
					"",
					"CACO_DamageMagickaDuration",
					0x00CCA014,
					{ "CACO_DamageIngM1st", "CACO_DamageIngM2nd", "CACO_DamageIngM3rd", "CACO_DamageIngM4th" },
					{ 0x001B93CF, 0x001B93D0, 0x001B93D1, 0x001B93D2 },
					{ "AlchDamageMagicka_1sec", "AlchDamageMagicka_5sec", "AlchDamageMagicka_10sec" },
					{ 0x001B93C5, 0x001B93C6, 0x001B93C7 },
					{ "", "", "" },
					{ 0, 0, 0 }
				},
				{
					"MagicAlchDamageStamina",
					"AlchDamageStamina",
					"",
					"CACO_DamageStaminaDuration",
					0x00CCA015,
					{ "CACO_DamageIngS1st", "CACO_DamageIngS2nd", "CACO_DamageIngS3rd", "CACO_DamageIngS4th" },
					{ 0x001B93D3, 0x001B93D4, 0x001B93D5, 0x001B93D6 },
					{ "AlchDamageStamina_1sec", "AlchDamageStamina_5sec", "AlchDamageStamina_10sec" },
					{ 0x001B93C2, 0x001B93C3, 0x001B93C4 },
					{ "", "", "" },
					{ 0, 0, 0 }
				}
			}
		};

		struct FamilyState
		{
			RE::TESGlobal* durationGlobal = nullptr;
			std::array<RE::BGSListForm*, 4> ingredientLists{};
			std::array<RE::EffectSetting*, 3> durationEffects{};
			std::array<RE::EffectSetting*, 3> alternateDurationEffects{};
			std::array<RE::EffectSetting*, 3> legacyEffects{};
		};

		struct State
		{
			bool initialized = false;
			bool detected = false;
			bool active = false;
			bool potionHandlingEnabled = false;
			bool impureProcessingEnabled = false;
			bool reweightingEnabled = false;
			bool renamingEnabled = false;
			RE::TESGlobal* alchemyXPMultiplier = nullptr;
			std::string pluginName;
			std::array<FamilyState, kFamilies.size()> families{};
			std::array<int, kFamilies.size()> durationIndices{};
			bool hasOverrides = false;
			std::array<int, 6> durationOverrideIndices{};
			std::uint64_t calculationRevision = 0;
			std::uint64_t seenGameSettingsRevision = 0;
			RE::TESGlobal* disablePotionHandling = nullptr;
			RE::TESGlobal* impurePotions = nullptr;
			RE::TESGlobal* reweightPotions = nullptr;
			RE::TESGlobal* renamePotions = nullptr;
			RE::BGSListForm* alchemyEffectsList = nullptr;
			RE::BGSListForm* allPotionList = nullptr;
			RE::AlchemyItem* cureDisease = nullptr;
			RE::AlchemyItem* curePoison = nullptr;
			RE::BGSPerk* durationModifierPerk = nullptr;
		};

		State g_state;

		struct PluginMatch
		{
			const RE::TESFile* file = nullptr;
			std::string name;
		};

		bool EqualsIgnoreCase(std::string_view a_left, std::string_view a_right) noexcept
		{
			if (a_left.size() != a_right.size()) {
				return false;
			}
			for (std::size_t i = 0; i < a_left.size(); ++i) {
				const auto left = a_left[i] >= 'A' && a_left[i] <= 'Z' ?
					static_cast<char>(a_left[i] + ('a' - 'A')) : a_left[i];
				const auto right = a_right[i] >= 'A' && a_right[i] <= 'Z' ?
					static_cast<char>(a_right[i] + ('a' - 'A')) : a_right[i];
				if (left != right) {
					return false;
				}
			}
			return true;
		}

		bool MatchesEditorPrefix(std::string_view a_editorID, std::string_view a_prefix) noexcept
		{
			if (a_editorID.empty() || a_prefix.empty() || a_editorID.size() < a_prefix.size()) {
				return false;
			}
			if (!EqualsIgnoreCase(a_editorID.substr(0, a_prefix.size()), a_prefix)) {
				return false;
			}
			return a_editorID.size() == a_prefix.size() || a_editorID[a_prefix.size()] == '_';
		}

		bool ContainsIgnoreCase(std::string_view a_value, std::string_view a_fragment) noexcept
		{
			if (a_fragment.empty()) {
				return true;
			}
			if (a_fragment.size() > a_value.size()) {
				return false;
			}
			for (std::size_t offset = 0; offset <= a_value.size() - a_fragment.size(); ++offset) {
				if (EqualsIgnoreCase(a_value.substr(offset, a_fragment.size()), a_fragment)) {
					return true;
				}
			}
			return false;
		}

		PluginMatch MakePluginMatch(const RE::TESFile* a_file, std::string_view a_candidate)
		{
			PluginMatch result;
			result.file = a_file;
			if (a_file) {
				const auto filename = a_file->GetFilename();
				result.name.assign(filename.data(), filename.size());
			}
			if (result.name.empty()) {
				result.name.assign(a_candidate.data(), a_candidate.size());
			}
			return result;
		}

		PluginMatch FindCacoPlugin()
		{
			PluginMatch result;
			try {
				if (const auto* file = plugin_utils::FindLoadedPlugin("Complete Alchemy & Cooking Overhaul")) {
					return MakePluginMatch(file, file->GetFilename());
				}
			} catch (...) {}
			return result;
		}

		template <class T>
		T* ResolveEditorID(std::string_view a_editorID) noexcept
		{
			if (a_editorID.empty()) {
				return nullptr;
			}
			try {
				if (auto* form = RE::TESForm::LookupByEditorID<T>(a_editorID)) {
					return form;
				}
			} catch (...) {
			}

			try {
				auto* dataHandler = RE::TESDataHandler::GetSingleton();
				if (!dataHandler) {
					return nullptr;
				}
				for (auto* form : dataHandler->GetFormArray<T>()) {
					if (!form) {
						continue;
					}
					const auto* editorID = form->GetFormEditorID();
					if (editorID && EqualsIgnoreCase(editorID, a_editorID)) {
						return form;
					}
				}
			} catch (...) {
			}
			return nullptr;
		}

		template <class T>
		T* ResolveRecord(std::string_view a_editorID, RE::FormID a_localFormID) noexcept
		{
			if (auto* form = ResolveEditorID<T>(a_editorID)) {
				return form;
			}
			if (a_localFormID == 0) {
				return nullptr;
			}

			try {
				if (!g_state.pluginName.empty()) {
					if (auto* form = plugin_utils::LookupFormFlexible<T>(a_localFormID, g_state.pluginName)) {
						return form;
					}
				}
				for (const auto plugin : kCacoPlugins) {
					if (auto* form = plugin_utils::LookupFormFlexible<T>(a_localFormID, plugin)) {
						return form;
					}
				}
				if (auto* form = plugin_utils::LookupFormFlexible<T>(a_localFormID, kLegacyPlugin)) {
					return form;
				}
				static constexpr std::array<std::string_view, 11> kFallbackPlugins{
					"ccbgssse037-curios.esl",
					"ccbgssse025-advdsgs.esm",
					"ccbgssse001-fish.esm",
					"ccbgssse067-daedinv.esm",
					"ccbgssse003-zombies.esl",
					"ccbgssse040-advobgg.esl",
					"ccasvsse001-almsivi.esm",
					"ccvsvsse004-beaskpeg.esl",
					"Dawnguard.esm",
					"Dragonborn.esm",
					"Skyrim.esm"
				};
				for (const auto plugin : kFallbackPlugins) {
					if (auto* form = plugin_utils::LookupFormFlexible<T>(a_localFormID, plugin)) {
						return form;
					}
				}
				return nullptr;
			} catch (...) {
				return nullptr;
			}
		}

		bool IsOne(RE::TESGlobal* a_global) noexcept
		{
			return a_global && std::isfinite(a_global->value) && a_global->value == 1.0f;
		}

		bool IsRestoreEffectsDoNotStack() noexcept
		{
			bool foundEffect = false;
			for (std::size_t familyIndex = 0; familyIndex < 3 && familyIndex < g_state.families.size(); ++familyIndex) {
				for (const auto* effect : g_state.families[familyIndex].durationEffects) {
					if (!effect) {
						continue;
					}
					foundEffect = true;
					if (!effect->HasArchetype(RE::EffectArchetypes::ArchetypeID::kPeakValueModifier)) {
						return false;
					}
				}
			}
			return foundEffect;
		}

		// CACO_AlchDurationModifier applies its 5-second (x0.2) and 10-second (x0.1)
		// magnitude entries only when GetGlobalValue(duration global) == 1 or == 2
		// exactly. Every other value (including out-of-range values such as 5 or 10)
		// matches neither entry and behaves like the 1-second option, so the index is
		// resolved by equality rather than by clamping.
		int NormalizeDurationIndex(float a_value) noexcept
		{
			if (a_value == 1.0f) {
				return 1;
			}
			if (a_value == 2.0f) {
				return 2;
			}
			return 0;
		}

		int GetDurationIndex(std::size_t a_familyIndex) noexcept
		{
			if (a_familyIndex >= g_state.families.size()) {
				return 0;
			}
			if (g_state.hasOverrides) {
				return NormalizeDurationIndex(static_cast<float>(g_state.durationOverrideIndices[a_familyIndex]));
			}
			const auto* global = g_state.families[a_familyIndex].durationGlobal;
			if (!global || !std::isfinite(global->value)) {
				return 0;
			}
			return NormalizeDurationIndex(global->value);
		}

		// Raw duration setting for confirmation telemetry: the live global value, so
		// an unexpected value (e.g. 10 instead of 2) is visible in the recorded row.
		float GetDurationSettingValue(std::size_t a_familyIndex) noexcept
		{
			if (a_familyIndex >= g_state.families.size()) {
				return 0.0f;
			}
			if (g_state.hasOverrides) {
				return static_cast<float>(g_state.durationOverrideIndices[a_familyIndex]);
			}
			const auto* global = g_state.families[a_familyIndex].durationGlobal;
			return global && std::isfinite(global->value) ? global->value : 0.0f;
		}

		void RefreshCalculationRevision() noexcept
		{
			std::array<int, kFamilies.size()> durationIndices{};
			for (std::size_t i = 0; i < durationIndices.size(); ++i) {
				durationIndices[i] = GetDurationIndex(i);
			}
			if (durationIndices != g_state.durationIndices) {
				g_state.durationIndices = durationIndices;
				if (g_state.calculationRevision < (std::numeric_limits<std::uint64_t>::max)()) {
					++g_state.calculationRevision;
				}
			}
		}

		int FindFamily(const RE::EffectSetting* a_effect) noexcept
		{
			if (!a_effect) {
				return -1;
			}

			for (std::size_t i = 0; i < kFamilies.size(); ++i) {
				const auto* editorID = a_effect->GetFormEditorID();
				if (a_effect->HasKeywordString(kFamilies[i].keyword) ||
					MatchesEditorPrefix(editorID ? std::string_view(editorID) : std::string_view{}, kFamilies[i].editorPrefix) ||
					MatchesEditorPrefix(editorID ? std::string_view(editorID) : std::string_view{}, kFamilies[i].alternateEditorPrefix)) {
					return static_cast<int>(i);
				}
			}
			return -1;
		}

		bool IsIngredientListedInFamily(
			const RE::IngredientItem* a_ingredient,
			const FamilyState& a_family) noexcept
		{
			if (!a_ingredient) {
				return false;
			}
			const bool hasLists = std::any_of(a_family.ingredientLists.begin(), a_family.ingredientLists.end(),
				[](const auto* list) { return list != nullptr; });
			if (!hasLists) {
				return true;
			}
			return std::any_of(a_family.ingredientLists.begin(), a_family.ingredientLists.end(),
				[a_ingredient](const auto* list) { return list && list->HasForm(a_ingredient); });
		}

		std::size_t GetComparisonPosition(const RE::EffectSetting* a_effect) noexcept
		{
			const int familyIndex = FindFamily(a_effect);
			return familyIndex >= 0 ? static_cast<std::size_t>(GetDurationIndex(static_cast<std::size_t>(familyIndex))) : 0;
		}

		bool IsSameFamily(const RE::EffectSetting* a_left, const RE::EffectSetting* a_right) noexcept
		{
			if (!a_left || !a_right) {
				return false;
			}
			if (a_left == a_right) {
				return true;
			}
			const int leftFamily = FindFamily(a_left);
			return leftFamily >= 0 && leftFamily == FindFamily(a_right);
		}

		RE::EffectSetting* ResolveDurationEffect(
			std::size_t a_familyIndex,
			const RE::EffectSetting* a_sourceEffect,
			std::size_t a_durationIndex) noexcept
		{
			if (a_familyIndex >= kFamilies.size()) {
				return nullptr;
			}

			const auto& family = g_state.families[a_familyIndex];
			if (a_durationIndex >= 3) {
				return nullptr;
			}

			const auto* sourceEditorID = a_sourceEffect ? a_sourceEffect->GetFormEditorID() : nullptr;
			const auto sourceFormID = a_sourceEffect ? a_sourceEffect->GetFormID() & 0x00FFFFFF : 0;
			const bool useAlternate = (sourceEditorID &&
				(ContainsIgnoreCase(sourceEditorID, "Blood") || ContainsIgnoreCase(sourceEditorID, "Undead"))) ||
				sourceFormID == 0x0010DE5F || sourceFormID == 0x00013812 || sourceFormID == 0x000E4857;

			if (useAlternate) {
				if (family.alternateDurationEffects[a_durationIndex]) {
					return family.alternateDurationEffects[a_durationIndex];
				}
				if (family.legacyEffects[a_durationIndex]) {
					return family.legacyEffects[a_durationIndex];
				}
				return nullptr;
			}

			return family.durationEffects[a_durationIndex];
		}

		RE::EffectSetting* ResolveDurationEffect(
			std::size_t a_familyIndex,
			const RE::EffectSetting* a_sourceEffect) noexcept
		{
			return ResolveDurationEffect(a_familyIndex, a_sourceEffect, static_cast<std::size_t>(GetDurationIndex(a_familyIndex)));
		}

		const RE::BGSListForm* FindPotionList(const RE::EffectSetting* a_primaryEffect) noexcept
		{
			if (!g_state.alchemyEffectsList || !g_state.allPotionList || !a_primaryEffect) {
				return nullptr;
			}

			std::size_t effectIndex = g_state.alchemyEffectsList->forms.size();
			for (std::size_t i = 0; i < g_state.alchemyEffectsList->forms.size(); ++i) {
				const auto* effect = g_state.alchemyEffectsList->forms[i] ?
					g_state.alchemyEffectsList->forms[i]->As<RE::EffectSetting>() : nullptr;
				if (effect == a_primaryEffect) {
					effectIndex = i;
					break;
				}
			}
			if (effectIndex == g_state.alchemyEffectsList->forms.size()) {
				for (std::size_t i = 0; i < g_state.alchemyEffectsList->forms.size(); ++i) {
					const auto* effect = g_state.alchemyEffectsList->forms[i] ?
						g_state.alchemyEffectsList->forms[i]->As<RE::EffectSetting>() : nullptr;
					if (IsSameFamily(effect, a_primaryEffect)) {
						effectIndex = i;
						break;
					}
				}
			}
			if (effectIndex >= g_state.allPotionList->forms.size()) {
				return nullptr;
			}
			return g_state.allPotionList->forms[effectIndex] ?
				g_state.allPotionList->forms[effectIndex]->As<RE::BGSListForm>() : nullptr;
		}

		const RE::AlchemyItem* GetPotionAt(const RE::BGSListForm* a_list, std::size_t a_index) noexcept
		{
			if (!a_list || a_index >= a_list->forms.size() || !a_list->forms[a_index]) {
				return nullptr;
			}
			return a_list->forms[a_index]->As<RE::AlchemyItem>();
		}

		bool GetExemplarValue(
			const RE::AlchemyItem* a_potion,
			std::size_t a_effectIndex,
			bool a_duration,
			float& a_value) noexcept
		{
			if (!a_potion || a_effectIndex >= a_potion->effects.size() || !a_potion->effects[a_effectIndex]) {
				return false;
			}
			const auto* effect = a_potion->effects[a_effectIndex];
			a_value = a_duration ? static_cast<float>(effect->GetDuration()) : effect->GetMagnitude();
			return std::isfinite(a_value);
		}

		bool SelectQuality(
			const RE::BGSListForm* a_compareList,
			float a_value,
			bool a_duration,
			std::size_t a_effectIndex,
			std::size_t& a_quality) noexcept
		{
			const auto* potion1 = GetPotionAt(a_compareList, 1);
			const auto* potion2 = GetPotionAt(a_compareList, 2);
			const auto* potion3 = GetPotionAt(a_compareList, 3);
			const auto* potion4 = GetPotionAt(a_compareList, 4);
			float threshold1 = 0.0f;
			float threshold2 = 0.0f;
			float threshold3 = 0.0f;
			float threshold4 = 0.0f;
			if (!potion1 || !potion2 || !potion3 ||
				!GetExemplarValue(potion1, a_effectIndex, a_duration, threshold1) ||
				!GetExemplarValue(potion2, a_effectIndex, a_duration, threshold2) ||
				!GetExemplarValue(potion3, a_effectIndex, a_duration, threshold3)) {
				return false;
			}

			if (a_value < threshold1) {
				a_quality = 0;
			} else if (a_value < threshold2) {
				a_quality = 1;
			} else if (a_value < threshold3) {
				a_quality = 2;
			} else if (!potion4) {
				a_quality = 3;
			} else {
				if (!GetExemplarValue(potion4, a_effectIndex, a_duration, threshold4)) {
					return false;
				}
				a_quality = a_value < threshold4 ? 3 : 4;
			}
			return true;
		}

		bool IsCureEffect(const RE::EffectSetting* a_effect) noexcept
		{
			return a_effect && (a_effect->HasKeywordString(kCureDiseaseKeyword) ||
				a_effect->HasKeywordString(kCurePoisonKeyword) ||
				a_effect->HasKeywordString(kBloodKeyword));
		}

		void AdoptPluginName(const RE::TESForm* a_form)
		{
			if (!g_state.pluginName.empty() || !a_form) {
				return;
			}
			try {
				const auto* file = a_form->GetFile();
				if (!file) {
					return;
				}
				const auto filename = file->GetFilename();
				if (filename.empty()) {
					return;
				}
				g_state.pluginName.assign(filename.data(), filename.size());
			} catch (...) {
			}
		}

		bool TryGetCureExemplar(const RE::EffectSetting* a_effect, ExemplarResult& a_result) noexcept
		{
			if (!a_effect) {
				return false;
			}
			if (a_effect->HasKeywordString(kCureDiseaseKeyword) && g_state.cureDisease) {
				a_result.potion = g_state.cureDisease;
				a_result.goldValue = g_state.cureDisease->GetGoldValue();
				return true;
			}
			if (a_effect->HasKeywordString(kCurePoisonKeyword) && g_state.curePoison) {
				a_result.potion = g_state.curePoison;
				a_result.goldValue = g_state.curePoison->GetGoldValue();
				return true;
			}
			return false;
		}

		void RefreshOptions() noexcept
		{
			const bool previousPotionHandling = g_state.potionHandlingEnabled;
			const bool previousImpureProcessing = g_state.impureProcessingEnabled;
			const bool previousReweighting = g_state.reweightingEnabled;
			const bool previousRenaming = g_state.renamingEnabled;
			if (!g_state.detected || !g_state.active) {
				g_state.potionHandlingEnabled = false;
				g_state.impureProcessingEnabled = false;
				g_state.reweightingEnabled = false;
				g_state.renamingEnabled = false;
			} else {
				g_state.potionHandlingEnabled = g_state.disablePotionHandling && !IsOne(g_state.disablePotionHandling);
				g_state.impureProcessingEnabled = g_state.potionHandlingEnabled && IsOne(g_state.impurePotions);
				g_state.reweightingEnabled = g_state.potionHandlingEnabled && IsOne(g_state.reweightPotions);
				g_state.renamingEnabled = g_state.potionHandlingEnabled && IsOne(g_state.renamePotions);
			}
			if (g_state.initialized && (previousPotionHandling != g_state.potionHandlingEnabled ||
				previousImpureProcessing != g_state.impureProcessingEnabled ||
				previousReweighting != g_state.reweightingEnabled ||
				previousRenaming != g_state.renamingEnabled) &&
				g_state.calculationRevision < (std::numeric_limits<std::uint64_t>::max)()) {
				++g_state.calculationRevision;
			}
		}
	}

	namespace
	{
		// How the shared vanilla perk evaluation should treat CACO's potion handling.
		vanilla::PerkPolicy MakePerkPolicy() noexcept
		{
			vanilla::PerkPolicy policy;
			policy.cacoActive = Adapter::IsActive();
			policy.potionHandlingEnabled = Adapter::IsPotionHandlingEnabled();
			policy.excludedPerk = g_state.durationModifierPerk;
			policy.excludedPerkName = kDurationModifierPerk;
			return policy;
		}
	}

	void Adapter::Initialize() noexcept
	{
		g_state = {};
		try {
			const auto plugin = FindCacoPlugin();
			if (plugin.file) {
				g_state.pluginName = plugin.name;
			}
			for (std::size_t i = 0; i < kFamilies.size(); ++i) {
				const auto& definition = kFamilies[i];
				auto& family = g_state.families[i];
				family.durationGlobal = ResolveRecord<RE::TESGlobal>(definition.durationGlobal, definition.durationGlobalFormID);
				for (std::size_t position = 0; position < definition.ingredientLists.size(); ++position) {
					family.ingredientLists[position] = ResolveRecord<RE::BGSListForm>(
						definition.ingredientLists[position], definition.ingredientListFormIDs[position]);
				}
				for (std::size_t d = 0; d < 3; ++d) {
					if (!definition.durationEffects[d].empty() || definition.durationEffectFormIDs[d] != 0) {
						family.durationEffects[d] = ResolveRecord<RE::EffectSetting>(
							definition.durationEffects[d], definition.durationEffectFormIDs[d]);
					}
					if (!definition.alternateDurationEffects[d].empty() || definition.alternateDurationEffectFormIDs[d] != 0) {
						family.alternateDurationEffects[d] = ResolveRecord<RE::EffectSetting>(
							definition.alternateDurationEffects[d], definition.alternateDurationEffectFormIDs[d]);
					}
				}
				if (i == 0) {
					static constexpr std::array<std::string_view, 3> legacyBloodEffects{
						"DLC1AlchRestoreHealthBlood_1sec",
						"DLC1AlchRestoreHealthBlood_5sec",
						"DLC1AlchRestoreHealthBlood_10sec"
					};
					static constexpr std::array<RE::FormID, 3> legacyBloodFormIDs{
						0x005BDD37, 0x005BDD39, 0x005BDD3A
					};
					for (std::size_t d = 0; d < 3; ++d) {
						family.legacyEffects[d] = ResolveRecord<RE::EffectSetting>(legacyBloodEffects[d], legacyBloodFormIDs[d]);
					}
				} else if (i == 3) {
					static constexpr std::array<std::string_view, 3> legacyUndeadEffects{
						"AlchDamageUndeadHealth_1sec",
						"AlchDamageUndeadHealth_5sec",
						"AlchDamageUndeadHealth_10sec"
					};
					static constexpr std::array<RE::FormID, 3> legacyUndeadFormIDs{
						0x00316D85, 0x00316D86, 0x00316D7F
					};
					for (std::size_t d = 0; d < 3; ++d) {
						family.legacyEffects[d] = ResolveRecord<RE::EffectSetting>(legacyUndeadEffects[d], legacyUndeadFormIDs[d]);
					}
				}
			}

			g_state.disablePotionHandling = ResolveRecord<RE::TESGlobal>(
				"CACO_OptionDisableAllPotionHandling", kDisablePotionHandlingFormID);
			if (!g_state.disablePotionHandling) {
				g_state.disablePotionHandling = ResolveEditorID<RE::TESGlobal>("CACO_OptionDisablePotionHandling");
			}
			g_state.impurePotions = ResolveRecord<RE::TESGlobal>("CACO_OptionImpurePotions", kImpurePotionsFormID);
			g_state.reweightPotions = ResolveRecord<RE::TESGlobal>("CACO_OptionReweightPotions", kReweightPotionsFormID);
			g_state.renamePotions = ResolveRecord<RE::TESGlobal>("CACO_OptionRenamePotions", kRenamePotionsFormID);
			if (!g_state.renamePotions) {
				g_state.renamePotions = ResolveEditorID<RE::TESGlobal>("CACORenamePotionOption_KRY");
			}
			g_state.alchemyXPMultiplier = ResolveEditorID<RE::TESGlobal>("CACO_OptionAlchXPRate");
			g_state.alchemyEffectsList = ResolveRecord<RE::BGSListForm>(
				"CACO_AlchemyEffectsList", kAlchemyEffectsListFormID);
			g_state.allPotionList = ResolveRecord<RE::BGSListForm>(
				"CACO_AlchemyAllPotionList", kAlchemyAllPotionListFormID);
			g_state.cureDisease = ResolveEditorID<RE::AlchemyItem>("CureDisease");
			g_state.curePoison = ResolveEditorID<RE::AlchemyItem>("CurePoison");
			g_state.durationModifierPerk = ResolveEditorID<RE::BGSPerk>(kDurationModifierPerk);
			if (g_state.pluginName.empty()) {
				AdoptPluginName(g_state.alchemyEffectsList);
				AdoptPluginName(g_state.allPotionList);
			}
			const bool alchemySettingsReady = vanilla::Adapter::Refresh();
			g_state.seenGameSettingsRevision = vanilla::Adapter::GetGameSettingsRevision();
			RefreshCalculationRevision();

			const bool coreListsFound = g_state.alchemyEffectsList && g_state.allPotionList;
			std::size_t ingredientListsFound = 0;
			std::size_t durationGlobalsFound = 0;
			for (const auto& family : g_state.families) {
				durationGlobalsFound += family.durationGlobal ? 1 : 0;
				ingredientListsFound += static_cast<std::size_t>(std::count_if(
					family.ingredientLists.begin(), family.ingredientLists.end(), [](const auto* list) { return list != nullptr; }));
			}
			const bool optionRecordsFound = g_state.disablePotionHandling || g_state.impurePotions ||
				g_state.reweightPotions || g_state.renamePotions;
			const bool cacoRecordsFound = coreListsFound || ingredientListsFound != 0 || durationGlobalsFound != 0;
			const bool pluginFound = plugin.file != nullptr;
			g_state.detected = pluginFound || cacoRecordsFound || optionRecordsFound || g_state.cureDisease || g_state.curePoison;
			const bool calculationRecordsFound = pluginFound || coreListsFound || ingredientListsFound != 0;
			g_state.active = calculationRecordsFound && alchemySettingsReady;
			g_state.initialized = true;
			RefreshOptions();

		} catch (const std::exception&) {
			g_state = {};
			g_state.initialized = true;
		} catch (...) {
			g_state = {};
			g_state.initialized = true;
		}
	}

	void Adapter::Refresh() noexcept
	{
		if (!g_state.initialized) {
			return;
		}
		try {
			vanilla::Adapter::Refresh();
			const auto gameSettingsRevision = vanilla::Adapter::GetGameSettingsRevision();
			if (gameSettingsRevision != g_state.seenGameSettingsRevision) {
				g_state.seenGameSettingsRevision = gameSettingsRevision;
				if (g_state.calculationRevision < (std::numeric_limits<std::uint64_t>::max)()) {
					++g_state.calculationRevision;
				}
			}
			RefreshOptions();
			RefreshCalculationRevision();
		} catch (const std::exception&) {
			g_state.potionHandlingEnabled = false;
			g_state.impureProcessingEnabled = false;
			g_state.reweightingEnabled = false;
			g_state.renamingEnabled = false;
		} catch (...) {
			g_state.potionHandlingEnabled = false;
			g_state.impureProcessingEnabled = false;
			g_state.reweightingEnabled = false;
			g_state.renamingEnabled = false;
		}
	}

	bool Adapter::IsDetected() noexcept
	{
		return g_state.initialized && g_state.detected;
	}

	bool Adapter::IsActive() noexcept
	{
		return g_state.initialized && g_state.active;
	}

	bool Adapter::TryGetSettings(Settings& a_settings) noexcept
	{
		if (!IsDetected()) {
			return false;
		}

		try {
			Refresh();
			Settings settings;
			settings.restoreHealthDuration = GetDurationSettingValue(0);
			settings.restoreMagickaDuration = GetDurationSettingValue(1);
			settings.restoreStaminaDuration = GetDurationSettingValue(2);
			settings.restoreEffectsDoNotStack = IsRestoreEffectsDoNotStack();
			settings.damageHealthDuration = GetDurationSettingValue(3);
			settings.damageMagickaDuration = GetDurationSettingValue(4);
			settings.damageStaminaDuration = GetDurationSettingValue(5);
			settings.disableAllPotionHandling = g_state.disablePotionHandling && IsOne(g_state.disablePotionHandling);
			settings.alchemyXPMultiplier = g_state.alchemyXPMultiplier && std::isfinite(g_state.alchemyXPMultiplier->value) &&
				g_state.alchemyXPMultiplier->value >= 0.0f ? g_state.alchemyXPMultiplier->value : 1.0f;
			static_cast<void>(vanilla::Adapter::TryGetGameSettings(
				settings.alchemyIngredientInitMultiplier, settings.alchemySkillFactor));
			settings.impureProcessingEnabled = IsImpureProcessingEnabled();
			a_settings = settings;
			return true;
		} catch (...) {
			return false;
		}
	}

	std::uint64_t Adapter::GetCalculationRevision() noexcept
	{
		return IsActive() ? g_state.calculationRevision : 0;
	}

	bool Adapter::IsPotionHandlingEnabled() noexcept
	{
		return IsActive() && g_state.potionHandlingEnabled;
	}

	bool Adapter::IsImpureProcessingEnabled() noexcept
	{
		return IsActive() && g_state.impureProcessingEnabled;
	}

	bool Adapter::IsReweightingEnabled() noexcept
	{
		return IsActive() && g_state.reweightingEnabled;
	}

	bool Adapter::IsRenamingEnabled() noexcept
	{
		return IsActive() && g_state.renamingEnabled;
	}

	bool Adapter::TryGetAlchemyEffectivenessMultiplier(
		float a_alchemyLevel,
		float a_fallbackPerkMultiplier,
		const vanilla::EvaluationContext& a_context,
		float& a_multiplier) noexcept
	{
		return TryGetAlchemyEffectivenessMultiplier(
			nullptr,
			a_alchemyLevel,
			a_fallbackPerkMultiplier,
			false,
			false,
			false,
			a_context,
			a_multiplier);
	}

	bool Adapter::TryGetAlchemyEffectivenessMultiplier(
		const RE::EffectSetting* a_effect,
		float a_alchemyLevel,
		float a_fallbackPerkMultiplier,
		bool a_potion,
		bool a_includeTypePerks,
		bool a_mixedPotion,
		const vanilla::EvaluationContext& a_context,
		float& a_multiplier) noexcept
	{
		float durationMultiplier = 1.0f;
		return TryGetAlchemyEffectivenessMultipliers(
			a_effect,
			a_alchemyLevel,
			a_fallbackPerkMultiplier,
			a_potion,
			a_includeTypePerks,
			a_mixedPotion,
			a_context,
			a_multiplier,
			durationMultiplier);
	}

	bool Adapter::TryGetAlchemyEffectivenessMultipliers(
		const RE::EffectSetting* a_effect,
		float a_alchemyLevel,
		float a_fallbackPerkMultiplier,
		bool a_potion,
		bool a_includeTypePerks,
		bool a_mixedPotion,
		const vanilla::EvaluationContext& a_context,
		float& a_magnitudeMultiplier,
		float& a_durationMultiplier) noexcept
	{
		if (!IsActive()) {
			return false;
		}
		float initMultiplier = 0.0f;
		float skillFactor = 0.0f;
		if (!vanilla::Adapter::TryGetGameSettings(initMultiplier, skillFactor)) {
			return false;
		}
		if (!std::isfinite(a_alchemyLevel) || !std::isfinite(a_fallbackPerkMultiplier) ||
			a_fallbackPerkMultiplier <= 0.0f) {
			return false;
		}
		const float baseEffectiveness = ::alchemist::algorithm::CalculateAlchemyEffectiveness(
			initMultiplier, skillFactor, a_alchemyLevel, 1.0f);
		if (!std::isfinite(baseEffectiveness) || baseEffectiveness <= 0.0f) {
			return false;
		}
		float magnitudePerkMultiplier = 1.0f;
		float durationPerkMultiplier = 1.0f;
		vanilla::Adapter::GetPerkMultipliers(
			a_effect,
			a_fallbackPerkMultiplier,
			a_potion,
			a_includeTypePerks,
			a_mixedPotion,
			a_context,
			MakePerkPolicy(),
			magnitudePerkMultiplier,
			durationPerkMultiplier);
		a_magnitudeMultiplier = baseEffectiveness * magnitudePerkMultiplier;
		a_durationMultiplier = baseEffectiveness * durationPerkMultiplier;

		// Restore/damage duration-family dilution (RestoreXDuration / DamageXDuration settings):
		// these six families deliver the same total effect over a longer window, so the
		// per-tick magnitude must shrink by the same factor the window grows.
		const auto familyIndex = FindFamily(a_effect);
		if (familyIndex >= 0) {
			const float familySeconds = GetFamilyDurationSeconds(familyIndex);
			if (std::isfinite(familySeconds) && familySeconds > 1.0f) {
				a_magnitudeMultiplier /= familySeconds;
			}
		}

		if (vanilla::Adapter::IsDurationBased(a_effect)) {
			a_durationMultiplier = ::alchemist::algorithm::CalculateDurationBasedIngredientPowerFactor(a_durationMultiplier);
		}
		if (!std::isfinite(a_magnitudeMultiplier) || a_magnitudeMultiplier <= 0.0f ||
			!std::isfinite(a_durationMultiplier) || a_durationMultiplier <= 0.0f) {
			return false;
		}
		return true;
	}

	std::int32_t Adapter::FindFamily(const RE::EffectSetting* a_effect) noexcept
	{
		return ::alchemist::caco::FindFamily(a_effect);
	}

	float Adapter::GetFamilyDurationSeconds(std::int32_t a_familyIndex) noexcept
	{
		if (!IsActive() || a_familyIndex < 0 ||
			static_cast<std::size_t>(a_familyIndex) >= kFamilies.size()) {
			return 1.0f;
		}

		// CACO's duration globals store the fixed 1-, 5-, and 10-second variant index.
		switch (GetDurationIndex(static_cast<std::size_t>(a_familyIndex))) {
		case 1:
			return 5.0f;
		case 2:
			return 10.0f;
		default:
			return 1.0f;
		}
	}

	RE::EffectSetting* Adapter::ResolveIngredientEffect(
		const RE::IngredientItem* a_ingredient,
		RE::EffectSetting* a_sourceEffect) noexcept
	{
		if (!IsActive() || !a_ingredient || !a_sourceEffect) {
			return a_sourceEffect;
		}
		const int familyIndex = FindFamily(a_sourceEffect);
		if (familyIndex < 0 || !IsIngredientListedInFamily(
				a_ingredient, g_state.families[static_cast<std::size_t>(familyIndex)])) {
			return a_sourceEffect;
		}
		if (auto* activeEffect = ResolveDurationEffect(static_cast<std::size_t>(familyIndex), a_sourceEffect)) {
			return activeEffect;
		}
		return a_sourceEffect;
	}

	RE::EffectSetting* Adapter::ResolveIngredientEffect(
		const RE::IngredientItem* a_ingredient,
		RE::EffectSetting* a_sourceEffect,
		std::size_t a_durationIndex) noexcept
	{
		if (!IsActive() || !a_ingredient || !a_sourceEffect) {
			return a_sourceEffect;
		}
		const int familyIndex = FindFamily(a_sourceEffect);
		if (familyIndex < 0 || !IsIngredientListedInFamily(
				a_ingredient, g_state.families[static_cast<std::size_t>(familyIndex)])) {
			return a_sourceEffect;
		}
		if (auto* variantEffect = ResolveDurationEffect(static_cast<std::size_t>(familyIndex), a_sourceEffect, a_durationIndex)) {
			return variantEffect;
		}
		return a_sourceEffect;
	}

	float Adapter::ApplyImpureMagnitude(float a_value) noexcept
	{
		if (!std::isfinite(a_value)) {
			return a_value;
		}
		return a_value * 0.2f;
	}

	float Adapter::ApplyImpureDuration(float a_value) noexcept
	{
		if (!std::isfinite(a_value)) {
			return a_value;
		}
		const double reduced = std::trunc(static_cast<double>(a_value) * 0.2);
		const double minimum = static_cast<double>((std::numeric_limits<std::int32_t>::min)());
		const double maximum = static_cast<double>((std::numeric_limits<std::int32_t>::max)());
		return static_cast<float>(static_cast<std::int32_t>((std::clamp)(reduced, minimum, maximum)));
	}

	float Adapter::ApplyImpureGold(float a_value) noexcept
	{
		if (!std::isfinite(a_value) || a_value <= 0.0f) {
			return 0.0f;
		}
		const double preAdjustment = (std::min)(std::floor(static_cast<double>(a_value)),
			static_cast<double>((std::numeric_limits<std::int32_t>::max)()));
		return static_cast<float>(algorithm::ApplyImpureGold(static_cast<std::int32_t>(preAdjustment)));
	}

	std::int32_t Adapter::ApplyImpureGold(std::int32_t a_value) noexcept
	{
		return algorithm::ApplyImpureGold(a_value);
	}

	bool Adapter::TryGetCrucibleExemplar(
		const RE::EffectSetting* a_primaryEffect,
		float a_magnitude,
		float a_duration,
		ExemplarResult& a_result) noexcept
	{
		a_result = {};
		if (!IsActive() || !a_primaryEffect || !std::isfinite(a_magnitude) || !std::isfinite(a_duration)) {
			return false;
		}
		if (TryGetCureExemplar(a_primaryEffect, a_result)) {
			return true;
		}
		const auto* compareList = FindPotionList(a_primaryEffect);
		if (!compareList) {
			return false;
		}
		const bool durationBased = vanilla::Adapter::IsDurationBased(a_primaryEffect);
		const float value = durationBased ? a_duration : a_magnitude;
		const std::size_t comparisonPosition = durationBased ? 0 : GetComparisonPosition(a_primaryEffect);
		std::size_t quality = 0;
		if (!SelectQuality(compareList, value, durationBased, comparisonPosition, quality)) {
			return false;
		}
		const auto* exemplar = GetPotionAt(compareList, quality);
		if (!exemplar) {
			return false;
		}
		a_result.potion = exemplar;
		a_result.goldValue = exemplar->GetGoldValue();
		return true;
	}

	bool Adapter::TryGetPotionName(
		std::size_t a_effectCount,
		const RE::EffectSetting* a_primaryEffect,
		float a_magnitude,
		float a_duration,
		std::string_view a_primaryName,
		std::string_view a_secondaryName,
		bool a_isPoison,
		bool a_impure,
		std::string_view a_potionPrefix,
		std::string_view a_poisonPrefix,
		std::string& a_name) noexcept
	{
		a_name.clear();
		if (!IsRenamingEnabled() || !a_primaryEffect || a_effectCount == 0 || a_primaryName.empty()) {
			return false;
		}
		try {
			std::string quality;
			if (a_impure) {
				quality = localization::Translate("caco.qualityImpure", "Impure ");
			} else if (!IsCureEffect(a_primaryEffect)) {
				const auto* compareList = FindPotionList(a_primaryEffect);
				std::size_t qualityIndex = 0;
				const bool durationBased = vanilla::Adapter::IsDurationBased(a_primaryEffect);
				const std::size_t comparisonPosition = durationBased ? 0 : GetComparisonPosition(a_primaryEffect);
				if (!compareList || !SelectQuality(compareList, durationBased ? a_duration : a_magnitude,
					durationBased, comparisonPosition, qualityIndex)) {
					return false;
				}
				if (a_isPoison) {
					static constexpr std::array<std::pair<std::string_view, std::string_view>, 5> harmful = {
						std::make_pair("caco.qualityWeak", "Weak "),
						std::make_pair("caco.qualityStandard", "Standard "),
						std::make_pair("caco.qualityPotent", "Potent "),
						std::make_pair("caco.qualityMalign", "Malign "),
						std::make_pair("caco.qualityDevastating", "Devastating ")
					};
					quality = localization::Translate(harmful[qualityIndex].first, harmful[qualityIndex].second);
				} else {
					static constexpr std::array<std::pair<std::string_view, std::string_view>, 5> beneficial = {
						std::make_pair("caco.qualityWeak", "Weak "),
						std::make_pair("caco.qualityStandard", "Standard "),
						std::make_pair("caco.qualityQuality", "Quality "),
						std::make_pair("caco.qualityPotent", "Potent "),
						std::make_pair("caco.qualityGrand", "Grand ")
					};
					quality = localization::Translate(beneficial[qualityIndex].first, beneficial[qualityIndex].second);
				}
			}
			const auto prefix = a_isPoison ? a_poisonPrefix : a_potionPrefix;
			a_name = quality;
			a_name += prefix;
			if (!a_name.empty() && a_name.back() != ' ') {
				a_name += ' ';
			}
			a_name += a_primaryName;
			if (a_effectCount == 2 && !a_secondaryName.empty()) {
				a_name += localization::Translate("caco.effectSeparator", " & ");
				a_name += a_secondaryName;
			}
			return true;
		} catch (...) {
			a_name.clear();
			return false;
		}
	}

	bool Adapter::TryGetPotionWeight(
		std::size_t a_effectCount,
		bool a_hasBeneficial,
		bool a_hasHarmful,
		bool a_hasPurity,
		float& a_weight) noexcept
	{
		if (!IsReweightingEnabled() || a_effectCount == 0) {
			return false;
		}
		const bool pureBeneficial = a_hasBeneficial && !a_hasHarmful && a_hasPurity;
		const bool reducedWeight = pureBeneficial;
		if (a_effectCount == 1) {
			a_weight = reducedWeight ? 0.2f : 0.3f;
		} else if (a_effectCount == 2) {
			a_weight = reducedWeight ? 0.3f : 0.4f;
		} else {
			a_weight = reducedWeight ? 0.4f : 0.5f;
		}
		return true;
	}

	SavedStateSnapshot Adapter::SaveStateSnapshot() noexcept
	{
		SavedStateSnapshot snapshot;
		if (!IsDetected()) {
			return snapshot;
		}
		for (std::size_t i = 0; i < kFamilies.size() && i < 6; ++i) {
			if (g_state.families[i].durationGlobal) {
				snapshot.durationGlobalValues[i] = g_state.families[i].durationGlobal->value;
			}
		}
		if (g_state.disablePotionHandling) {
			snapshot.disablePotionHandlingValue = g_state.disablePotionHandling->value;
		}
		if (g_state.impurePotions) {
			snapshot.impurePotionsValue = g_state.impurePotions->value;
		}
		snapshot.valid = true;
		return snapshot;
	}

	void Adapter::RestoreStateSnapshot(const SavedStateSnapshot& a_snapshot) noexcept
	{
		g_state.hasOverrides = false;
		g_state.durationOverrideIndices = {};
		if (!a_snapshot.valid || !IsDetected()) {
			return;
		}
		for (std::size_t i = 0; i < kFamilies.size() && i < 6; ++i) {
			if (g_state.families[i].durationGlobal) {
				g_state.families[i].durationGlobal->value = a_snapshot.durationGlobalValues[i];
			}
		}
		if (g_state.disablePotionHandling) {
			g_state.disablePotionHandling->value = a_snapshot.disablePotionHandlingValue;
		}
		if (g_state.impurePotions) {
			g_state.impurePotions->value = a_snapshot.impurePotionsValue;
		}
		RefreshOptions();
	}

	bool Adapter::ApplySettingsJson(const nlohmann::json& a_json) noexcept
	{
		if (!IsDetected() || !a_json.is_object()) {
			return false;
		}
		const auto& cacoJson = (a_json.contains("caco") && a_json["caco"].is_object()) ? a_json["caco"] : a_json;

		auto parseVal = [](const nlohmann::json& obj, const char* key) -> std::optional<float> {
			const auto it = obj.find(key);
			if (it == obj.end()) return std::nullopt;
			if (it->is_number()) return it->get<float>();
			if (it->is_string()) {
				try { return std::stof(it->get<std::string>()); } catch (...) {}
			}
			return std::nullopt;
		};

		static constexpr std::array<const char*, 6> durationKeys{
			"RestoreHealthDuration", "RestoreMagickaDuration", "RestoreStaminaDuration",
			"DamageHealthDuration", "DamageMagickaDuration", "DamageStaminaDuration"
		};
		g_state.hasOverrides = true;
		for (std::size_t i = 0; i < 6; ++i) {
			const float v = parseVal(cacoJson, durationKeys[i]).value_or(0.0f);
			const int durationIdx = NormalizeDurationIndex(v);
			g_state.durationOverrideIndices[i] = durationIdx;
			if (g_state.families[i].durationGlobal) {
				g_state.families[i].durationGlobal->value = static_cast<float>(durationIdx);
			}
		}

		if (auto v = parseVal(cacoJson, "DisableAllPotionHandling")) {
			if (g_state.disablePotionHandling) {
				g_state.disablePotionHandling->value = *v;
			}
		}
		if (auto v = parseVal(cacoJson, "ImpurePotionProcessing")) {
			if (g_state.impurePotions) {
				g_state.impurePotions->value = *v;
			}
		}
		if (auto v = parseVal(cacoJson, "AlchemyIngredientInitMultiplier")) {
			vanilla::Adapter::SetGameSettings(*v, vanilla::Adapter::GetAlchemySkillFactor());
		}
		if (auto v = parseVal(cacoJson, "AlchemySkillFactor")) {
			vanilla::Adapter::SetGameSettings(vanilla::Adapter::GetAlchemyIngredientInitMultiplier(), *v);
		}

		RefreshOptions();
		return true;
	}
}
