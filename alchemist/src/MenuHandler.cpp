#include "MenuHandler.h"

#include "AlchemistWindow.h"
#include "AlchemistEngine.h"
#include "DeveloperTestHub.h"
#include "PotionConfirmation.h"
#include "main.h"

#include "RE/Skyrim.h"
#include "RE/B/BSInputDeviceManager.h"
#include "RE/B/ButtonEvent.h"
#include "RE/B/BSWin32MouseDevice.h"
#include "RE/M/MenuCursor.h"
#include "RE/M/MouseMoveEvent.h"

#include <atomic>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <mutex>

namespace alchemist::menu {
	namespace {
		void QueueRecalculation(bool a_force = false);
		std::atomic_uint64_t menuGeneration = 0;
		std::atomic_bool nativeAlchemyOpen = false;
		std::atomic_bool confirmationQueued = false;
		std::atomic_bool inventoryEventObserved = false;
		CursorSnapshot nativeCursorSnapshot{};
		bool nativeCursorValid = false;
		std::mutex nativeCursorMutex;

		void QueueConfirmationDrainTask(std::uint64_t a_generation)
		{
			auto* taskInterface = SKSE::GetTaskInterface();
			if (!taskInterface) {
				confirmationQueued.store(false, std::memory_order_release);
				return;
			}
			taskInterface->AddTask([a_generation]() {
				const bool currentMenu = nativeAlchemyOpen.load(std::memory_order_acquire) &&
					a_generation == menuGeneration.load(std::memory_order_acquire);
				if (!currentMenu) {
					confirmationQueued.store(false, std::memory_order_release);
					return;
				}
				if (!confirmations::IsDrainReady()) {
					QueueConfirmationDrainTask(a_generation);
					return;
				}
				confirmationQueued.store(false, std::memory_order_release);
				confirmations::DrainPendingConfirmations(player);
			});
		}

		void QueueConfirmationRecording()
		{
			bool expected = false;
			if (!confirmationQueued.compare_exchange_strong(expected, true)) {
				return;
			}

			const auto generation = menuGeneration.load(std::memory_order_acquire);
			QueueConfirmationDrainTask(generation);
		}

		void CaptureNativeCursor()
		{
			auto* menuCursor = RE::MenuCursor::GetSingleton();
			if (!menuCursor) {
				std::scoped_lock lock(nativeCursorMutex);
				nativeCursorValid = false;
				return;
			}

			const auto& cursorData = menuCursor->GetRuntimeData();
			if (!std::isfinite(cursorData.cursorPosX) || !std::isfinite(cursorData.cursorPosY) ||
				!std::isfinite(cursorData.screenWidthX) || !std::isfinite(cursorData.screenWidthY) ||
				cursorData.screenWidthX <= 0.0f || cursorData.screenWidthY <= 0.0f ||
				cursorData.cursorPosX < 0.0f || cursorData.cursorPosY < 0.0f ||
				cursorData.cursorPosX > cursorData.screenWidthX || cursorData.cursorPosY > cursorData.screenWidthY) {
				std::scoped_lock lock(nativeCursorMutex);
				nativeCursorValid = false;
				return;
			}

		const CursorSnapshot cursorSnapshot{
			.x = cursorData.cursorPosX,
			.y = cursorData.cursorPosY,
			.width = cursorData.screenWidthX,
			.height = cursorData.screenWidthY
		};
		std::scoped_lock lock(nativeCursorMutex);
		nativeCursorSnapshot = cursorSnapshot;
		nativeCursorValid = true;
		}

		void ResetNativeCursor()
		{
			std::scoped_lock lock(nativeCursorMutex);
			nativeCursorValid = false;
		}

		bool IsAlchemySubMenu(const RE::CraftingSubMenus::CraftingSubMenu* a_submenu)
		{
			if (!a_submenu) {
				return false;
			}
			const auto vtable = *reinterpret_cast<const std::uintptr_t*>(a_submenu);
			for (const auto& vtableAddress : RE::CraftingSubMenus::CraftingSubMenus::AlchemyMenu::VTABLE) {
				if (vtable == vtableAddress.address()) {
					return true;
				}
			}
			return false;
		}

		bool IsAlchemyMenuActive()
		{
			auto* uiInterface = RE::UI::GetSingleton();
			if (!uiInterface) {
				return false;
			}
			auto craftingMenu = uiInterface->GetMenu<RE::CraftingMenu>();
			return craftingMenu && IsAlchemySubMenu(craftingMenu->GetCraftingSubMenu());
		}

		class InputHandler final : public RE::BSTEventSink<RE::InputEvent*> {
		public:
			RE::BSEventNotifyControl ProcessEvent(RE::InputEvent* const* a_event,
				RE::BSTEventSource<RE::InputEvent*>*) override
			{
				if (!a_event || !*a_event || !ui::IsVisible()) {
					return RE::BSEventNotifyControl::kContinue;
				}

				const bool leftMouseButtonDownAtStart = ui::IsLeftMouseButtonDown();
				bool stopMousePropagation = false;
				bool stopKeyboardPropagation = false;
				bool mouseMoveEventPresent = false;
				bool heldLeftButtonEventPresent = false;
				for (auto* event = *a_event; event; event = event->next) {
					if (event->GetEventType() == RE::INPUT_EVENT_TYPE::kMouseMove) {
						mouseMoveEventPresent = true;
						CaptureNativeCursor();
						continue;
					}
					if (event->GetEventType() == RE::INPUT_EVENT_TYPE::kButton) {
						CaptureNativeCursor();
					}
					if (event->GetEventType() == RE::INPUT_EVENT_TYPE::kChar) {
						if (const auto* charEvent = event->AsCharEvent()) {
							ui::AddInputCharacter(charEvent->keyCode);
						}
						stopKeyboardPropagation = stopKeyboardPropagation || ui::IsSearchInputFocused();
						continue;
					}
					if (event->GetEventType() != RE::INPUT_EVENT_TYPE::kButton) {
						continue;
					}

					auto* buttonEvent = event->AsButtonEvent();
					if (buttonEvent && buttonEvent->GetDevice() == RE::INPUT_DEVICE::kKeyboard) {
						ui::AddInputKey(buttonEvent->GetIDCode(), buttonEvent->IsPressed());
						stopKeyboardPropagation = stopKeyboardPropagation || ui::IsSearchInputFocused();
						continue;
					}
					if (buttonEvent && buttonEvent->GetDevice() == RE::INPUT_DEVICE::kMouse) {
						const auto buttonID = buttonEvent->GetIDCode();
						const bool leftButton = buttonID == static_cast<std::uint32_t>(RE::BSWin32MouseDevice::Key::kLeftButton);
						if (leftButton && buttonEvent->IsHeld()) {
							heldLeftButtonEventPresent = true;
						}
						if (leftButton) {
							ui::SetLeftMouseButtonDown(buttonEvent->IsPressed());
						}
						if (buttonEvent->IsPressed()) {
							switch (buttonID) {
							case RE::BSWin32MouseDevice::Key::kWheelUp:
								ui::AddMouseWheel(1.0f);
								break;
							case RE::BSWin32MouseDevice::Key::kWheelDown:
								ui::AddMouseWheel(-1.0f);
								break;
							default:
								break;
							}
						}
						const auto cursorOverWindow = ui::IsCursorOverWindow();
						stopMousePropagation = stopMousePropagation || cursorOverWindow;
						continue;
					}
					stopKeyboardPropagation = stopKeyboardPropagation || ui::IsSearchInputFocused();
				}

				const bool activeLeftDrag = leftMouseButtonDownAtStart || heldLeftButtonEventPresent;
				const bool forwardNativeMouseMotion = activeLeftDrag && mouseMoveEventPresent;
				if (forwardNativeMouseMotion) {
					stopMousePropagation = false;
				}
				const bool stopPropagation = stopKeyboardPropagation || stopMousePropagation;
				return stopPropagation ? RE::BSEventNotifyControl::kStop : RE::BSEventNotifyControl::kContinue;
			}
		};

		class MenuOpenCloseHandler final : public RE::BSTEventSink<RE::MenuOpenCloseEvent> {
		public:
			RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* a_event,
				RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override
			{
				if (!a_event || a_event->menuName != RE::CraftingMenu::MENU_NAME) {
					return RE::BSEventNotifyControl::kContinue;
				}
				if (!a_event->opening) {
					nativeAlchemyOpen.store(false, std::memory_order_release);
					ResetNativeCursor();
					menuGeneration.fetch_add(1, std::memory_order_acq_rel);
					devhub::OnMenuClosed();
					ui::SetVisible(false);
					engine::NotifyAlchemyMenuClosed();
					return RE::BSEventNotifyControl::kContinue;
				}

				auto* uiInterface = RE::UI::GetSingleton();
				if (!uiInterface) {
					return RE::BSEventNotifyControl::kContinue;
				}
				auto craftingMenu = uiInterface->GetMenu<RE::CraftingMenu>();
				if (!craftingMenu) {
					return RE::BSEventNotifyControl::kContinue;
				}

				auto* submenu = craftingMenu->GetCraftingSubMenu();
				if (!submenu) {
					return RE::BSEventNotifyControl::kContinue;
				}
				const bool isAlchemyMenu = IsAlchemySubMenu(submenu);
				if (isAlchemyMenu) {
					nativeAlchemyOpen.store(true, std::memory_order_release);
					CaptureNativeCursor();
					menuGeneration.fetch_add(1, std::memory_order_acq_rel);
					ui::SetVisible(true);
					engine::NotifyAlchemyMenuOpened();
					QueueRecalculation();
				} else {
					nativeAlchemyOpen.store(false, std::memory_order_release);
					menuGeneration.fetch_add(1, std::memory_order_acq_rel);
					ui::SetVisible(false);
					engine::NotifyAlchemyMenuClosed();
				}
				return RE::BSEventNotifyControl::kContinue;
			}
		};

		class InventoryChangeHandler final : public RE::BSTEventSink<RE::TESContainerChangedEvent> {
		public:
			RE::BSEventNotifyControl ProcessEvent(const RE::TESContainerChangedEvent* a_event,
				RE::BSTEventSource<RE::TESContainerChangedEvent>*) override
			{
				const bool menuActive = IsAlchemyMenuActive();
				if (!a_event || (!nativeAlchemyOpen.load(std::memory_order_acquire) && !menuActive && !confirmations::IsObservationCaptureActive())) {
					return RE::BSEventNotifyControl::kContinue;
				}
				bool expected = false;
				inventoryEventObserved.compare_exchange_strong(expected, true, std::memory_order_acq_rel);
				if (!nativeAlchemyOpen.load(std::memory_order_acquire) && menuActive) {
					nativeAlchemyOpen.store(true, std::memory_order_release);
					menuGeneration.fetch_add(1, std::memory_order_acq_rel);
					engine::NotifyAlchemyMenuOpened();
				}

				auto* player = RE::PlayerCharacter::GetSingleton();
				if (!player) {
					return RE::BSEventNotifyControl::kContinue;
				}
				const auto playerFormID = player->GetFormID();
				const bool addedToPlayer = a_event->newContainer == playerFormID && a_event->oldContainer != playerFormID;
				const bool removedFromPlayer = a_event->oldContainer == playerFormID && a_event->newContainer != playerFormID;
				if (!addedToPlayer && !removedFromPlayer) {
					return RE::BSEventNotifyControl::kContinue;
				}

				auto* form = RE::TESForm::LookupByID(a_event->baseObj);
				if (!form || (!form->Is(RE::FormType::Ingredient) && !form->Is(RE::FormType::AlchemyItem) && !form->Is(RE::FormType::Armor))) {
					return RE::BSEventNotifyControl::kContinue;
				}
				const auto eventCount = static_cast<std::int64_t>(a_event->itemCount);
				if (eventCount == 0) {
					return RE::BSEventNotifyControl::kContinue;
				}
				const auto eventMagnitude = eventCount < 0 ? -eventCount : eventCount;
				confirmations::ObserveInventoryChange(
					form->GetFormID(),
					addedToPlayer ? eventMagnitude : -eventMagnitude);
				QueueConfirmationRecording();
				QueueRecalculation();
				return RE::BSEventNotifyControl::kContinue;
			}
		};

		class EquipChangeHandler final : public RE::BSTEventSink<RE::TESEquipEvent> {
		public:
			RE::BSEventNotifyControl ProcessEvent(const RE::TESEquipEvent* a_event,
				RE::BSTEventSource<RE::TESEquipEvent>*) override
			{
				if (!a_event || !nativeAlchemyOpen.load(std::memory_order_acquire) || !a_event->actor) {
					return RE::BSEventNotifyControl::kContinue;
				}
				auto* player = RE::PlayerCharacter::GetSingleton();
				if (!player || a_event->actor.get() != player) {
					return RE::BSEventNotifyControl::kContinue;
				}
				QueueRecalculation();
				return RE::BSEventNotifyControl::kContinue;
			}
		};

		MenuOpenCloseHandler handler;
		InventoryChangeHandler inventoryChangeHandler;
		EquipChangeHandler equipChangeHandler;
		InputHandler inputHandler;
		std::atomic_bool recalculationQueued = false;
		std::atomic_bool recalculationForceQueued = false;
		bool menuOpenCloseHandlerRegistered = false;
		bool inventoryChangeHandlerRegistered = false;
		bool equipChangeHandlerRegistered = false;
		bool inputHandlerRegistered = false;

		void QueueRecalculation(bool a_force)
		{
			if (devhub::ShouldSuppressInventoryRecalculation()) {
				return;
			}
			if (a_force) {
				recalculationForceQueued.store(true, std::memory_order_release);
			}
			bool expected = false;
			if (!recalculationQueued.compare_exchange_strong(expected, true)) {
				return;
			}
			const auto generation = menuGeneration.load(std::memory_order_acquire);

			auto* taskInterface = SKSE::GetTaskInterface();
			if (!taskInterface) {
				recalculationQueued.store(false);
				recalculationForceQueued.store(false);
				return;
			}
			taskInterface->AddTask([generation]() {
				recalculationQueued.store(false);
				const bool force = recalculationForceQueued.exchange(false, std::memory_order_acq_rel);
				const bool currentMenu = nativeAlchemyOpen.load(std::memory_order_acquire) && generation == menuGeneration.load(std::memory_order_acquire);
				if (!ui::IsVisible() || !currentMenu) {
					return;
				}
				engine::RecalculateAsync([generation]() {
					auto* task = SKSE::GetTaskInterface();
					if (!task) {
						return;
					}
					task->AddTask([generation]() {
						const bool active = nativeAlchemyOpen.load(std::memory_order_acquire) && generation == menuGeneration.load(std::memory_order_acquire);
						if (!active) {
							return;
						}
						confirmations::DrainPendingConfirmations(player);
						RefreshAlchemyMenu(player.hasPerkPurity);
					});
				}, force);
			});
		}
	}

	void Register()
	{
		if (!menuOpenCloseHandlerRegistered) {
			if (auto* uiInterface = RE::UI::GetSingleton()) {
				uiInterface->AddEventSink<RE::MenuOpenCloseEvent>(&handler);
				menuOpenCloseHandlerRegistered = true;
			}
		}
		if (!inventoryChangeHandlerRegistered) {
			if (auto* scriptEventSourceHolder = RE::ScriptEventSourceHolder::GetSingleton()) {
				if (auto* eventSource = scriptEventSourceHolder->GetEventSource<RE::TESContainerChangedEvent>()) {
					eventSource->AddEventSink(&inventoryChangeHandler);
					inventoryChangeHandlerRegistered = true;
				}
			}
		}
		if (!equipChangeHandlerRegistered) {
			if (auto* scriptEventSourceHolder = RE::ScriptEventSourceHolder::GetSingleton()) {
				if (auto* eventSource = scriptEventSourceHolder->GetEventSource<RE::TESEquipEvent>()) {
					eventSource->AddEventSink(&equipChangeHandler);
					equipChangeHandlerRegistered = true;
				}
			}
		}
		if (!inputHandlerRegistered) {
			if (auto* inputDeviceManager = RE::BSInputDeviceManager::GetSingleton()) {
				inputDeviceManager->PrependEventSink<RE::InputEvent*>(&inputHandler);
				inputHandlerRegistered = true;
			}
		}
	}

	void RequestRecalculation(bool a_force)
	{
		QueueRecalculation(a_force);
	}

	void RefreshAlchemyMenu(bool a_hasPurityPerk)
	{
		if (!nativeAlchemyOpen.load(std::memory_order_acquire)) {
			return;
		}
		auto* uiInterface = RE::UI::GetSingleton();
		if (!uiInterface) {
			return;
		}
		auto craftingMenu = uiInterface->GetMenu<RE::CraftingMenu>();
		if (!craftingMenu) {
			return;
		}
		auto* submenu = craftingMenu->GetCraftingSubMenu();
		if (!IsAlchemySubMenu(submenu)) {
			return;
		}
		auto* alchemyMenu = static_cast<RE::CraftingSubMenus::CraftingSubMenus::AlchemyMenu*>(submenu);
		alchemyMenu->playerHasPurityPerk = a_hasPurityPerk;
		alchemyMenu->UpdateCraftingInfo(RE::ActorValue::kAlchemy);
		alchemyMenu->playerHasPurityPerk = a_hasPurityPerk;
	}

	bool GetCursorSnapshot(CursorSnapshot& a_snapshot)
	{
		CaptureNativeCursor();
		std::scoped_lock lock(nativeCursorMutex);
		if (!nativeCursorValid) {
			return false;
		}
		a_snapshot = nativeCursorSnapshot;
		return true;
	}

	std::vector<std::uint32_t> GetSelectedIngredientFormIDsInSelectionOrder()
	{
		std::vector<std::uint32_t> selectedFormIDs;
		if (!nativeAlchemyOpen.load(std::memory_order_acquire)) {
			return selectedFormIDs;
		}

		auto* uiInterface = RE::UI::GetSingleton();
		if (!uiInterface) {
			return selectedFormIDs;
		}
		auto craftingMenu = uiInterface->GetMenu<RE::CraftingMenu>();
		if (!craftingMenu) {
			return selectedFormIDs;
		}
		auto* submenu = craftingMenu->GetCraftingSubMenu();
		if (!IsAlchemySubMenu(submenu)) {
			return selectedFormIDs;
		}

		auto* alchemyMenu = static_cast<RE::CraftingSubMenus::CraftingSubMenus::AlchemyMenu*>(submenu);
		for (const auto selectedIndex : alchemyMenu->selectedIndexes) {
			if (selectedIndex >= alchemyMenu->ingredientEntries.size()) {
				continue;
			}
			const auto& entry = alchemyMenu->ingredientEntries[selectedIndex];
			if (!entry.ingredient || !entry.ingredient->object) {
				continue;
			}
			selectedFormIDs.push_back(entry.ingredient->object->GetFormID());
		}

		return selectedFormIDs;
	}

	std::vector<std::uint32_t> GetSelectedIngredientFormIDs()
	{
		auto selectedFormIDs = GetSelectedIngredientFormIDsInSelectionOrder();
		std::sort(selectedFormIDs.begin(), selectedFormIDs.end());
		selectedFormIDs.erase(std::unique(selectedFormIDs.begin(), selectedFormIDs.end()), selectedFormIDs.end());
		return selectedFormIDs;
	}
}
