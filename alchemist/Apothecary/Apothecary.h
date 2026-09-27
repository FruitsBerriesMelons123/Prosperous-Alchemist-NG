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

		inline constexpr std::array<std::string_view, 6> kResistKeywords{
			"MagicAlchResistFire",
			"MagicAlchResistFrost",
			"MagicAlchResistShock",
			"MagicAlchResistMagic",
			"MagicAlchResistPoison",
			"MagicSlow"
		};

		inline constexpr std::array<std::string_view, 1> kReflectKeywords{
			"MAG_MagicAlchReflectDamage"
		};

		inline constexpr std::array<std::string_view, 1> kIllusionKeywords{
			"MAG_MagicAlchIllusionEffect"
		};

		// Fitted against confirmed in-game crafts (see potion_prediction_test.py).
		inline constexpr float kRestoreSlope = 0.00667f;
		inline constexpr float kDamageSlope = 0.0052f;   // was shared with restore
		inline constexpr float kReflectSlope = 0.015f;
		inline constexpr float kIllusionEffectMultiplier = 0.8f;

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
			float a_skillFactor = 1.5f,
			float a_effectPerkMultiplier = 1.0f) noexcept
		{
			if (!std::isfinite(a_alchemyLevel) || a_alchemyLevel < 0.0f) {
				return 1.0f;
			}

			const double skillLevel = static_cast<double>(a_alchemyLevel);
			const double perkMult = (std::isfinite(a_perkMultiplier) && a_perkMultiplier >= 0.0f) ? static_cast<double>(a_perkMultiplier) : 1.0;

			const double base = static_cast<double>(a_initMultiplier) * (1.0 + (static_cast<double>(a_skillFactor) - 1.0) * (skillLevel / 100.0));
			const double mult = base * perkMult;

			const bool isDurationBased = HasKeyword(a_effect, "MagicAlchDurationBased") ||
				(a_effect && a_effect->data.flags.all(RE::EffectSetting::EffectSettingData::Flag::kNoMagnitude));

			double categoryMult = 1.0;
			if (isDurationBased || HasAnyKeyword(a_effect, kSkillKeywords)) {
				categoryMult = 1.0;
			} else if (HasAnyKeyword(a_effect, kResistKeywords)) {
				categoryMult = 1.0;
			} else if (HasAnyKeyword(a_effect, kReflectKeywords)) {
				categoryMult = 1.0 + static_cast<double>(kReflectSlope) * skillLevel;
			} else if (HasAnyKeyword(a_effect, kRestoreKeywords)) {
				categoryMult = 1.0 + static_cast<double>(kRestoreSlope) * skillLevel;      // skill, not skill-15
			} else if (HasAnyKeyword(a_effect, kDamageKeywords)) {
				categoryMult = 1.0 + static_cast<double>(kDamageSlope) * skillLevel;       // split from restore
			} else if (HasAnyKeyword(a_effect, kRegenRateKeywords) || HasAnyKeyword(a_effect, kFortifyAttributeKeywords)) {
				categoryMult = 1.0 + 0.015 * skillLevel;             // unchanged
			} else if (HasAnyKeyword(a_effect, kPowerKeywords)) {
				categoryMult = 1.0;                                   // unchanged
			} else if (HasAnyKeyword(a_effect, kIllusionKeywords)) {
				categoryMult = static_cast<double>(kIllusionEffectMultiplier);              // new
			} else {
				categoryMult = 1.0;                                   // was 1 + 0.0125 * levels
			}

			// Physician / Benefactor / Poisoner / Seeker of Shadows product, computed by the caller
			// because it depends on the effect's beneficial/harmful classification and the potion type.
			const double effectPerkMult = (std::isfinite(a_effectPerkMultiplier) && a_effectPerkMultiplier > 0.0f) ? static_cast<double>(a_effectPerkMultiplier) : 1.0;
			return static_cast<float>(mult * categoryMult * effectPerkMult);
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
			float a_effectPerkMultiplier,
			const EvaluationContext& a_context,
			float& a_magnitudeMultiplier,
			float& a_durationMultiplier) noexcept;
	};
}
