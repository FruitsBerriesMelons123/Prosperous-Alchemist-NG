#pragma once

#include <cstddef>
#include <cstdint>
#include <cmath>
#include <algorithm>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

namespace RE
{
	class Actor;
	class BGSKeyword;
	class BGSPerk;
	class EffectSetting;
	class TESNPC;
}

namespace alchemist::requiem
{
	struct Settings
	{
		float alchemyIngredientInitMultiplier = 4.0f;
		float alchemySkillFactor = 1.1f;
	};

	struct EvaluationContext
	{
		std::vector<const RE::BGSPerk*> activePerks;
		std::int32_t alchemicalLoreRank = 0;
		float fortifyAlchemyLevel = 0.0f;
		bool hasAlchemicalLore1 = false;
		bool hasAlchemicalLore2 = false;
		bool hasImprovedElixirs = false;
		bool hasImprovedPoisons = false;
		bool hasPurificationProcess = false;
		bool hasUnperkedKeyword = false;
		bool captured = false;
	};

	namespace algorithm
	{
		inline constexpr float CalculateAlchemyEffectiveness(
			float a_ingredientInitMultiplier,
			float a_skillFactor,
			float a_alchemyLevel,
			float a_perkMultiplier) noexcept
		{
			const double skillRatio = static_cast<double>(a_alchemyLevel) / 100.0;
			const double factor = static_cast<double>(a_ingredientInitMultiplier) *
				(1.0 + (static_cast<double>(a_skillFactor) - 1.0) * skillRatio) *
				static_cast<double>(a_perkMultiplier);
			return static_cast<float>(factor);
		}

		inline constexpr float CalculateRequiemEffectiveness(
			float a_alchemyLevel,
			float a_perkMultiplier = 1.0f,
			float a_ingredientInitMultiplier = 4.0f,
			float a_skillFactor = 1.1f) noexcept
		{
			return CalculateAlchemyEffectiveness(a_ingredientInitMultiplier, a_skillFactor, a_alchemyLevel, a_perkMultiplier);
		}
	}

	class Adapter final
	{
	public:
		static void Initialize() noexcept;
		static void Refresh() noexcept;

		[[nodiscard]] static bool IsDetected() noexcept;
		[[nodiscard]] static bool IsActive() noexcept;

		[[nodiscard]] static float GetAlchemySkillFactor() noexcept;
		[[nodiscard]] static float GetAlchemyIngredientInitMultiplier() noexcept;
		static void SetGameSettings(float a_initMult, float a_skillFactor) noexcept;
		[[nodiscard]] static bool TryGetSettings(Settings& a_settings) noexcept;

		[[nodiscard]] static bool HasBeneficialKeyword(const RE::EffectSetting* a_effect) noexcept;
		[[nodiscard]] static bool HasHarmfulKeyword(const RE::EffectSetting* a_effect) noexcept;
		[[nodiscard]] static bool HasRestoreAttributeKeyword(const RE::EffectSetting* a_effect) noexcept;
		[[nodiscard]] static bool HasFortifySkillPenaltyKeyword(const RE::EffectSetting* a_effect) noexcept;
		[[nodiscard]] static bool HasUnperkedCraftingKeyword(const RE::Actor* a_actor) noexcept;

		[[nodiscard]] static bool TryGetAlchemyEffectivenessMultipliers(
			const RE::EffectSetting* a_effect,
			float a_alchemyLevel,
			float a_fallbackAlchemistMultiplier,
			bool a_potion,
			bool a_includeTypePerks,
			const EvaluationContext& a_context,
			float& a_magnitudeMultiplier,
			float& a_durationMultiplier) noexcept;
	};
}
