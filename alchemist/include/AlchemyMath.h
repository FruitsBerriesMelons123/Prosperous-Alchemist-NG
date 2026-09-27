#pragma once

// Shared, side-effect-free alchemy math used by every calculation path (Vanilla, Alchemy Plus, CACO,
// Requiem and Apothecary). These helpers mirror the value-bearing portions of Skyrim's potion
// construction pipeline so hypothetical recipes can be evaluated off the active menu. Mod-specific
// rules live in their own adapters (e.g. alchemist::caco::algorithm).

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>

namespace alchemist::algorithm
{
	struct EffectInput
	{
		float magnitude = 0.0f;
		float duration = 0.0f;
		bool valid = false;
	};

	struct EffectValue
	{
		float magnitude = 0.0f;
		float duration = 0.0f;
		double cost = 0.0;
		std::int32_t goldValue = 0;
		bool valid = false;
	};

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

	inline constexpr float CalculateAlchemyActorValueMultiplier(float a_fortifyAlchemyLevel) noexcept
	{
		return 1.0f + a_fortifyAlchemyLevel * 0.01f;
	}

	inline constexpr float CalculateVanillaAlchemyEffectiveness(
		float a_alchemyLevel,
		float a_alchemistMultiplier,
		float a_perkMultiplier = 1.0f,
		float a_ingredientInitMultiplier = 4.0f,
		float a_skillFactor = 1.5f) noexcept
	{
		return CalculateAlchemyEffectiveness(a_ingredientInitMultiplier, a_skillFactor, a_alchemyLevel, a_alchemistMultiplier * a_perkMultiplier);
	}

	inline constexpr float CalculateDurationBasedIngredientPowerFactor(float a_effectiveness) noexcept
	{
		return a_effectiveness * 0.01f;
	}

	inline double CalculateEffectCostPrecise(
		float a_baseCost,
		float a_magnitude,
		float a_duration,
		bool a_noMagnitude,
		bool a_noDuration) noexcept
	{
		if (!std::isfinite(a_baseCost) || a_baseCost <= 0.0f) {
			return 0.0f;
		}

		const double magnitude = !a_noMagnitude && std::isfinite(a_magnitude) ?
			(std::max)(1.0, static_cast<double>(a_magnitude)) : 1.0;
		const double duration = !a_noDuration && std::isfinite(a_duration) && a_duration > 0.0f ?
			static_cast<double>(a_duration) / 10.0 : 1.0;
		const double cost = static_cast<double>(a_baseCost) *
			std::pow(magnitude, 1.1) * std::pow(duration, 1.1);
		return std::isfinite(cost) && cost > 0.0 ? cost : 0.0;
	}

	inline EffectInput CalculateEffectInput(
		float a_sourceMagnitude,
		float a_sourceDuration,
		bool a_noMagnitude,
		bool a_noDuration,
		bool a_powerAffectsMagnitude,
		bool a_powerAffectsDuration,
		float a_magnitudePowerFactor,
		float a_durationPowerFactor,
		bool a_allowZeroPowerFactor = false) noexcept
	{
		EffectInput result;
		// Power factors must be finite and positive. Callers may allow exactly 0 (e.g. Requiem without
		// Alchemical Lore or the unperked crafting keyword, which yields magnitude-0 potions).
		const auto invalidFactor = [a_allowZeroPowerFactor](float a_factor) {
			return !std::isfinite(a_factor) || a_factor < 0.0f || (a_factor == 0.0f && !a_allowZeroPowerFactor);
		};
		if ((a_powerAffectsMagnitude && !a_noMagnitude && invalidFactor(a_magnitudePowerFactor)) ||
			(a_powerAffectsDuration && !a_noDuration && invalidFactor(a_durationPowerFactor))) {
			return result;
		}

		result.magnitude = a_noMagnitude ? 0.0f :
			(std::isfinite(a_sourceMagnitude) ? (std::max)(0.0f, a_sourceMagnitude) :
				std::numeric_limits<float>::quiet_NaN());
		if (a_powerAffectsMagnitude && !a_noMagnitude) {
			result.magnitude = std::round(result.magnitude * a_magnitudePowerFactor);
		}

		result.duration = a_noDuration ? 0.0f :
			(!std::isfinite(a_sourceDuration) ? std::numeric_limits<float>::quiet_NaN() :
				(std::max)(0.0f, a_sourceDuration));
		if (a_powerAffectsDuration && !a_noDuration) {
			result.duration = std::round(result.duration * a_durationPowerFactor);
		}

		if ((!a_noMagnitude && !std::isfinite(result.magnitude)) ||
			(!a_noDuration && !std::isfinite(result.duration))) {
			return result;
		}
		result.valid = true;
		return result;
	}

	inline double CalculateEffectContribution(
		float a_baseCost,
		const EffectInput& a_input,
		bool a_noMagnitude,
		bool a_noDuration) noexcept
	{
		if (!a_input.valid ||
			(!a_noMagnitude && !std::isfinite(a_input.magnitude)) ||
			(!a_noDuration && !std::isfinite(a_input.duration))) {
			return 0.0;
		}
		return CalculateEffectCostPrecise(
			a_baseCost, a_input.magnitude, a_input.duration, a_noMagnitude, a_noDuration);
	}

	inline std::int32_t FloorGoldValue(double a_cost) noexcept
	{
		if (!std::isfinite(a_cost) || a_cost <= 0.0) {
			return 0;
		}
		const double maximum = static_cast<double>((std::numeric_limits<std::int32_t>::max)());
		return static_cast<std::int32_t>((std::min)(std::floor(a_cost), maximum));
	}

	inline constexpr bool ShouldRemoveOpposingAlchemyEffect(
		bool a_potion,
		bool a_beneficial,
		bool a_harmful) noexcept
	{
		return a_potion ? a_harmful : a_beneficial;
	}

	inline float CalculateEffectCost(
		float a_baseCost,
		float a_magnitude,
		float a_duration,
		bool a_noMagnitude,
		bool a_noDuration) noexcept
	{
		const double cost = CalculateEffectCostPrecise(
			a_baseCost, a_magnitude, a_duration, a_noMagnitude, a_noDuration);
		return std::isfinite(cost) && cost <= static_cast<double>((std::numeric_limits<float>::max)()) ?
			static_cast<float>(cost) : 0.0f;
	}

	inline EffectValue CalculateEffectValue(
		float a_baseCost,
		const EffectInput& a_input,
		bool a_noMagnitude,
		bool a_noDuration) noexcept
	{
		EffectValue result;
		if (!std::isfinite(a_baseCost) || a_baseCost <= 0.0f) {
			return result;
		}

		const double cost = CalculateEffectContribution(a_baseCost, a_input, a_noMagnitude, a_noDuration);
		if (!std::isfinite(cost) || cost <= 0.0) {
			return result;
		}
		result.magnitude = a_input.magnitude;
		result.duration = a_input.duration;
		result.cost = cost;
		result.goldValue = FloorGoldValue(cost);
		result.valid = true;
		return result;
	}

	inline EffectValue CalculateEffectValue(
		float a_baseCost,
		float a_sourceMagnitude,
		float a_sourceDuration,
		bool a_noMagnitude,
		bool a_noDuration,
		bool a_powerAffectsMagnitude,
		bool a_powerAffectsDuration,
		float a_magnitudePowerFactor,
		float a_durationPowerFactor) noexcept
	{
		EffectValue result;
		if (!std::isfinite(a_baseCost) || a_baseCost <= 0.0f) {
			return result;
		}

		const auto input = CalculateEffectInput(
			a_sourceMagnitude,
			a_sourceDuration,
			a_noMagnitude,
			a_noDuration,
			a_powerAffectsMagnitude,
			a_powerAffectsDuration,
			a_magnitudePowerFactor,
			a_durationPowerFactor);
		return CalculateEffectValue(a_baseCost, input, a_noMagnitude, a_noDuration);
	}

	inline EffectValue CalculateEffectValue(
		float a_baseCost,
		float a_sourceMagnitude,
		float a_sourceDuration,
		bool a_noMagnitude,
		bool a_noDuration,
		bool a_powerAffectsMagnitude,
		bool a_powerAffectsDuration,
		float a_powerFactor) noexcept
	{
		return CalculateEffectValue(
			a_baseCost,
			a_sourceMagnitude,
			a_sourceDuration,
			a_noMagnitude,
			a_noDuration,
			a_powerAffectsMagnitude,
			a_powerAffectsDuration,
			a_powerFactor,
			a_powerFactor);
	}

	inline float CalculateEffectCost(
		float a_baseCost,
		float a_magnitude,
		float a_duration) noexcept
	{
		return CalculateEffectCost(a_baseCost, a_magnitude, a_duration, false, false);
	}

	inline constexpr bool ShouldApplyBenefactor(
		bool a_potion,
		bool a_beneficial,
		bool a_includeTypePerks,
		bool a_mixedPotion = false,
		bool a_disableAllPotionHandling = false) noexcept
	{
		const bool allowsBenefactor = a_potion && (a_disableAllPotionHandling || !a_mixedPotion);
		return a_includeTypePerks && allowsBenefactor && a_beneficial;
	}

	inline constexpr bool ShouldApplyBenefactorFallback(
		bool a_potion,
		bool a_beneficial,
		bool a_includeTypePerks,
		bool a_hasBenefactor,
		bool a_benefactorApplied,
		bool a_benefactorEntryPointFound,
		bool a_mixedPotion = false,
		bool a_disableAllPotionHandling = false) noexcept
	{
		return ShouldApplyBenefactor(a_potion, a_beneficial, a_includeTypePerks, a_mixedPotion, a_disableAllPotionHandling) &&
			a_hasBenefactor && !a_benefactorApplied && !a_benefactorEntryPointFound;
	}

	inline constexpr bool ShouldApplyPhysicianFallback(
		bool a_cacoActive,
		bool a_hasPhysician,
		bool a_physicianApplied,
		bool a_physicianEffect) noexcept
	{
		return !a_cacoActive && a_hasPhysician && !a_physicianApplied && a_physicianEffect;
	}

	inline constexpr bool ShouldApplyPoisoner(
		bool a_potion,
		bool a_harmful,
		bool a_includeTypePerks) noexcept
	{
		return a_includeTypePerks && !a_potion && a_harmful;
	}

	static_assert(CalculateAlchemyEffectiveness(4.0f, 1.5f, 100.0f, 1.0f) > 5.99f);
	static_assert(CalculateAlchemyEffectiveness(4.0f, 1.5f, 100.0f, 1.0f) < 6.01f);
	static_assert(CalculateAlchemyEffectiveness(4.0f, 1.5f, 15.0f, 1.0f) > 4.29f);
	static_assert(CalculateAlchemyEffectiveness(4.0f, 1.5f, 15.0f, 1.0f) < 4.31f);
	static_assert(CalculateAlchemyEffectiveness(3.0f, 3.0f, 15.0f, 1.0f) > 3.89f);
	static_assert(CalculateAlchemyEffectiveness(3.0f, 3.0f, 15.0f, 1.0f) < 3.91f);
	static_assert(CalculateVanillaAlchemyEffectiveness(100.0f, 2.0f) > 11.99f);
	static_assert(CalculateVanillaAlchemyEffectiveness(100.0f, 2.0f) < 12.01f);
	static_assert(CalculateVanillaAlchemyEffectiveness(100.0f, 2.0f, 1.25f) > 14.99f);
	static_assert(CalculateVanillaAlchemyEffectiveness(100.0f, 2.0f, 1.25f) < 15.01f);
	static_assert(CalculateAlchemyActorValueMultiplier(15.0f) > 1.14f);
	static_assert(CalculateAlchemyActorValueMultiplier(15.0f) < 1.16f);
	static_assert(CalculateDurationBasedIngredientPowerFactor(3.9f) > 0.038f);
	static_assert(CalculateDurationBasedIngredientPowerFactor(3.9f) < 0.040f);
	static_assert(ShouldRemoveOpposingAlchemyEffect(true, true, false) == false);
	static_assert(ShouldRemoveOpposingAlchemyEffect(true, false, true) == true);
	static_assert(ShouldRemoveOpposingAlchemyEffect(false, true, false) == true);
	static_assert(ShouldRemoveOpposingAlchemyEffect(false, false, true) == false);
	static_assert(ShouldApplyBenefactor(true, true, true));
	static_assert(!ShouldApplyBenefactor(true, true, true, true));
	static_assert(!ShouldApplyBenefactor(false, true, true));
	static_assert(!ShouldApplyBenefactor(true, false, true));
	static_assert(!ShouldApplyBenefactor(true, true, false));
	static_assert(ShouldApplyBenefactorFallback(true, true, true, true, false, false));
	static_assert(!ShouldApplyBenefactorFallback(true, true, true, true, false, true));
	static_assert(!ShouldApplyBenefactorFallback(true, true, true, true, true, false));
	static_assert(!ShouldApplyBenefactorFallback(true, true, true, true, false, false, true));
	static_assert(ShouldApplyPoisoner(false, true, true));
	static_assert(!ShouldApplyPoisoner(true, true, true));
	static_assert(!ShouldApplyPoisoner(false, false, true));
	static_assert(!ShouldApplyPoisoner(false, true, false));
}
