#pragma once

#include <cstdint>

namespace alchemist
{
	class Player;

	namespace confirmations
	{
		void BeginAlchemySession() noexcept;
		void EndAlchemySession() noexcept;
		bool IsSessionActive() noexcept;
		bool IsObservationCaptureActive() noexcept;
		bool IsDrainReady() noexcept;
		void ObserveInventoryChange(std::uint32_t a_formID, std::int64_t a_delta) noexcept;
		void RecordCraftedPotions(const Player& a_player) noexcept;
		bool ExportPotionObservations() noexcept;
		void DrainPendingConfirmations(const Player& a_player) noexcept;
	}
}
