#pragma once

#include <array>
#include <string>

namespace RE
{
	class BGSPerk;
	class EffectSetting;
	class PlayerCharacter;
}

namespace alchemist::ordinator
{
	class Adapter final
	{
	public:
		[[nodiscard]] static bool IsActive() noexcept;
		[[nodiscard]] static int GetAdvancedLabType() noexcept;
		[[nodiscard]] static bool IsAdvancedLabActive(RE::PlayerCharacter* a_player) noexcept;
		[[nodiscard]] static std::string GetPhysicianAttribute(const RE::PlayerCharacter* a_player) noexcept;
		[[nodiscard]] static std::array<bool, 3> GetPhysicianAttributes(const RE::PlayerCharacter* a_player) noexcept;
		[[nodiscard]] static bool IsPhysicianEffect(const RE::EffectSetting* a_effect, const std::array<bool, 3>& a_attributes) noexcept;
		[[nodiscard]] static int GetAlchemyMasteryRank(const RE::PlayerCharacter* a_player) noexcept;
		[[nodiscard]] static bool HasPhysician(const RE::PlayerCharacter* a_player) noexcept;
		[[nodiscard]] static bool HasPoisoner(const RE::PlayerCharacter* a_player) noexcept;
		[[nodiscard]] static bool HasPureMixture(const RE::PlayerCharacter* a_player) noexcept;
		[[nodiscard]] static bool HasMagnumOpus(const RE::PlayerCharacter* a_player) noexcept;
		[[nodiscard]] static float GetMagnumOpusMultiplier(const RE::PlayerCharacter* a_player) noexcept;
		[[nodiscard]] static bool IsPoisonerPerk(const RE::BGSPerk* a_perk) noexcept;
		[[nodiscard]] static bool IsHandledEffectivenessPerk(const RE::BGSPerk* a_perk) noexcept;
		[[nodiscard]] static float GetPoisonerMultiplier(const RE::PlayerCharacter* a_player, float a_alchemyLevel) noexcept;
		[[nodiscard]] static float GetAdvancedLabPotionMultiplier(RE::PlayerCharacter* a_player) noexcept;
	};
}
