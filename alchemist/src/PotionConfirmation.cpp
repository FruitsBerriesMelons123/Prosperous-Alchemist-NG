#include "PotionConfirmation.h"

#include "AlchemyPlus/AlchemyPlus.h"
#include "CACO/CACO.h"
#include "MenuHandler.h"
#include "ModSettings.h"
#include "PluginPaths.h"
#include "main.h"

#include <Windows.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <exception>
#include <iomanip>
#include <iterator>
#include <limits>
#include <sstream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

namespace alchemist::confirmations
{
	namespace
	{
		constexpr char kFileName[] = "alchemist.potions-confirmed.csv";
		constexpr char kAllFileName[] = "alchemist.potions-confirmed-all.csv";
		constexpr char kObservationFileName[] = "alchemist.potion-observations.csv";
		constexpr std::array<std::string_view, 15> kObservationHeader{
			"session_id",
			"event_sequence",
			"potion_add_index",
			"mode",
			"caco_settings",
			"alchemy_plus_settings",
			"potion_form_id",
			"potion_event_delta",
			"potion_value",
			"potion_cost_override",
			"potion_effects",
			"inventory_event_order",
			"ingredient_event_order",
			"capture_note",
			"ingredient_selection_order"
		};
		constexpr auto kPostMenuDiagnosticCapture = std::chrono::seconds(10);
		constexpr std::array<std::string_view, 20> kHeader{
			"mode",
			"ingredients",
			"actual_value",
			"alchemy_level",
			"fortify_alchemy_level",
			"alchemist_rank",
			"physician",
			"benefactor",
			"poisoner",
			"purity",
			"seeker_of_shadows",
			"concentrated_poison",
			"caco_settings",
			"alchemy_plus_settings",
			"alchemist_perk_multiplier",
			"ingredient_details",
			"potion_form_id",
			"potion_cost_override",
			"crafted_effects",
			"ingredient_selection_order"
		};

		using InventoryCounts = std::unordered_map<std::uint32_t, int>;
		using EvidenceCounts = std::unordered_map<std::uint32_t, std::int64_t>;

		struct InventorySnapshot
		{
			InventoryCounts counts;
			std::unordered_map<std::uint32_t, int> potionValues;
			bool valid = false;
		};

		struct InventoryDelta
		{
			std::uint32_t formID = 0;
			std::int64_t count = 0;
		};

		struct ConsumedIngredient
		{
			std::string name;
			std::uint32_t formID = 0;
			std::int64_t count = 0;
		};

		struct PotionSnapshot
		{
			bool available = false;
			bool hasInventoryValue = false;
			int inventoryValue = 0;
			float costOverride = 0.0f;
			std::string effects = "unavailable";
		};

		struct DiagnosticInventoryEvent
		{
			std::uint64_t sequence = 0;
			std::uint32_t formID = 0;
			std::int64_t delta = 0;
			bool ingredient = false;
			bool alchemyItem = false;
			std::string name;
		};

		struct DiagnosticPotionObservation
		{
			std::uint64_t sessionID = 0;
			std::uint64_t eventSequence = 0;
			std::uint64_t potionAddIndex = 0;
			std::string mode;
			std::string cacoSettings;
			std::string alchemyPlusSettings;
			std::uint32_t formID = 0;
			std::int64_t delta = 0;
			PotionSnapshot snapshot;
			std::string inventoryEventOrder;
			std::string ingredientEventOrder;
			std::string captureNote;
			std::string ingredientSelectionOrder;
		};

		struct PendingInventoryChanges
		{
			EvidenceCounts netDeltas;
			EvidenceCounts removedIngredients;
		};

		InventorySnapshot currentInventory()
		{
			InventorySnapshot snapshot;
			auto* playerCharacter = RE::PlayerCharacter::GetSingleton();
			if (!playerCharacter) {
				return snapshot;
			}

			const auto inventory = playerCharacter->GetInventory();
			for (const auto& [form, entry] : inventory) {
				if (!form || entry.first <= 0) {
					continue;
				}
				if (form->Is(RE::FormType::Ingredient) || form->Is(RE::FormType::AlchemyItem)) {
					snapshot.counts.emplace(form->GetFormID(), entry.first);
				}
				if (form->Is(RE::FormType::AlchemyItem)) {
					const auto* alchemyItem = static_cast<const RE::AlchemyItem*>(form);
					const int value = entry.second ? static_cast<int>(entry.second->GetValue()) : alchemyItem->data.costOverride;
					snapshot.potionValues.emplace(form->GetFormID(), value);
				}
			}
			snapshot.valid = true;
			return snapshot;
		}

		int inventoryCount(const InventoryCounts& a_counts, std::uint32_t a_formID)
		{
			const auto found = a_counts.find(a_formID);
			return found == a_counts.end() ? 0 : found->second;
		}

		bool addEvidenceDelta(EvidenceCounts& a_counts, std::uint32_t a_formID, std::int64_t a_delta)
		{
			if (a_delta == 0) {
				return true;
			}
			auto found = a_counts.find(a_formID);
			const auto current = found == a_counts.end() ? 0 : found->second;
			if ((a_delta > 0 && current > (std::numeric_limits<std::int64_t>::max)() - a_delta) ||
				(a_delta < 0 && current < (std::numeric_limits<std::int64_t>::min)() - a_delta)) {
				return false;
			}
			const auto updated = current + a_delta;
			if (updated == 0) {
				if (found != a_counts.end()) {
					a_counts.erase(found);
				}
			} else {
				a_counts[a_formID] = updated;
			}
			return true;
		}

		std::vector<InventoryDelta> positiveAlchemyDeltas(const PendingInventoryChanges& a_pending)
		{
			std::vector<InventoryDelta> deltas;
			for (const auto& [formID, netDelta] : a_pending.netDeltas) {
				if (netDelta <= 0) {
					continue;
				}
				const auto* form = RE::TESForm::LookupByID(formID);
				if (!form || !form->Is(RE::FormType::AlchemyItem)) {
					continue;
				}
				deltas.push_back({ formID, netDelta });
			}
			std::sort(deltas.begin(), deltas.end(), [](const auto& a_left, const auto& a_right) {
				return a_left.formID < a_right.formID;
			});
			return deltas;
		}

		std::vector<ConsumedIngredient> consumedIngredients(const PendingInventoryChanges& a_pending)
		{
			std::vector<ConsumedIngredient> consumed;
			for (const auto& [formID, removedCount] : a_pending.removedIngredients) {
				const auto* form = RE::TESForm::LookupByID(formID);
				if (!form || !form->Is(RE::FormType::Ingredient)) {
					continue;
				}
				if (removedCount <= 0) {
					continue;
				}
				const auto* ingredient = static_cast<const RE::IngredientItem*>(form);
				const auto* fullName = ingredient->GetFullName();
				if (!fullName || !*fullName) {
					return {};
				}
				consumed.push_back({ fullName, formID, removedCount });
			}
			std::sort(consumed.begin(), consumed.end(), [](const auto& a_left, const auto& a_right) {
				if (a_left.name != a_right.name) {
					return a_left.name < a_right.name;
				}
				return a_left.formID < a_right.formID;
			});
			return consumed;
		}

		std::string mode()
		{
			const bool cacoActive = caco::Adapter::IsActive();
			const bool alchemyPlusActive = alchemyplus::Adapter::IsActive();
			if (cacoActive && alchemyPlusActive) {
				return "CACO+AP";
			}
			if (cacoActive) {
				return "CACO";
			}
			if (alchemyPlusActive) {
				return "AP";
			}
			return "Vanilla";
		}

		std::string formatFloat(float a_value)
		{
			std::ostringstream value;
			value << std::setprecision(std::numeric_limits<float>::max_digits10) << a_value;
			return value.str();
		}

		std::string formatFormID(std::uint32_t a_formID)
		{
			std::ostringstream value;
			value << "0x" << std::uppercase << std::hex << std::setw(8) << std::setfill('0') << a_formID;
			return value.str();
		}

		std::string formatIngredientSelectionOrder(const std::vector<std::uint32_t>& a_formIDs)
		{
			if (a_formIDs.empty()) {
				return "unavailable";
			}

			std::ostringstream details;
			for (std::size_t index = 0; index < a_formIDs.size(); ++index) {
				const auto* form = RE::TESForm::LookupByID(a_formIDs[index]);
				if (!form || !form->Is(RE::FormType::Ingredient)) {
					return "unavailable";
				}
				const auto* ingredient = static_cast<const RE::IngredientItem*>(form);
				const auto* fullName = ingredient->GetFullName();
				if (!fullName || !*fullName) {
					return "unavailable";
				}
				if (index > 0) {
					details << ';';
				}
				details << "selection=" << (index + 1)
						<< "|form_id=" << formatFormID(a_formIDs[index])
						<< "|name=" << *fullName;
			}
			return details.str();
		}

		std::string craftedEffectDetails(const RE::AlchemyItem* a_alchemyItem)
		{
			if (!a_alchemyItem) {
				return {};
			}

			std::ostringstream details;
			std::size_t effectIndex = 0;
			for (const auto* effect : a_alchemyItem->effects) {
				if (!effect || !effect->baseEffect) {
					continue;
				}
				if (effectIndex > 0) {
					details << ';';
				}
				details << "index=" << effectIndex
						<< "|form_id=" << formatFormID(effect->baseEffect->GetFormID())
						<< "|magnitude=" << formatFloat(effect->effectItem.magnitude)
						<< "|duration=" << effect->effectItem.duration
						<< "|area=" << effect->effectItem.area
						<< "|base_cost=" << formatFloat(effect->baseEffect->data.baseCost)
						<< "|flags=" << formatFormID(static_cast<std::uint32_t>(effect->baseEffect->data.flags.get()));
				++effectIndex;
			}
			return details.str();
		}

		PotionSnapshot capturePotionSnapshot(const InventorySnapshot& a_inventory, std::uint32_t a_formID)
		{
			PotionSnapshot snapshot;
			const auto* alchemyItem = RE::TESForm::LookupByID<RE::AlchemyItem>(a_formID);
			if (!alchemyItem) {
				return snapshot;
			}
			snapshot.available = true;
			snapshot.costOverride = alchemyItem->data.costOverride;
			snapshot.effects = craftedEffectDetails(alchemyItem);
			const auto found = a_inventory.potionValues.find(a_formID);
			if (found != a_inventory.potionValues.end()) {
				snapshot.hasInventoryValue = true;
				snapshot.inventoryValue = found->second;
			}
			return snapshot;
		}

		std::string diagnosticEventOrder(const std::vector<DiagnosticInventoryEvent>& a_events, bool a_ingredientsOnly)
		{
			std::ostringstream result;
			bool first = true;
			for (const auto& event : a_events) {
				if (a_ingredientsOnly && !event.ingredient) {
					continue;
				}
				if (!first) {
					result << ';';
				}
				first = false;
				result << "sequence=" << event.sequence
						<< "|form_id=" << formatFormID(event.formID)
						<< "|delta=" << event.delta
						<< "|name=" << event.name;
			}
			return first ? "none" : result.str();
		}

		std::string escapeCsv(std::string_view a_value)
		{
			const bool quote = a_value.find_first_of(",\"\r\n") != std::string_view::npos;
			if (!quote) {
				return std::string(a_value);
			}
			std::string escaped;
			escaped.reserve(a_value.size() + 2);
			escaped.push_back('"');
			for (const char character : a_value) {
				if (character == '"') {
					escaped.push_back('"');
				}
				escaped.push_back(character);
			}
			escaped.push_back('"');
			return escaped;
		}

		std::vector<std::string> parseCsvRecord(std::string_view a_record)
		{
			std::vector<std::string> fields;
			std::string field;
			bool quoted = false;
			for (std::size_t index = 0; index < a_record.size(); ++index) {
				const char character = a_record[index];
				if (quoted) {
					if (character == '"') {
						if (index + 1 < a_record.size() && a_record[index + 1] == '"') {
							field.push_back('"');
							++index;
						} else {
							quoted = false;
						}
					} else {
						field.push_back(character);
					}
					continue;
				}
				if (character == '"' && field.empty()) {
					quoted = true;
				} else if (character == ',') {
					fields.push_back(std::move(field));
					field.clear();
				} else {
					field.push_back(character);
				}
			}
			fields.push_back(std::move(field));
			return fields;
		}

		std::vector<std::vector<std::string>> parseCsv(std::string_view a_contents)
		{
			std::vector<std::vector<std::string>> records;
			std::string record;
			bool quoted = false;
			for (std::size_t index = 0; index < a_contents.size(); ++index) {
				const char character = a_contents[index];
				record.push_back(character);
				if (character == '"') {
					if (quoted && index + 1 < a_contents.size() && a_contents[index + 1] == '"') {
						record.push_back(a_contents[++index]);
					} else {
						quoted = !quoted;
					}
				} else if (character == '\n' && !quoted) {
					record.pop_back();
					if (!record.empty() && record.back() == '\r') {
						record.pop_back();
					}
					if (!record.empty()) {
						records.push_back(parseCsvRecord(record));
					}
					record.clear();
				}
			}
			if (!record.empty()) {
				if (record.back() == '\r') {
					record.pop_back();
				}
				if (!record.empty()) {
					records.push_back(parseCsvRecord(record));
				}
			}
			return records;
		}

		std::vector<std::string> headerFields()
		{
			std::vector<std::string> fields;
			fields.reserve(kHeader.size());
			for (const auto field : kHeader) {
				fields.emplace_back(field);
			}
			return fields;
		}

		bool isCompatibleHeader(const std::vector<std::string>& a_fields)
		{
			return !a_fields.empty() && a_fields.size() <= kHeader.size() &&
				std::equal(a_fields.begin(), a_fields.end(), kHeader.begin(),
					[](const std::string& a_field, std::string_view a_expected) { return a_field == a_expected; });
		}

		bool normalizeRecords(std::vector<std::vector<std::string>>& a_records)
		{
			const auto expectedHeader = headerFields();
			if (a_records.empty()) {
				a_records.push_back(expectedHeader);
				return true;
			}

			if (!isCompatibleHeader(a_records.front())) {
				return false;
			}
			a_records.front() = expectedHeader;
			for (auto record = a_records.begin() + 1; record != a_records.end(); ++record) {
				record->resize(expectedHeader.size());
			}
			return true;
		}

		bool loadRecords(const std::filesystem::path& a_path, std::vector<std::vector<std::string>>& a_records)
		{
			std::error_code error;
			if (!std::filesystem::exists(a_path, error)) {
				if (error) {
					return false;
				}
				a_records.clear();
				return normalizeRecords(a_records);
			}

			std::ifstream input(a_path, std::ios::binary);
			if (!input) {
				return false;
			}
			const std::string contents(
				(std::istreambuf_iterator<char>(input)),
				std::istreambuf_iterator<char>());
			a_records = parseCsv(contents);
			if (!a_records.empty() && !a_records.front().empty()) {
				std::string& firstField = a_records.front().front();
				if (firstField.size() >= 3 &&
					static_cast<unsigned char>(firstField[0]) == 0xEF &&
					static_cast<unsigned char>(firstField[1]) == 0xBB &&
					static_cast<unsigned char>(firstField[2]) == 0xBF) {
					firstField.erase(0, 3);
				}
			}
			return normalizeRecords(a_records);
		}

		bool writeRecords(const std::filesystem::path& a_path, const std::vector<std::vector<std::string>>& a_records)
		{
			const auto temporaryPath = a_path.wstring() + L".tmp";
			std::ofstream output(std::filesystem::path(temporaryPath), std::ios::binary | std::ios::trunc);
			if (!output) {
				return false;
			}
			for (const auto& record : a_records) {
				for (std::size_t index = 0; index < record.size(); ++index) {
					if (index > 0) {
						output << ',';
					}
					output << escapeCsv(record[index]);
				}
				output << '\n';
			}
			output.close();
			if (!output) {
				DeleteFileW(temporaryPath.c_str());
				return false;
			}
			if (!MoveFileExW(
				temporaryPath.c_str(),
				a_path.c_str(),
				MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
				DeleteFileW(temporaryPath.c_str());
				return false;
			}
			return true;
		}

		bool isDuplicateConfirmedRow(const std::vector<std::string>& a_left, const std::vector<std::string>& a_right)
		{
			if (a_left.size() != a_right.size()) {
				return false;
			}
			for (std::size_t index = 0; index < a_left.size(); ++index) {
				if (index < kHeader.size() &&
					(kHeader[index] == "potion_form_id" || kHeader[index] == "potion_cost_override")) {
					continue;
				}
				if (a_left[index] != a_right[index]) {
					return false;
				}
			}
			return true;
		}

		bool appendRows(const std::vector<std::vector<std::string>>& a_rows, std::size_t& a_appendedRowCount)
		{
			a_appendedRowCount = 0;
			if (a_rows.empty()) {
				return true;
			}
			const auto pluginDirectory = paths::GetPluginDirectory();
			if (pluginDirectory.empty()) {
				return false;
			}

			// Append ALL crafted rows unconditionally to alchemist.potions-confirmed-all.csv
			const auto allPath = pluginDirectory / kAllFileName;
			const auto confirmedPath = pluginDirectory / kFileName;
			std::vector<std::vector<std::string>> allRecords;
			loadRecords(allPath, allRecords);
			if (allRecords.size() == 1 && std::filesystem::exists(confirmedPath)) {
				std::vector<std::vector<std::string>> existingConfirmedRecords;
				if (loadRecords(confirmedPath, existingConfirmedRecords) && existingConfirmedRecords.size() > 1) {
					for (std::size_t index = 1; index < existingConfirmedRecords.size(); ++index) {
						allRecords.push_back(existingConfirmedRecords[index]);
					}
				}
			}
			for (const auto& row : a_rows) {
				allRecords.push_back(row);
			}
			writeRecords(allPath, allRecords);

			// Filter duplicates for alchemist.potions-confirmed.csv
			std::vector<std::vector<std::string>> records;
			if (!loadRecords(confirmedPath, records)) {
				return false;
			}
			const auto existingRecordCount = records.size();
			std::size_t duplicateRowCount = 0;
			for (const auto& row : a_rows) {
				if (std::find_if(
						records.begin() + 1,
						records.end(),
						[&row](const auto& record) { return isDuplicateConfirmedRow(record, row); }) != records.end()) {
					++duplicateRowCount;
					continue;
				}
				records.push_back(row);
			}
			a_appendedRowCount = records.size() - existingRecordCount;
			if (a_appendedRowCount == 0) {
				return true;
			}
			if (!writeRecords(confirmedPath, records)) {
				return false;
			}
			return true;
		}

		std::vector<std::string> buildRow(
			const Player& a_player,
			std::string a_ingredients,
			int a_actualValue,
			const ConfirmationSettings& a_settings,
			std::string a_ingredientDetails,
			std::string a_potionFormID,
			std::string a_potionCostOverride,
			std::string a_craftedEffects,
			std::string a_ingredientSelectionOrder)
		{
			return {
				mode(),
				std::move(a_ingredients),
				std::to_string(a_actualValue),
				formatFloat(a_player.alchemyLevel),
				formatFloat(a_player.fortifyAlchemyLevel),
				std::to_string(static_cast<int>(a_player.alchemistPerkLevel)),
				a_player.hasPerkPhysician ? "1" : "0",
				a_player.hasPerkBenefactor ? "1" : "0",
				a_player.hasPerkPoisoner ? "1" : "0",
				a_player.hasPerkPurity ? "1" : "0",
				a_player.hasSeekerOfShadows ? "1" : "0",
				a_player.hasPerkConcentratedPoison ? "1" : "0",
				a_settings.caco,
				a_settings.alchemyPlus,
				formatFloat(a_player.alchemistPerkMultiplier),
				std::move(a_ingredientDetails),
				std::move(a_potionFormID),
				std::move(a_potionCostOverride),
				std::move(a_craftedEffects),
				std::move(a_ingredientSelectionOrder)
			};
		}

		bool sessionActive = false;
		InventorySnapshot sessionBaseline;
		PendingInventoryChanges pendingInventoryChanges;
		std::chrono::steady_clock::time_point lastInventoryEvidence;
		std::vector<DiagnosticInventoryEvent> diagnosticEvents;
		std::vector<DiagnosticPotionObservation> diagnosticObservations;
		std::vector<DiagnosticPotionObservation> diagnosticHistory;
		std::uint64_t diagnosticSessionID = 0;
		std::uint64_t diagnosticEventSequence = 0;
		std::chrono::steady_clock::time_point diagnosticCaptureUntil;

		bool diagnosticCaptureActive() noexcept
		{
			return sessionActive ||
				(diagnosticCaptureUntil != std::chrono::steady_clock::time_point{} &&
					std::chrono::steady_clock::now() < diagnosticCaptureUntil);
		}

		void captureDiagnosticEvent(std::uint32_t a_formID, std::int64_t a_delta, const RE::TESForm* a_form)
		{
			DiagnosticInventoryEvent event;
			event.sequence = ++diagnosticEventSequence;
			event.formID = a_formID;
			event.delta = a_delta;
			event.ingredient = a_form->Is(RE::FormType::Ingredient);
			event.alchemyItem = a_form->Is(RE::FormType::AlchemyItem);
			const auto* name = a_form->GetName();
			event.name = name ? name : "";
			diagnosticEvents.push_back(event);
			if (!event.alchemyItem || a_delta <= 0) {
				return;
			}

			const auto inventory = currentInventory();
			const auto settings = modsettings::GetConfirmationSettings();
			DiagnosticPotionObservation observation;
			observation.sessionID = diagnosticSessionID;
			observation.eventSequence = event.sequence;
			observation.potionAddIndex = static_cast<std::uint64_t>(std::count_if(
				diagnosticEvents.begin(), diagnosticEvents.end(), [](const DiagnosticInventoryEvent& a_event) {
					return a_event.alchemyItem && a_event.delta > 0;
				}));
			observation.mode = mode();
			observation.cacoSettings = settings.caco;
			observation.alchemyPlusSettings = settings.alchemyPlus;
			observation.formID = a_formID;
			observation.delta = a_delta;
			observation.snapshot = capturePotionSnapshot(inventory, a_formID);
			observation.inventoryEventOrder = diagnosticEventOrder(diagnosticEvents, false);
			observation.ingredientEventOrder = diagnosticEventOrder(diagnosticEvents, true);
			observation.captureNote = sessionActive ? "menu_active" : "post_menu_grace";
			observation.ingredientSelectionOrder = formatIngredientSelectionOrder(menu::GetSelectedIngredientFormIDsInSelectionOrder());
			diagnosticObservations.push_back(std::move(observation));
		}

		bool getPotionValue(const InventorySnapshot& a_snapshot, std::uint32_t a_formID, int& a_value)
		{
			const auto found = a_snapshot.potionValues.find(a_formID);
			if (found != a_snapshot.potionValues.end()) {
				a_value = found->second;
				return true;
			}
			const auto* form = RE::TESForm::LookupByID(a_formID);
			if (!form || !form->Is(RE::FormType::AlchemyItem)) {
				return false;
			}
			const auto* alchemyItem = static_cast<const RE::AlchemyItem*>(form);
			a_value = static_cast<int>(alchemyItem->data.costOverride);
			return true;
		}

		void commitInventoryBaseline(const InventorySnapshot& a_after)
		{
			InventorySnapshot committed = a_after;
			for (const auto& [formID, delta] : pendingInventoryChanges.netDeltas) {
				const auto before = static_cast<std::int64_t>(inventoryCount(sessionBaseline.counts, formID));
				const auto expected = before + delta;
				if (expected < 0 || expected > (std::numeric_limits<int>::max)()) {
					continue;
				}
				if (inventoryCount(a_after.counts, formID) == expected) {
					continue;
				}
				if (expected == 0) {
					committed.counts.erase(formID);
					committed.potionValues.erase(formID);
					continue;
				}
				committed.counts[formID] = static_cast<int>(expected);
				if (const auto* form = RE::TESForm::LookupByID(formID); form && form->Is(RE::FormType::AlchemyItem)) {
					int value = 0;
					if (getPotionValue(a_after, formID, value)) {
						committed.potionValues[formID] = value;
					}
				}
			}
			committed.valid = true;
			sessionBaseline = std::move(committed);
			pendingInventoryChanges = {};
			lastInventoryEvidence = {};
		}
	}

	void BeginAlchemySession() noexcept
	{
		if (kDeveloper.GetValue() != 1) {
			sessionActive = false;
			return;
		}
		try {
			for (auto& observation : diagnosticObservations) {
				diagnosticHistory.push_back(std::move(observation));
			}
			diagnosticObservations.clear();
			diagnosticEvents.clear();
			diagnosticSessionID += 1;
			diagnosticEventSequence = 0;
			diagnosticCaptureUntil = {};
			sessionActive = true;
			sessionBaseline = currentInventory();
			pendingInventoryChanges = {};
			lastInventoryEvidence = {};
		} catch (const std::exception&) {
			sessionActive = false;
			sessionBaseline = {};
			pendingInventoryChanges = {};
			diagnosticCaptureUntil = {};
		} catch (...) {
			sessionActive = false;
			sessionBaseline = {};
			pendingInventoryChanges = {};
			lastInventoryEvidence = {};
			diagnosticCaptureUntil = {};
		}
	}

	void EndAlchemySession() noexcept
	{
		sessionActive = false;
		sessionBaseline = {};
		pendingInventoryChanges = {};
		lastInventoryEvidence = {};
		if (kDeveloper.GetValue() == 1) {
			diagnosticCaptureUntil = std::chrono::steady_clock::now() + kPostMenuDiagnosticCapture;
		} else {
			diagnosticCaptureUntil = {};
		}
	}

	bool IsSessionActive() noexcept
	{
		return kDeveloper.GetValue() == 1 && sessionActive;
	}

	bool IsObservationCaptureActive() noexcept
	{
		return kDeveloper.GetValue() == 1 && diagnosticCaptureActive();
	}

	bool IsDrainReady() noexcept
	{
		if (kDeveloper.GetValue() != 1) {
			return false;
		}
		if (!sessionActive || (pendingInventoryChanges.netDeltas.empty() && pendingInventoryChanges.removedIngredients.empty())) {
			return true;
		}
		const auto debounceMs = (std::max)(0, kCraftDebounceMs.GetValue());
		if (debounceMs == 0 || lastInventoryEvidence == std::chrono::steady_clock::time_point{}) {
			return true;
		}
		return std::chrono::steady_clock::now() - lastInventoryEvidence >= std::chrono::milliseconds(debounceMs);
	}

	void ObserveInventoryChange(std::uint32_t a_formID, std::int64_t a_delta) noexcept
	{
		if (kDeveloper.GetValue() != 1) {
			return;
		}
		try {
			if (!diagnosticCaptureActive()) {
				return;
			}
			if (a_delta == 0) {
				return;
			}
			const auto* form = RE::TESForm::LookupByID(a_formID);
			if (!form || (!form->Is(RE::FormType::Ingredient) && !form->Is(RE::FormType::AlchemyItem))) {
				return;
			}
			const auto delta = static_cast<std::int64_t>(a_delta);
			captureDiagnosticEvent(a_formID, delta, form);
			if (!sessionActive) {
				return;
			}
			if (!addEvidenceDelta(pendingInventoryChanges.netDeltas, a_formID, delta)) {
				pendingInventoryChanges = {};
				lastInventoryEvidence = {};
				return;
			}
			if (form->Is(RE::FormType::Ingredient) && delta < 0 &&
				!addEvidenceDelta(pendingInventoryChanges.removedIngredients, a_formID, -delta)) {
				pendingInventoryChanges = {};
				lastInventoryEvidence = {};
				return;
			}
			lastInventoryEvidence = std::chrono::steady_clock::now();
		} catch (const std::exception&) {
		} catch (...) {
		}
	}

	void RecordCraftedPotions(const Player& a_player) noexcept
	{
		if (kDeveloper.GetValue() != 1) {
			return;
		}
		try {
			if (!sessionActive) {
				return;
			}
			const auto after = currentInventory();
			if (!after.valid) {
				return;
			}
			if (!sessionBaseline.valid) {
				sessionBaseline = after;
				return;
			}

			if (pendingInventoryChanges.netDeltas.empty() && pendingInventoryChanges.removedIngredients.empty()) {
				return;
			}
			const auto addedPotions = positiveAlchemyDeltas(pendingInventoryChanges);
			const auto consumed = consumedIngredients(pendingInventoryChanges);
			if (addedPotions.empty() || consumed.empty()) {
				commitInventoryBaseline(after);
				return;
			}
			if (consumed.size() != 2 && consumed.size() != 3) {
				commitInventoryBaseline(after);
				return;
			}

			std::int64_t craftCount = 0;
			for (const auto& potion : addedPotions) {
				if (potion.count > (std::numeric_limits<std::int64_t>::max)() - craftCount) {
					commitInventoryBaseline(after);
					return;
				}
				craftCount += potion.count;
			}
			if (craftCount <= 0) {
				commitInventoryBaseline(after);
				return;
			}
			for (const auto& ingredient : consumed) {
				if (ingredient.count != craftCount) {
					commitInventoryBaseline(after);
					return;
				}
			}

			std::ostringstream ingredients;
			std::ostringstream ingredientDetails;
			for (std::size_t index = 0; index < consumed.size(); ++index) {
				const auto& ingredient = consumed[index];
				if (index > 0) {
					ingredients << ", ";
					ingredientDetails << "; ";
				}
				ingredients << ingredient.name;
				ingredientDetails << ingredient.name << " [form=0x"
					<< std::uppercase << std::hex << std::setw(8) << std::setfill('0') << ingredient.formID
					<< std::dec << std::setfill(' ') << ", count=" << ingredient.count << "]";
			}
			const auto ingredientSelectionOrder = formatIngredientSelectionOrder(menu::GetSelectedIngredientFormIDsInSelectionOrder());

			const auto settings = modsettings::GetConfirmationSettings();
			std::vector<std::vector<std::string>> rows;
			if (static_cast<std::uint64_t>(craftCount) > (std::numeric_limits<std::size_t>::max)()) {
				commitInventoryBaseline(after);
				return;
			}
			rows.reserve(static_cast<std::size_t>(craftCount));
			for (const auto& potion : addedPotions) {
				int value = 0;
				if (!getPotionValue(after, potion.formID, value)) {
					commitInventoryBaseline(after);
					return;
				}

				auto* alchemyItem = RE::TESForm::LookupByID<RE::AlchemyItem>(potion.formID);
				const std::string potionFormID = formatFormID(potion.formID);
				const std::string potionCostOverride = alchemyItem ? formatFloat(alchemyItem->data.costOverride) : std::string{};
				const std::string craftedEffects = craftedEffectDetails(alchemyItem);
				for (std::int64_t count = 0; count < potion.count; ++count) {
					rows.push_back(buildRow(
						a_player,
						ingredients.str(),
						value,
						settings,
						ingredientDetails.str(),
						potionFormID,
						potionCostOverride,
						craftedEffects,
						ingredientSelectionOrder));
				}
			}
			std::size_t appendedRowCount = 0;
			if (appendRows(rows, appendedRowCount)) {
				commitInventoryBaseline(after);
			}
		} catch (const std::exception&) {
		} catch (...) {
		}
	}

	bool ExportPotionObservations() noexcept
	{
		if (kDeveloper.GetValue() != 1) {
			return false;
		}
		try {
			const auto pluginDirectory = paths::GetPluginDirectory();
			if (pluginDirectory.empty()) {
				return false;
			}
			const auto path = pluginDirectory / kObservationFileName;
			std::ofstream output(path, std::ios::binary | std::ios::trunc);
			if (!output) {
				return false;
			}
			for (std::size_t index = 0; index < kObservationHeader.size(); ++index) {
				if (index > 0) {
					output << ',';
				}
				output << kObservationHeader[index];
			}
			output << '\n';

			std::size_t rowCount = 0;
			auto writeObservation = [&output, &rowCount](const DiagnosticPotionObservation& a_observation) {
				const auto& snapshot = a_observation.snapshot;
				const std::vector<std::string> fields{
					std::to_string(a_observation.sessionID),
					std::to_string(a_observation.eventSequence),
					std::to_string(a_observation.potionAddIndex),
					a_observation.mode,
					a_observation.cacoSettings,
					a_observation.alchemyPlusSettings,
					formatFormID(a_observation.formID),
					std::to_string(a_observation.delta),
					snapshot.hasInventoryValue ? std::to_string(snapshot.inventoryValue) : "unavailable",
					snapshot.available ? formatFloat(snapshot.costOverride) : "unavailable",
					snapshot.effects,
					a_observation.inventoryEventOrder,
					a_observation.ingredientEventOrder,
					a_observation.captureNote,
					a_observation.ingredientSelectionOrder
				};
				for (std::size_t index = 0; index < fields.size(); ++index) {
					if (index > 0) {
						output << ',';
					}
					output << escapeCsv(fields[index]);
				}
				output << '\n';
				++rowCount;
			};
			for (const auto& observation : diagnosticHistory) {
				writeObservation(observation);
			}
			for (const auto& observation : diagnosticObservations) {
				writeObservation(observation);
			}
			output.close();
			if (!output) {
				return false;
			}
			return true;
		} catch (const std::exception&) {
			return false;
		} catch (...) {
			return false;
		}
	}

	void DrainPendingConfirmations(const Player& a_player) noexcept
	{
		if (kDeveloper.GetValue() != 1) {
			return;
		}
		try {
			if (!sessionActive) {
				BeginAlchemySession();
				return;
			}
			if (!IsDrainReady()) {
				return;
			}
			RecordCraftedPotions(a_player);
		} catch (const std::exception&) {
		} catch (...) {
		}
	}
}
