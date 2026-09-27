#include "Vanilla.h"

#include "AlchemyMath.h"
#include "PluginUtils.h"

#include <RE/B/BGSKeyword.h>
#include <RE/B/BGSPerk.h>
#include <RE/B/BGSEntryPointFunctionDataOneValue.h>
#include <RE/B/BGSEntryPointPerkEntry.h>
#include <RE/E/Effect.h>
#include <RE/E/EffectSetting.h>
#include <RE/G/GameSettingCollection.h>
#include <RE/T/TESGlobal.h>
#include <RE/T/TESCondition.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <set>
#include <string>
#include <string_view>

namespace alchemist::vanilla
{
	namespace
	{
		using plugin_utils::EqualsIgnoreCase;

		constexpr std::string_view kBeneficialKeyword = "MagicAlchBeneficial";
		constexpr std::string_view kHarmfulKeyword = "MagicAlchHarmful";
		constexpr std::string_view kDurationBasedKeyword = "MagicAlchDurationBased";
		constexpr float kAlchemyItemType = 17.0f;

		struct GameSettingsState
		{
			bool ready = false;
			float alchemyIngredientInitMultiplier = 0.0f;
			float alchemySkillFactor = 0.0f;
			std::uint64_t revision = 0;
		};

		GameSettingsState g_settings;

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

		bool ReadGameSetting(std::string_view a_name, float& a_value) noexcept
		{
			try {
				auto* collection = RE::GameSettingCollection::GetSingleton();
				if (!collection) {
					return false;
				}
				const std::string name(a_name);
				auto* setting = collection->GetSetting(name.c_str());
				if (!setting || setting->GetType() != RE::Setting::Type::kFloat) {
					return false;
				}
				const float value = setting->GetFloat();
				if (!std::isfinite(value) || value <= 0.0f) {
					return false;
				}
				a_value = value;
				return true;
			} catch (...) {
				return false;
			}
		}

		bool HasAlchemyEffectKeyword(
			const RE::EffectSetting* a_effect,
			const RE::BGSKeyword* a_keyword) noexcept
		{
			if (!a_effect || !a_keyword) {
				return false;
			}
			const auto* editorID = a_keyword->GetFormEditorID();
			if (editorID && EqualsIgnoreCase(editorID, kBeneficialKeyword)) {
				return Adapter::HasBeneficialKeyword(a_effect);
			}
			if (editorID && EqualsIgnoreCase(editorID, kHarmfulKeyword)) {
				return Adapter::HasHarmfulKeyword(a_effect);
			}
			if (editorID && EqualsIgnoreCase(editorID, kDurationBasedKeyword)) {
				return Adapter::IsDurationBased(a_effect);
			}
			return a_effect->HasKeyword(a_keyword);
		}

		bool CompareCondition(float a_left, float a_right, RE::CONDITION_ITEM_DATA::OpCode a_opCode) noexcept
		{
			switch (a_opCode) {
			case RE::CONDITION_ITEM_DATA::OpCode::kEqualTo:
				return a_left == a_right;
			case RE::CONDITION_ITEM_DATA::OpCode::kNotEqualTo:
				return a_left != a_right;
			case RE::CONDITION_ITEM_DATA::OpCode::kGreaterThan:
				return a_left > a_right;
			case RE::CONDITION_ITEM_DATA::OpCode::kGreaterThanOrEqualTo:
				return a_left >= a_right;
			case RE::CONDITION_ITEM_DATA::OpCode::kLessThan:
				return a_left < a_right;
			case RE::CONDITION_ITEM_DATA::OpCode::kLessThanOrEqualTo:
				return a_left <= a_right;
			default:
				return false;
			}
		}

		bool GetConditionComparisonValue(
			const RE::CONDITION_ITEM_DATA& a_condition,
			float& a_value) noexcept
		{
			if (a_condition.flags.global) {
				if (!a_condition.comparisonValue.g || !std::isfinite(a_condition.comparisonValue.g->value)) {
					return false;
				}
				a_value = a_condition.comparisonValue.g->value;
				return true;
			}
			if (!std::isfinite(a_condition.comparisonValue.f)) {
				return false;
			}
			a_value = a_condition.comparisonValue.f;
			return true;
		}

		bool HasActivePerk(
			const EvaluationContext& a_context,
			const RE::BGSPerk* a_perk) noexcept
		{
			if (!a_perk) {
				return false;
			}
			if (a_context.seeker.nativeContract && a_context.seeker.perk == a_perk) {
				return true;
			}
			return std::find(a_context.activePerks.begin(), a_context.activePerks.end(), a_perk) != a_context.activePerks.end();
		}

		bool EvaluateConditionItem(
			const RE::TESConditionItem* a_item,
			const RE::EffectSetting* a_effect,
			bool a_potion,
			const EvaluationContext& a_context,
			bool& a_effectSpecific,
			bool& a_typeSpecific) noexcept
		{
			bool result = true;
			bool first = true;
			bool prevIsOR = false;
			for (auto* item = a_item; item; item = item->next) {
				float comparison = 0.0f;
				if (!GetConditionComparisonValue(item->data, comparison)) {
					return false;
				}
				float value = 0.0f;
				bool conditionResult = false;
				const auto function = item->data.functionData.function.get();
				switch (function) {
				case RE::FUNCTION_DATA::FunctionID::kEPAlchemyEffectHasKeyword: {
					a_effectSpecific = true;
					if (!a_effect || !item->data.functionData.params[0]) {
						return false;
					}
					const auto* form = static_cast<const RE::TESForm*>(item->data.functionData.params[0]);
					const auto* keyword = form ? form->As<RE::BGSKeyword>() : nullptr;
					value = HasAlchemyEffectKeyword(a_effect, keyword) ? 1.0f : 0.0f;
					conditionResult = CompareCondition(value, comparison, item->data.flags.opCode);
					break;
				}
				case RE::FUNCTION_DATA::FunctionID::kHasKeyword: {
					a_effectSpecific = true;
					if (!a_effect || !item->data.functionData.params[0]) {
						return false;
					}
					const auto* form = static_cast<const RE::TESForm*>(item->data.functionData.params[0]);
					const auto* keyword = form ? form->As<RE::BGSKeyword>() : nullptr;
					value = HasAlchemyEffectKeyword(a_effect, keyword) ? 1.0f : 0.0f;
					conditionResult = CompareCondition(value, comparison, item->data.flags.opCode);
					break;
				}
				case RE::FUNCTION_DATA::FunctionID::kEPAlchemyGetMakingPoison:
					a_typeSpecific = true;
					value = a_potion ? 0.0f : 1.0f;
					conditionResult = CompareCondition(value, comparison, item->data.flags.opCode);
					break;
				case RE::FUNCTION_DATA::FunctionID::kGetIsUsedItemType:
					value = kAlchemyItemType;
					conditionResult = CompareCondition(value, comparison, item->data.flags.opCode);
					break;
				case RE::FUNCTION_DATA::FunctionID::kHasPerk: {
					if (!item->data.functionData.params[0]) {
						return false;
					}
					const auto* form = static_cast<const RE::TESForm*>(item->data.functionData.params[0]);
					const auto* perk = form ? form->As<RE::BGSPerk>() : nullptr;
					value = HasActivePerk(a_context, perk) ? 1.0f : 0.0f;
					conditionResult = CompareCondition(value, comparison, item->data.flags.opCode);
					break;
				}
				case RE::FUNCTION_DATA::FunctionID::kGetGlobalValue: {
					if (!item->data.functionData.params[0]) {
						return false;
					}
					const auto* form = static_cast<const RE::TESForm*>(item->data.functionData.params[0]);
					const auto* global = form ? form->As<RE::TESGlobal>() : nullptr;
					if (!global || !std::isfinite(global->value)) {
						return false;
					}
					value = global->value;
					conditionResult = CompareCondition(value, comparison, item->data.flags.opCode);
					break;
				}
				default:
					return false;
				}

				if (first) {
					result = conditionResult;
					first = false;
				} else if (prevIsOR) {
					result = result || conditionResult;
				} else {
					result = result && conditionResult;
				}
				prevIsOR = item->data.flags.isOR;
			}
			return result;
		}

		bool EvaluateEntryConditions(
			const RE::BGSEntryPointPerkEntry* a_entry,
			const RE::EffectSetting* a_effect,
			bool a_potion,
			const EvaluationContext& a_context,
			bool& a_effectSpecific,
			bool& a_typeSpecific) noexcept
		{
			a_effectSpecific = false;
			a_typeSpecific = false;
			try {
				bool result = true;
				bool first = true;
				bool prevIsOR = false;
				for (const auto& condition : a_entry->conditions) {
					if (!condition.head) {
						continue;
					}
					const bool conditionResult = EvaluateConditionItem(
						condition.head, a_effect, a_potion, a_context, a_effectSpecific, a_typeSpecific);
					if (first) {
						result = conditionResult;
						first = false;
					} else if (prevIsOR) {
						result = result || conditionResult;
					} else {
						result = result && conditionResult;
					}
					prevIsOR = condition.head->data.flags.isOR;
				}
				return result;
			} catch (...) {
				return false;
			}
		}

		bool IsAlchemistPerk(const RE::BGSPerk* a_perk) noexcept
		{
			if (!a_perk) {
				return false;
			}
			const auto formID = a_perk->GetFormID();
			constexpr std::array<RE::FormID, 5> vanillaAlchemistFormIDs{
				0x000BE127,
				0x000C07CA,
				0x000C07CB,
				0x000C07CC,
				0x000C07CD
			};
			if (std::find(vanillaAlchemistFormIDs.begin(), vanillaAlchemistFormIDs.end(), formID) != vanillaAlchemistFormIDs.end()) {
				return true;
			}
			const auto* editorID = a_perk->GetFormEditorID();
			if (!editorID) {
				return false;
			}
			const std::string_view value(editorID);
			constexpr std::string_view alchemistPrefix = "Alchemist";
			return (value.size() > alchemistPrefix.size() &&
				EqualsIgnoreCase(value.substr(0, alchemistPrefix.size()), alchemistPrefix)) ||
				ContainsIgnoreCase(value, "ORD_Alc_AlchemyMastery");
		}

		bool IsPerkIdentity(const RE::BGSPerk* a_perk, RE::FormID a_localFormID,
			std::string_view a_firstEditorID, std::string_view a_secondEditorID) noexcept
		{
			if (!a_perk) {
				return false;
			}
			if (a_perk->GetFormID() == a_localFormID) {
				return true;
			}
			const auto* editorID = a_perk->GetFormEditorID();
			return editorID && (EqualsIgnoreCase(editorID, a_firstEditorID) ||
				EqualsIgnoreCase(editorID, a_secondEditorID));
		}

		bool IsPhysicianPerk(const RE::BGSPerk* a_perk) noexcept
		{
			return IsPerkIdentity(a_perk, 0x00058215, "Physician", "AlchPhysician");
		}

		bool IsBenefactorPerk(const RE::BGSPerk* a_perk) noexcept
		{
			return IsPerkIdentity(a_perk, 0x00058216, "Benefactor", "AlchBenefactor");
		}

		bool IsPoisonerPerk(const RE::BGSPerk* a_perk) noexcept
		{
			return IsPerkIdentity(a_perk, 0x00058217, "Poisoner", "AlchPoisoner");
		}

		bool IsExcludedPerk(const RE::BGSPerk* a_perk, const PerkPolicy& a_policy) noexcept
		{
			if (!a_perk) {
				return false;
			}
			if (a_policy.excludedPerk && a_perk == a_policy.excludedPerk) {
				return true;
			}
			if (a_policy.excludedPerkName.empty()) {
				return false;
			}
			const auto* editorID = a_perk->GetFormEditorID();
			if (editorID && EqualsIgnoreCase(editorID, a_policy.excludedPerkName)) {
				return true;
			}
			const auto* fullName = a_perk->GetFullName();
			return fullName && EqualsIgnoreCase(fullName, a_policy.excludedPerkName);
		}

		bool IsPhysicianEffect(const RE::EffectSetting* a_effect) noexcept
		{
			return a_effect && (a_effect->HasKeywordString("MagicAlchRestoreHealth") ||
				a_effect->HasKeywordString("MagicAlchRestoreMagicka") ||
				a_effect->HasKeywordString("MagicAlchRestoreStamina"));
		}

		void GetAlchemyPerkMultipliers(
			const RE::EffectSetting* a_effect,
			float a_fallback,
			bool a_potion,
			bool a_includeTypePerks,
			bool a_mixedPotion,
			const EvaluationContext& a_context,
			const PerkPolicy& a_policy,
			float& a_magnitudeMultiplier,
			float& a_durationMultiplier) noexcept
		{
			const float fallback = std::isfinite(a_fallback) && a_fallback > 0.0f ? a_fallback : 1.0f;
			float rankFallback = 1.0f;
			if (a_policy.cacoActive) {
				if (!a_policy.potionHandlingEnabled) {
					const int rank = (std::max)(0, static_cast<int>(a_context.alchemistPerkRank));
					if (rank == 1) rankFallback = 1.20f;
					else if (rank == 3) rankFallback = 1.45f;
					else if (rank == 5) rankFallback = 1.75f;
					else rankFallback = 1.0f;
				} else if (a_context.alchemistPerkRank == 1) {
					rankFallback = 1.20f;
				} else if (a_context.alchemistPerkRank > 1) {
					rankFallback = 1.0f + 0.20f + static_cast<float>(a_context.alchemistPerkRank - 1) * 0.15f;
				}
			} else {
				rankFallback = a_context.alchemistPerkRank > 0 ?
					1.0f + static_cast<float>(a_context.alchemistPerkRank) * 0.2f : 1.0f;
			}
			const double contextFallback = a_context.captured ?
				static_cast<double>((std::max)(fallback, rankFallback)) : static_cast<double>(fallback);
			a_magnitudeMultiplier = static_cast<float>(contextFallback);
			a_durationMultiplier = static_cast<float>(contextFallback);
			if (!a_context.captured) {
				return;
			}

			double alchemistMagnitude = 1.0;
			double alchemistDuration = 1.0;
			bool hasAlchemistMagnitude = false;
			bool hasAlchemistDuration = false;
			double otherMagnitude = 1.0;
			double otherDuration = 1.0;
			std::set<const RE::BGSPerk*> inspectedPerks;
			bool physicianApplied = false;
			bool benefactorApplied = false;
			bool benefactorEntryPointFound = false;
			bool poisonerApplied = false;
			bool seekerApplied = false;
			const bool disableAllPotionHandling = !a_policy.cacoActive || !a_policy.potionHandlingEnabled;

			const auto applyValue = [&](const RE::BGSPerk* a_perk, float a_value, bool a_affectsMagnitude, bool a_affectsDuration) {
				if (IsAlchemistPerk(a_perk)) {
					if (disableAllPotionHandling) {
						return;
					}
					if (a_affectsMagnitude) {
						alchemistMagnitude = hasAlchemistMagnitude ? (std::max)(alchemistMagnitude, static_cast<double>(a_value)) : static_cast<double>(a_value);
						hasAlchemistMagnitude = true;
					}
					if (a_affectsDuration) {
						alchemistDuration = hasAlchemistDuration ? (std::max)(alchemistDuration, static_cast<double>(a_value)) : static_cast<double>(a_value);
						hasAlchemistDuration = true;
					}
				} else {
					if (a_affectsMagnitude) {
						otherMagnitude *= static_cast<double>(a_value);
					}
					if (a_affectsDuration) {
						otherDuration *= static_cast<double>(a_value);
					}
				}
			};

			const auto inspectPerk = [&](const RE::BGSPerk* a_perk) {
				if (!a_perk || !inspectedPerks.insert(a_perk).second ||
					(a_perk == a_context.seeker.perk && !a_context.seeker.nativeContract) ||
					IsExcludedPerk(a_perk, a_policy)) {
					return;
				}
				const bool benefactorPerk = IsBenefactorPerk(a_perk);
				const bool poisonerPerk = IsPoisonerPerk(a_perk);
				if ((benefactorPerk && !algorithm::ShouldApplyBenefactor(
						a_potion, a_effect && Adapter::HasBeneficialKeyword(a_effect), a_includeTypePerks, a_mixedPotion, disableAllPotionHandling)) ||
					(poisonerPerk && !algorithm::ShouldApplyPoisoner(
						a_potion, a_effect && Adapter::HasHarmfulKeyword(a_effect), a_includeTypePerks))) {
					return;
				}
				for (const auto* entry : a_perk->perkEntries) {
					if (!entry || entry->GetType() != RE::PERK_ENTRY_TYPE::kEntryPoint) {
						continue;
					}
					const auto* entryPoint = static_cast<const RE::BGSEntryPointPerkEntry*>(entry);
					if (!entryPoint->IsEntryPoint(RE::BGSEntryPoint::ENTRY_POINTS::kModAlchemyEffectiveness) ||
						!entryPoint->functionData ||
						entryPoint->functionData->GetType() != RE::BGSEntryPointFunctionData::ENTRY_POINT_FUNCTION_DATA::kOneValue) {
						continue;
					}
					const auto* functionData = static_cast<const RE::BGSEntryPointFunctionDataOneValue*>(entryPoint->functionData);
					if (!std::isfinite(functionData->data) || functionData->data <= 0.0f ||
						entryPoint->entryData.function.get() != RE::BGSEntryPointFunction::ENTRY_POINT_FUNCTIONS::kMultiplyValue) {
						continue;
					}
					if (IsBenefactorPerk(a_perk)) {
						benefactorEntryPointFound = true;
					}
					bool effectSpecific = false;
					bool typeSpecific = false;
					if (!EvaluateEntryConditions(entryPoint, a_effect, a_potion, a_context, effectSpecific, typeSpecific) ||
						(typeSpecific && !a_includeTypePerks)) {
						continue;
					}
					if (effectSpecific && a_effect && Adapter::IsDurationBased(a_effect) &&
						std::abs(functionData->data - 0.01f) < 0.001f) {
						continue;
					}
					const bool affectsMagnitude = !a_effect || a_effect->data.flags.all(
						RE::EffectSetting::EffectSettingData::Flag::kPowerAffectsMagnitude);
					const bool affectsDuration = !a_effect || a_effect->data.flags.all(
						RE::EffectSetting::EffectSettingData::Flag::kPowerAffectsDuration);
					if (affectsMagnitude || affectsDuration) {
						physicianApplied = physicianApplied || IsPhysicianPerk(a_perk);
						benefactorApplied = benefactorApplied || IsBenefactorPerk(a_perk);
						poisonerApplied = poisonerApplied || IsPoisonerPerk(a_perk);
						seekerApplied = seekerApplied || a_perk == a_context.seeker.perk;
						applyValue(a_perk, functionData->data, affectsMagnitude, affectsDuration);
					}
				}
			};

			try {
				for (const auto* perk : a_context.activePerks) {
					inspectPerk(perk);
				}
				if (a_context.seeker.nativeContract && !seekerApplied) {
					inspectPerk(a_context.seeker.perk);
				}
			} catch (...) {
			}

			if (algorithm::ShouldApplyPhysicianFallback(
				a_policy.cacoActive,
				a_context.hasPhysician,
				physicianApplied,
				IsPhysicianEffect(a_effect))) {
				otherMagnitude *= 1.25;
				otherDuration *= 1.25;
			}
			if (algorithm::ShouldApplyBenefactorFallback(
				a_potion,
				a_effect && Adapter::HasBeneficialKeyword(a_effect),
				a_includeTypePerks,
				a_context.hasBenefactor,
				benefactorApplied,
				benefactorEntryPointFound,
				a_mixedPotion,
				disableAllPotionHandling)) {
				otherMagnitude *= 1.25;
				otherDuration *= 1.25;
			}
			if (algorithm::ShouldApplyPoisoner(
				a_potion, a_effect && Adapter::HasHarmfulKeyword(a_effect), a_includeTypePerks) &&
				a_context.hasPoisoner && !poisonerApplied) {
				otherMagnitude *= 1.25;
				otherDuration *= 1.25;
			}
			if (a_context.hasSeekerOfShadows && !seekerApplied) {
				otherMagnitude *= 1.1;
				otherDuration *= 1.1;
			}

			const double magnitude = otherMagnitude * (hasAlchemistMagnitude ? (std::max)(contextFallback, alchemistMagnitude) : contextFallback);
			const double duration = otherDuration * (hasAlchemistDuration ? (std::max)(contextFallback, alchemistDuration) : contextFallback);
			a_magnitudeMultiplier = std::isfinite(magnitude) && magnitude > 0.0 ? static_cast<float>(magnitude) : static_cast<float>(contextFallback);
			a_durationMultiplier = std::isfinite(duration) && duration > 0.0 ? static_cast<float>(duration) : static_cast<float>(contextFallback);
		}

	}

	bool Adapter::Refresh() noexcept
	{
		float alchemyIngredientInitMultiplier = 0.0f;
		float alchemySkillFactor = 0.0f;
		if (!ReadGameSetting("fAlchemyIngredientInitMult", alchemyIngredientInitMultiplier) ||
			!ReadGameSetting("fAlchemySkillFactor", alchemySkillFactor)) {
			return false;
		}

		const bool changed = !g_settings.ready ||
			g_settings.alchemyIngredientInitMultiplier != alchemyIngredientInitMultiplier ||
			g_settings.alchemySkillFactor != alchemySkillFactor;
		g_settings.alchemyIngredientInitMultiplier = alchemyIngredientInitMultiplier;
		g_settings.alchemySkillFactor = alchemySkillFactor;
		g_settings.ready = true;
		if (changed && g_settings.revision < (std::numeric_limits<std::uint64_t>::max)()) {
			++g_settings.revision;
		}
		return true;
	}

	bool Adapter::TryGetGameSettings(float& a_initMult, float& a_skillFactor) noexcept
	{
		if (!g_settings.ready) {
			return false;
		}
		a_initMult = g_settings.alchemyIngredientInitMultiplier;
		a_skillFactor = g_settings.alchemySkillFactor;
		return true;
	}

	float Adapter::GetAlchemyIngredientInitMultiplier() noexcept
	{
		if (g_settings.ready && g_settings.alchemyIngredientInitMultiplier > 0.0f) {
			return g_settings.alchemyIngredientInitMultiplier;
		}
		float val = 4.0f;
		if (ReadGameSetting("fAlchemyIngredientInitMult", val) && val > 0.0f) {
			return val;
		}
		return 4.0f;
	}

	float Adapter::GetAlchemySkillFactor() noexcept
	{
		if (g_settings.ready && g_settings.alchemySkillFactor > 0.0f) {
			return g_settings.alchemySkillFactor;
		}
		float val = 1.5f;
		if (ReadGameSetting("fAlchemySkillFactor", val) && val > 0.0f) {
			return val;
		}
		return 1.5f;
	}

	void Adapter::SetGameSettings(float a_initMult, float a_skillFactor) noexcept
	{
		if (std::isfinite(a_initMult) && a_initMult > 0.0f) {
			g_settings.alchemyIngredientInitMultiplier = a_initMult;
		}
		if (std::isfinite(a_skillFactor) && a_skillFactor > 0.0f) {
			g_settings.alchemySkillFactor = a_skillFactor;
		}
		g_settings.ready = true;
	}

	std::uint64_t Adapter::GetGameSettingsRevision() noexcept
	{
		return g_settings.revision;
	}

	bool Adapter::HasBeneficialKeyword(const RE::EffectSetting* a_effect) noexcept
	{
		return a_effect && (a_effect->HasKeywordString(kBeneficialKeyword) ||
			(!a_effect->HasKeywordString(kHarmfulKeyword) && !a_effect->IsHostile()));
	}

	bool Adapter::HasHarmfulKeyword(const RE::EffectSetting* a_effect) noexcept
	{
		return a_effect && (a_effect->HasKeywordString(kHarmfulKeyword) || a_effect->IsHostile());
	}

	bool Adapter::IsDurationBased(const RE::EffectSetting* a_effect) noexcept
	{
		return a_effect && a_effect->HasKeywordString(kDurationBasedKeyword);
	}

	void Adapter::GetPerkMultipliers(
		const RE::EffectSetting* a_effect,
		float a_fallback,
		bool a_potion,
		bool a_includeTypePerks,
		bool a_mixedPotion,
		const EvaluationContext& a_context,
		const PerkPolicy& a_policy,
		float& a_magnitudeMultiplier,
		float& a_durationMultiplier) noexcept
	{
		GetAlchemyPerkMultipliers(
			a_effect, a_fallback, a_potion, a_includeTypePerks, a_mixedPotion, a_context, a_policy,
			a_magnitudeMultiplier, a_durationMultiplier);
	}

	bool Adapter::TryGetAlchemyEffectivenessMultipliers(
		const RE::EffectSetting* a_effect,
		float a_alchemyLevel,
		float a_fallbackAlchemistMultiplier,
		bool a_potion,
		bool a_includeTypePerks,
		bool a_mixedPotion,
		const EvaluationContext& a_context,
		float& a_magnitudeMultiplier,
		float& a_durationMultiplier) noexcept
	{
		if (!a_context.captured || !std::isfinite(a_alchemyLevel) ||
			!std::isfinite(a_fallbackAlchemistMultiplier) || a_fallbackAlchemistMultiplier <= 0.0f) {
			return false;
		}
		const float initMult = GetAlchemyIngredientInitMultiplier();
		const float skillFactor = GetAlchemySkillFactor();
		const float baseEffectiveness = ::alchemist::algorithm::CalculateVanillaAlchemyEffectiveness(
			a_alchemyLevel, 1.0f, 1.0f, initMult, skillFactor);
		if (!std::isfinite(baseEffectiveness) || baseEffectiveness <= 0.0f) {
			return false;
		}
		float magnitudePerkMultiplier = 1.0f;
		float durationPerkMultiplier = 1.0f;
		GetAlchemyPerkMultipliers(
			a_effect,
			a_fallbackAlchemistMultiplier,
			a_potion,
			a_includeTypePerks,
			a_mixedPotion,
			a_context,
			PerkPolicy{},
			magnitudePerkMultiplier,
			durationPerkMultiplier);
		a_magnitudeMultiplier = baseEffectiveness * magnitudePerkMultiplier;
		a_durationMultiplier = baseEffectiveness * durationPerkMultiplier;
		return std::isfinite(a_magnitudeMultiplier) && a_magnitudeMultiplier > 0.0f &&
			std::isfinite(a_durationMultiplier) && a_durationMultiplier > 0.0f;
	}
}
