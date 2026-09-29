#pragma once

#include "PluginUtils.h"
#include "Vanilla/Vanilla.h"

#include <RE/E/EffectSetting.h>

#include <cstdint>
#include <string>

namespace RE
{
	class EffectSetting;
}

namespace alchemist::apafa
{
	struct Settings
	{
		float alchemyIngredientInitMultiplier = 4.0f;
		float alchemySkillFactor = 1.5f;
	};

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

		[[nodiscard]] static bool TryGetAlchemyEffectivenessMultipliers(
			const RE::EffectSetting* a_effect,
			float a_alchemyLevel,
			float a_fallbackAlchemistMultiplier,
			bool a_potion,
			bool a_includeTypePerks,
			bool a_mixedPotion,
			const vanilla::EvaluationContext& a_context,
			float& a_magnitudeMultiplier,
			float& a_durationMultiplier) noexcept;
	};
}
