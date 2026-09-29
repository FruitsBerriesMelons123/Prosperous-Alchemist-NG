#include "ModSettings.h"

#include "AlchemyPlus/AlchemyPlus.h"
#include "APAFA/APAFA.h"
#include "Apothecary/Apothecary.h"
#include "CACO/CACO.h"
#include "Requiem/Requiem.h"
#include "Ordinator/Ordinator.h"
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

		SectionValues BuildPlayerValues(const Player& a_player)
		{
			return {
				{ "AlchemyLevel", FormatFloat(a_player.alchemyLevel) },
				{ "FortifyAlchemyLevel", FormatFloat(a_player.fortifyAlchemyLevel) },
				{ "AlchemyPowerModifier", FormatFloat(a_player.alchemyPowerModifier) },
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
				{ "RestoreHealthDuration", FormatFloat(a_settings.restoreHealthDuration) },
				{ "RestoreMagickaDuration", FormatFloat(a_settings.restoreMagickaDuration) },
				{ "RestoreStaminaDuration", FormatFloat(a_settings.restoreStaminaDuration) },
				{ "RestoreEffectsDoNotStack", FormatBool(a_settings.restoreEffectsDoNotStack) },
				{ "DamageHealthDuration", FormatFloat(a_settings.damageHealthDuration) },
				{ "DamageMagickaDuration", FormatFloat(a_settings.damageMagickaDuration) },
				{ "DamageStaminaDuration", FormatFloat(a_settings.damageStaminaDuration) },
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
			if (requiem::Adapter::IsActive()) {
				nlohmann::json reqJson = nlohmann::json::parse(SerializeSectionValues(BuildRequiemValues(a_player)));
				settings.modSettings = reqJson.dump();
			} else if (ordinator::Adapter::IsActive()) {
				nlohmann::json ordinatorJson = nlohmann::json::object();
				ordinatorJson["AdvancedLabType"] = ordinator::Adapter::GetAdvancedLabType();
				ordinatorJson["AdvancedLabActive"] = a_player.ordinatorAdvancedLabActive;
				const auto& attributes = a_player.ordinatorPhysicianAttributes;
				const int attributeCount = static_cast<int>(attributes[0]) + static_cast<int>(attributes[1]) + static_cast<int>(attributes[2]);
				ordinatorJson["PhysicianAttribute"] = attributeCount == 1 ? (attributes[0] ? "Health" : attributes[1] ? "Magicka" : "Stamina") : "";
				// Multiple choice perks can coexist; capture every active attribute.
				const auto physicianAttributes = a_player.ordinatorPhysicianAttributes;
				ordinatorJson["PhysicianAttributes"] = nlohmann::json::array();
				if (physicianAttributes[0]) ordinatorJson["PhysicianAttributes"].push_back("Health");
				if (physicianAttributes[1]) ordinatorJson["PhysicianAttributes"].push_back("Magicka");
				if (physicianAttributes[2]) ordinatorJson["PhysicianAttributes"].push_back("Stamina");
				settings.modSettings = nlohmann::json{ { "ordinator", ordinatorJson } }.dump();
			} else if (apafa::Adapter::IsActive()) {
				nlohmann::json apafaJson = nlohmann::json::object();
				settings.modSettings = apafaJson.dump();
			} else if (apothecary::Adapter::IsActive()) {
				nlohmann::json apotJson = nlohmann::json::object();
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
				settings.modSettings = combined.dump();
			} else if (caco::Adapter::IsActive()) {
				caco::Settings cacoSettings;
				if (caco::Adapter::TryGetSettings(cacoSettings)) {
					nlohmann::json cacoJson = nlohmann::json::parse(SerializeSectionValues(BuildCacoValues(cacoSettings)));
					settings.modSettings = cacoJson.dump();
				}
			} else if (alchemyplus::Adapter::IsActive()) {
				const auto* configuration = alchemyplus::Adapter::GetConfiguration();
				nlohmann::json apJson = nlohmann::json::object();
				if (configuration) {
					apJson = *configuration;
				}
				settings.modSettings = apJson.dump();
			} else {
				nlohmann::json vanillaJson = nlohmann::json::object();
				settings.modSettings = vanillaJson.dump();
			}
			// Engine settings have no dedicated confirmed-CSV columns. Capture the
			// actual pre-craft values once, separately from overhaul-specific options.
			auto payload = nlohmann::json::parse(settings.modSettings);
			if (payload.contains("caco") && payload["caco"].is_object()) {
				payload["caco"].erase("AlchemyIngredientInitMultiplier");
				payload["caco"].erase("AlchemySkillFactor");
			}
			payload.erase("AlchemyIngredientInitMultiplier");
			payload.erase("AlchemySkillFactor");
			payload["engine"] = {
				{ "AlchemyIngredientInitMultiplier", a_player.alchemyIngredientInitMultiplier },
				{ "AlchemySkillFactor", a_player.alchemySkillFactor },
				{ "AlchemyPowerModifier", a_player.alchemyPowerModifier }
			};
			settings.modSettings = payload.dump();
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

