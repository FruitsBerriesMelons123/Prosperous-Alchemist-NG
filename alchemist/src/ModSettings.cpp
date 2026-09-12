#include "ModSettings.h"

#include "AlchemyPlus/AlchemyPlus.h"
#include "CACO/CACO.h"
#include "ProfileManager.h"
#include "main.h"

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
				{ "ConcentratedPoison", FormatBool(a_player.hasPerkConcentratedPoison) },
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

		std::string SerializeSectionValues(const SectionValues& a_values)
		{
			nlohmann::json values = nlohmann::json::object();
			for (const auto& [key, value] : a_values) {
				values[key] = value;
			}
			return values.dump();
		}

	}

	ConfirmationSettings GetConfirmationSettings() noexcept
	{
		ConfirmationSettings settings;
		try {
			if (caco::Adapter::IsDetected()) {
				caco::Settings cacoSettings;
				if (caco::Adapter::TryGetSettings(cacoSettings)) {
					settings.caco = SerializeSectionValues(BuildCacoValues(cacoSettings));
				}
			}
			if (alchemyplus::Adapter::IsDetected()) {
				const auto* configuration = alchemyplus::Adapter::GetConfiguration();
				settings.alchemyPlus = configuration ? configuration->dump() : "{}";
			}
		} catch (...) {
		}
		return settings;
	}

	void RefreshAndSynchronize(const Player& a_player) noexcept
	{
		try {
			const auto playerSnapshot = SerializeSectionValues(BuildPlayerValues(a_player));
			std::string cacoSnapshot;
			if (caco::Adapter::IsDetected()) {
				caco::Settings settings;
				if (caco::Adapter::TryGetSettings(settings)) {
					cacoSnapshot = SerializeSectionValues(BuildCacoValues(settings));
				}
			}

			std::string alchemyPlusSnapshot;
			if (alchemyplus::Adapter::IsDetected()) {
				alchemyPlusSnapshot = SerializeSectionValues(BuildAlchemyPlusValues());
			}
			profiles::UpdateExternalSnapshots(playerSnapshot, cacoSnapshot, alchemyPlusSnapshot);
		} catch (...) {
		}
	}
}
