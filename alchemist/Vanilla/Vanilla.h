#pragma once

#include <cstdint>
#include <string_view>
#include <vector>

namespace RE
{
	class BGSPerk;
	class EffectSetting;
	class SpellItem;
	class TESGlobal;
}

// Skyrim's own alchemy rules, shared by every mode: game-setting effectiveness, perk entry-point
// evaluation, and effect classification. Mod adapters (CACO, Requiem, Apothecary, Alchemy Plus) build on this.
namespace alchemist::vanilla
{
	struct SeekerEvaluationState
	{
		const RE::SpellItem* spell = nullptr;
		const RE::BGSPerk* perk = nullptr;
		const RE::TESGlobal* rewardGlobal = nullptr;
		bool spellListed = false;
		bool spellActive = false;
		std::int32_t perkRank = 0;
		float rewardGlobalValue = 0.0f;
		bool rewardGlobalAvailable = false;
		bool nativeContract = false;
	};

	// The player's alchemy perk state at evaluation time.
	struct EvaluationContext
	{
		std::vector<const RE::BGSPerk*> activePerks;
		SeekerEvaluationState seeker;
		std::int32_t alchemistPerkRank = 0;
		float fortifyAlchemyLevel = 0.0f;
		bool hasPhysician = false;
		bool hasBenefactor = false;
		bool hasPoisoner = false;
		bool hasSeekerOfShadows = false;
		bool hasPurity = false;
		bool captured = false;
	};

	// Lets a mod adapter adjust how the shared perk evaluation treats potion handling. The default
	// (no mod) is plain Skyrim behavior.
	struct PerkPolicy
	{
		bool cacoActive = false;
		bool potionHandlingEnabled = false;
		// A perk (matched by pointer, editor ID or name) whose entry points the mod applies itself.
		const RE::BGSPerk* excludedPerk = nullptr;
		std::string_view excludedPerkName;
	};

	class Adapter final
	{
	public:
		// Reads fAlchemyIngredientInitMult / fAlchemySkillFactor. Returns false if they cannot be read.
		static bool Refresh() noexcept;
		[[nodiscard]] static bool TryGetGameSettings(float& a_initMult, float& a_skillFactor) noexcept;
		[[nodiscard]] static float GetAlchemyIngredientInitMultiplier() noexcept;
		[[nodiscard]] static float GetAlchemySkillFactor() noexcept;
		static void SetGameSettings(float a_initMult, float a_skillFactor) noexcept;
		// Increments whenever a Refresh observes changed game settings.
		[[nodiscard]] static std::uint64_t GetGameSettingsRevision() noexcept;

		[[nodiscard]] static bool HasBeneficialKeyword(const RE::EffectSetting* a_effect) noexcept;
		[[nodiscard]] static bool HasHarmfulKeyword(const RE::EffectSetting* a_effect) noexcept;
		[[nodiscard]] static bool IsDurationBased(const RE::EffectSetting* a_effect) noexcept;

		// Evaluates Skyrim/Alchemy Plus perk entry points without requiring any overhaul mod's records.
		[[nodiscard]] static bool TryGetAlchemyEffectivenessMultipliers(
			const RE::EffectSetting* a_effect,
			float a_alchemyLevel,
			float a_fallbackAlchemistMultiplier,
			bool a_potion,
			bool a_includeTypePerks,
			bool a_mixedPotion,
			const EvaluationContext& a_context,
			float& a_magnitudeMultiplier,
			float& a_durationMultiplier) noexcept;

		// The perk-only multipliers (no game-setting effectiveness), for mods that supply their own base.
		static void GetPerkMultipliers(
			const RE::EffectSetting* a_effect,
			float a_fallback,
			bool a_potion,
			bool a_includeTypePerks,
			bool a_mixedPotion,
			const EvaluationContext& a_context,
			const PerkPolicy& a_policy,
			float& a_magnitudeMultiplier,
			float& a_durationMultiplier) noexcept;
	};
}
