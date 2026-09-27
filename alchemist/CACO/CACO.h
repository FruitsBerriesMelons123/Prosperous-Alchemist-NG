#pragma once

#include "Vanilla/Vanilla.h"

#include <nlohmann/json_fwd.hpp>

#include <cstddef>
#include <cstdint>
#include <cmath>
#include <algorithm>
#include <array>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace RE
{
	class BGSPerk;
	class AlchemyItem;
	class EffectSetting;
	class IngredientItem;
	class SpellItem;
	class TESGlobal;
}

namespace alchemist::caco
{
	struct Settings
	{
		// Raw CACO duration global values (normally 0/1/2); see GetDurationIndex for
		// how CACO resolves them.
		float restoreHealthDuration = 0.0f;
		float restoreMagickaDuration = 0.0f;
		float restoreStaminaDuration = 0.0f;
		bool restoreEffectsDoNotStack = false;
		float damageHealthDuration = 0.0f;
		float damageMagickaDuration = 0.0f;
		float damageStaminaDuration = 0.0f;
		bool disableAllPotionHandling = false;
		float alchemyXPMultiplier = 1.0f;
		float alchemyIngredientInitMultiplier = 0.0f;
		float alchemySkillFactor = 0.0f;
		bool impureProcessingEnabled = false;
	};

	struct SavedStateSnapshot
	{
		std::array<float, 6> durationGlobalValues{};
		float disablePotionHandlingValue = 0.0f;
		float impurePotionsValue = 0.0f;
		bool valid = false;
	};

	namespace algorithm
	{
		// CACO-specific rules. Generic alchemy math lives in AlchemyMath.h.
		inline constexpr std::int32_t ApplyImpureGold(std::int32_t a_preAdjustmentGold) noexcept
		{
			return a_preAdjustmentGold > 0 ? static_cast<std::int32_t>(a_preAdjustmentGold / 5) : 0;
		}
	}

	static_assert(algorithm::ApplyImpureGold(466) == 93);
	static_assert(algorithm::ApplyImpureGold(4) == 0);

	// A pure one-effect result can use the authored CACO exemplar instead of a calculated value.
	struct ExemplarResult
	{
		const RE::AlchemyItem* potion = nullptr;
		std::int32_t goldValue = 0;
	};

	class Adapter final
	{
	public:
		static void Initialize() noexcept;
		static void Refresh() noexcept;

		[[nodiscard]] static bool IsDetected() noexcept;
		[[nodiscard]] static bool IsActive() noexcept;
		[[nodiscard]] static bool TryGetSettings(Settings& a_settings) noexcept;
		[[nodiscard]] static std::uint64_t GetCalculationRevision() noexcept;
		[[nodiscard]] static bool IsPotionHandlingEnabled() noexcept;
		[[nodiscard]] static bool IsImpureProcessingEnabled() noexcept;
		[[nodiscard]] static bool IsReweightingEnabled() noexcept;
		[[nodiscard]] static bool IsRenamingEnabled() noexcept;
		[[nodiscard]] static bool TryGetAlchemyEffectivenessMultiplier(
			float a_alchemyLevel,
			float a_fallbackPerkMultiplier,
			const vanilla::EvaluationContext& a_context,
			float& a_multiplier) noexcept;
		[[nodiscard]] static bool TryGetAlchemyEffectivenessMultiplier(
			const RE::EffectSetting* a_effect,
			float a_alchemyLevel,
			float a_fallbackPerkMultiplier,
			bool a_potion,
			bool a_includeTypePerks,
			bool a_mixedPotion,
			const vanilla::EvaluationContext& a_context,
			float& a_multiplier) noexcept;
		[[nodiscard]] static bool TryGetAlchemyEffectivenessMultipliers(
			const RE::EffectSetting* a_effect,
			float a_alchemyLevel,
			float a_fallbackPerkMultiplier,
			bool a_potion,
			bool a_includeTypePerks,
			bool a_mixedPotion,
			const vanilla::EvaluationContext& a_context,
			float& a_magnitudeMultiplier,
			float& a_durationMultiplier) noexcept;

		[[nodiscard]] static std::int32_t FindFamily(const RE::EffectSetting* a_effect) noexcept;
		[[nodiscard]] static float GetFamilyDurationSeconds(std::int32_t a_familyIndex) noexcept;
		[[nodiscard]] static RE::EffectSetting* ResolveIngredientEffect(
			const RE::IngredientItem* a_ingredient,
			RE::EffectSetting* a_sourceEffect) noexcept;
		[[nodiscard]] static RE::EffectSetting* ResolveIngredientEffect(
			const RE::IngredientItem* a_ingredient,
			RE::EffectSetting* a_sourceEffect,
			std::size_t a_durationIndex) noexcept;

		[[nodiscard]] static float ApplyImpureMagnitude(float a_value) noexcept;
		[[nodiscard]] static float ApplyImpureDuration(float a_value) noexcept;
		[[nodiscard]] static std::int32_t ApplyImpureGold(std::int32_t a_value) noexcept;
		[[nodiscard]] static float ApplyImpureGold(float a_value) noexcept;

		[[nodiscard]] static bool TryGetCrucibleExemplar(
			const RE::EffectSetting* a_primaryEffect,
			float a_magnitude,
			float a_duration,
			ExemplarResult& a_result) noexcept;

		[[nodiscard]] static bool TryGetPotionName(
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
			std::string& a_name) noexcept;

		[[nodiscard]] static bool TryGetPotionWeight(
			std::size_t a_effectCount,
			bool a_hasBeneficial,
			bool a_hasHarmful,
			bool a_hasPurity,
			float& a_weight) noexcept;

		[[nodiscard]] static SavedStateSnapshot SaveStateSnapshot() noexcept;
		static void RestoreStateSnapshot(const SavedStateSnapshot& a_snapshot) noexcept;
		static bool ApplySettingsJson(const nlohmann::json& a_cacoJson) noexcept;
	};
}
