#pragma once

#include "PluginUtils.h"

#include <RE/B/BGSKeyword.h>
#include <RE/E/EffectSetting.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
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

namespace alchemist::apothecary
{
	struct Settings
	{
		float alchemyIngredientInitMultiplier = 4.0f;
		float alchemySkillFactor = 1.5f;
	};

	struct EvaluationContext
	{
		std::vector<const RE::BGSPerk*> activePerks;
		float fortifyAlchemyLevel = 0.0f;
		bool captured = false;
	};

	namespace algorithm
	{
		inline constexpr std::array<std::string_view, 7> kSkillKeywords{
			"MagicAlchFortifyMarksman",
			"MagicAlchFortifyOneHanded",
			"MagicAlchFortifyTwoHanded",
			"MagicAlchFortifyBlock",
			"MagicAlchFortifyUnarmed",
			"MagicAlchFortifySneakAttacks",
			"MagicAlchFortifyPowerAttacks"
		};

		inline constexpr std::array<std::string_view, 5> kPowerKeywords{
			"MagicAlchFortifyAlteration",
			"MagicAlchFortifyConjuration",
			"MagicAlchFortifyDestruction",
			"MagicAlchFortifyIllusion",
			"MagicAlchFortifyRestoration"
		};

		inline constexpr std::array<std::string_view, 3> kRegenRateKeywords{
			"MagicAlchFortifyHealRate",
			"MagicAlchFortifyMagickaRate",
			"MagicAlchFortifyStaminaRate"
		};

		inline constexpr std::array<std::string_view, 3> kFortifyAttributeKeywords{
			"MagicAlchFortifyHealth",
			"MagicAlchFortifyMagicka",
			"MagicAlchFortifyStamina"
		};

		inline constexpr std::array<std::string_view, 3> kRestoreKeywords{
			"MagicAlchRestoreHealth",
			"MagicAlchRestoreMagicka",
			"MagicAlchRestoreStamina"
		};

		inline constexpr std::array<std::string_view, 3> kDamageKeywords{
			"MagicAlchDamageHealth",
			"MagicAlchDamageMagicka",
			"MagicAlchDamageStamina"
		};

		inline bool HasKeyword(const RE::EffectSetting* a_effect, std::string_view a_keyword) noexcept
		{
			if (!a_effect) {
				return false;
			}
			if (a_effect->HasKeywordString(a_keyword)) {
				return true;
			}
			for (std::uint32_t i = 0; i < a_effect->numKeywords; ++i) {
				if (const auto* kw = a_effect->keywords[i]) {
					const auto* editorID = kw->GetFormEditorID();
					if (editorID && plugin_utils::EqualsIgnoreCase(editorID, a_keyword)) {
						return true;
					}
				}
			}
			return false;
		}

		template <std::size_t N>
		inline bool HasAnyKeyword(const RE::EffectSetting* a_effect, const std::array<std::string_view, N>& a_keywords) noexcept
		{
			if (!a_effect) {
				return false;
			}
			for (const auto& kw : a_keywords) {
				if (HasKeyword(a_effect, kw)) {
					return true;
				}
			}
			return false;
		}

		inline float CalculateApothecaryEffectiveness(
			const RE::EffectSetting* a_effect,
			float a_alchemyLevel,
			float a_perkMultiplier = 1.0f,
			float a_initMultiplier = 4.0f,
			float a_skillFactor = 1.5f) noexcept
		{
			if (!std::isfinite(a_alchemyLevel) || a_alchemyLevel < 0.0f) {
				return 1.0f;
			}

			const float skillLevel = a_alchemyLevel;
			const float perkMult = (std::isfinite(a_perkMultiplier) && a_perkMultiplier >= 0.0f) ? a_perkMultiplier : 1.0f;

			const float base = a_initMultiplier * (1.0f + (a_skillFactor - 1.0f) * (skillLevel / 100.0f));
			const float mult = base * perkMult;

			const float levels = std::max(0.0f, skillLevel - 15.0f);

			const bool isDurationBased = HasKeyword(a_effect, "MagicAlchDurationBased") ||
				(a_effect && a_effect->data.flags.all(RE::EffectSetting::EffectSettingData::Flag::kNoMagnitude));

			float categoryMult = 1.0f;
			if (isDurationBased || HasAnyKeyword(a_effect, kSkillKeywords)) {
				categoryMult = 1.0f;
			} else if (HasAnyKeyword(a_effect, kRestoreKeywords) || HasAnyKeyword(a_effect, kDamageKeywords)) {
				categoryMult = 1.0f + 0.00667f * levels;
			} else if (HasAnyKeyword(a_effect, kRegenRateKeywords) || HasAnyKeyword(a_effect, kFortifyAttributeKeywords)) {
				categoryMult = 1.0f + 0.015f * skillLevel;
			} else if (HasAnyKeyword(a_effect, kPowerKeywords)) {
				categoryMult = 1.0f;
			} else {
				categoryMult = 1.0f + 0.0125f * levels;
			}

			return mult * categoryMult;
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
