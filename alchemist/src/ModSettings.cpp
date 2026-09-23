#include "ModSettings.h"

#include "AlchemyPlus/AlchemyPlus.h"
#include "Apothecary/Apothecary.h"
#include "CACO/CACO.h"
#include "Requiem/Requiem.h"
#include "ProfileManager.h"
#include "main.h"

#include <RE/G/GameSettingCollection.h>

#include <nlohmann/json.hpp>

#include <iomanip>
#include <limits>
#include <map>
#include <sstream>
#include <string>

namespace alchemist::modsettings
{
	namespace
	{
		using SectionValues = std::map<std::string, std::string>;

		std::string FormatFloat(float a_value)
		{
			std::ostringstream value;
			value << std::setprecision(std::numeric_limits<float>::max_digits10) << a_value;
			return value.str();
		}

		std::string FormatBool(bool a_value)
		{
			return a_value ? "1" : "0";
		}

		float GetActiveIngredientInitMultiplier() noexcept
		{
			if (caco::Adapter::IsActive()) {
				return caco::Adapter::GetAlchemyIngredientInitMultiplier();
			}
			if (requiem::Adapter::IsActive()) {
				return requiem::Adapter::GetAlchemyIngredientInitMultiplier();
			}
			if (apothecary::Adapter::IsActive()) {
				return apothecary::Adapter::GetAlchemyIngredientInitMultiplier();
			}
			auto* collection = RE::GameSettingCollection::GetSingleton();
			if (collection) {
				auto* setting = collection->GetSetting("fAlchemyIngredientInitMult");
				if (setting && setting->GetType() == RE::Setting::Type::kFloat) {
					return setting->GetFloat();
				}
			}
			return 4.0f;
		}

		float GetActiveSkillFactor() noexcept
		{
			if (caco::Adapter::IsActive()) {
				return caco::Adapter::GetAlchemySkillFactor();
			}
			if (requiem::Adapter::IsActive()) {
				return requiem::Adapter::GetAlchemySkillFactor();
			}
			if (apothecary::Adapter::IsActive()) {
				return apothecary::Adapter::GetAlchemySkillFactor();
			}
			auto* collection = RE::GameSettingCollection::GetSingleton();
			if (collection) {
				auto* setting = collection->GetSetting("fAlchemySkillFactor");
				if (setting && setting->GetType() == RE::Setting::Type::kFloat) {
					return setting->GetFloat();
				}
			}
			return 1.5f;
		}

		SectionValues BuildPlayerValues(const Player& a_player)
		{
			return {
				{ "AlchemyLevel", FormatFloat(a_player.alchemyLevel) },
				{ "FortifyAlchemyLevel", FormatFloat(a_player.fortifyAlchemyLevel) },
				{ "AlchemistPerkRank", std::to_string(static_cast<int>(a_player.alchemistPerkLevel)) },
				{ "AlchemistPerkMultiplier", FormatFloat(a_player.alchemistPerkMultiplier) },
				{ "Purity", FormatBool(a_player.hasPerkPurity) },
				{ "Physician", FormatBool(a_player.hasPerkPhysician) },
				{ "Benefactor", FormatBool(a_player.hasPerkBenefactor) },
				{ "Poisoner", FormatBool(a_player.hasPerkPoisoner) },
				{ "SeekerOfShadows", FormatBool(a_player.hasSeekerOfShadows) }
			};
		}

		SectionValues BuildCacoValues(const caco::Settings& a_settings)
		{
			return {
				{ "RestoreHealthDuration", std::to_string(a_settings.restoreHealthDuration) },
				{ "RestoreMagickaDuration", std::to_string(a_settings.restoreMagickaDuration) },
				{ "RestoreStaminaDuration", std::to_string(a_settings.restoreStaminaDuration) },
				{ "RestoreEffectsDoNotStack", FormatBool(a_settings.restoreEffectsDoNotStack) },
				{ "DamageHealthDuration", std::to_string(a_settings.damageHealthDuration) },
				{ "DamageMagickaDuration", std::to_string(a_settings.damageMagickaDuration) },
				{ "DamageStaminaDuration", std::to_string(a_settings.damageStaminaDuration) },
				{ "DisableAllPotionHandling", FormatBool(a_settings.disableAllPotionHandling) },
				{ "AlchemyXPMultiplier", FormatFloat(a_settings.alchemyXPMultiplier) },
				{ "AlchemyIngredientInitMultiplier", FormatFloat(a_settings.alchemyIngredientInitMultiplier) },
				{ "AlchemySkillFactor", FormatFloat(a_settings.alchemySkillFactor) },
				{ "ImpurePotionProcessing", FormatBool(a_settings.impureProcessingEnabled) }
			};
		}

		SectionValues BuildAlchemyPlusValues()
		{
			SectionValues values;
			const auto* configuration = alchemyplus::Adapter::GetConfiguration();
			values.emplace("ConfigurationLoaded", configuration ? "1" : "0");
			values.emplace("Configuration", configuration ? configuration->dump() : "{}");
			return values;
		}

		// Only Requiem's specific perk and keyword mechanics; no duplicate GMST multipliers
		SectionValues BuildRequiemValues(const Player& a_player)
		{
			return {
				{ "AlchemicalLoreRank", std::to_string(a_player.requiemContext.alchemicalLoreRank) },
				{ "HasImprovedElixirs", FormatBool(a_player.requiemContext.hasImprovedElixirs) },
				{ "HasImprovedPoisons", FormatBool(a_player.requiemContext.hasImprovedPoisons) },
				{ "HasPurificationProcess", FormatBool(a_player.requiemContext.hasPurificationProcess) },
				{ "HasUnperkedCraftingKeyword", FormatBool(a_player.requiemContext.hasUnperkedKeyword) }
			};
		}

		std::string SerializeSectionValues(const SectionValues& a_values)
		{
			nlohmann::json values = nlohmann::json::object();
			for (const auto& [key, value] : a_values) {
				values[key] = value;
			}
			return values.dump();
		}
	}

	ConfirmationSettings GetConfirmationSettings(const Player& a_player) noexcept
	{
		ConfirmationSettings settings;
		try {
			const float initMult = GetActiveIngredientInitMultiplier();
			const float skillFactor = GetActiveSkillFactor();

			if (requiem::Adapter::IsActive()) {
				nlohmann::json reqJson = nlohmann::json::parse(SerializeSectionValues(BuildRequiemValues(a_player)));
				reqJson["AlchemyIngredientInitMultiplier"] = initMult;
				reqJson["AlchemySkillFactor"] = skillFactor;
				settings.modSettings = reqJson.dump();
			} else if (apothecary::Adapter::IsActive()) {
				nlohmann::json apotJson = nlohmann::json::object();
				apotJson["AlchemyIngredientInitMultiplier"] = initMult;
				apotJson["AlchemySkillFactor"] = skillFactor;
				settings.modSettings = apotJson.dump();
			} else if (caco::Adapter::IsActive() && alchemyplus::Adapter::IsActive()) {
				nlohmann::json combined = nlohmann::json::object();
				caco::Settings cacoSettings;
				if (caco::Adapter::TryGetSettings(cacoSettings)) {
					combined["caco"] = nlohmann::json::parse(SerializeSectionValues(BuildCacoValues(cacoSettings)));
				}
				const auto* configuration = alchemyplus::Adapter::GetConfiguration();
				if (configuration) {
					combined["alchemyPlus"] = *configuration;
				}
				combined["AlchemyIngredientInitMultiplier"] = initMult;
				combined["AlchemySkillFactor"] = skillFactor;
				settings.modSettings = combined.dump();
			} else if (caco::Adapter::IsActive()) {
				caco::Settings cacoSettings;
				if (caco::Adapter::TryGetSettings(cacoSettings)) {
					nlohmann::json cacoJson = nlohmann::json::parse(SerializeSectionValues(BuildCacoValues(cacoSettings)));
					cacoJson["AlchemyIngredientInitMultiplier"] = initMult;
					cacoJson["AlchemySkillFactor"] = skillFactor;
					settings.modSettings = cacoJson.dump();
				}
			} else if (alchemyplus::Adapter::IsActive()) {
				const auto* configuration = alchemyplus::Adapter::GetConfiguration();
				nlohmann::json apJson = nlohmann::json::object();
				if (configuration) {
					apJson = *configuration;
				}
				apJson["AlchemyIngredientInitMultiplier"] = initMult;
				apJson["AlchemySkillFactor"] = skillFactor;
				settings.modSettings = apJson.dump();
			} else {
				nlohmann::json vanillaJson = nlohmann::json::object();
				vanillaJson["AlchemyIngredientInitMultiplier"] = initMult;
				vanillaJson["AlchemySkillFactor"] = skillFactor;
				settings.modSettings = vanillaJson.dump();
			}
		} catch (...) {
			settings.modSettings = "{}";
		}

		if (settings.modSettings.empty()) {
			settings.modSettings = "{}";
		}
		return settings;
	}

	ConfirmationSettings GetConfirmationSettings() noexcept
	{
		return GetConfirmationSettings(player);
	}

	void RefreshAndSynchronize(const Player& a_player) noexcept
	{
		try {
			const auto playerSnapshot = SerializeSectionValues(BuildPlayerValues(a_player));
			std::string cacoSnapshot;
			if (caco::Adapter::IsActive()) {
				caco::Settings settings;
				if (caco::Adapter::TryGetSettings(settings)) {
					cacoSnapshot = SerializeSectionValues(BuildCacoValues(settings));
				}
			}

			std::string alchemyPlusSnapshot;
			if (alchemyplus::Adapter::IsActive()) {
				alchemyPlusSnapshot = SerializeSectionValues(BuildAlchemyPlusValues());
			}

			std::string requiemSnapshot;
			if (requiem::Adapter::IsActive()) {
				requiemSnapshot = SerializeSectionValues(BuildRequiemValues(a_player));
			}
			profiles::UpdateExternalSnapshots(playerSnapshot, cacoSnapshot, alchemyPlusSnapshot, requiemSnapshot);
		} catch (...) {
		}
	}
}

