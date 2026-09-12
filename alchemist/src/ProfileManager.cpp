#include "ProfileManager.h"

#include "main.h"
#include "PluginPaths.h"
#include "RE/B/BGSSaveLoadManager.h"

#include <SimpleIni.h>
#include <nlohmann/json.hpp>

#include <Windows.h>

#include <algorithm>
#include <charconv>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <map>
#include <mutex>
#include <optional>
#include <string_view>
#include <system_error>

namespace alchemist::profiles {
	namespace {
		using json = nlohmann::json;

		constexpr char kConfigurationPath[] = "Data\\SKSE\\Plugins\\alchemist.ini";
		constexpr char kConfigurationFileName[] = "alchemist.ini";
		constexpr std::string_view kUtf8Bom = "\xEF\xBB\xBF";
		constexpr char kProfilesSection[] = "Profiles";
		constexpr char kCurrentKey[] = "Current";
		constexpr char kNewGameKey[] = "NewGame";
		constexpr char kProfilePrefix[] = "Profile ";
		constexpr char kGeneralSection[] = "General";
		constexpr char kTrackingSection[] = "Tracking";
		constexpr char kLocalizationSection[] = "Localization";
		constexpr char kWindowSection[] = "Window";
		constexpr char kPlayerSection[] = "Player";
		constexpr char kCacoSection[] = "CACO";
		constexpr char kAlchemyPlusSection[] = "AlchemyPlus";

		struct ProfileData
		{
			int index = 0;
			std::string profileName;
			Identity identity;
			int ignorePlayer = 0;
			int developer = 0;
			bool singleProfile = false;
			std::string autoprovision; // Obsolete setting; new preferred method is pat <mode> scripts
			int protectIngredients = 0;
			int singlethreaded = 0;
			std::string protectedIngredients;
			int manualProtectionOnly = 0;
			std::string protectedEffects;
			std::string protectedEffectCounts;
			std::string requirements;
			int cacheDurationSeconds = 180;
			int staleRecalculateThresholdMs = 500;
			int craftDebounceMs = 400;
			int filterPotionsBySelectedIngredients = 1;
			std::string language;
			float windowPositionX = -1.0f;
			float windowPositionY = -1.0f;
			float windowWidth = -1.0f;
			float windowHeight = -1.0f;
			std::string playerSnapshot;
			std::string cacoSnapshot;
			std::string alchemyPlusSnapshot;
		};

		std::mutex profileMutex;
		std::vector<ProfileData> profiles;
		std::map<std::uint32_t, int> characterProfiles;
		Identity observedIdentity;
		int activeProfile = 0;
		std::uint32_t previousCharacterID = 0;
		bool awaitingNewGameCharacterID = false;
		bool awaitingGameLoadCharacterID = false;
		bool selectionLost = true;
		bool initialized = false;
		std::atomic_bool profileTransitioning = false;
		std::atomic<std::uint64_t> profileGeneration = 0;

		std::string Trim(std::string_view a_value)
		{
			std::size_t begin = 0;
			while (begin < a_value.size() && std::isspace(static_cast<unsigned char>(a_value[begin])) != 0) {
				++begin;
			}
			std::size_t end = a_value.size();
			while (end > begin && std::isspace(static_cast<unsigned char>(a_value[end - 1])) != 0) {
				--end;
			}
			return std::string(a_value.substr(begin, end - begin));
		}

		std::string Fold(std::string_view a_value)
		{
			std::string result = Trim(a_value);
			for (auto& character : result) {
				character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
			}
			return result;
		}

		bool IsIdentityMatch(const Identity& a_left, const Identity& a_right)
		{
			return a_left.characterID != 0 && a_left.characterID == a_right.characterID;
		}

		bool IsIdentityKnown(const Identity& a_identity)
		{
			return a_identity.characterID != 0 && !a_identity.name.empty() && !a_identity.race.empty() && !a_identity.gender.empty() && Fold(a_identity.gender) != "unknown";
		}

		bool SameIdentity(const Identity& a_left, const Identity& a_right)
		{
			return a_left.characterID == a_right.characterID && a_left.name == a_right.name && a_left.race == a_right.race &&
				a_left.raceID == a_right.raceID && a_left.gender == a_right.gender;
		}

		std::string ProfileSection(int a_index)
		{
			return std::string(kProfilePrefix) + std::to_string(a_index);
		}

		std::filesystem::path ConfigurationPath()
		{
			const auto pluginDirectory = paths::GetPluginDirectory();
			if (!pluginDirectory.empty()) {
				const auto moduleConfiguration = pluginDirectory / kConfigurationFileName;
				std::error_code error;
				if (std::filesystem::exists(moduleConfiguration, error) || error) {
					return moduleConfiguration;
				}
			}
			return std::filesystem::path(kConfigurationPath);
		}

		bool ParseProfileIndex(std::string_view a_section, int& a_index)
		{
			if (!a_section.starts_with(kProfilePrefix)) {
				return false;
			}
			const auto number = a_section.substr(std::string_view(kProfilePrefix).size());
			if (number.empty()) {
				return false;
			}
			const auto* begin = number.data();
			const auto* end = begin + number.size();
			const auto result = std::from_chars(begin, end, a_index);
			return result.ec == std::errc{} && result.ptr == end && a_index > 0;
		}

		bool ParseProfileReference(std::string_view a_value, int& a_index)
		{
			const auto value = Trim(a_value);
			return ParseProfileIndex(value, a_index);
		}

		std::string GetValue(const CSimpleIniA& a_file, const std::string& a_section, const char* a_key, const std::string& a_default)
		{
			const auto* value = a_file.GetValue(a_section.c_str(), a_key, a_default.c_str());
			return value ? value : a_default;
		}

		bool ReadInteger(const CSimpleIniA& a_file, const std::string& a_section, const char* a_key, int a_default, int& a_value)
		{
			const auto* rawValue = a_file.GetValue(a_section.c_str(), a_key, nullptr);
			if (!rawValue) {
				a_value = a_default;
				return true;
			}
			const auto value = Trim(rawValue);
			if (value.empty()) {
				return false;
			}
			int parsed = 0;
			const auto result = std::from_chars(value.data(), value.data() + value.size(), parsed);
			if (result.ec != std::errc{} || result.ptr != value.data() + value.size()) {
				return false;
			}
			a_value = parsed;
			return true;
		}

		bool ParseCharacterID(std::string_view a_rawValue, std::uint32_t& a_value)
		{
			const auto value = Trim(a_rawValue);
			if (value.empty()) {
				a_value = 0;
				return true;
			}
			std::uint64_t parsed = 0;
			int base = 10;
			const char* begin = value.data();
			if (value.size() > 2 && value[0] == '0' && (value[1] == 'x' || value[1] == 'X')) {
				begin += 2;
				base = 16;
			}
			if (begin == value.data() + value.size()) {
				return false;
			}
			const auto result = std::from_chars(begin, value.data() + value.size(), parsed, base);
			if (result.ec != std::errc{} || result.ptr != value.data() + value.size() || parsed > (std::numeric_limits<std::uint32_t>::max)()) {
				return false;
			}
			a_value = static_cast<std::uint32_t>(parsed);
			return true;
		}

		bool ReadCharacterID(const CSimpleIniA& a_file, const std::string& a_section, const char* a_key, std::uint32_t a_default, std::uint32_t& a_value)
		{
			const auto* rawValue = a_file.GetValue(a_section.c_str(), a_key, nullptr);
			if (!rawValue) {
				a_value = a_default;
				return true;
			}
			return ParseCharacterID(rawValue, a_value);
		}

		bool ReadFloat(const CSimpleIniA& a_file, const std::string& a_section, const char* a_key, float a_default, float& a_value)
		{
			const auto* rawValue = a_file.GetValue(a_section.c_str(), a_key, nullptr);
			if (!rawValue) {
				a_value = a_default;
				return true;
			}
			const auto value = Trim(rawValue);
			if (value.empty()) {
				return false;
			}
			char* end = nullptr;
			const auto parsed = std::strtof(value.c_str(), &end);
			if (end != value.c_str() + value.size() || !std::isfinite(parsed)) {
				return false;
			}
			a_value = parsed;
			return true;
		}

		bool ReadFlag(const CSimpleIniA& a_file, const std::string& a_section, const char* a_key, bool a_default, bool& a_value)
		{
			int parsed = 0;
			if (!ReadInteger(a_file, a_section, a_key, a_default ? 1 : 0, parsed) || (parsed != 0 && parsed != 1)) {
				return false;
			}
			a_value = parsed != 0;
			return true;
		}

		std::string DefaultRequirements()
		{
			return kDefaultTrackedRequirements;
		}

		ProfileData MakeDefaultProfile(int a_index)
		{
			ProfileData result;
			result.index = a_index;
			result.profileName = std::string(kProfilePrefix) + std::to_string(a_index);
			result.ignorePlayer = kDefaultIgnorePlayer;
			result.developer = kDefaultDeveloper;
			result.singleProfile = kDefaultSingleProfile != 0;
			result.autoprovision = kDefaultAutoprovision;
			result.protectIngredients = kDefaultProtectIngredients;
			result.singlethreaded = kDefaultSinglethreaded;
			result.protectedIngredients = kDefaultProtectedIngredients;
			result.manualProtectionOnly = kDefaultManualProtectionOnly;
			result.protectedEffects = kDefaultProtectedEffects;
			result.protectedEffectCounts = kDefaultProtectedEffectCounts;
			result.requirements = DefaultRequirements();
			result.cacheDurationSeconds = kDefaultCacheDurationSeconds;
			result.staleRecalculateThresholdMs = kDefaultStaleRecalculateThresholdMs;
			result.craftDebounceMs = kDefaultCraftDebounceMs;
			result.filterPotionsBySelectedIngredients = kDefaultFilterPotionsBySelectedIngredients;
			result.language = kDefaultLanguage;
			result.windowPositionX = kDefaultWindowPositionX;
			result.windowPositionY = kDefaultWindowPositionY;
			result.windowWidth = kDefaultWindowWidth;
			result.windowHeight = kDefaultWindowHeight;
			return result;
		}

		bool ReadProfileValues(
			const CSimpleIniA& a_file,
			const std::string& a_section,
			ProfileData& a_profile,
			std::string* a_failureReason = nullptr)
		{
			if (a_failureReason) {
				a_failureReason->clear();
			}
			const auto recordFailure = [a_failureReason](std::string_view a_reason) {
				if (a_failureReason && a_failureReason->empty()) {
					*a_failureReason = a_reason;
				}
			};
			bool valid = true;
			CSimpleIniA::TNamesDepend keys;
			if (!a_file.GetAllKeys(a_section.c_str(), keys)) {
				recordFailure("the section has no readable keys");
				return false;
			}
			a_profile.profileName = Trim(GetValue(a_file, a_section, "ProfileName", a_profile.profileName));
			valid = ReadCharacterID(a_file, a_section, "CharacterID", a_profile.identity.characterID, a_profile.identity.characterID) && valid;
			a_profile.identity.name = GetValue(a_file, a_section, "Name", a_profile.identity.name);
			a_profile.identity.race = GetValue(a_file, a_section, "Race", a_profile.identity.race);
			a_profile.identity.raceID = GetValue(a_file, a_section, "RaceID", a_profile.identity.raceID);
			a_profile.identity.gender = GetValue(a_file, a_section, "Gender", a_profile.identity.gender);
			valid = ReadInteger(a_file, a_section, "IgnorePlayer", a_profile.ignorePlayer, a_profile.ignorePlayer) && valid;
			valid = ReadInteger(a_file, a_section, "developer", a_profile.developer, a_profile.developer) && valid;
			bool singleProfile = a_profile.singleProfile;
			valid = ReadFlag(a_file, a_section, "singleprofile", a_profile.singleProfile, singleProfile) && valid;
			a_profile.singleProfile = singleProfile;
			a_profile.autoprovision = GetValue(a_file, a_section, "autoprovision", a_profile.autoprovision);
			valid = ReadInteger(a_file, a_section, "ProtectIngredients", a_profile.protectIngredients, a_profile.protectIngredients) && valid;
			valid = ReadInteger(a_file, a_section, "Singlethreaded", a_profile.singlethreaded, a_profile.singlethreaded) && valid;
			a_profile.protectedIngredients = GetValue(a_file, a_section, "ProtectedIngredients", a_profile.protectedIngredients);
			valid = ReadInteger(a_file, a_section, "ManualProtectionOnly", a_profile.manualProtectionOnly, a_profile.manualProtectionOnly) && valid;
			a_profile.protectedEffects = GetValue(a_file, a_section, "ProtectedEffects", a_profile.protectedEffects);
			a_profile.protectedEffectCounts = GetValue(a_file, a_section, "ProtectedEffectCounts", a_profile.protectedEffectCounts);
			a_profile.requirements = GetValue(a_file, a_section, "Requirements", a_profile.requirements);
			valid = ReadInteger(a_file, a_section, "CacheDurationSeconds", a_profile.cacheDurationSeconds, a_profile.cacheDurationSeconds) && valid;
			valid = ReadInteger(a_file, a_section, "StaleRecalculateThresholdMs", a_profile.staleRecalculateThresholdMs, a_profile.staleRecalculateThresholdMs) && valid;
			valid = ReadInteger(a_file, a_section, "CraftDebounceMs", a_profile.craftDebounceMs, a_profile.craftDebounceMs) && valid;
			valid = ReadInteger(a_file, a_section, "FilterPotionsBySelectedIngredients", a_profile.filterPotionsBySelectedIngredients, a_profile.filterPotionsBySelectedIngredients) && valid;
			a_profile.language = GetValue(a_file, a_section, "Language", a_profile.language);
			valid = ReadFloat(a_file, a_section, "PositionX", a_profile.windowPositionX, a_profile.windowPositionX) && valid;
			valid = ReadFloat(a_file, a_section, "PositionY", a_profile.windowPositionY, a_profile.windowPositionY) && valid;
			valid = ReadFloat(a_file, a_section, "Width", a_profile.windowWidth, a_profile.windowWidth) && valid;
			valid = ReadFloat(a_file, a_section, "Height", a_profile.windowHeight, a_profile.windowHeight) && valid;
			a_profile.playerSnapshot = GetValue(a_file, a_section, "Player", a_profile.playerSnapshot);
			a_profile.cacoSnapshot = GetValue(a_file, a_section, "CACO", a_profile.cacoSnapshot);
			a_profile.alchemyPlusSnapshot = GetValue(a_file, a_section, "AlchemyPlus", a_profile.alchemyPlusSnapshot);
			const auto validateSnapshot = [&recordFailure](const char* a_key, const std::string& a_snapshot) {
				if (a_snapshot.empty()) {
					return true;
				}
				try {
					const auto document = json::parse(a_snapshot);
					if (!document.is_object()) {
						recordFailure(std::string("snapshot '") + a_key + "' is not a JSON object");
						return false;
					}
				} catch (const json::exception&) {
					recordFailure(std::string("snapshot '") + a_key + "' contains invalid JSON");
					return false;
				}
				return true;
			};
			valid = validateSnapshot("Requirements", a_profile.requirements) && valid;
			valid = validateSnapshot("Player", a_profile.playerSnapshot) && valid;
			valid = validateSnapshot("CACO", a_profile.cacoSnapshot) && valid;
			valid = validateSnapshot("AlchemyPlus", a_profile.alchemyPlusSnapshot) && valid;
			if (!valid && a_failureReason && a_failureReason->empty()) {
				recordFailure("one or more scalar, flag, or floating-point values are invalid");
			}
			return valid;
		}

		bool LoadFile(CSimpleIniA& a_file)
		{
			a_file.SetUnicode(true);
			a_file.SetQuotes(true);
			const auto configurationPath = ConfigurationPath();
			if (configurationPath.empty()) {
				return false;
			}
			std::error_code error;
			const bool exists = std::filesystem::exists(configurationPath, error);
			if (error) {
				return false;
			}
			if (!exists) {
				return true;
			}
			return a_file.LoadFile(configurationPath.string().c_str()) >= 0;
		}

		bool IsKnownLegacySection(std::string_view a_section)
		{
			return a_section == kGeneralSection ||
				a_section == kTrackingSection || a_section == kLocalizationSection || a_section == kWindowSection ||
				a_section == kPlayerSection || a_section == kCacoSection || a_section == kAlchemyPlusSection;
		}

		bool ReadLegacySnapshot(const CSimpleIniA& a_file, const char* a_section, std::string& a_snapshot)
		{
			if (!a_file.SectionExists(a_section)) {
				return true;
			}
			CSimpleIniA::TNamesDepend keys;
			if (!a_file.GetAllKeys(a_section, keys)) {
				return false;
			}
			json snapshot = json::object();
			for (const auto& key : keys) {
				if (!key.pItem) {
					return false;
				}
				const auto* value = a_file.GetValue(a_section, key.pItem, nullptr);
				if (!value) {
					return false;
				}
				snapshot[key.pItem] = value;
			}
			a_snapshot = snapshot.dump();
			return true;
		}

		void BackupMalformedFile()
		{
			const auto source = ConfigurationPath();
			if (source.empty()) {
				return;
			}
			for (std::uint32_t suffix = 0; suffix < 10000; ++suffix) {
				const auto backupName = suffix == 0 ? "alchemist.backup.ini" : "alchemist.backup" + std::to_string(suffix + 1) + ".ini";
				const auto backupPath = source.parent_path() / backupName;
				std::error_code error;
				if (std::filesystem::exists(backupPath, error)) {
					continue;
				}
				if (error) {
					return;
				}
				std::filesystem::copy_file(source, backupPath, std::filesystem::copy_options::none, error);
				if (!error) {
					return;
				}
				return;
			}
		}

		void SetInteger(CSimpleIniA& a_file, const std::string& a_section, const char* a_key, int a_value)
		{
			const auto value = std::to_string(a_value);
			a_file.SetValue(a_section.c_str(), a_key, value.c_str());
		}

		void SetCharacterID(CSimpleIniA& a_file, const std::string& a_section, const char* a_key, std::uint32_t a_value)
		{
			const auto value = std::to_string(a_value);
			a_file.SetValue(a_section.c_str(), a_key, value.c_str());
		}

		void SetFloat(CSimpleIniA& a_file, const std::string& a_section, const char* a_key, float a_value)
		{
			const auto value = std::to_string(a_value);
			a_file.SetValue(a_section.c_str(), a_key, value.c_str());
		}

		void WriteProfile(CSimpleIniA& a_file, const ProfileData& a_profile)
		{
			const auto section = ProfileSection(a_profile.index);
			a_file.SetValue(section.c_str(), "ProfileName", a_profile.profileName.c_str());
			SetCharacterID(a_file, section, "CharacterID", a_profile.identity.characterID);
			a_file.SetValue(section.c_str(), "Name", a_profile.identity.name.c_str());
			a_file.SetValue(section.c_str(), "Race", a_profile.identity.race.c_str());
			a_file.SetValue(section.c_str(), "RaceID", a_profile.identity.raceID.c_str());
			a_file.SetValue(section.c_str(), "Gender", a_profile.identity.gender.c_str());
			SetInteger(a_file, section, "IgnorePlayer", a_profile.ignorePlayer);
			SetInteger(a_file, section, "developer", a_profile.developer);
			SetInteger(a_file, section, "singleprofile", a_profile.singleProfile ? 1 : 0);
			a_file.SetValue(section.c_str(), "autoprovision", a_profile.autoprovision.c_str());
			SetInteger(a_file, section, "ProtectIngredients", a_profile.protectIngredients);
			SetInteger(a_file, section, "Singlethreaded", a_profile.singlethreaded);
			a_file.SetValue(section.c_str(), "ProtectedIngredients", a_profile.protectedIngredients.c_str());
			SetInteger(a_file, section, "ManualProtectionOnly", a_profile.manualProtectionOnly);
			a_file.SetValue(section.c_str(), "ProtectedEffects", a_profile.protectedEffects.c_str());
			a_file.SetValue(section.c_str(), "ProtectedEffectCounts", a_profile.protectedEffectCounts.c_str());
			a_file.SetValue(section.c_str(), "Requirements", a_profile.requirements.c_str());
			SetInteger(a_file, section, "CacheDurationSeconds", a_profile.cacheDurationSeconds);
			SetInteger(a_file, section, "StaleRecalculateThresholdMs", a_profile.staleRecalculateThresholdMs);
			SetInteger(a_file, section, "CraftDebounceMs", a_profile.craftDebounceMs);
			SetInteger(a_file, section, "FilterPotionsBySelectedIngredients", a_profile.filterPotionsBySelectedIngredients);
			a_file.SetValue(section.c_str(), "Language", a_profile.language.c_str());
			SetFloat(a_file, section, "PositionX", a_profile.windowPositionX);
			SetFloat(a_file, section, "PositionY", a_profile.windowPositionY);
			SetFloat(a_file, section, "Width", a_profile.windowWidth);
			SetFloat(a_file, section, "Height", a_profile.windowHeight);
			a_file.SetValue(section.c_str(), "Player", a_profile.playerSnapshot.c_str());
			a_file.SetValue(section.c_str(), "CACO", a_profile.cacoSnapshot.c_str());
			a_file.SetValue(section.c_str(), "AlchemyPlus", a_profile.alchemyPlusSnapshot.c_str());
		}

		std::size_t FindSectionHeader(std::string_view a_data, std::size_t a_start, std::string_view a_name = {})
		{
			std::size_t lineStart = a_start;
			while (lineStart < a_data.size()) {
				const auto newline = a_data.find('\n', lineStart);
				const auto lineEnd = newline == std::string_view::npos ? a_data.size() : newline;
				std::string_view line = a_data.substr(lineStart, lineEnd - lineStart);
				if (!line.empty() && line.back() == '\r') {
					line.remove_suffix(1);
				}
				std::size_t headerOffset = 0;
				if (lineStart == 0 && line.starts_with(kUtf8Bom)) {
					headerOffset = kUtf8Bom.size();
					line.remove_prefix(headerOffset);
				}
				const auto normalizedLine = Trim(line);
				if (normalizedLine.size() >= 2 && normalizedLine.front() == '[' && normalizedLine.back() == ']' &&
					(a_name.empty() || normalizedLine.substr(1, normalizedLine.size() - 2) == a_name)) {
					return lineStart + headerOffset;
				}
				if (newline == std::string_view::npos) {
					break;
				}
				lineStart = newline + 1;
			}
			return std::string_view::npos;
		}

		bool MoveProfilesSectionToFront(const std::filesystem::path& a_path)
		{
			std::ifstream input(a_path, std::ios::binary);
			if (!input) {
				return false;
			}
			const std::string contents((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
			input.close();
			const auto firstSection = FindSectionHeader(contents, 0);
			const auto profilesSection = FindSectionHeader(contents, 0, kProfilesSection);
			if (firstSection == std::string_view::npos || profilesSection == std::string_view::npos) {
				return false;
			}
			if (firstSection == profilesSection) {
				return true;
			}
			const auto profileHeaderEnd = contents.find('\n', profilesSection);
			const auto profileBodyStart = profileHeaderEnd == std::string::npos ? contents.size() : profileHeaderEnd + 1;
			const auto profilesEnd = FindSectionHeader(contents, profileBodyStart);
			const auto profileBlockEnd = profilesEnd == std::string_view::npos ? contents.size() : profilesEnd;
			std::string reordered;
			reordered.reserve(contents.size());
			reordered.append(contents, 0, firstSection);
			reordered.append(contents, profilesSection, profileBlockEnd - profilesSection);
			reordered.append(contents, firstSection, profilesSection - firstSection);
			reordered.append(contents, profileBlockEnd, std::string::npos);
			std::ofstream output(a_path, std::ios::binary | std::ios::trunc);
			if (!output) {
				return false;
			}
			output.write(reordered.data(), static_cast<std::streamsize>(reordered.size()));
			if (!output) {
				return false;
			}
			return true;
		}

		bool ProfilesSectionIsFirst(const std::filesystem::path& a_path)
		{
			std::ifstream input(a_path, std::ios::binary);
			if (!input) {
				return false;
			}
			const std::string contents((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
			if (input.bad()) {
				return false;
			}
			const auto firstSection = FindSectionHeader(contents, 0);
			const auto profilesSection = FindSectionHeader(contents, 0, kProfilesSection);
			return firstSection != std::string_view::npos && firstSection == profilesSection;
		}

		bool SaveProfilesLocked()
		{
			CSimpleIniA file;
			if (profiles.empty()) {
				return false;
			}
			std::set<std::string> profileNames;
			for (const auto& profile : profiles) {
				if (profile.profileName.empty() || !profileNames.insert(Fold(profile.profileName)).second) {
					return false;
				}
			}
			if (!LoadFile(file)) {
				file.Reset();
				file.SetUnicode(true);
				file.SetQuotes(true);
			} else {
				CSimpleIniA::TNamesDepend sections;
				file.GetAllSections(sections);
				std::vector<std::string> sectionsToDelete;
				std::vector<std::string> profileSectionsToClean;
				for (const auto& section : sections) {
					if (!section.pItem) {
						continue;
					}
					const auto sectionName = std::string(section.pItem);
					int profileIndex = 0;
					if (ParseProfileIndex(sectionName, profileIndex)) {
						const auto profile = std::find_if(profiles.begin(), profiles.end(), [profileIndex](const auto& entry) {
							return entry.index == profileIndex;
						});
						if (profile == profiles.end()) {
							sectionsToDelete.push_back(sectionName);
						} else {
							profileSectionsToClean.push_back(sectionName);
						}
					} else if (IsKnownLegacySection(sectionName) || sectionName == kProfilesSection) {
						sectionsToDelete.push_back(sectionName);
					}
				}
				for (const auto& section : sectionsToDelete) {
					file.Delete(section.c_str(), nullptr);
				}
				for (const auto& section : profileSectionsToClean) {
					file.Delete(section.c_str(), kCurrentKey);
					file.Delete(section.c_str(), kNewGameKey);
				}
				file.Delete("", kCurrentKey);
				file.Delete("", kNewGameKey);
			}
			file.SetValue(kProfilesSection, nullptr, nullptr);
			for (const auto& [characterID, profileIndex] : characterProfiles) {
				if (characterID == 0) {
					return false;
				}
				const auto profile = std::find_if(profiles.begin(), profiles.end(), [profileIndex](const auto& entry) {
					return entry.index == profileIndex;
				});
				if (profile == profiles.end() || profile->identity.characterID != characterID) {
					return false;
				}
				const auto key = std::to_string(characterID);
				const auto section = ProfileSection(profileIndex);
				file.SetValue(kProfilesSection, key.c_str(), section.c_str());
			}
			for (const auto& profile : profiles) {
				WriteProfile(file, profile);
			}
			const auto target = ConfigurationPath();
			if (target.empty()) {
				return false;
			}
			std::filesystem::path temporary;
			for (std::uint32_t suffix = 0; suffix < 10000; ++suffix) {
				const auto temporaryName = suffix == 0 ? "alchemist.ini.tmp" : "alchemist.ini.tmp" + std::to_string(suffix + 1);
				const auto candidate = target.parent_path() / temporaryName;
				std::error_code error;
				if (!std::filesystem::exists(candidate, error)) {
					if (error) {
						return false;
					}
					temporary = candidate;
					break;
				}
			}
			if (temporary.empty()) {
				return false;
			}

			if (file.SaveFile(temporary.string().c_str()) < 0) {
				return false;
			}
			if (!MoveProfilesSectionToFront(temporary)) {
				std::error_code removeError;
				std::filesystem::remove(temporary, removeError);
				return false;
			}

			if (!MoveFileExW(temporary.c_str(), target.c_str(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
				std::error_code removeError;
				std::filesystem::remove(temporary, removeError);
				return false;
			}
			if (!ProfilesSectionIsFirst(target)) {
				if (!MoveProfilesSectionToFront(target) || !ProfilesSectionIsFirst(target)) {
					return false;
				}
			}
			return true;
		}

		bool ReadProfiles(
			const CSimpleIniA& a_file,
			std::vector<ProfileData>& a_profiles,
			std::map<std::uint32_t, int>& a_characterProfiles,
			bool& a_requiresSave)
		{
			const auto reject = [](const char*) {
				return false;
			};
			CSimpleIniA::TNamesDepend sections;
			a_file.GetAllSections(sections);
			std::uint32_t rootCurrentCharacterID = 0;
			int rootNewGame = 0;
			bool hasRootCurrentCharacterID = false;
			bool hasRootNewGame = false;
			CSimpleIniA::TNamesDepend rootKeys;
			if (a_file.GetAllKeys("", rootKeys)) {
				for (const auto& key : rootKeys) {
					if (!key.pItem) {
						return reject("the root section contains a key without a name");
					}
					if (std::string_view(key.pItem) == kCurrentKey) {
						if (hasRootCurrentCharacterID || !ReadCharacterID(a_file, "", kCurrentKey, 0, rootCurrentCharacterID)) {
							return reject("the root Current value is duplicated or invalid");
						}
						hasRootCurrentCharacterID = true;
					} else if (std::string_view(key.pItem) == kNewGameKey) {
						if (hasRootNewGame || !ReadInteger(a_file, "", kNewGameKey, 0, rootNewGame) || (rootNewGame != 0 && rootNewGame != 1)) {
							return reject("the root NewGame value is duplicated or invalid");
						}
						hasRootNewGame = true;
					} else {
						return reject("the root section contains an unknown key");
					}
				}
			}
			bool hasProfileSections = false;
			bool hasLegacySections = false;
			bool hasProfilesSection = false;
			bool everyProfileHasCharacterIDKey = true;
			std::vector<int> indices;
			for (const auto& section : sections) {
				if (!section.pItem) {
					return reject("a section has no name");
				}
				if (*section.pItem == '\0') {
					continue;
				}
				int index = 0;
				if (ParseProfileIndex(section.pItem, index)) {
					if (std::find(indices.begin(), indices.end(), index) != indices.end()) {
						return false;
					}
					CSimpleIniA::TNamesDepend profileKeys;
					bool hasCharacterIDKey = false;
					if (a_file.GetAllKeys(section.pItem, profileKeys)) {
						for (const auto& key : profileKeys) {
							if (key.pItem && std::string_view(key.pItem) == "CharacterID") {
								hasCharacterIDKey = true;
								break;
							}
						}
					}
					everyProfileHasCharacterIDKey = everyProfileHasCharacterIDKey && hasCharacterIDKey;
					hasProfileSections = true;
					indices.push_back(index);
				} else if (std::string_view(section.pItem) == kProfilesSection) {
					hasProfilesSection = true;
				} else if (IsKnownLegacySection(section.pItem)) {
					hasLegacySections = true;
				} else {
					return false;
				}
			}
			if (!hasProfileSections && !hasLegacySections) {
				if (rootKeys.empty() && !hasProfilesSection) {
					a_profiles.clear();
					a_profiles.push_back(MakeDefaultProfile(1));
					a_characterProfiles.clear();
					a_requiresSave = true;
					return true;
				}
				return reject("the file contains neither profile sections nor recognized legacy sections");
			}

			std::map<std::uint32_t, int> parsedCharacterProfiles;
			bool mappingNeedsNormalization = false;
			int legacyCurrentProfile = 0;
			bool hasLegacyCurrentProfile = false;
			int legacyNewGame = 0;
			bool hasLegacyNewGame = false;
			if (hasProfilesSection) {
				CSimpleIniA::TNamesDepend profileMapKeys;
				if (a_file.GetAllKeys(kProfilesSection, profileMapKeys)) {
					for (const auto& key : profileMapKeys) {
						if (!key.pItem) {
							return reject("the Profiles section contains a key without a name");
						}
						const auto keyName = Trim(key.pItem);
						if (keyName == "CurrentProfile") {
							if (hasLegacyCurrentProfile || !ReadInteger(a_file, kProfilesSection, "CurrentProfile", 0, legacyCurrentProfile) || legacyCurrentProfile < 0) {
								return reject("the legacy Profiles CurrentProfile value is duplicated or invalid");
							}
							hasLegacyCurrentProfile = true;
							continue;
						}
						if (keyName == kNewGameKey) {
							if (hasLegacyNewGame || !ReadInteger(a_file, kProfilesSection, kNewGameKey, 0, legacyNewGame) || (legacyNewGame != 0 && legacyNewGame != 1)) {
								return reject("the legacy Profiles NewGame value is duplicated or invalid");
							}
							hasLegacyNewGame = true;
							continue;
						}

						std::uint32_t characterID = 0;
						if (!ParseCharacterID(keyName, characterID) || characterID == 0) {
							return reject("the Profiles section contains an invalid Character ID key");
						}
						const auto* rawProfile = a_file.GetValue(kProfilesSection, key.pItem, nullptr);
						int profileIndex = 0;
						if (!rawProfile || !ParseProfileReference(rawProfile, profileIndex)) {
							return reject("the Profiles section contains an invalid profile reference");
						}
						if (!parsedCharacterProfiles.emplace(characterID, profileIndex).second) {
							return reject("the Profiles section contains duplicate Character ID mappings");
						}
						mappingNeedsNormalization = mappingNeedsNormalization || keyName != std::to_string(characterID);
					}
				}
			}

			ProfileData legacyDefaults = MakeDefaultProfile(1);
			const auto readProfileValues = [&a_file](const char* a_section, ProfileData& a_profile) {
				std::string failureReason;
				if (ReadProfileValues(a_file, a_section, a_profile, &failureReason)) {
					return true;
				}
				return false;
			};
			if (hasLegacySections) {
				if (a_file.SectionExists(kGeneralSection) && !readProfileValues(kGeneralSection, legacyDefaults)) {
					return false;
				}
				if (a_file.SectionExists(kTrackingSection) && !readProfileValues(kTrackingSection, legacyDefaults)) {
					return false;
				}
				if (a_file.SectionExists(kLocalizationSection) && !readProfileValues(kLocalizationSection, legacyDefaults)) {
					return false;
				}
				if (a_file.SectionExists(kWindowSection) && !readProfileValues(kWindowSection, legacyDefaults)) {
					return false;
				}
				if (!ReadLegacySnapshot(a_file, kPlayerSection, legacyDefaults.playerSnapshot) ||
					!ReadLegacySnapshot(a_file, kCacoSection, legacyDefaults.cacoSnapshot) ||
					!ReadLegacySnapshot(a_file, kAlchemyPlusSection, legacyDefaults.alchemyPlusSnapshot)) {
					return false;
				}
			}

			std::sort(indices.begin(), indices.end());
			a_profiles.clear();
			a_profiles.reserve((std::max)(std::size_t{ 1 }, indices.size()));
			for (const auto index : indices) {
				a_profiles.push_back(legacyDefaults);
				a_profiles.back().index = index;
				if (!readProfileValues(ProfileSection(index).c_str(), a_profiles.back())) {
					return false;
				}
			}
			if (a_profiles.empty()) {
				legacyDefaults.index = 1;
				a_profiles.push_back(std::move(legacyDefaults));
			}

			bool hasProfileMetadata = false;
			int profileFlagCurrent = 0;
			for (const auto index : indices) {
				CSimpleIniA::TNamesDepend keys;
				if (a_file.GetAllKeys(ProfileSection(index).c_str(), keys)) {
					for (const auto& key : keys) {
						if (!key.pItem) {
							return reject("a profile section contains a key without a name");
						}
						if (std::string_view(key.pItem) == kCurrentKey) {
							bool current = false;
							if (!ReadFlag(a_file, ProfileSection(index), kCurrentKey, false, current)) {
								return reject("a legacy profile Current value is invalid");
							}
							if (current) {
								if (profileFlagCurrent != 0) {
									return reject("more than one profile is marked current");
								}
								profileFlagCurrent = index;
							}
							hasProfileMetadata = true;
						} else if (std::string_view(key.pItem) == kNewGameKey) {
							bool newGame = false;
							if (!ReadFlag(a_file, ProfileSection(index), kNewGameKey, false, newGame)) {
								return reject("a legacy profile NewGame value is invalid");
							}
							hasProfileMetadata = true;
						}
					}
				}
			}

			// Re-emit the file on every successful load so the section-order invariant is
			// self-healing even if an older plugin or an external editor rewrote it.
			a_requiresSave = true;
			std::set<std::string> profileNames;
			for (const auto& profile : a_profiles) {
				if (profile.profileName.empty() || !profileNames.insert(Fold(profile.profileName)).second) {
					return false;
				}
			}

			const auto parsedMappingCount = parsedCharacterProfiles.size();
			a_characterProfiles = std::move(parsedCharacterProfiles);
			const auto findProfile = [&a_profiles](int a_profileIndex) {
				return std::find_if(a_profiles.begin(), a_profiles.end(), [a_profileIndex](const auto& profile) {
					return profile.index == a_profileIndex;
				});
			};
			for (const auto& [characterID, profileIndex] : a_characterProfiles) {
				const auto profile = findProfile(profileIndex);
				if (profile == a_profiles.end() || profile->identity.characterID != characterID) {
					return reject("a Character ID mapping points to a profile with a different Character ID");
				}
			}

			int legacySelectedProfile = hasLegacyCurrentProfile ? legacyCurrentProfile : profileFlagCurrent;
			if (hasRootCurrentCharacterID && rootCurrentCharacterID != 0) {
				const auto exactMatches = std::find_if(a_profiles.rbegin(), a_profiles.rend(), [rootCurrentCharacterID](const auto& profile) {
					return profile.identity.characterID == rootCurrentCharacterID;
				});
				if (exactMatches != a_profiles.rend() && a_characterProfiles.find(rootCurrentCharacterID) == a_characterProfiles.end()) {
					a_characterProfiles.emplace(rootCurrentCharacterID, exactMatches->index);
				}
				if (exactMatches == a_profiles.rend() && rootCurrentCharacterID <= static_cast<std::uint32_t>((std::numeric_limits<int>::max)())) {
					const auto legacyProfile = findProfile(static_cast<int>(rootCurrentCharacterID));
					if (legacyProfile != a_profiles.end() && legacyProfile->identity.characterID != 0) {
						a_characterProfiles.emplace(legacyProfile->identity.characterID, legacyProfile->index);
					}
				}
			}
			if (legacySelectedProfile != 0) {
				const auto legacyProfile = findProfile(legacySelectedProfile);
				if (legacyProfile == a_profiles.end()) {
					a_requiresSave = true;
				} else if (legacyProfile->identity.characterID != 0 && a_characterProfiles.find(legacyProfile->identity.characterID) == a_characterProfiles.end()) {
					a_characterProfiles.emplace(legacyProfile->identity.characterID, legacyProfile->index);
				}
			}
			for (const auto& profile : a_profiles) {
				if (profile.identity.characterID == 0 || a_characterProfiles.find(profile.identity.characterID) != a_characterProfiles.end()) {
					continue;
				}
				a_characterProfiles[profile.identity.characterID] = profile.index;
			}
			if (a_characterProfiles.size() != parsedMappingCount) {
				a_requiresSave = true;
			}
			if (hasProfileSections && hasLegacySections) {
				a_requiresSave = true;
			}
			return true;
		}

		std::string RaceDisplayName(const RE::TESRace* a_race)
		{
			if (!a_race) {
				return {};
			}
			if (const auto* name = a_race->GetName(); name && *name) {
				return name;
			}
			if (const auto* editorID = a_race->GetFormEditorID(); editorID && *editorID) {
				return editorID;
			}
			return "formid:" + std::to_string(a_race->GetFormID());
		}

		Identity CaptureIdentity()
		{
			Identity result;
			if (const auto* saveManager = RE::BGSSaveLoadManager::GetSingleton()) {
				result.characterID = saveManager->currentCharacterID;
			}
			const auto* player = RE::PlayerCharacter::GetSingleton();
			if (!player) {
				return result;
			}
			const auto* actorBase = player->GetActorBase();
			const auto* actorBaseName = actorBase ? actorBase->GetName() : nullptr;
			const auto* playerName = player->GetName();
			if (actorBaseName && *actorBaseName) {
				result.name = actorBaseName;
			} else if (playerName && *playerName) {
				result.name = playerName;
			}
			const auto* race = player->GetRace();
			result.race = RaceDisplayName(race);
			if (race) {
				if (const auto* editorID = race->GetFormEditorID(); editorID && *editorID) {
					result.raceID = editorID;
				} else {
					result.raceID = "formid:" + std::to_string(race->GetFormID());
				}
			}
			if (actorBase) {
				switch (actorBase->GetSex()) {
				case RE::SEXES::kMale:
					result.gender = "Male";
					break;
				case RE::SEXES::kFemale:
					result.gender = "Female";
					break;
				default:
					result.gender = "Unknown";
					break;
				}
			}
			return result;
		}

		int CountTokens(const std::string& a_value)
		{
			int result = 0;
			std::size_t begin = 0;
			while (begin < a_value.size()) {
				const auto end = a_value.find(',', begin);
				const auto token = std::string_view(a_value).substr(begin, end == std::string::npos ? std::string::npos : end - begin);
				if (!Trim(token).empty()) {
					++result;
				}
				if (end == std::string::npos) {
					break;
				}
				begin = end + 1;
			}
			return result;
		}

		void CountRequirements(const std::string& a_value, int& a_completed, int& a_marked)
		{
			try {
				const auto document = json::parse(a_value);
				if (!document.is_object()) {
					return;
				}
				for (const auto* key : { "manual", "overrides" }) {
					if (!document.contains(key) || !document.at(key).is_array()) {
						continue;
					}
					for (const auto& value : document.at(key)) {
						++a_marked;
						if (value.is_object() && value.value("completed", false)) {
							++a_completed;
						}
					}
				}
			} catch (const json::exception&) {
			}
		}

		ProfileSummary Summarize(const ProfileData& a_profile)
		{
			ProfileSummary result;
			result.index = a_profile.index;
			result.profileName = a_profile.profileName;
			result.identity = a_profile.identity;
			result.protectedIngredientCount = CountTokens(a_profile.protectedIngredients);
			result.protectedEffectCount = CountTokens(a_profile.protectedEffects);
			CountRequirements(a_profile.requirements, result.completedCount, result.markedCount);
			result.hasTrackingData = a_profile.protectedIngredients != kDefaultProtectedIngredients ||
				a_profile.protectedEffects != kDefaultProtectedEffects ||
				a_profile.protectedEffectCounts != kDefaultProtectedEffectCounts ||
				a_profile.requirements != kDefaultTrackedRequirements;
			return result;
		}

		void ApplyProfileToSettings(const ProfileData& a_profile)
		{
			kIgnorePlayer.SetValue(a_profile.ignorePlayer);
			kDeveloper.SetValue(a_profile.developer);
			kSingleProfile.SetValue(a_profile.singleProfile ? 1 : 0);
			kAutoprovision.SetValue(a_profile.autoprovision);
			kProtectIngredients.SetValue(a_profile.protectIngredients);
			kSinglethreaded.SetValue(a_profile.singlethreaded);
			kProtectedIngredients.SetValue(a_profile.protectedIngredients);
			kManualProtectionOnly.SetValue(a_profile.manualProtectionOnly);
			kProtectedEffects.SetValue(a_profile.protectedEffects);
			kProtectedEffectCounts.SetValue(a_profile.protectedEffectCounts);
			kTrackedRequirements.SetValue(a_profile.requirements);
			kCacheDurationSeconds.SetValue(a_profile.cacheDurationSeconds);
			kStaleRecalculateThresholdMs.SetValue(a_profile.staleRecalculateThresholdMs);
			kCraftDebounceMs.SetValue(a_profile.craftDebounceMs);
			kFilterPotionsBySelectedIngredients.SetValue(a_profile.filterPotionsBySelectedIngredients);
			kLanguage.SetValue(a_profile.language);
			kWindowPositionX.SetValue(a_profile.windowPositionX);
			kWindowPositionY.SetValue(a_profile.windowPositionY);
			kWindowWidth.SetValue(a_profile.windowWidth);
			kWindowHeight.SetValue(a_profile.windowHeight);
		}

		void CaptureSettings(ProfileData& a_profile)
		{
			a_profile.ignorePlayer = kIgnorePlayer.GetValue();
			a_profile.developer = kDeveloper.GetValue();
			a_profile.singleProfile = kSingleProfile.GetValue() != 0;
			a_profile.autoprovision = kAutoprovision.GetValue();
			a_profile.protectIngredients = kProtectIngredients.GetValue();
			a_profile.singlethreaded = kSinglethreaded.GetValue();
			a_profile.protectedIngredients = kProtectedIngredients.GetValue();
			a_profile.manualProtectionOnly = kManualProtectionOnly.GetValue();
			a_profile.protectedEffects = kProtectedEffects.GetValue();
			a_profile.protectedEffectCounts = kProtectedEffectCounts.GetValue();
			a_profile.requirements = kTrackedRequirements.GetValue();
			a_profile.cacheDurationSeconds = kCacheDurationSeconds.GetValue();
			a_profile.staleRecalculateThresholdMs = kStaleRecalculateThresholdMs.GetValue();
			a_profile.craftDebounceMs = kCraftDebounceMs.GetValue();
			a_profile.filterPotionsBySelectedIngredients = kFilterPotionsBySelectedIngredients.GetValue();
			a_profile.language = kLanguage.GetValue();
			a_profile.windowPositionX = kWindowPositionX.GetValue();
			a_profile.windowPositionY = kWindowPositionY.GetValue();
			a_profile.windowWidth = kWindowWidth.GetValue();
			a_profile.windowHeight = kWindowHeight.GetValue();
		}

		ProfileData* FindProfileLocked(int a_profileIndex)
		{
			const auto found = std::find_if(profiles.begin(), profiles.end(), [a_profileIndex](const auto& profile) {
				return profile.index == a_profileIndex;
			});
			return found == profiles.end() ? nullptr : std::addressof(*found);
		}

		std::string MakeUniqueProfileNameLocked(int a_index)
		{
			const auto baseName = std::string(kProfilePrefix) + std::to_string(a_index);
			std::string candidate = baseName;
			std::uint32_t suffix = 2;
			while (std::any_of(profiles.begin(), profiles.end(), [&candidate](const auto& profile) {
				return Fold(profile.profileName) == Fold(candidate);
			})) {
				candidate = baseName + " (" + std::to_string(suffix++) + ")";
			}
			return candidate;
		}

		const ProfileData* FindProfileLocked(int a_profileIndex, std::nullptr_t)
		{
			const auto found = std::find_if(profiles.begin(), profiles.end(), [a_profileIndex](const auto& profile) {
				return profile.index == a_profileIndex;
			});
			return found == profiles.end() ? nullptr : std::addressof(*found);
		}

		int FindSingleProfileLocked()
		{
			int selected = 0;
			for (const auto& profile : profiles) {
				if (profile.singleProfile && (selected == 0 || profile.index < selected)) {
					selected = profile.index;
				}
			}
			return selected;
		}

		void RemoveProfileMappingsLocked(int a_profileIndex)
		{
			for (auto mapping = characterProfiles.begin(); mapping != characterProfiles.end();) {
				if (mapping->second == a_profileIndex) {
					mapping = characterProfiles.erase(mapping);
				} else {
					++mapping;
				}
			}
		}

		void BindProfileIdentityLocked(ProfileData& a_profile, const Identity& a_identity)
		{
			RemoveProfileMappingsLocked(a_profile.index);
			a_profile.identity = a_identity;
			if (a_identity.characterID != 0) {
				characterProfiles[a_identity.characterID] = a_profile.index;
			}
		}

		void ResetToDefaultLocked(bool a_backupMalformedFile)
		{
			if (a_backupMalformedFile) {
				BackupMalformedFile();
			}
			profiles.clear();
			characterProfiles.clear();
			auto profile = MakeDefaultProfile(1);
			profiles.push_back(std::move(profile));
			activeProfile = 0;
			previousCharacterID = 0;
			awaitingNewGameCharacterID = false;
			awaitingGameLoadCharacterID = false;
			selectionLost = true;
			ApplyProfileToSettings(profiles.front());
			SaveProfilesLocked();
		}

		void EnsureInitializedLocked()
		{
			if (initialized) {
				return;
			}
			std::error_code error;
			const auto configurationPath = ConfigurationPath();
			const bool exists = !configurationPath.empty() && std::filesystem::exists(configurationPath, error);
			if (configurationPath.empty() || error) {
				ResetToDefaultLocked(false);
			} else if (!exists) {
				ResetToDefaultLocked(false);
			} else {
				CSimpleIniA file;
				std::vector<ProfileData> loadedProfiles;
				std::map<std::uint32_t, int> loadedCharacterProfiles;
				bool requiresSave = false;
				const bool fileLoaded = LoadFile(file);
				const bool profilesRead = fileLoaded && ReadProfiles(file, loadedProfiles, loadedCharacterProfiles, requiresSave);
				if (!fileLoaded || !profilesRead) {
					ResetToDefaultLocked(true);
				} else {
					profiles = std::move(loadedProfiles);
					characterProfiles = std::move(loadedCharacterProfiles);
					ApplyProfileToSettings(MakeDefaultProfile(0));
					if (requiresSave) {
						SaveProfilesLocked();
					}
				}
			}
			activeProfile = 0;
			selectionLost = true;
			initialized = true;
		}

	}

	bool Identity::IsKnown() const noexcept
	{
		return IsIdentityKnown(*this);
	}

	bool Identity::Matches(const Identity& a_other) const
	{
		return IsIdentityMatch(*this, a_other);
	}

	void Initialize()
	{
		std::scoped_lock lock(profileMutex);
		EnsureInitializedLocked();
	}

	void NotifyNewGame()
	{
		const auto managerIdentity = CaptureIdentity();
		std::scoped_lock lock(profileMutex);
		EnsureInitializedLocked();
		previousCharacterID = observedIdentity.characterID != 0 ? observedIdentity.characterID : managerIdentity.characterID;
		awaitingNewGameCharacterID = true;
		awaitingGameLoadCharacterID = false;
		profileTransitioning.store(true, std::memory_order_release);
		profileGeneration.fetch_add(1, std::memory_order_acq_rel);
		if (activeProfile != 0) {
			if (auto* active = FindProfileLocked(activeProfile)) {
				CaptureSettings(*active);
			}
		}
		selectionLost = true;
		activeProfile = 0;
		observedIdentity = {};
		ApplyProfileToSettings(MakeDefaultProfile(0));
		SaveProfilesLocked();
		profileTransitioning.store(false, std::memory_order_release);
	}

	void NotifyGameLoadStarted()
	{
		const auto managerIdentity = CaptureIdentity();
		std::scoped_lock lock(profileMutex);
		EnsureInitializedLocked();
		previousCharacterID = observedIdentity.characterID != 0 ? observedIdentity.characterID : managerIdentity.characterID;
		awaitingNewGameCharacterID = false;
		awaitingGameLoadCharacterID = true;
		profileTransitioning.store(true, std::memory_order_release);
		profileGeneration.fetch_add(1, std::memory_order_acq_rel);
		if (activeProfile != 0) {
			if (auto* active = FindProfileLocked(activeProfile)) {
				CaptureSettings(*active);
			}
		}
		selectionLost = true;
		activeProfile = 0;
		observedIdentity = {};
		ApplyProfileToSettings(MakeDefaultProfile(0));
		SaveProfilesLocked();
		profileTransitioning.store(false, std::memory_order_release);
	}

	void NotifyGameLoadFinished()
	{
		std::scoped_lock lock(profileMutex);
		awaitingGameLoadCharacterID = false;
	}

	WindowState PrepareForWindow()
	{
		Initialize();
		auto identity = CaptureIdentity();
		int profileToSelect = 0;
		bool createProfile = false;
		bool saveMetadata = false;
		{
			std::scoped_lock lock(profileMutex);
			if (awaitingGameLoadCharacterID) {
				identity.characterID = 0;
			} else if (awaitingNewGameCharacterID) {
				if (identity.characterID == 0 || (previousCharacterID != 0 && identity.characterID == previousCharacterID)) {
					identity.characterID = 0;
				} else {
					awaitingNewGameCharacterID = false;
					previousCharacterID = 0;
				}
			}
			observedIdentity = identity;
			if (!identity.IsKnown()) {
				return WindowState::kUnavailable;
			}
			const int forcedProfile = FindSingleProfileLocked();
			if (activeProfile != 0 && !selectionLost) {
				auto* active = FindProfileLocked(activeProfile);
				const bool activeIsForced = active && forcedProfile != 0 && activeProfile == forcedProfile;
				if (active && (activeIsForced || (forcedProfile == 0 && IsIdentityMatch(active->identity, identity)))) {
					if (!SameIdentity(active->identity, identity)) {
						BindProfileIdentityLocked(*active, identity);
						SaveProfilesLocked();
					}
					return WindowState::kReady;
				}
				profileTransitioning.store(true, std::memory_order_release);
				profileGeneration.fetch_add(1, std::memory_order_acq_rel);
				if (auto* previous = FindProfileLocked(activeProfile)) {
					CaptureSettings(*previous);
				}
				SaveProfilesLocked();
				activeProfile = 0;
				selectionLost = true;
				ApplyProfileToSettings(MakeDefaultProfile(0));
				profileTransitioning.store(false, std::memory_order_release);
			}
			if (forcedProfile != 0) {
				profileToSelect = forcedProfile;
			} else {
				const auto mappedProfile = characterProfiles.find(identity.characterID);
				if (mappedProfile != characterProfiles.end()) {
					const auto* profile = FindProfileLocked(mappedProfile->second, nullptr);
					if (profile && profile->identity.characterID == identity.characterID) {
						profileToSelect = profile->index;
					} else {
						characterProfiles.erase(mappedProfile);
						saveMetadata = true;
					}
				}
				if (profileToSelect == 0) {
					int matchingProfile = 0;
					int matchingCount = 0;
					for (const auto& profile : profiles) {
						if (IsIdentityMatch(profile.identity, identity)) {
							matchingProfile = profile.index;
							++matchingCount;
						}
					}
					if (matchingCount == 1) {
						profileToSelect = matchingProfile;
					} else if (profiles.size() == 1 && profiles.front().identity.characterID == 0) {
						profileToSelect = profiles.front().index;
					} else {
						createProfile = true;
					}
				}
			}
		}
		if (saveMetadata) {
			std::scoped_lock lock(profileMutex);
			SaveProfilesLocked();
		}
		if (profileToSelect != 0) {
			const bool selected = SelectProfile(profileToSelect);
			return selected ? WindowState::kReady : WindowState::kUnavailable;
		}
		if (createProfile) {
			if (CreateProfile()) {
				return WindowState::kReady;
			}
			return WindowState::kUnavailable;
		}
		return WindowState::kUnavailable;
	}

	Identity GetObservedIdentity()
	{
		std::scoped_lock lock(profileMutex);
		EnsureInitializedLocked();
		return observedIdentity;
	}

	std::vector<ProfileSummary> GetProfiles()
	{
		std::scoped_lock lock(profileMutex);
		EnsureInitializedLocked();
		std::vector<ProfileSummary> result;
		result.reserve(profiles.size());
		for (const auto& profile : profiles) {
			result.push_back(Summarize(profile));
		}
		return result;
	}

	int GetCurrentProfile()
	{
		std::scoped_lock lock(profileMutex);
		EnsureInitializedLocked();
		return activeProfile;
	}

	bool HasActiveProfile()
	{
		std::scoped_lock lock(profileMutex);
		EnsureInitializedLocked();
		return activeProfile != 0 && !selectionLost;
	}

	bool SelectProfile(int a_profileIndex)
	{
		Initialize();
		const auto currentIdentity = CaptureIdentity();
		if (!currentIdentity.IsKnown()) {
			return false;
		}

		std::unique_lock lock(profileMutex);
		EnsureInitializedLocked();
		if (profileTransitioning.load(std::memory_order_acquire) || awaitingNewGameCharacterID || awaitingGameLoadCharacterID) {
			return false;
		}
		const int forcedProfile = FindSingleProfileLocked();
		if (forcedProfile != 0 && a_profileIndex != forcedProfile) {
			return false;
		}
		auto* profile = FindProfileLocked(a_profileIndex);
		const bool characterIDMatches = profile && (a_profileIndex == forcedProfile || IsIdentityMatch(profile->identity, currentIdentity));
		const bool canBindUnassignedProfile = profile && profile->identity.characterID == 0;
		if (!profile || (!characterIDMatches && !canBindUnassignedProfile)) {
			return false;
		}

		if (activeProfile != 0) {
			if (auto* previous = FindProfileLocked(activeProfile)) {
				CaptureSettings(*previous);
			}
		}
		const auto rollbackProfiles = profiles;
		const auto rollbackCharacterProfiles = characterProfiles;
		const auto rollbackObservedIdentity = observedIdentity;
		const auto rollbackActiveProfile = activeProfile;
		const auto rollbackSelectionLost = selectionLost;

		profileTransitioning.store(true, std::memory_order_release);
		profileGeneration.fetch_add(1, std::memory_order_acq_rel);
		observedIdentity = currentIdentity;
		if (auto* selectedProfile = FindProfileLocked(a_profileIndex)) {
			BindProfileIdentityLocked(*selectedProfile, currentIdentity);
			activeProfile = a_profileIndex;
			selectionLost = false;
			const auto selected = *selectedProfile;
			ApplyProfileToSettings(selected);
			if (SaveProfilesLocked()) {
				profileTransitioning.store(false, std::memory_order_release);
				lock.unlock();
				localization::Initialize(kLanguage.GetValue());
				return true;
			}
		}

		profiles = rollbackProfiles;
		characterProfiles = rollbackCharacterProfiles;
		observedIdentity = rollbackObservedIdentity;
		activeProfile = rollbackActiveProfile;
		selectionLost = rollbackSelectionLost;
		if (rollbackActiveProfile != 0) {
			if (const auto* previous = FindProfileLocked(rollbackActiveProfile, nullptr)) {
				ApplyProfileToSettings(*previous);
			} else {
				ApplyProfileToSettings(MakeDefaultProfile(0));
			}
		} else {
			ApplyProfileToSettings(MakeDefaultProfile(0));
		}
		profileTransitioning.store(false, std::memory_order_release);
		return false;
	}

	static bool CreateProfileImpl(std::optional<int> a_sourceProfileIndex)
	{
		const auto sourceProfileIndex = a_sourceProfileIndex.value_or(0);
		Initialize();
		const auto currentIdentity = CaptureIdentity();
		if (!currentIdentity.IsKnown()) {
			return false;
		}

		std::unique_lock lock(profileMutex);
		EnsureInitializedLocked();
		if (profileTransitioning.load(std::memory_order_acquire) || awaitingNewGameCharacterID || awaitingGameLoadCharacterID) {
			return false;
		}
		const int forcedProfile = FindSingleProfileLocked();
		if (forcedProfile != 0) {
			return false;
		}
		if (activeProfile != 0) {
			if (auto* previous = FindProfileLocked(activeProfile)) {
				CaptureSettings(*previous);
			}
		}
		const auto rollbackProfiles = profiles;
		const auto rollbackCharacterProfiles = characterProfiles;
		const auto rollbackObservedIdentity = observedIdentity;
		const auto rollbackActiveProfile = activeProfile;
		const auto rollbackSelectionLost = selectionLost;

		const auto maximum = std::max_element(profiles.begin(), profiles.end(), [](const auto& left, const auto& right) {
			return left.index < right.index;
		});
		if (maximum != profiles.end() && maximum->index == (std::numeric_limits<int>::max)()) {
			return false;
		}
		const auto newIndex = maximum == profiles.end() ? 1 : maximum->index + 1;
		ProfileData created;
		if (!a_sourceProfileIndex) {
			created = MakeDefaultProfile(newIndex);
		} else {
			const auto* source = FindProfileLocked(*a_sourceProfileIndex, nullptr);
			if (!source) {
				return false;
			}
			created = *source;
			created.index = newIndex;
			created.protectedIngredients = kDefaultProtectedIngredients;
			created.protectedEffects = kDefaultProtectedEffects;
			created.protectedEffectCounts = kDefaultProtectedEffectCounts;
			created.requirements = kDefaultTrackedRequirements;
		}
		created.profileName = MakeUniqueProfileNameLocked(newIndex);
		created.identity = currentIdentity;
		created.playerSnapshot.clear();
		created.cacoSnapshot.clear();
		created.alchemyPlusSnapshot.clear();

		profileTransitioning.store(true, std::memory_order_release);
		profileGeneration.fetch_add(1, std::memory_order_acq_rel);
		observedIdentity = currentIdentity;
		profiles.push_back(created);
		activeProfile = created.index;
		characterProfiles[currentIdentity.characterID] = created.index;
		selectionLost = false;
		ApplyProfileToSettings(created);
		if (SaveProfilesLocked()) {
			profileTransitioning.store(false, std::memory_order_release);
			lock.unlock();
			localization::Initialize(kLanguage.GetValue());
			return true;
		}

		profiles = rollbackProfiles;
		characterProfiles = rollbackCharacterProfiles;
		observedIdentity = rollbackObservedIdentity;
		activeProfile = rollbackActiveProfile;
		selectionLost = rollbackSelectionLost;
		if (rollbackActiveProfile != 0) {
			if (const auto* previous = FindProfileLocked(rollbackActiveProfile, nullptr)) {
				ApplyProfileToSettings(*previous);
			} else {
				ApplyProfileToSettings(MakeDefaultProfile(0));
			}
		} else {
			ApplyProfileToSettings(MakeDefaultProfile(0));
		}
		profileTransitioning.store(false, std::memory_order_release);
		return false;
	}

	bool CreateProfile()
	{
		return CreateProfileImpl(std::nullopt);
	}

	bool CloneProfile(int a_sourceProfileIndex)
	{
		if (a_sourceProfileIndex <= 0) {
			return false;
		}
		return CreateProfileImpl(a_sourceProfileIndex);
	}

	bool RenameProfile(int a_profileIndex, const std::string& a_profileName)
	{
		Initialize();
		const auto trimmedName = Trim(a_profileName);
		if (trimmedName.empty()) {
			return false;
		}

		std::scoped_lock lock(profileMutex);
		EnsureInitializedLocked();
		if (profileTransitioning.load(std::memory_order_acquire) || activeProfile == 0 || selectionLost || a_profileIndex != activeProfile) {
			return false;
		}
		if (std::any_of(profiles.begin(), profiles.end(), [a_profileIndex, &trimmedName](const auto& profile) {
			return profile.index != a_profileIndex && Fold(profile.profileName) == Fold(trimmedName);
		})) {
			return false;
		}
		const auto found = FindProfileLocked(a_profileIndex);
		if (!found) {
			return false;
		}
		if (found->profileName == trimmedName) {
			return true;
		}

		const auto rollbackProfiles = profiles;
		found->profileName = trimmedName;
		profileTransitioning.store(true, std::memory_order_release);
		profileGeneration.fetch_add(1, std::memory_order_acq_rel);
		if (SaveProfilesLocked()) {
			profileTransitioning.store(false, std::memory_order_release);
			return true;
		}
		profiles = rollbackProfiles;
		profileTransitioning.store(false, std::memory_order_release);
		return false;
	}

	bool DeleteProfile(int a_profileIndex)
	{
		Initialize();
		std::scoped_lock lock(profileMutex);
		EnsureInitializedLocked();
		if (profiles.size() <= 1 || a_profileIndex <= 0 || a_profileIndex == activeProfile) {
			return false;
		}
		const auto found = std::find_if(profiles.begin(), profiles.end(), [a_profileIndex](const auto& profile) {
			return profile.index == a_profileIndex;
		});
		if (found == profiles.end()) {
			return false;
		}

		const auto rollbackProfiles = profiles;
		const auto rollbackCharacterProfiles = characterProfiles;
		profiles.erase(found);
		for (auto mapping = characterProfiles.begin(); mapping != characterProfiles.end();) {
			if (mapping->second == a_profileIndex) {
				mapping = characterProfiles.erase(mapping);
			} else {
				++mapping;
			}
		}
		profileTransitioning.store(true, std::memory_order_release);
		profileGeneration.fetch_add(1, std::memory_order_acq_rel);
		if (SaveProfilesLocked()) {
			profileTransitioning.store(false, std::memory_order_release);
			return true;
		}
		profiles = rollbackProfiles;
		characterProfiles = rollbackCharacterProfiles;
		profileTransitioning.store(false, std::memory_order_release);
		return false;
	}

	void UpdateExternalSnapshots(std::string a_player, std::string a_caco, std::string a_alchemyPlus)
	{
		Initialize();
		const auto generation = profileGeneration.load(std::memory_order_acquire);
		if (profileTransitioning.load(std::memory_order_acquire)) {
			return;
		}
		std::scoped_lock lock(profileMutex);
		if (generation != profileGeneration.load(std::memory_order_acquire) || profileTransitioning.load(std::memory_order_acquire) || activeProfile == 0 || selectionLost) {
			return;
		}
		if (auto* profile = FindProfileLocked(activeProfile)) {
			if (profile->playerSnapshot == a_player && profile->cacoSnapshot == a_caco && profile->alchemyPlusSnapshot == a_alchemyPlus) {
				return;
			}
			const auto previousPlayerSnapshot = profile->playerSnapshot;
			const auto previousCacoSnapshot = profile->cacoSnapshot;
			const auto previousAlchemyPlusSnapshot = profile->alchemyPlusSnapshot;
			CaptureSettings(*profile);
			profile->playerSnapshot = std::move(a_player);
			profile->cacoSnapshot = std::move(a_caco);
			profile->alchemyPlusSnapshot = std::move(a_alchemyPlus);
			if (!SaveProfilesLocked()) {
				profile->playerSnapshot = previousPlayerSnapshot;
				profile->cacoSnapshot = previousCacoSnapshot;
				profile->alchemyPlusSnapshot = previousAlchemyPlusSnapshot;
			}
		}
	}

	bool SaveCurrentProfile()
	{
		Initialize();
		const auto generation = profileGeneration.load(std::memory_order_acquire);
		if (profileTransitioning.load(std::memory_order_acquire)) {
			return false;
		}
		std::scoped_lock lock(profileMutex);
		if (generation != profileGeneration.load(std::memory_order_acquire) || profileTransitioning.load(std::memory_order_acquire) || activeProfile == 0 || selectionLost) {
			return false;
		}
		if (auto* profile = FindProfileLocked(activeProfile)) {
			CaptureSettings(*profile);
			if (profile->identity.characterID != 0) {
				characterProfiles[profile->identity.characterID] = profile->index;
			}
			return SaveProfilesLocked();
		}
		return false;
	}
}
