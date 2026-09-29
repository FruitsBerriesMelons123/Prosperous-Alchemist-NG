#include "APAFA.h"

#include "PluginUtils.h"
#include "Vanilla/Vanilla.h"

#include <RE/E/EffectSetting.h>
#include <RE/G/GameSettingCollection.h>
#include <RE/T/TESDataHandler.h>
#include <RE/T/TESFile.h>

#include <cmath>
#include <string_view>

namespace alchemist::apafa
{
	namespace
	{
		// APAFA identifies itself with this fixed plugin filename; its BSA and script names are not reliable activation signals.
		constexpr std::string_view kAPAFAPlugin = "AlchemyAdjustments.esp";

		struct State
		{
			bool initialized = false;
			bool detected = false;
			bool active = false;
			std::string pluginName;
			float alchemyIngredientInitMultiplier = 4.0f;
			float alchemySkillFactor = 1.5f;
		};

		State g_state;
	}

	void Adapter::Initialize() noexcept
	{
		g_state = State{};
		g_state.initialized = true;

		if (const auto* file = plugin_utils::FindLoadedPlugin(kAPAFAPlugin)) {
			const auto filename = file->GetFilename();
			g_state.pluginName.assign(filename.data(), filename.size());
			g_state.detected = true;
		}

		if (!g_state.detected) {
			return;
		}

		Refresh();
		g_state.active = true;
	}

	void Adapter::Refresh() noexcept
	{
		if (!g_state.detected) {
			return;
		}

		auto* gmstCollection = RE::GameSettingCollection::GetSingleton();
		if (gmstCollection) {
			auto* initSetting = gmstCollection->GetSetting("fAlchemyIngredientInitMult");
			if (initSetting && std::isfinite(initSetting->GetFloat()) && initSetting->GetFloat() > 0.0f) {
				g_state.alchemyIngredientInitMultiplier = initSetting->GetFloat();
			}
			auto* skillSetting = gmstCollection->GetSetting("fAlchemySkillFactor");
			if (skillSetting && std::isfinite(skillSetting->GetFloat()) && skillSetting->GetFloat() > 0.0f) {
				g_state.alchemySkillFactor = skillSetting->GetFloat();
			}
		}
	}

	bool Adapter::IsDetected() noexcept
	{
		return g_state.detected;
	}

	bool Adapter::IsActive() noexcept
	{
		return g_state.detected && g_state.active;
	}

	float Adapter::GetAlchemySkillFactor() noexcept
	{
		return g_state.alchemySkillFactor;
	}

	float Adapter::GetAlchemyIngredientInitMultiplier() noexcept
	{
		return g_state.alchemyIngredientInitMultiplier;
	}

	void Adapter::SetGameSettings(float a_initMult, float a_skillFactor) noexcept
	{
		if (std::isfinite(a_initMult) && a_initMult > 0.0f) {
			g_state.alchemyIngredientInitMultiplier = a_initMult;
		}
		if (std::isfinite(a_skillFactor) && a_skillFactor > 0.0f) {
			g_state.alchemySkillFactor = a_skillFactor;
		}
	}

	bool Adapter::TryGetSettings(Settings& a_settings) noexcept
	{
		if (!IsActive()) {
			return false;
		}
		a_settings.alchemyIngredientInitMultiplier = g_state.alchemyIngredientInitMultiplier;
		a_settings.alchemySkillFactor = g_state.alchemySkillFactor;
		return true;
	}

	bool Adapter::TryGetAlchemyEffectivenessMultipliers(
		const RE::EffectSetting* a_effect,
		float a_alchemyLevel,
		float a_fallbackAlchemistMultiplier,
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

		return vanilla::Adapter::TryGetAlchemyEffectivenessMultipliers(
			a_effect,
			a_alchemyLevel,
			a_fallbackAlchemistMultiplier,
			a_potion,
			a_includeTypePerks,
			a_mixedPotion,
			a_context,
			a_magnitudeMultiplier,
			a_durationMultiplier);
	}
}
