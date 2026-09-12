#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace alchemist::profiles {
	struct Identity
	{
		std::uint32_t characterID = 0;
		std::string name;
		std::string race;
		std::string raceID;
		std::string gender;

		[[nodiscard]] bool IsKnown() const noexcept;
		[[nodiscard]] bool Matches(const Identity& a_other) const;
	};

	struct ProfileSummary
	{
		int index = 0;
		std::string profileName;
		Identity identity;
		int completedCount = 0;
		int markedCount = 0;
		int protectedEffectCount = 0;
		int protectedIngredientCount = 0;
		bool hasTrackingData = false;
	};

	enum class WindowState
	{
		kUnavailable,
		kReady
	};

	void Initialize();
	void NotifyNewGame();
	void NotifyGameLoadStarted();
	void NotifyGameLoadFinished();
	WindowState PrepareForWindow();
	[[nodiscard]] Identity GetObservedIdentity();
	[[nodiscard]] std::vector<ProfileSummary> GetProfiles();
	[[nodiscard]] int GetCurrentProfile();
	[[nodiscard]] bool HasActiveProfile();
	[[nodiscard]] bool SelectProfile(int a_profileIndex);
	[[nodiscard]] bool CreateProfile();
	[[nodiscard]] bool CloneProfile(int a_sourceProfileIndex);
	[[nodiscard]] bool RenameProfile(int a_profileIndex, const std::string& a_profileName);
	[[nodiscard]] bool DeleteProfile(int a_profileIndex);
	void UpdateExternalSnapshots(std::string a_player, std::string a_caco, std::string a_alchemyPlus);
	bool SaveCurrentProfile();
}
