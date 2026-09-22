#include "IngredientTracker.h"

#include "Localization.h"
#include "main.h"
#include "ProfileManager.h"

#include "RE/B/BGSListForm.h"
#include "RE/B/BGSConstructibleObject.h"
#include "RE/E/Effect.h"
#include "RE/I/IngredientItem.h"
#include "RE/T/TESLevCharacter.h"
#include "RE/T/TESLevItem.h"
#include "RE/T/TESLevSpell.h"
#include "RE/T/TESNPC.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <cctype>
#include <chrono>
#include <limits>
#include <map>
#include <mutex>
#include <optional>
#include <iomanip>
#include <sstream>
#include <set>
#include <string_view>
#include <vector>

namespace alchemist::tracker {
	namespace {
		using json = nlohmann::json;
		constexpr int kUnlimitedProtectionCount = 999;
		constexpr std::size_t kMaxForgeResultNames = 32;
		constexpr std::size_t kMaxForgeResultDepth = 8;
		constexpr std::size_t kMaxForgeResultForms = 256;

		bool IsTrackingEnabled()
		{
			return kProtectIngredients.GetValue() != 0;
		}

		struct StoredRequirement
		{
			std::string key;
			std::string source;
			std::string detail;
			std::string ingredient;
			std::uint32_t ingredientFormID = 0;
			int count = 1;
			bool completed = false;
			bool completionOverridden = false;
			int previousCount = 0;
		};

		std::mutex stateMutex;
		bool stateLoaded = false;
		std::uint64_t nextManualID = 1;
		std::vector<StoredRequirement> manualRequirements;
		std::map<std::string, StoredRequirement> overrides;
		bool selectedEffectsLoaded = false;
		std::vector<std::string> selectedEffectTokens;
		bool selectedEffectCountsLoaded = false;
		std::map<std::string, int> selectedEffectCounts;
		std::vector<Requirement> detectedRequirements;
		std::vector<QuestInfo> detectedQuests;
		std::uint64_t stateRevision = 0;
		std::string statusMessage;

		std::string FoldText(std::string_view a_text)
		{
			std::string result;
			result.reserve(a_text.size());
			for (const auto character : a_text) {
				const auto value = static_cast<unsigned char>(character);
				result.push_back(value < 128 ? static_cast<char>(std::tolower(value)) : character);
			}
			return result;
		}

		std::string TrimText(std::string_view a_text)
		{
			const auto isWhitespace = [](char a_character) {
				return std::isspace(static_cast<unsigned char>(a_character)) != 0;
			};
			std::size_t begin = 0;
			while (begin < a_text.size() && isWhitespace(a_text[begin])) {
				++begin;
			}
			std::size_t end = a_text.size();
			while (end > begin && isWhitespace(a_text[end - 1])) {
				--end;
			}
			return std::string(a_text.substr(begin, end - begin));
		}

		bool IsBoundaryCharacter(unsigned char a_character)
		{
			return std::isalnum(a_character) != 0 || a_character == '_';
		}

		std::size_t FindIngredientName(std::string_view a_text, std::string_view a_name, std::size_t a_start)
		{
			if (a_name.empty() || a_start >= a_text.size()) {
				return std::string::npos;
			}
			const auto foldedText = FoldText(a_text);
			const auto foldedName = FoldText(a_name);
			std::size_t position = foldedText.find(foldedName, a_start);
			while (position != std::string::npos) {
				const bool leftBoundary = position == 0 || !IsBoundaryCharacter(static_cast<unsigned char>(foldedText[position - 1]));
				const auto end = position + foldedName.size();
				const bool rightBoundary = end >= foldedText.size() || !IsBoundaryCharacter(static_cast<unsigned char>(foldedText[end]));
				if (leftBoundary && rightBoundary) {
					return position;
				}
				position = foldedText.find(foldedName, position + 1);
			}
			return std::string::npos;
		}

		int ParseQuantity(std::string_view a_text, std::size_t a_namePosition, std::size_t a_nameLength = 0)
		{
			std::size_t end = a_namePosition;
			while (end > 0 && std::isspace(static_cast<unsigned char>(a_text[end - 1])) != 0) {
				--end;
			}
			std::size_t begin = end;
			while (begin > 0 && std::isdigit(static_cast<unsigned char>(a_text[begin - 1])) != 0) {
				--begin;
			}
			if (begin != end) {
				try {
					return (std::clamp)(std::stoi(std::string(a_text.substr(begin, end - begin))), 1, 999);
				} catch (...) {}
			}

			begin = a_namePosition + a_nameLength;
			while (begin < a_text.size() && std::isspace(static_cast<unsigned char>(a_text[begin])) != 0) {
				++begin;
			}
			if (begin < a_text.size() && (a_text[begin] == 'x' || a_text[begin] == 'X')) {
				++begin;
				while (begin < a_text.size() && std::isspace(static_cast<unsigned char>(a_text[begin])) != 0) {
					++begin;
				}
			}
			end = begin;
			while (end < a_text.size() && std::isdigit(static_cast<unsigned char>(a_text[end])) != 0) {
				++end;
			}
			if (begin != end) {
				try {
					return (std::clamp)(std::stoi(std::string(a_text.substr(begin, end - begin))), 1, 999);
				} catch (...) {}
			}
			return 1;
		}

		std::string FormLabel(const RE::TESForm* a_form)
		{
			if (!a_form) {
				return {};
			}
			if (const auto* editorID = a_form->GetFormEditorID(); editorID && *editorID) {
				return editorID;
			}
			return "0x" + std::to_string(a_form->GetFormID());
		}

		std::string FormDisplayName(const RE::TESForm* a_form)
		{
			if (!a_form) {
				return {};
			}
			if (const auto* name = a_form->GetName(); name && *name) {
				return name;
			}
			return FormLabel(a_form);
		}

		std::string QuestLabel(const RE::TESQuest* a_quest)
		{
			if (a_quest && a_quest->GetFullName() && *a_quest->GetFullName()) {
				return a_quest->GetFullName();
			}
			return FormLabel(a_quest);
		}

		std::string MakeManualKey(std::uint64_t a_id)
		{
			return "manual:" + std::to_string(a_id);
		}

		std::string MakeQuestKey(RE::FormID a_questID, std::uint16_t a_objectiveIndex, RE::FormID a_ingredientID)
		{
			return "quest:" + std::to_string(a_questID) + ":" + std::to_string(a_objectiveIndex) + ":" + std::to_string(a_ingredientID);
		}

		std::string MakeQuestInfoKey(RE::FormID a_questID)
		{
			return "quest-info:" + std::to_string(a_questID);
		}

		std::string MakeConstructibleKey(RE::FormID a_recipeID, RE::FormID a_ingredientID)
		{
			return "constructible:" + std::to_string(a_recipeID) + ":" + std::to_string(a_ingredientID);
		}

		std::string FormIDText(RE::FormID a_formID)
		{
			std::ostringstream stream;
			stream << "0x" << std::uppercase << std::hex << std::setw(8) << std::setfill('0') << a_formID;
			return stream.str();
		}

		struct ForgeRoot
		{
			RE::FormID formID;
			RE::FormID resultFormID;
			std::string_view name;
		};

		struct ForgeIngredientReference
		{
			std::size_t rootIndex = 0;
			std::size_t recipeIndex = 0;
			RE::FormID ingredientFormID = 0;
			std::vector<RE::FormID> listPath;
			std::vector<std::uint32_t> entryPath;
		};

		struct ForgeResolution
		{
			std::vector<ForgeIngredientReference> ingredientReferences;
		};

		constexpr std::array<ForgeRoot, 2> kForgeRoots{ {
			{ 0x000CDE01, 0x000CDE02, "Atronach Forge"sv },
			{ 0x0010F73F, 0x0010F740, "Atronach Forge Sigil Stone"sv }
		} };

		std::string MakeForgeKey(const ForgeRoot& a_root, const ForgeIngredientReference& a_reference)
		{
			std::string key = "forge:" + FormIDText(a_root.formID);
			for (std::size_t index = 0; index < a_reference.listPath.size(); ++index) {
				key += ":" + FormIDText(a_reference.listPath[index]);
				if (index < a_reference.entryPath.size()) {
					key += "@" + std::to_string(a_reference.entryPath[index]);
				}
			}
			key += ":" + FormIDText(a_reference.ingredientFormID);
			return key;
		}

		std::string ForgePathText(const ForgeIngredientReference& a_reference)
		{
			std::string result;
			for (std::size_t index = 0; index < a_reference.listPath.size(); ++index) {
				if (!result.empty()) {
					result += " -> ";
				}
				const auto* list = RE::TESForm::LookupByID(a_reference.listPath[index]);
				result += list ? FormDisplayName(list) : FormIDText(a_reference.listPath[index]);
				result += " (" + FormIDText(a_reference.listPath[index]) + ")";
				if (index < a_reference.entryPath.size()) {
					result += "[" + std::to_string(a_reference.entryPath[index]) + "]";
				}
			}
			return result;
		}

		void ResolveForgeList(
			std::size_t a_rootIndex,
			const RE::BGSListForm* a_list,
			ForgeResolution& a_result,
			std::vector<RE::FormID>& a_listPath,
			std::vector<std::uint32_t>& a_entryPath,
			std::set<RE::FormID>& a_activeLists,
			std::optional<std::size_t> a_recipeIndex = std::nullopt)
		{
			if (!a_list || a_rootIndex >= kForgeRoots.size()) {
				return;
			}

			const auto listFormID = a_list->GetFormID();
			if (!a_activeLists.insert(listFormID).second) {
				return;
			}

			a_listPath.push_back(listFormID);
			std::uint32_t entryIndex = 0;
			a_list->ForEachForm([&](RE::TESForm* a_form) {
				const auto currentEntryIndex = entryIndex++;
				if (!a_form) {
					return RE::BSContainer::ForEachResult::kContinue;
				}

				if (a_form->Is(RE::FormType::FormList)) {
					const auto* nestedList = a_form->As<RE::BGSListForm>();
					if (!nestedList) {
						return RE::BSContainer::ForEachResult::kContinue;
					}
					const auto recipeIndex = a_recipeIndex.value_or(static_cast<std::size_t>(currentEntryIndex));
					a_entryPath.push_back(currentEntryIndex);
					ResolveForgeList(a_rootIndex, nestedList, a_result, a_listPath, a_entryPath, a_activeLists, recipeIndex);
					a_entryPath.pop_back();
					return RE::BSContainer::ForEachResult::kContinue;
				}

				if (!a_form->Is(RE::FormType::Ingredient)) {
					return RE::BSContainer::ForEachResult::kContinue;
				}

				const auto* ingredient = a_form->As<RE::IngredientItem>();
				if (!ingredient) {
					return RE::BSContainer::ForEachResult::kContinue;
				}

				a_entryPath.push_back(currentEntryIndex);
				ForgeIngredientReference reference{
					.rootIndex = a_rootIndex,
					.recipeIndex = a_recipeIndex.value_or(static_cast<std::size_t>(currentEntryIndex)),
					.ingredientFormID = ingredient->GetFormID(),
					.listPath = a_listPath,
					.entryPath = a_entryPath
				};
				a_entryPath.pop_back();
				a_result.ingredientReferences.push_back(std::move(reference));
				return RE::BSContainer::ForEachResult::kContinue;
			});

			a_listPath.pop_back();
			a_activeLists.erase(listFormID);
		}

		ForgeResolution ResolveAtronachForgeLists(RE::TESDataHandler* a_dataHandler)
		{
			ForgeResolution result;
			if (!a_dataHandler) {
				return result;
			}

			for (std::size_t rootIndex = 0; rootIndex < kForgeRoots.size(); ++rootIndex) {
				const auto& root = kForgeRoots[rootIndex];
				const auto* rootForm = RE::TESForm::LookupByID(root.formID);
				if (!rootForm) {
					continue;
				}
				if (!rootForm->Is(RE::FormType::FormList)) {
					continue;
				}
				const auto* rootList = rootForm->As<RE::BGSListForm>();
				if (!rootList) {
					continue;
				}

				std::vector<RE::FormID> listPath;
				std::vector<std::uint32_t> entryPath;
				std::set<RE::FormID> activeLists;
				ResolveForgeList(rootIndex, rootList, result, listPath, entryPath, activeLists);
			}
			return result;
		}

		const RE::TESLeveledList* GetForgeLeveledList(const RE::TESForm* a_form)
		{
			if (!a_form) {
				return nullptr;
			}
			if (const auto* leveledItem = a_form->As<RE::TESLevItem>()) {
				return leveledItem;
			}
			if (const auto* leveledCharacter = a_form->As<RE::TESLevCharacter>()) {
				return leveledCharacter;
			}
			if (const auto* leveledSpell = a_form->As<RE::TESLevSpell>()) {
				return leveledSpell;
			}
			return nullptr;
		}

		std::string ForgeLeafName(const RE::TESForm* a_form)
		{
			if (!a_form) {
				return {};
			}
			if (const auto* npc = a_form->As<RE::TESNPC>()) {
				if (const auto* fullName = npc->GetFullName(); fullName && *fullName) {
					return fullName;
				}
			}
			if (const auto* name = a_form->GetName(); name && *name) {
				return name;
			}
			return {};
		}

		void CollectForgeResultNames(
			const RE::TESForm* a_form,
			std::size_t a_depth,
			std::size_t& a_visitedForms,
			std::vector<std::string>& a_names,
			std::set<std::string>& a_seenNames,
			std::set<RE::FormID>& a_activeLeveledLists,
			std::set<RE::FormID>& a_activeTemplateForms)
		{
			if (!a_form || a_depth > kMaxForgeResultDepth || a_visitedForms >= kMaxForgeResultForms || a_names.size() >= kMaxForgeResultNames) {
				return;
			}
			++a_visitedForms;

			if (const auto* leveledList = GetForgeLeveledList(a_form)) {
				if (a_depth == kMaxForgeResultDepth || !a_activeLeveledLists.insert(a_form->GetFormID()).second) {
					return;
				}
				for (const auto* containedForm : leveledList->GetContainedForms()) {
					CollectForgeResultNames(containedForm, a_depth + 1, a_visitedForms, a_names, a_seenNames, a_activeLeveledLists, a_activeTemplateForms);
					if (a_visitedForms >= kMaxForgeResultForms || a_names.size() >= kMaxForgeResultNames) {
						break;
					}
				}
				a_activeLeveledLists.erase(a_form->GetFormID());
				return;
			}

			const auto name = ForgeLeafName(a_form);
			if (!name.empty()) {
				if (a_seenNames.insert(name).second) {
					a_names.push_back(name);
				}
				return;
			}

			if (const auto* npc = a_form->As<RE::TESNPC>(); npc && npc->baseTemplateForm) {
				const auto npcFormID = a_form->GetFormID();
				if (a_activeTemplateForms.insert(npcFormID).second) {
					CollectForgeResultNames(npc->baseTemplateForm, a_depth + 1, a_visitedForms, a_names, a_seenNames, a_activeLeveledLists, a_activeTemplateForms);
					a_activeTemplateForms.erase(npcFormID);
				}
			}
		}

		std::string ForgeResultFormName(const RE::TESForm* a_form)
		{
			std::vector<std::string> names;
			std::set<std::string> seenNames;
			std::set<RE::FormID> activeLeveledLists;
			std::set<RE::FormID> activeTemplateForms;
			std::size_t visitedForms = 0;
			CollectForgeResultNames(a_form, 0, visitedForms, names, seenNames, activeLeveledLists, activeTemplateForms);

			std::string result;
			for (const auto& name : names) {
				if (!result.empty()) {
					result += ", ";
				}
				result += name;
			}
			return result;
		}

		std::string ForgeResultName(const ForgeRoot& a_root, std::size_t a_recipeIndex)
		{
			const auto* resultForm = RE::TESForm::LookupByID(a_root.resultFormID);
			if (!resultForm || !resultForm->Is(RE::FormType::FormList)) {
				return {};
			}
			const auto* resultList = resultForm->As<RE::BGSListForm>();
			if (!resultList) {
				return {};
			}

			std::size_t resultIndex = 0;
			std::string result;
			resultList->ForEachForm([&](RE::TESForm* a_form) {
				if (resultIndex++ != a_recipeIndex) {
					return RE::BSContainer::ForEachResult::kContinue;
				}
				result = ForgeResultFormName(a_form);
				return RE::BSContainer::ForEachResult::kStop;
			});
			return result;
		}

		std::string MakeEffectKey(RE::FormID a_effectID, RE::FormID a_ingredientID)
		{
			return "effect:" + std::to_string(a_effectID) + ":" + std::to_string(a_ingredientID);
		}

		void LoadSelectedEffectsLocked()
		{
			if (selectedEffectsLoaded) {
				return;
			}
			selectedEffectsLoaded = true;
			for (const auto& token : str::split(kProtectedEffects.GetValue(), ',')) {
				const auto normalizedToken = TrimText(token);
				if (!normalizedToken.empty() && std::none_of(selectedEffectTokens.begin(), selectedEffectTokens.end(), [&normalizedToken](const auto& existing) {
						return FoldText(existing) == FoldText(normalizedToken);
					})) {
					selectedEffectTokens.push_back(normalizedToken);
				}
			}
		}

		void SaveSelectedEffectsLocked()
		{
			std::string value;
			for (const auto& token : selectedEffectTokens) {
				if (!value.empty()) {
					value += ",";
				}
				value += token;
			}
			kProtectedEffects.SetValue(std::move(value));
			profiles::SaveCurrentProfile();
		}

		void LoadSelectedEffectCountsLocked()
		{
			if (selectedEffectCountsLoaded) {
				return;
			}
			selectedEffectCountsLoaded = true;
			for (const auto& token : str::split(kProtectedEffectCounts.GetValue(), ',')) {
				const auto parts = str::split(token, '|');
				if (parts.size() < 2 || parts.front().empty()) {
					continue;
				}
				selectedEffectCounts[parts.front()] = (std::clamp)(str::toInt(parts.at(1)), 1, 999);
			}
		}

		void SaveSelectedEffectCountsLocked()
		{
			std::string value;
			for (const auto& [key, count] : selectedEffectCounts) {
				if (!value.empty()) {
					value += ",";
				}
				value += key + "|" + std::to_string((std::clamp)(count, 1, 999));
			}
			kProtectedEffectCounts.SetValue(std::move(value));
			profiles::SaveCurrentProfile();
		}

		std::vector<EffectInfo> ScanAvailableEffects(RE::TESDataHandler* a_dataHandler)
		{
			std::map<RE::FormID, EffectInfo> effects;
			if (!a_dataHandler) {
				return {};
			}
			for (const auto* ingredient : a_dataHandler->GetFormArray<RE::IngredientItem>()) {
				if (!ingredient) {
					continue;
				}
				for (const auto* effect : ingredient->effects) {
					if (!effect || !effect->baseEffect || !effect->baseEffect->GetFullName() || !*effect->baseEffect->GetFullName()) {
						continue;
					}
					const auto* editorID = effect->baseEffect->GetFormEditorID();
					effects.try_emplace(effect->baseEffect->GetFormID(), EffectInfo{
						.key = FormIDText(effect->baseEffect->GetFormID()),
						.name = effect->baseEffect->GetFullName(),
						.editorID = editorID ? editorID : "",
						.formIDValue = effect->baseEffect->GetFormID()
					});
				}
			}
			std::vector<EffectInfo> result;
			result.reserve(effects.size());
			for (auto& [formID, effect] : effects) {
				result.push_back(std::move(effect));
			}
			std::sort(result.begin(), result.end(), [](const auto& left, const auto& right) {
				return left.name == right.name ? left.key < right.key : left.name < right.name;
			});
			return result;
		}

		bool EffectTokenMatches(const std::string& a_token, const EffectInfo& a_effect)
		{
			const auto trimmedToken = TrimText(a_token);
			const auto token = FoldText(trimmedToken);
			if (token == FoldText(a_effect.key) || token == FoldText(a_effect.name) ||
				(!a_effect.editorID.empty() && token == FoldText(a_effect.editorID))) {
				return true;
			}

			// Magic effect editor IDs like MagicAlchFortifyEnchanting are keywords, not form editor IDs.
			// Match the token against effect keywords by iterating all loaded effects.
			auto* dataHandler = RE::TESDataHandler::GetSingleton();
			if (!dataHandler) {
				return false;
			}

			for (const auto* effectForm : dataHandler->GetFormArray<RE::EffectSetting>()) {
				if (!effectForm || effectForm->GetFormID() != a_effect.formIDValue) {
					continue;
				}

				// Check if this effect has a keyword matching the token
				if (effectForm->HasKeywordString(trimmedToken)) {
					return true;
				}
			}

			return false;
		}

		json ToJson(const StoredRequirement& a_requirement)
		{
			return json{
				{ "key", a_requirement.key },
				{ "source", a_requirement.source },
				{ "detail", a_requirement.detail },
				{ "ingredient", a_requirement.ingredient },
				{ "ingredientFormID", a_requirement.ingredientFormID },
				{ "count", a_requirement.count },
				{ "completed", a_requirement.completed },
				{ "completionOverridden", a_requirement.completionOverridden },
				{ "previousCount", a_requirement.previousCount }
			};
		}

		std::optional<StoredRequirement> FromJson(const json& a_value)
		{
			if (!a_value.is_object() || !a_value.contains("key") || !a_value.contains("ingredient") ||
				!a_value.at("key").is_string() || !a_value.at("ingredient").is_string()) {
				return std::nullopt;
			}
			StoredRequirement result;
			result.key = a_value.at("key").get<std::string>();
			result.source = a_value.value("source", std::string{});
			result.detail = a_value.value("detail", std::string{});
			result.ingredient = a_value.at("ingredient").get<std::string>();
			if (a_value.contains("ingredientFormID") && a_value.at("ingredientFormID").is_number_unsigned()) {
				result.ingredientFormID = a_value.at("ingredientFormID").get<std::uint32_t>();
			}
			result.count = (std::clamp)(a_value.value("count", 1), 1, 999);
			result.completed = a_value.value("completed", false);
			result.completionOverridden = a_value.value("completionOverridden", false);
			const auto previousCount = a_value.value("previousCount", 0);
			result.previousCount = previousCount > 0 ? (std::clamp)(previousCount, 1, kUnlimitedProtectionCount - 1) : 0;
			return result.key.empty() || result.ingredient.empty() ? std::nullopt : std::optional(std::move(result));
		}

		void LoadStateLocked()
		{
			if (stateLoaded) {
				return;
			}
			stateLoaded = true;
			try {
				const auto document = json::parse(kTrackedRequirements.GetValue());
				if (!document.is_object()) {
					return;
				}
				nextManualID = (std::max)(std::uint64_t{ 1 }, document.value("nextManualId", std::uint64_t{ 1 }));
				if (document.contains("manual") && document.at("manual").is_array()) {
					for (const auto& value : document.at("manual")) {
						if (const auto requirement = FromJson(value); requirement && requirement->key.rfind("manual:", 0) == 0) {
							manualRequirements.push_back(*requirement);
						}
					}
				}
				if (document.contains("overrides") && document.at("overrides").is_array()) {
					for (const auto& value : document.at("overrides")) {
						if (const auto requirement = FromJson(value); requirement && requirement->key.rfind("manual:", 0) != 0) {
							overrides[requirement->key] = *requirement;
						}
					}
				}
			} catch (const json::exception&) {
				manualRequirements.clear();
				overrides.clear();
				nextManualID = 1;
			}
		}

		void SaveStateLocked()
		{
			json document{
				{ "nextManualId", nextManualID },
				{ "manual", json::array() },
				{ "overrides", json::array() }
			};
			for (const auto& requirement : manualRequirements) {
				document["manual"].push_back(ToJson(requirement));
			}
			for (const auto& [key, requirement] : overrides) {
				document["overrides"].push_back(ToJson(requirement));
			}
			kTrackedRequirements.SetValue(document.dump());
			profiles::SaveCurrentProfile();
		}

		StoredRequirement ToStored(const Requirement& a_requirement)
		{
			return StoredRequirement{
				.key = a_requirement.key,
				.source = a_requirement.source,
				.detail = a_requirement.detail,
				.ingredient = a_requirement.ingredient,
				.ingredientFormID = a_requirement.ingredientFormID,
				.count = (std::clamp)(a_requirement.count, 1, 999),
				.completed = a_requirement.completed,
				.completionOverridden = a_requirement.completionOverridden,
				.previousCount = a_requirement.count < kUnlimitedProtectionCount ?
					(std::clamp)(a_requirement.count, 1, kUnlimitedProtectionCount - 1) :
					(a_requirement.previousCount > 0 ? (std::clamp)(a_requirement.previousCount, 1, kUnlimitedProtectionCount - 1) : 0)
			};
		}

		Requirement ToRequirement(const StoredRequirement& a_requirement, bool a_automatic, bool a_overridden = false, int a_automaticCount = 0)
		{
			return Requirement{
				.key = a_requirement.key,
				.source = a_requirement.source,
				.detail = a_requirement.detail,
				.ingredient = a_requirement.ingredient,
				.ingredientFormID = a_requirement.ingredientFormID,
				.count = a_requirement.count,
				.completed = a_requirement.completed,
				.automatic = a_automatic,
				.overridden = a_overridden,
				.completionOverridden = a_automatic && a_overridden ? a_requirement.completionOverridden : false,
				.automaticCount = a_automaticCount,
				.previousCount = a_requirement.previousCount
			};
		}

		std::vector<Requirement> GetRequirementsLocked()
		{
			std::vector<Requirement> result;
			result.reserve(detectedRequirements.size() + manualRequirements.size());
			for (const auto& detected : detectedRequirements) {
				if (const auto overrideIt = overrides.find(detected.key); overrideIt != overrides.end()) {
					auto requirement = ToRequirement(overrideIt->second, true, true, detected.count);
					if (requirement.ingredientFormID == 0) {
						requirement.ingredientFormID = detected.ingredientFormID;
					}
					result.push_back(std::move(requirement));
				} else {
					auto requirement = detected;
					requirement.automaticCount = detected.count;
					result.push_back(std::move(requirement));
				}
			}
			for (const auto& manual : manualRequirements) {
				result.push_back(ToRequirement(manual, false));
			}
			return result;
		}

		struct IngredientCandidate
		{
			RE::FormID formID = 0;
			std::string name;
		};

		std::vector<IngredientCandidate> GetIngredientCandidates(RE::TESDataHandler* a_dataHandler)
		{
			std::vector<IngredientCandidate> candidates;
			if (!a_dataHandler) {
				return candidates;
			}
			for (const auto* ingredient : a_dataHandler->GetFormArray<RE::IngredientItem>()) {
				if (ingredient && ingredient->GetFullName() && *ingredient->GetFullName()) {
					candidates.push_back({ ingredient->GetFormID(), ingredient->GetFullName() });
				}
			}
			std::sort(candidates.begin(), candidates.end(), [](const auto& left, const auto& right) {
				return left.name.size() == right.name.size() ? left.name < right.name : left.name.size() > right.name.size();
			});
			return candidates;
		}

		std::vector<QuestInfo> ScanQuestInfo(RE::TESDataHandler* a_dataHandler)
		{
			std::vector<QuestInfo> result;
			if (!a_dataHandler) {
				return result;
			}
			for (auto* quest : a_dataHandler->GetFormArray<RE::TESQuest>()) {
				if (!quest) {
					continue;
				}
			QuestInfo info{
				.key = MakeQuestInfoKey(quest->GetFormID()),
				.title = QuestLabel(quest),
				.formIDValue = quest->GetFormID(),
				.formID = FormIDText(quest->GetFormID()),
				.editorID = quest->GetFormEditorID() ? quest->GetFormEditorID() : "",
				.modName = quest->GetFile(0) ? std::string(quest->GetFile(0)->GetFilename()) : std::string{},
				.typeID = static_cast<std::uint8_t>(quest->data.questType.get()),
				.currentStage = quest->GetCurrentStageID(),
				.running = quest->IsRunning(),
				.active = quest->IsActive(),
				.completed = quest->IsCompleted()
			};
			if (quest->executedStages) {
				for (const auto& stage : *quest->executedStages) {
					info.stages.push_back(QuestStage{
						.index = stage.data.index,
						.executed = true,
						.startUp = stage.data.flags.any(RE::QUEST_STAGE_DATA::Flag::kStartUpStage),
						.shutDown = stage.data.flags.any(RE::QUEST_STAGE_DATA::Flag::kShutDownStage)
					});
				}
			}
			if (quest->waitingStages) {
				for (const auto* stage : *quest->waitingStages) {
					if (!stage) {
						continue;
					}
					info.stages.push_back(QuestStage{
						.index = stage->data.index,
						.executed = false,
						.startUp = stage->data.flags.any(RE::QUEST_STAGE_DATA::Flag::kStartUpStage),
						.shutDown = stage->data.flags.any(RE::QUEST_STAGE_DATA::Flag::kShutDownStage)
					});
				}
			}
			std::stable_sort(info.stages.begin(), info.stages.end(), [](const auto& left, const auto& right) {
				return left.index < right.index;
			});
			info.stages.erase(std::unique(info.stages.begin(), info.stages.end(), [](const auto& left, const auto& right) {
				return left.index == right.index;
			}), info.stages.end());
			std::uint32_t objectiveNumber = 0;
			for (auto iterator = quest->objectives.begin(); iterator != quest->objectives.end(); ++iterator) {
				const auto* objective = *iterator;
				if (!objective) {
					++objectiveNumber;
					continue;
				}
				const auto state = static_cast<std::uint32_t>(objective->state.underlying());
				info.objectives.push_back(QuestObjective{
					.index = objectiveNumber,
					.text = objective->displayText.c_str() ? objective->displayText.c_str() : "",
					.state = state,
					.completed = state == static_cast<std::uint32_t>(RE::QUEST_OBJECTIVE_STATE::kCompleted) ||
						state == static_cast<std::uint32_t>(RE::QUEST_OBJECTIVE_STATE::kCompletedDisplayed) ||
						state == static_cast<std::uint32_t>(RE::QUEST_OBJECTIVE_STATE::kFailed) ||
						state == static_cast<std::uint32_t>(RE::QUEST_OBJECTIVE_STATE::kFailedDisplayed),
					.dormant = state == static_cast<std::uint32_t>(RE::QUEST_OBJECTIVE_STATE::kDormant)
				});
				++objectiveNumber;
			}
			result.push_back(std::move(info));
			}
			std::sort(result.begin(), result.end(), [](const auto& left, const auto& right) {
				return left.title == right.title ? left.formID < right.formID : left.title < right.title;
			});
			return result;
		}

		std::vector<Requirement> ScanQuestObjectives(RE::TESDataHandler* a_dataHandler, const std::vector<IngredientCandidate>& a_candidates)
		{
			std::vector<Requirement> result;
			if (!a_dataHandler) {
				return result;
			}
			for (auto* quest : a_dataHandler->GetFormArray<RE::TESQuest>()) {
				if (!quest) {
					continue;
				}
				const auto source = QuestLabel(quest);
				std::size_t objectiveNumber = 0;
				for (auto iterator = quest->objectives.begin(); iterator != quest->objectives.end(); ++iterator) {
					const auto* objective = *iterator;
					if (!objective || !objective->displayText.c_str() || !*objective->displayText.c_str()) {
						++objectiveNumber;
						continue;
					}
					const std::string objectiveText = objective->displayText.c_str();
					std::string detail = "Quest FormID: " + FormIDText(quest->GetFormID()) + "; objective " + std::to_string(objectiveNumber) + "; text: " + objectiveText;
					if (const auto* editorID = quest->GetFormEditorID(); editorID && *editorID) {
						detail += "; editor ID: ";
						detail += editorID;
					}
					const bool objectiveCompleted = quest->IsCompleted() ||
						objective->state.any(RE::QUEST_OBJECTIVE_STATE::kCompleted, RE::QUEST_OBJECTIVE_STATE::kCompletedDisplayed,
							RE::QUEST_OBJECTIVE_STATE::kFailed, RE::QUEST_OBJECTIVE_STATE::kFailedDisplayed);
					for (const auto& candidate : a_candidates) {
						const auto matchPosition = FindIngredientName(objectiveText, candidate.name, 0);
						if (matchPosition == std::string::npos) {
							continue;
						}
						result.push_back(Requirement{
							.key = MakeQuestKey(quest->GetFormID(), static_cast<std::uint16_t>(objectiveNumber), candidate.formID),
							.source = source,
							.detail = detail,
							.ingredient = candidate.name,
							.ingredientFormID = candidate.formID,
							.count = ParseQuantity(objectiveText, matchPosition, candidate.name.length()),
							.completed = objectiveCompleted,
							.automatic = true
						});
					}
					++objectiveNumber;
				}
			}
			return result;
		}

		std::vector<Requirement> ScanConstructibleRecipes(RE::TESDataHandler* a_dataHandler, const std::vector<IngredientCandidate>& a_candidates)
		{
			std::vector<Requirement> result;
			if (!a_dataHandler) {
				return result;
			}
			for (const auto* recipe : a_dataHandler->GetFormArray<RE::BGSConstructibleObject>()) {
				if (!recipe) {
					continue;
				}
				const auto benchName = recipe->benchKeyword ? FormDisplayName(recipe->benchKeyword) : std::string{};
				const std::string benchEditorID = recipe->benchKeyword && recipe->benchKeyword->GetFormEditorID() ? recipe->benchKeyword->GetFormEditorID() : std::string{};
				if (!recipe->createdItem || recipe->requiredItems.numContainerObjects == 0) {
					continue;
				}
				const auto createdName = FormDisplayName(recipe->createdItem);
				const std::uint32_t outputCount = (std::max)(std::uint32_t{ 1 }, static_cast<std::uint32_t>(recipe->data.numConstructed));
				const std::uint32_t craftsForOne = (1u + outputCount - 1u) / outputCount;
				for (std::uint32_t index = 0; index < recipe->requiredItems.numContainerObjects; ++index) {
					const auto* required = recipe->requiredItems.containerObjects[index];
					if (!required || !required->obj || !required->obj->Is(RE::FormType::Ingredient)) {
						continue;
					}
					const auto* ingredient = static_cast<const RE::IngredientItem*>(required->obj);
					const auto candidate = std::find_if(a_candidates.begin(), a_candidates.end(), [ingredient](const auto& value) {
						return value.formID == ingredient->GetFormID();
					});
					if (candidate == a_candidates.end()) {
						continue;
					}
					const std::uint32_t requiredCount = (std::max)(std::uint32_t{ 1 }, static_cast<std::uint32_t>(required->count));
					const std::uint32_t count = (std::min)(std::uint32_t{ 999 }, requiredCount * craftsForOne);
					std::string detail = "Recipe FormID: " + FormIDText(recipe->GetFormID()) + "; created item: " + createdName +
						"; outputs per craft: " + std::to_string(outputCount);
					if (!benchName.empty()) {
						detail += "; bench: " + benchName;
						if (!benchEditorID.empty()) {
							detail += " (" + benchEditorID + ")";
						}
					}
					result.push_back(Requirement{
						.key = MakeConstructibleKey(recipe->GetFormID(), ingredient->GetFormID()),
						.source = localization::Format("tracking.sourceCrafting", "Crafting: {name}", { { "name", createdName } }),
						.detail = std::move(detail),
						.ingredient = candidate->name,
						.ingredientFormID = candidate->formID,
						.count = static_cast<int>(count),
						.completed = false,
						.automatic = true
					});
				}
			}
			return result;
		}

		std::vector<Requirement> ScanIngredientEffects(RE::TESDataHandler* a_dataHandler, const std::vector<EffectInfo>& a_effects)
		{
			std::vector<Requirement> result;
			if (!a_dataHandler || a_effects.empty()) {
				return result;
			}
			for (const auto* ingredient : a_dataHandler->GetFormArray<RE::IngredientItem>()) {
				if (!ingredient || !ingredient->GetFullName() || !*ingredient->GetFullName()) {
					continue;
				}
				for (const auto& selectedEffect : a_effects) {
					const auto found = std::find_if(ingredient->effects.begin(), ingredient->effects.end(), [&selectedEffect](const auto* effect) {
						return effect && effect->baseEffect && effect->baseEffect->GetFormID() == selectedEffect.formIDValue;
					});
					if (found == ingredient->effects.end()) {
						continue;
					}
					result.push_back(Requirement{
						.key = MakeEffectKey(selectedEffect.formIDValue, ingredient->GetFormID()),
						.source = localization::Format("tracking.sourceEffect", "Ingredient effect: {name}", { { "name", selectedEffect.name } }),
						.detail = "Effect FormID: " + selectedEffect.key + (selectedEffect.editorID.empty() ? std::string{} : "; editor ID: " + selectedEffect.editorID),
						.ingredient = ingredient->GetFullName(),
						.ingredientFormID = ingredient->GetFormID(),
						.count = (selectedEffect.protectedCount > 0 ? selectedEffect.protectedCount : kUnlimitedProtectionCount),
						.completed = false,
						.automatic = true
					});
				}
			}
			return result;
		}

		bool QuestObjectivesEqual(const QuestInfo& a_left, const QuestInfo& a_right)
		{
			if (a_left.key != a_right.key || a_left.title != a_right.title || a_left.formIDValue != a_right.formIDValue ||
				a_left.formID != a_right.formID || a_left.editorID != a_right.editorID || a_left.modName != a_right.modName ||
				a_left.typeID != a_right.typeID || a_left.currentStage != a_right.currentStage || a_left.running != a_right.running ||
				a_left.active != a_right.active || a_left.completed != a_right.completed || a_left.stages.size() != a_right.stages.size() ||
				a_left.objectives.size() != a_right.objectives.size()) {
				return false;
			}
			if (!std::equal(a_left.stages.begin(), a_left.stages.end(), a_right.stages.begin(), [](const auto& left, const auto& right) {
				return left.index == right.index && left.executed == right.executed && left.startUp == right.startUp && left.shutDown == right.shutDown;
			})) {
				return false;
			}
			return std::equal(a_left.objectives.begin(), a_left.objectives.end(), a_right.objectives.begin(), [](const auto& left, const auto& right) {
				return left.index == right.index && left.text == right.text && left.state == right.state &&
					left.completed == right.completed && left.dormant == right.dormant;
			});
		}

		std::vector<Requirement> ScanAtronachForgeRecipes(RE::TESDataHandler* a_dataHandler, const std::vector<IngredientCandidate>& a_candidates)
		{
			std::vector<Requirement> result;
			auto resolution = ResolveAtronachForgeLists(a_dataHandler);
			for (const auto& reference : resolution.ingredientReferences) {
				if (reference.rootIndex >= kForgeRoots.size()) {
					continue;
				}
				const auto& root = kForgeRoots[reference.rootIndex];
				const auto candidate = std::find_if(a_candidates.begin(), a_candidates.end(), [&reference](const auto& value) {
					return value.formID == reference.ingredientFormID;
				});
				const auto key = MakeForgeKey(root, reference);
				if (candidate == a_candidates.end()) {
					continue;
				}

				const auto path = ForgePathText(reference);
				const auto resultName = ForgeResultName(root, reference.recipeIndex);
				const auto source = resultName.empty() ?
					localization::Translate("tracking.sourceForgeDefault", "Atronach Forge") :
					localization::Format("tracking.sourceForge", "Atronach Forge: {name}", { { "name", resultName } });
				const auto detail = "Root: " + std::string(root.name) + " (" + FormIDText(root.formID) + "); result: " +
					(resultName.empty() ? std::string("unavailable") : resultName) + "; recipe path: " + path +
					"; selected ingredient: " + candidate->name + " (" + FormIDText(reference.ingredientFormID) + ")";
				result.push_back(Requirement{
					.key = key,
					.source = source,
					.detail = detail,
					.ingredient = candidate->name,
					.ingredientFormID = candidate->formID,
					.count = 1,
					.completed = false,
					.automatic = true
				});
			}
			return result;
		}

		void SetStatus(std::string a_status)
		{
			std::scoped_lock lock(stateMutex);
			statusMessage = std::move(a_status);
		}

		bool DispatchQuestMethod(
			RE::TESQuest* a_quest,
			std::string_view a_function,
			RE::BSScript::IFunctionArguments* a_arguments,
			std::string& a_error)
		{
			auto* vm = RE::BSScript::Internal::VirtualMachine::GetSingleton();
			auto* policy = vm ? vm->GetObjectHandlePolicy() : nullptr;
			if (!vm || !policy) {
				a_error = "Papyrus VM unavailable";
				return false;
			}
			const auto handle = policy->GetHandleForObject(static_cast<RE::VMTypeID>(RE::FormType::Quest), a_quest);
			if (handle == policy->EmptyHandle()) {
				a_error = "Could not obtain a VM handle for the quest";
				return false;
			}
			RE::BSTSmartPointer<RE::BSScript::IStackCallbackFunctor> callback;
			if (!vm->DispatchMethodCall(handle, "Quest"sv, a_function, a_arguments, callback)) {
				a_error = "VM rejected the call";
				return false;
			}
			return true;
		}

		void DoSetQuestStage(std::uint32_t a_formID, std::uint16_t a_stage, bool a_force)
		{
			if (!IsTrackingEnabled() || kDeveloper.GetValue() != 1) {
				return;
			}
			auto* quest = RE::TESForm::LookupByID<RE::TESQuest>(a_formID);
			if (!quest) {
				SetStatus("Quest " + FormIDText(a_formID) + " no longer exists");
				return;
			}
			const auto currentStage = quest->GetCurrentStageID();
			if (!quest->IsRunning() && !a_force) {
				SetStatus("Quest is not running - enable Force to set the stage anyway");
				return;
			}
			if (currentStage == a_stage) {
				SetStatus("Quest is already at stage " + std::to_string(a_stage));
				return;
			}
			if (a_stage < currentStage && !a_force) {
				SetStatus("Stage " + std::to_string(a_stage) + " is lower than the current stage - enable Force to allow regression");
				return;
			}

			std::string error;
			if (!DispatchQuestMethod(quest, "SetStage"sv, RE::MakeFunctionArguments(static_cast<std::int32_t>(a_stage)), error)) {
				SetStatus(error);
				return;
			}
			SetStatus("Stage " + std::to_string(a_stage) + " requested for " + FormIDText(a_formID));
			RefreshDetection();
		}

		void DoSetQuestObjective(std::uint32_t a_formID, std::uint16_t a_objective, ObjectiveAction a_action)
		{
			if (!IsTrackingEnabled() || kDeveloper.GetValue() != 1) {
				return;
			}
			auto* quest = RE::TESForm::LookupByID<RE::TESQuest>(a_formID);
			if (!quest) {
				SetStatus("Quest " + FormIDText(a_formID) + " no longer exists");
				return;
			}

			std::string_view function;
			std::string_view verb;
			RE::BSScript::IFunctionArguments* arguments = nullptr;
			switch (a_action) {
			case ObjectiveAction::kShow:
				function = "SetObjectiveDisplayed"sv;
				arguments = RE::MakeFunctionArguments(static_cast<std::int32_t>(a_objective), true, true);
				verb = "shown"sv;
				break;
			case ObjectiveAction::kHide:
				function = "SetObjectiveDisplayed"sv;
				arguments = RE::MakeFunctionArguments(static_cast<std::int32_t>(a_objective), false, true);
				verb = "hidden"sv;
				break;
			case ObjectiveAction::kComplete:
				function = "SetObjectiveCompleted"sv;
				arguments = RE::MakeFunctionArguments(static_cast<std::int32_t>(a_objective), true);
				verb = "completed"sv;
				break;
			case ObjectiveAction::kFail:
				function = "SetObjectiveFailed"sv;
				arguments = RE::MakeFunctionArguments(static_cast<std::int32_t>(a_objective), true);
				verb = "failed"sv;
				break;
			default:
				return;
			}

			std::string error;
			if (!DispatchQuestMethod(quest, function, arguments, error)) {
				SetStatus(error);
				return;
			}
			SetStatus("Objective " + std::to_string(a_objective) + " " + std::string(verb));
			RefreshDetection();
		}

		std::vector<Requirement> ScanDetectedRequirements()
		{
			auto* dataHandler = RE::TESDataHandler::GetSingleton();
			const auto candidates = GetIngredientCandidates(dataHandler);
			auto result = ScanQuestObjectives(dataHandler, candidates);
			const auto effects = GetEffects();
			std::vector<EffectInfo> selectedEffects;
			std::copy_if(effects.begin(), effects.end(), std::back_inserter(selectedEffects), [](const auto& effect) {
				return effect.selected;
			});
			auto craftRequirements = ScanConstructibleRecipes(dataHandler, candidates);
			result.insert(result.end(), craftRequirements.begin(), craftRequirements.end());
			auto forgeRequirements = ScanAtronachForgeRecipes(dataHandler, candidates);
			result.insert(result.end(), forgeRequirements.begin(), forgeRequirements.end());
			auto effectRequirements = ScanIngredientEffects(dataHandler, selectedEffects);
			result.insert(result.end(), effectRequirements.begin(), effectRequirements.end());
			return result;
		}

		bool RequirementsEqual(const Requirement& a_left, const Requirement& a_right)
		{
			return a_left.key == a_right.key && a_left.source == a_right.source && a_left.detail == a_right.detail &&
				a_left.ingredient == a_right.ingredient && a_left.ingredientFormID == a_right.ingredientFormID &&
				a_left.count == a_right.count && a_left.completed == a_right.completed;
		}
	}

	std::string GetIngredientKey(std::uint32_t a_formID)
	{
		return a_formID == 0 ? std::string{} : "formid:" + FormIDText(a_formID);
	}

	bool RefreshDetection()
	{
		if (!IsTrackingEnabled()) {
			return false;
		}
		auto detected = ScanDetectedRequirements();
		auto quests = kDeveloper.GetValue() == 1 ?
			ScanQuestInfo(RE::TESDataHandler::GetSingleton()) :
			std::vector<QuestInfo>{};
		std::scoped_lock lock(stateMutex);
		LoadStateLocked();
		const bool changed = detected.size() != detectedRequirements.size() ||
			!std::equal(detected.begin(), detected.end(), detectedRequirements.begin(), RequirementsEqual);
		detectedRequirements = std::move(detected);
		const bool questsChanged = quests.size() != detectedQuests.size() ||
			!std::equal(quests.begin(), quests.end(), detectedQuests.begin(), QuestObjectivesEqual);
		detectedQuests = std::move(quests);
		if (changed || questsChanged) {
			++stateRevision;
		}
		return changed || questsChanged;
	}

	bool HasPersistedTrackingData()
	{
		std::scoped_lock lock(stateMutex);
		return kProtectedIngredients.GetValue() != kDefaultProtectedIngredients ||
			kProtectedEffects.GetValue() != kDefaultProtectedEffects ||
			kProtectedEffectCounts.GetValue() != kDefaultProtectedEffectCounts ||
			kTrackedRequirements.GetValue() != kDefaultTrackedRequirements;
	}

	void ResetForNewGame()
	{
		std::scoped_lock lock(stateMutex);
		kProtectedIngredients.SetValue(kDefaultProtectedIngredients);
		kProtectedEffects.SetValue(kDefaultProtectedEffects);
		kProtectedEffectCounts.SetValue(kDefaultProtectedEffectCounts);
		kTrackedRequirements.SetValue(kDefaultTrackedRequirements);
		stateLoaded = false;
		nextManualID = 1;
		manualRequirements.clear();
		overrides.clear();
		selectedEffectsLoaded = false;
		selectedEffectTokens.clear();
		selectedEffectCountsLoaded = false;
		selectedEffectCounts.clear();
		detectedRequirements.clear();
		detectedQuests.clear();
		statusMessage.clear();
		++stateRevision;
		profiles::SaveCurrentProfile();
	}

	void ReloadForProfile()
	{
		std::scoped_lock lock(stateMutex);
		stateLoaded = false;
		nextManualID = 1;
		manualRequirements.clear();
		overrides.clear();
		selectedEffectsLoaded = false;
		selectedEffectTokens.clear();
		selectedEffectCountsLoaded = false;
		selectedEffectCounts.clear();
		detectedRequirements.clear();
		detectedQuests.clear();
		statusMessage.clear();
		++stateRevision;
	}

	std::vector<EffectInfo> GetEffects()
	{
		if (!IsTrackingEnabled()) {
			return {};
		}
		std::scoped_lock lock(stateMutex);
		LoadSelectedEffectsLocked();
			LoadSelectedEffectCountsLocked();
		auto result = ScanAvailableEffects(RE::TESDataHandler::GetSingleton());
		for (auto& effect : result) {
			effect.selected = std::any_of(selectedEffectTokens.begin(), selectedEffectTokens.end(), [&effect](const auto& token) {
				return EffectTokenMatches(token, effect);
			});
				if (const auto found = selectedEffectCounts.find(effect.key); found != selectedEffectCounts.end()) {
					effect.protectedCount = found->second;
				}
		}
		return result;
	}

	std::vector<QuestInfo> GetQuests()
	{
		if (!IsTrackingEnabled() || kDeveloper.GetValue() != 1) {
			return {};
		}
		std::scoped_lock lock(stateMutex);
		LoadStateLocked();
		return detectedQuests;
	}

	std::vector<Requirement> GetRequirements()
	{
		if (!IsTrackingEnabled()) {
			return {};
		}
		std::scoped_lock lock(stateMutex);
		LoadStateLocked();
		return GetRequirementsLocked();
	}

	std::uint64_t GetRevision()
	{
		if (!IsTrackingEnabled()) {
			return 0;
		}
		std::scoped_lock lock(stateMutex);
		LoadStateLocked();
		return stateRevision;
	}

	std::string GetStatus()
	{
		if (!IsTrackingEnabled()) {
			return {};
		}
		std::scoped_lock lock(stateMutex);
		return statusMessage;
	}

	std::map<std::string, int> GetProtectedIngredients()
	{
		if (!IsTrackingEnabled()) {
			return {};
		}
		std::scoped_lock lock(stateMutex);
		LoadStateLocked();
		std::map<std::string, int> result;
		const bool manualProtectionOnly = kManualProtectionOnly.GetValue() != 0;
		for (const auto& requirement : GetRequirementsLocked()) {
			if (requirement.completed || requirement.ingredient.empty()) {
				continue;
			}
			if (manualProtectionOnly && requirement.automatic && requirement.key.rfind("effect:", 0) != 0) {
				continue;
			}
			const auto ingredientKey = requirement.ingredientFormID != 0 ? GetIngredientKey(requirement.ingredientFormID) : requirement.ingredient;
			const int count = (std::max)(1, requirement.count);
			if (result[ingredientKey] == 999 || count == 999) {
				result[ingredientKey] = 999;
			} else {
				result[ingredientKey] = (std::min)(999, result[ingredientKey] + count);
			}
			}
		return result;
	}

	void SetEffectSelected(const std::string& a_key, bool a_selected)
	{
		if (!IsTrackingEnabled()) {
			return;
		}
		std::scoped_lock lock(stateMutex);
		LoadSelectedEffectsLocked();
			LoadSelectedEffectCountsLocked();
		const auto effects = ScanAvailableEffects(RE::TESDataHandler::GetSingleton());
		selectedEffectTokens.erase(std::remove_if(selectedEffectTokens.begin(), selectedEffectTokens.end(), [&a_key, &effects](const auto& token) {
			const auto found = std::find_if(effects.begin(), effects.end(), [&a_key](const auto& effect) {
				return effect.key == a_key;
			});
			return token == a_key || (found != effects.end() && EffectTokenMatches(token, *found));
		}), selectedEffectTokens.end());
			selectedEffectCounts.erase(a_key);
		if (a_selected) {
			selectedEffectTokens.push_back(a_key);
		}
		SaveSelectedEffectsLocked();
			SaveSelectedEffectCountsLocked();
		}

		void SetEffectProtectionCount(const std::string& a_key, int a_count)
		{
		if (!IsTrackingEnabled()) {
			return;
		}
			std::scoped_lock lock(stateMutex);
			LoadSelectedEffectsLocked();
			LoadSelectedEffectCountsLocked();
			const auto effects = ScanAvailableEffects(RE::TESDataHandler::GetSingleton());
			const auto found = std::find_if(effects.begin(), effects.end(), [&a_key](const auto& effect) {
				return effect.key == a_key;
			});
			if (found == effects.end() || std::none_of(selectedEffectTokens.begin(), selectedEffectTokens.end(), [&found](const auto& token) {
				return EffectTokenMatches(token, *found);
			})) {
				return;
			}
			selectedEffectCounts[a_key] = (std::clamp)(a_count, 1, 999);
			SaveSelectedEffectCountsLocked();
	}

	void AddManual(std::string a_source, std::string a_detail, std::string a_ingredient, int a_count)
	{
		if (!IsTrackingEnabled()) {
			return;
		}
		if (a_ingredient.empty()) {
			return;
		}
		std::scoped_lock lock(stateMutex);
		LoadStateLocked();
		manualRequirements.push_back(StoredRequirement{
			.key = MakeManualKey(nextManualID++),
			.source = std::move(a_source),
			.detail = std::move(a_detail),
			.ingredient = std::move(a_ingredient),
			.ingredientFormID = 0,
			.count = (std::clamp)(a_count, 1, 999),
			.completed = false
		});
		SaveStateLocked();
	}

	void UpdateRequirement(const Requirement& a_requirement)
	{
		if (!IsTrackingEnabled()) {
			return;
		}
		if (a_requirement.key.empty() || a_requirement.ingredient.empty()) {
			return;
		}
		std::scoped_lock lock(stateMutex);
		LoadStateLocked();
		const auto stored = ToStored(a_requirement);
		if (a_requirement.automatic) {
			overrides[a_requirement.key] = stored;
		} else {
			const auto found = std::find_if(manualRequirements.begin(), manualRequirements.end(), [&a_requirement](const auto& requirement) {
				return requirement.key == a_requirement.key;
			});
			if (found != manualRequirements.end()) {
				*found = stored;
			}
		}
		SaveStateLocked();
	}

	void RemoveManual(const std::string& a_key)
	{
		if (!IsTrackingEnabled()) {
			return;
		}
		std::scoped_lock lock(stateMutex);
		LoadStateLocked();
		manualRequirements.erase(std::remove_if(manualRequirements.begin(), manualRequirements.end(), [&a_key](const auto& requirement) {
			return requirement.key == a_key;
		}), manualRequirements.end());
		SaveStateLocked();
	}

	void ClearOverrides()
	{
		if (!IsTrackingEnabled()) {
			return;
		}
		std::scoped_lock lock(stateMutex);
		LoadStateLocked();
		for (auto iterator = overrides.begin(); iterator != overrides.end();) {
			if (iterator->second.completionOverridden) {
				iterator = overrides.erase(iterator);
			} else {
				++iterator;
			}
		}
		SaveStateLocked();
	}

	void ResetToDetected()
	{
		if (!IsTrackingEnabled()) {
			return;
		}
		std::scoped_lock lock(stateMutex);
		LoadStateLocked();
		manualRequirements.clear();
		overrides.clear();
		SaveStateLocked();
	}

	void RequestQuestStage(std::uint32_t a_formID, std::uint16_t a_stage, bool a_force)
	{
		if (!IsTrackingEnabled() || kDeveloper.GetValue() != 1) {
			return;
		}
		const auto* tasks = SKSE::GetTaskInterface();
		if (!tasks) {
			SetStatus("SKSE task interface unavailable");
			return;
		}
		tasks->AddTask([a_formID, a_stage, a_force]() {
			DoSetQuestStage(a_formID, a_stage, a_force);
		});
		SetStatus("Stage request queued");
	}

	void RequestQuestObjective(std::uint32_t a_formID, std::uint16_t a_objective, ObjectiveAction a_action)
	{
		if (!IsTrackingEnabled() || kDeveloper.GetValue() != 1) {
			return;
		}
		const auto* tasks = SKSE::GetTaskInterface();
		if (!tasks) {
			SetStatus("SKSE task interface unavailable");
			return;
		}
		tasks->AddTask([a_formID, a_objective, a_action]() {
			DoSetQuestObjective(a_formID, a_objective, a_action);
		});
		SetStatus("Objective request queued");
	}
}
