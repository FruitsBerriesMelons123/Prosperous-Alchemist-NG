#include "main.h"
#include "PotionConfirmation.h"
#include "AlchemistEngine.h"
#include "AlchemyPlus/AlchemyPlus.h"
#include "DeveloperTestHub.h"
#include "IngredientTracker.h"
#include "MenuHandler.h"
#include "AlchemistWindow.h"
#include "ProfileManager.h"
#include "RenderHook.h"
#include "Localization.h"
#include "ModSettings.h"

#include <Windows.h>
#include <array>

namespace alchemist {
	Potion costliestPotion;
	set<Ingredient> lastIngredientList;
	set<Ingredient> ingredients;
	set<Potion> potions;
	int combinations;

	namespace {
		inline bool IsSystemMemorySafe()
		{
			MEMORYSTATUSEX status{};
			status.dwLength = sizeof(status);
			if (GlobalMemoryStatusEx(&status)) {
				// High "memory load" is normal (cache). Only bail out on genuine exhaustion.
				if (status.ullAvailPhys < (256ULL * 1024 * 1024) ||
					status.ullAvailPageFile < (512ULL * 1024 * 1024)) {
					return false;
				}
			}
			return true;
		}

		// Leaves at least 2 cores free on >= 6-core CPUs and 1 core free on 2-4 core CPUs
		inline std::size_t GetSafeWorkerCount(std::size_t candidateCount, bool multithreaded)
		{
			if (!multithreaded || candidateCount <= 1) {
				return 1;
			}
			const auto hw = std::thread::hardware_concurrency();
			if (hw <= 1) {
				return 1;
			}
			const std::size_t target = hw > 4 ? hw - 2 : hw - 1;
			return (std::min)(target, candidateCount);
		}

		struct IngredientCombination
		{
			std::array<std::size_t, 3> indices{};
			std::size_t size = 0;
		};

		struct CandidateResult
		{
			IngredientCombination combination;
			Potion potion;
		};

		set<Effect> getPossibleEffects(const Ingredient& ingredient1, const Ingredient& ingredient2)
		{
			set<Effect> possibleEffects;
			possibleEffects.insert(ingredient1.effects.begin(), ingredient1.effects.end());
			possibleEffects.insert(ingredient2.effects.begin(), ingredient2.effects.end());
			for (const auto& effect : ingredient1.effects) {
				if (std::find(ingredient2.effects.begin(), ingredient2.effects.end(), effect) != ingredient2.effects.end()) {
					possibleEffects.erase(effect);
				}
			}
			return possibleEffects;
		}

		std::optional<Potion> evaluateCombination(
			const IngredientCombination& combination,
			const vector<const Ingredient*>& availableIngredients,
			const Player& evaluatedPlayer = player)
		{
			if (combination.size < 2 || combination.size > 3) {
				return std::nullopt;
			}
			vector<const Ingredient*> selectedIngredients;
			selectedIngredients.reserve(combination.size);
			for (std::size_t index = 0; index < combination.size; ++index) {
				if (combination.indices[index] >= availableIngredients.size() || !availableIngredients[combination.indices[index]]) {
					return std::nullopt;
				}
				selectedIngredients.push_back(availableIngredients[combination.indices[index]]);
			}

			const auto nativeResult = effect::evaluatePotion(selectedIngredients, evaluatedPlayer);
			if (!nativeResult.valid || !std::isfinite(nativeResult.cost)) {
				return std::nullopt;
			}
			const auto& ingredient1 = *selectedIngredients[0];
			const auto& ingredient2 = *selectedIngredients[1];
			if (combination.size == 2) {
				return Potion(2, ingredient1, ingredient2, nativeResult.effects,
					getPossibleEffects(ingredient1, ingredient2), nativeResult.controlEffect, nativeResult.isPoison, nativeResult.cost, evaluatedPlayer);
			}
			return Potion(3, ingredient1, ingredient2, *selectedIngredients[2],
				nativeResult.effects, nativeResult.controlEffect, nativeResult.isPoison, nativeResult.cost, evaluatedPlayer);
		}

		// Queue canonical pairs only (first < second)
		vector<IngredientCombination> buildPairCombinations(
			std::size_t ingredientCount,
			const std::vector<bool>* isNewIngredient = nullptr)
		{
			vector<IngredientCombination> combinations;
			if (ingredientCount < 2) {
				return combinations;
			}
			combinations.reserve(ingredientCount * (ingredientCount - 1) / 2);
			for (std::size_t first = 0; first + 1 < ingredientCount; ++first) {
				for (std::size_t second = first + 1; second < ingredientCount; ++second) {
					if (isNewIngredient && !(*isNewIngredient)[first] && !(*isNewIngredient)[second]) {
						continue;
					}
					combinations.push_back({ { first, second, 0 }, 2 });
				}
			}
			return combinations;
		}

		// Queue canonical triples only (first < second < third)
		vector<IngredientCombination> buildTripleCombinations(
			const vector<const Ingredient*>& availableIngredients,
			const std::atomic<bool>* cancelToken = nullptr,
			const std::vector<bool>* isNewIngredient = nullptr)
		{
			const std::size_t ingredientCount = availableIngredients.size();
			vector<IngredientCombination> combinations;
			if (ingredientCount < 3) {
				return combinations;
			}

			std::vector<std::vector<const RE::EffectSetting*>> identities(ingredientCount);
			for (std::size_t i = 0; i < ingredientCount; ++i) {
				const auto& ing = *availableIngredients[i];
				for (std::size_t e = 0; e < ing.effects.size(); ++e) {
					const auto effect = effect::getAlgorithmEffect(ing, e);
					const auto* id = effect::getSourceIdentity(effect);
					if (id) {
						identities[i].push_back(id);
					}
				}
			}

			if (cancelToken && cancelToken->load(std::memory_order_relaxed)) {
				return combinations;
			}

			std::vector<std::vector<bool>> shares(ingredientCount, std::vector<bool>(ingredientCount, false));
			for (std::size_t i = 0; i < ingredientCount; ++i) {
				for (std::size_t j = i + 1; j < ingredientCount; ++j) {
					bool match = false;
					for (const auto* id1 : identities[i]) {
						if (!id1) continue;
						const auto fid1 = id1->GetFormID();
						for (const auto* id2 : identities[j]) {
							if (!id2) continue;
							const auto fid2 = id2->GetFormID();
							if ((fid1 != 0 && fid1 == fid2) || id1 == id2) {
								match = true;
								break;
							}
						}
						if (match) {
							break;
						}
					}
					shares[i][j] = match;
					shares[j][i] = match;
				}
			}

			combinations.reserve((std::min)(ingredientCount * (ingredientCount - 1) * (ingredientCount - 2) / 6, static_cast<std::size_t>(2000000)));
			for (std::size_t first = 0; first + 2 < ingredientCount; ++first) {
				if ((first & 0x7) == 0 && cancelToken && cancelToken->load(std::memory_order_relaxed)) {
					return {};
				}
				for (std::size_t second = first + 1; second + 1 < ingredientCount; ++second) {
					const bool ab = shares[first][second];
					for (std::size_t third = second + 1; third < ingredientCount; ++third) {
						if (isNewIngredient && !(*isNewIngredient)[first] && !(*isNewIngredient)[second] && !(*isNewIngredient)[third]) {
							continue;
						}
						const bool ac = shares[first][third];
						const bool bc = shares[second][third];
						const bool validTriple = ab ? (ac || bc) : (ac && bc);
						if (validTriple) {
							// Push canonical triple once
							combinations.push_back({ { first, second, third }, 3 });
						}
					}
				}
			}
			return combinations;
		}

		bool isBetterPotion(const Potion& candidate, const Potion& currentBest)
		{
			if (currentBest.size <= 0) {
				return true;
			}
			if (candidate.cost != currentBest.cost) {
				return candidate.cost > currentBest.cost;
			}
			return candidate.id < currentBest.id;
		}

		std::string getSelectionOrderString(const Potion& potion)
		{
			if (potion.size == 2) {
				return potion.ingredient1.name + ", " + potion.ingredient2.name;
			}
			if (potion.size == 3) {
				return potion.ingredient1.name + ", " + potion.ingredient2.name + ", " + potion.ingredient3.name;
			}
			return {};
		}

		void processAndAddCandidates(
			const vector<CandidateResult>& candidateResults,
			RecipeCalculationOutput& output)
		{
			output.potions.reserve(output.potions.size() + candidateResults.size());
			for (const auto& res : candidateResults) {
				if (!res.potion.effects.empty() && std::isfinite(res.potion.cost) && res.potion.cost >= 0.0f) {
					if (isBetterPotion(res.potion, output.costliestPotion)) {
						output.costliestPotion = res.potion;
					}
					output.potions.push_back(res.potion);
				}
			}
		}

		vector<CandidateResult> evaluateCombinations(
			const vector<IngredientCombination>& candidates,
			const vector<const Ingredient*>& availableIngredients,
			bool multithreaded,
			const Player& evaluatedPlayer = player,
			const std::atomic<bool>* cancelToken = nullptr,
			const std::function<void(std::size_t current, std::size_t total)>& progressCallback = nullptr,
			std::atomic<bool>* memoryAborted = nullptr)
		{
			if (candidates.empty() || (cancelToken && cancelToken->load(std::memory_order_relaxed))) {
				return {};
			}

			const std::size_t workerCount = GetSafeWorkerCount(candidates.size(), multithreaded);
			std::atomic<std::size_t> nextCandidate = 0;
			std::atomic<bool> memoryAbort = false;
			vector<vector<CandidateResult>> workerResults(workerCount);

			constexpr std::size_t kPermOrders3[6][3] = {
				{ 0, 1, 2 }, { 0, 2, 1 },
				{ 1, 0, 2 }, { 1, 2, 0 },
				{ 2, 0, 1 }, { 2, 1, 0 }
			};
			constexpr std::size_t kPermOrders2[2][2] = {
				{ 0, 1 }, { 1, 0 }
			};

			struct LocalEvaluation {
				IngredientCombination combo;
				NativePotionResult native;
				int intVal = 0;
				std::string selectionOrder;
			};

			const auto evaluateWorker = [&](std::size_t workerIndex) {
				SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_BELOW_NORMAL);

				auto& results = workerResults[workerIndex];
				std::vector<const Ingredient*> selectedIngredients;
				selectedIngredients.reserve(3);
				LocalEvaluation stackEvals[6];

				while (true) {
					if (cancelToken && cancelToken->load(std::memory_order_relaxed)) {
						break;
					}
					if (memoryAbort.load(std::memory_order_relaxed)) {
						break;
					}

					const auto candidateIndex = nextCandidate.fetch_add(1, std::memory_order_relaxed);
					if (candidateIndex >= candidates.size()) {
						break;
					}

					// Periodically check memory and yield CPU execution
					if ((candidateIndex & 0x7FF) == 0) {
						if (!IsSystemMemorySafe()) {
							memoryAbort.store(true, std::memory_order_relaxed);
							break;
						}
						std::this_thread::yield();
					}

					if (progressCallback && ((candidateIndex & 0x3F) == 0 || candidateIndex + 1 == candidates.size())) {
						progressCallback(candidateIndex + 1, candidates.size());
					}

					const auto& baseCombo = candidates[candidateIndex];
					const std::size_t permCount = baseCombo.size == 3 ? 6 : 2;
					std::size_t validCount = 0;

					// 1. Evaluate all permutations on the stack
					for (std::size_t p = 0; p < permCount; ++p) {
						IngredientCombination permCombo;
						permCombo.size = baseCombo.size;
						selectedIngredients.clear();

						for (std::size_t i = 0; i < baseCombo.size; ++i) {
							const auto originalIndex = baseCombo.size == 3 ?
								baseCombo.indices[kPermOrders3[p][i]] :
								baseCombo.indices[kPermOrders2[p][i]];
							permCombo.indices[i] = originalIndex;
							selectedIngredients.push_back(availableIngredients[originalIndex]);
						}

						auto nativeRes = effect::evaluatePotion(selectedIngredients, evaluatedPlayer);
						if (nativeRes.valid && std::isfinite(nativeRes.cost) && nativeRes.cost >= 0.0f) {
							stackEvals[validCount].combo = permCombo;
							stackEvals[validCount].intVal = static_cast<int>(std::floor(nativeRes.cost));

							if (permCombo.size == 2) {
								stackEvals[validCount].selectionOrder = selectedIngredients[0]->name + ", " + selectedIngredients[1]->name;
							} else {
								stackEvals[validCount].selectionOrder = selectedIngredients[0]->name + ", " + selectedIngredients[1]->name + ", " + selectedIngredients[2]->name;
							}

							stackEvals[validCount].native = std::move(nativeRes);
							++validCount;
						}
					}

					if (validCount == 0) {
						continue;
					}

					// 2. In-flight deduplication: preserve distinct values produced by selection order
					for (std::size_t i = 0; i < validCount; ++i) {
						bool alreadySeen = false;
						for (std::size_t prev = 0; prev < i; ++prev) {
							if (stackEvals[prev].intVal == stackEvals[i].intVal) {
								alreadySeen = true;
								break;
							}
						}
						if (alreadySeen) {
							continue;
						}

						std::size_t bestIdx = i;
						for (std::size_t j = i + 1; j < validCount; ++j) {
							if (stackEvals[j].intVal == stackEvals[i].intVal) {
								if (stackEvals[j].selectionOrder < stackEvals[bestIdx].selectionOrder) {
									bestIdx = j;
								}
							}
						}

						// 3. Allocate the heavy Potion object ONLY for kept winning candidates
						const auto& win = stackEvals[bestIdx];
						const auto& ing1 = *availableIngredients[win.combo.indices[0]];
						const auto& ing2 = *availableIngredients[win.combo.indices[1]];

						Potion potion = (win.combo.size == 2)
							? Potion(2, ing1, ing2, win.native.effects, getPossibleEffects(ing1, ing2),
									 win.native.controlEffect, win.native.isPoison, win.native.cost, evaluatedPlayer)
							: Potion(3, ing1, ing2, *availableIngredients[win.combo.indices[2]],
									 win.native.effects, win.native.controlEffect, win.native.isPoison, win.native.cost, evaluatedPlayer);

						results.push_back({ win.combo, std::move(potion) });
					}
				}
			};

			if (workerCount == 1) {
				evaluateWorker(0);
			} else {
				vector<thread> workers;
				workers.reserve(workerCount);
				for (std::size_t workerIndex = 0; workerIndex < workerCount; ++workerIndex) {
					workers.emplace_back(evaluateWorker, workerIndex);
				}
				for (auto& worker : workers) {
					worker.join();
				}
			}

			if (cancelToken && cancelToken->load(std::memory_order_relaxed)) {
				return {};
			}
			if (memoryAbort.load(std::memory_order_relaxed)) {
				if (memoryAborted) memoryAborted->store(true, std::memory_order_relaxed);
				return {};
			}

			std::size_t resultCount = 0;
			for (const auto& r : workerResults) {
				resultCount += r.size();
			}
			vector<CandidateResult> evaluated;
			evaluated.reserve(resultCount);
			for (auto& r : workerResults) {
				for (auto& item : r) {
					evaluated.push_back(std::move(item));
				}
			}
			return evaluated;
		}

		void setCostliestDescription(Potion& targetCostliestPotion)
		{
			if (targetCostliestPotion.size != 2 && targetCostliestPotion.size != 3) {
				return;
			}
			string effectDescriptions;
			for (const auto& effect : targetCostliestPotion.effects) {
				effectDescriptions += " " + effect::getPerkCalcDescription(effect, targetCostliestPotion.controlEffect.beneficial);
			}
			const auto ingredientText = targetCostliestPotion.size == 2 ?
				str::printSort2(targetCostliestPotion.ingredient1.name, targetCostliestPotion.ingredient2.name) :
				str::printSort3(targetCostliestPotion.ingredient1.name, targetCostliestPotion.ingredient2.name, targetCostliestPotion.ingredient3.name);
			targetCostliestPotion.description = targetCostliestPotion.name + ":" + effectDescriptions +
				"\n Value: " + str::fromFloat(floor(targetCostliestPotion.cost)) + "\n" + ingredientText;
		}
	}

	RecipeCalculationOutput CalculateRecipesFromSnapshot(
		const vector<Ingredient>& inputIngredients,
		const Player& evaluatedPlayer,
		bool multithreaded,
		const std::atomic<bool>* cancelToken,
		const CalculationProgressCallback& progressCallback,
		const std::vector<bool>* isNewIngredient)
	{
		RecipeCalculationOutput output;
		std::atomic<bool> memoryAborted{ false };
		if (inputIngredients.size() < 2) {
			if (progressCallback) {
				progressCallback(1.0f, "Completed", 0, 0);
			}
			return output;
		}

		vector<const Ingredient*> availableIngredients;
		availableIngredients.reserve(inputIngredients.size());
		for (const auto& ingredient : inputIngredients) {
			availableIngredients.push_back(&ingredient);
		}

		if (cancelToken && cancelToken->load(std::memory_order_relaxed)) {
			output.cancelled = true;
			return output;
		}

		if (progressCallback) {
			progressCallback(0.0f, "Evaluating 2-ingredient recipes", 0, 0);
		}

		const auto pairCandidates = buildPairCombinations(availableIngredients.size(), isNewIngredient);
		const auto pairProgress = [&](std::size_t curr, std::size_t tot) {
			if (progressCallback && tot > 0) {
				const float fraction = 0.05f * (static_cast<float>(curr) / static_cast<float>(tot));
				progressCallback(fraction, "Evaluating 2-ingredient recipes", curr, tot);
			}
		};
		const auto validPairs = evaluateCombinations(pairCandidates, availableIngredients, multithreaded, evaluatedPlayer, cancelToken, pairProgress, &memoryAborted);
		if (cancelToken && cancelToken->load(std::memory_order_relaxed)) {
			output.cancelled = true;
			return output;
		}
		if (memoryAborted.load()) {
			output.cancelled = true;
			return output;
		}

		processAndAddCandidates(validPairs, output);

		if (progressCallback) {
			progressCallback(0.05f, "Finding 3-ingredient combinations", 0, 0);
		}

		const auto tripleCandidates = buildTripleCombinations(availableIngredients, cancelToken, isNewIngredient);

		if (cancelToken && cancelToken->load(std::memory_order_relaxed)) {
			output.cancelled = true;
			return output;
		}

		if (progressCallback) {
			progressCallback(0.10f, "Evaluating 3-ingredient recipes", 0, tripleCandidates.size());
		}

		const auto tripleProgress = [&](std::size_t curr, std::size_t tot) {
			if (progressCallback && tot > 0) {
				const float fraction = 0.10f + 0.75f * (static_cast<float>(curr) / static_cast<float>(tot));
				progressCallback(fraction, "Evaluating 3-ingredient recipes", curr, tot);
			}
		};
		const auto validTriples = evaluateCombinations(tripleCandidates, availableIngredients, multithreaded, evaluatedPlayer, cancelToken, tripleProgress, &memoryAborted);
		if (cancelToken && cancelToken->load(std::memory_order_relaxed)) {
			output.cancelled = true;
			return output;
		}
		if (memoryAborted.load()) {
			output.cancelled = true;
			return output;
		}

		if (progressCallback) {
			progressCallback(0.85f, "Collecting recipes...", tripleCandidates.size(), tripleCandidates.size());
		}

		processAndAddCandidates(validTriples, output);

		if (progressCallback) {
			progressCallback(0.87f, "Preparing recipes for sorting...", output.potions.size(), output.potions.size());
		}

		output.combinations = static_cast<int>(output.potions.size());
		setCostliestDescription(output.costliestPotion);
		return output;
	}

	namespace {
		void generatePotions(bool multithreaded)
		{
			vector<Ingredient> inputList(ingredients.begin(), ingredients.end());
			auto output = CalculateRecipesFromSnapshot(inputList, player, multithreaded);
			potions.clear();
			for (auto& p : output.potions) {
				potions.insert(std::move(p));
			}
			costliestPotion = std::move(output.costliestPotion);
			combinations = output.combinations;
		}
	}

	void makePotions()
	{
		initAlchemist();
		confirmations::DrainPendingConfirmations(player);
		modsettings::RefreshAndSynchronize(player);
		generatePotions(true);
	}

	void makePotionsST()
	{
		initAlchemist();
		confirmations::DrainPendingConfirmations(player);
		modsettings::RefreshAndSynchronize(player);
		generatePotions(false);
	}


	void initAlchemist() {
		caco::Adapter::Refresh();
		alchemyplus::Adapter::Refresh();
		int ignorePlayer = kIgnorePlayer.GetValue();
		auto* playerCharacter = RE::PlayerCharacter::GetSingleton();
		if (!playerCharacter) {
			return;
		}
		if (ignorePlayer == 0) {
			player.init();
			player.fortifyAlchemyLevel = 0;
		} else {
			player = Player();
			player.alchemyLevel = 15.0f;
			player.fortifyAlchemyLevel = 0.0f;
			player.alchemistPerkLevel = 0;
			player.alchemistPerkMultiplier = 1.0f;
			player.hasPerkPurity = false;
			player.hasPerkPhysician = false;
			player.hasPerkBenefactor = false;
			player.hasPerkPoisoner = false;
			player.hasPerkConcentratedPoison = false;
			player.hasSeekerOfShadows = false;
			player.alchemyEvaluationContext = {};
			player.alchemyEvaluationContext.captured = true;
			player.setState();
		}
		auto inventory = playerCharacter->GetInventory();
		set<Ingredient> ingredientCount;
		for (const auto& [form, entry] : inventory) {
			auto* ingredient = form && form->Is(RE::FormType::Ingredient) ? static_cast<IngredientItem*>(form) : nullptr;
			if (ingredient) {
				Ingredient ownedIngredient(ingredient);
				ownedIngredient.inventoryCount = entry.first;
				ingredientCount.insert(std::move(ownedIngredient));
			}
		}

		if (ignorePlayer == 0) {
			for (const auto& [form, entry] : inventory) {
				if (!entry.second || !entry.second->IsWorn()) {
					continue;
				}
				if (auto* enchantment = entry.second->GetEnchantment()) {
					for (auto* effect : enchantment->effects) {
						if (effect::isFortifyAlchemy(effect)) {
							player.fortifyAlchemyLevel += effect::getMagnitude(effect);
						}
					}
				}
			}

			if (const auto* playerCharacter = RE::PlayerCharacter::GetSingleton()) {
				if (auto* magicTarget = const_cast<RE::PlayerCharacter*>(playerCharacter)->GetMagicTarget()) {
					if (auto* activeEffects = magicTarget->GetActiveEffectList()) {
						for (const auto* activeEffect : *activeEffects) {
							if (!activeEffect || activeEffect->flags.any(RE::ActiveEffect::Flag::kInactive, RE::ActiveEffect::Flag::kDispelled)) {
								continue;
							}
							if (activeEffect->flags.any(RE::ActiveEffect::Flag::kEnchanting) ||
								(activeEffect->spell && activeEffect->spell->Is(RE::FormType::Enchantment))) {
								continue;
							}
							if (effect::isFortifyAlchemy(activeEffect->GetBaseObject())) {
								player.fortifyAlchemyLevel += activeEffect->GetMagnitude();
							}
						}
					}
				}
			}
		}

		const bool protectIngredients = kProtectIngredients.GetValue() != 0;
		map<string, int> moreIngredients;
		if (protectIngredients) {
			string additionalIngredients = kProtectedIngredients.GetValue();
			vector<string> iTokens = str::split(additionalIngredients, ',');
			for (auto& iToken : iTokens) {
				vector<string> iParts = str::split(iToken, '|');
				if (iParts.size() == 1) {
					moreIngredients[iParts.at(0)] = 999;
				}
				else if (iParts.size() == 2) {
					moreIngredients[iParts.at(0)] = str::toInt(iParts.at(1));
				}
			}
			for (const auto& [ingredient, count] : tracker::GetProtectedIngredients()) {
				auto found = moreIngredients.find(ingredient);
				if (found == moreIngredients.end() || found->second == 999 || count == 999) {
					moreIngredients[ingredient] = (found != moreIngredients.end() && found->second == 999) || count == 999 ? 999 : count;
				} else {
					found->second = (std::min)(999, found->second + count);
				}
			}
		}
		ingredients.clear();
		for (const auto& [form, entry] : inventory) {
			auto* ingredient = form && form->Is(RE::FormType::Ingredient) ? static_cast<IngredientItem*>(form) : nullptr;
			if (ingredient && (!protectIngredients || !ingredient::isProtected(ingredient, ingredientCount, moreIngredients))) {
				ingredients.insert(Ingredient(ingredient));
			}
		}
		if (ignorePlayer == 0) {
			player.captureAlchemyEvaluationContext();
			player.setState();
		}
	}

}

void MessageHandler(SKSE::MessagingInterface::Message* msg)
{
	if (!msg) {
		return;
	}
	if (msg->type == SKSE::MessagingInterface::kPreLoadGame) {
		alchemist::ui::NotifyGameLoadStarted();
		alchemist::devhub::Shutdown();
		alchemist::engine::InvalidateMasterCache();
	}
	if (msg->type == SKSE::MessagingInterface::kPostLoadGame) {
		alchemist::ui::NotifyGameLoadFinished();
	}
	if (msg->type == SKSE::MessagingInterface::kNewGame) {
		alchemist::ui::NotifyNewGame();
		alchemist::devhub::Shutdown();
		alchemist::engine::InvalidateMasterCache();
	}

	if (msg->type == SKSE::MessagingInterface::kPostPostLoad) {
		alchemist::menu::Register();
		alchemist::render::Install();
	}
	if (msg->type == SKSE::MessagingInterface::kDataLoaded) {
		alchemist::caco::Adapter::Initialize();
	}
	if (msg->type == SKSE::MessagingInterface::kInputLoaded) {
		alchemist::alchemyplus::Adapter::Initialize();
		alchemist::menu::Register();
		alchemist::render::Install();
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* skse)
{
	SKSE::Init(skse);

	REX::INI::SettingStore::GetSingleton()->Init("Data\\SKSE\\Plugins\\alchemist.ini", "");
	REX::INI::SettingStore::GetSingleton()->Load();
	alchemist::profiles::Initialize();
	alchemist::localization::Initialize(kLanguage.GetValue());

	const auto* messaging = SKSE::GetMessagingInterface();
	if (!messaging || messaging->Version() < SKSE::MessagingInterface::kVersion) {
		return false;
	}
	if (!messaging->RegisterListener("SKSE", MessageHandler)) {
		return false;
	}

	srand(static_cast<unsigned int>(time(nullptr)));
	return true;
}
