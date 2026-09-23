#pragma once

#include <string>

namespace alchemist
{
	class Player;

	struct ConfirmationSettings
	{
		std::string modSettings = "{}";
	};

	namespace modsettings
	{
		void RefreshAndSynchronize(const Player& a_player) noexcept;
		[[nodiscard]] ConfirmationSettings GetConfirmationSettings(const Player& a_player) noexcept;
		[[nodiscard]] ConfirmationSettings GetConfirmationSettings() noexcept;
	}
}
