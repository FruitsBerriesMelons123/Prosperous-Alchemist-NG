#pragma once

#include <RE/Skyrim.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <string>
#include <string_view>

namespace alchemist::plugin_utils
{
	inline bool EqualsIgnoreCase(std::string_view a_left, std::string_view a_right) noexcept
	{
		if (a_left.size() != a_right.size()) {
			return false;
		}
		for (std::size_t i = 0; i < a_left.size(); ++i) {
			const auto left = static_cast<unsigned char>(a_left[i]);
			const auto right = static_cast<unsigned char>(a_right[i]);
			if (std::tolower(left) != std::tolower(right)) {
				return false;
			}
		}
		return true;
	}

	inline std::string_view GetFileStem(std::string_view a_filename) noexcept
	{
		const auto dot = a_filename.rfind('.');
		return (dot == std::string_view::npos) ? a_filename : a_filename.substr(0, dot);
	}

	inline const RE::TESFile* FindLoadedPlugin(std::string_view a_pluginName) noexcept
	{
		if (a_pluginName.empty()) {
			return nullptr;
		}

		auto* dataHandler = RE::TESDataHandler::GetSingleton();
		if (!dataHandler) {
			return nullptr;
		}

		// 1. Direct name lookup (regular and light mods)
		try {
			if (const auto* file = dataHandler->LookupLoadedModByName(a_pluginName)) {
				return file;
			}
			if (const auto* file = dataHandler->LookupLoadedLightModByName(a_pluginName)) {
				return file;
			}
		} catch (...) {}

		const auto stem = GetFileStem(a_pluginName);
		static constexpr std::array<std::string_view, 3> kExtensions{ ".esp", ".esm", ".esl" };

		// 2. Try alternate extensions (.esp, .esm, .esl)
		for (const auto ext : kExtensions) {
			std::string candidate(stem);
			candidate.append(ext);
			try {
				if (const auto* file = dataHandler->LookupLoadedModByName(candidate)) {
					return file;
				}
				if (const auto* file = dataHandler->LookupLoadedLightModByName(candidate)) {
					return file;
				}
			} catch (...) {}
		}

		// 3. Scan all loaded files in dataHandler->files by case-insensitive stem match
		try {
			for (const auto* file : dataHandler->files) {
				if (!file) {
					continue;
				}
				const auto loadedFilename = file->GetFilename();
				if (EqualsIgnoreCase(GetFileStem(loadedFilename), stem)) {
					return file;
				}
			}
		} catch (...) {}

		// 4. Known common aliases (e.g., CACO acronym variants)
		if (EqualsIgnoreCase(stem, "Complete Alchemy & Cooking Overhaul") || EqualsIgnoreCase(stem, "CACO")) {
			for (const auto aliasStem : { "Complete Alchemy & Cooking Overhaul", "CACO" }) {
				for (const auto ext : kExtensions) {
					std::string candidate(aliasStem);
					candidate.append(ext);
					try {
						if (const auto* file = dataHandler->LookupLoadedModByName(candidate)) {
							return file;
						}
						if (const auto* file = dataHandler->LookupLoadedLightModByName(candidate)) {
							return file;
						}
					} catch (...) {}
				}
			}
		}

		return nullptr;
	}

	template <class T = RE::TESForm>
	inline T* LookupFormFlexible(RE::FormID a_localFormID, std::string_view a_pluginName) noexcept
	{
		if (a_localFormID == 0 || a_pluginName.empty()) {
			return nullptr;
		}

		auto* dataHandler = RE::TESDataHandler::GetSingleton();
		if (!dataHandler) {
			return nullptr;
		}

		// 1. Direct lookup
		try {
			if (auto* form = dataHandler->LookupForm<T>(a_localFormID, a_pluginName)) {
				return form;
			}
		} catch (...) {}

		// 2. Extension swap candidates
		const auto stem = GetFileStem(a_pluginName);
		static constexpr std::array<std::string_view, 3> kExtensions{ ".esp", ".esm", ".esl" };
		for (const auto ext : kExtensions) {
			std::string candidate(stem);
			candidate.append(ext);
			if (EqualsIgnoreCase(candidate, a_pluginName)) {
				continue;
			}
			try {
				if (auto* form = dataHandler->LookupForm<T>(a_localFormID, candidate)) {
					return form;
				}
			} catch (...) {}
		}

		// 3. Match across loaded files
		if (const auto* loadedFile = FindLoadedPlugin(a_pluginName)) {
			try {
				if (auto* form = dataHandler->LookupForm<T>(a_localFormID, loadedFile->GetFilename())) {
					return form;
				}
			} catch (...) {}
		}

		// 4. Fallback for Skyrim.esm / DLC / Creation Club content
		if (EqualsIgnoreCase(stem, "Skyrim") || EqualsIgnoreCase(stem, "Update")) {
			static constexpr std::array<std::string_view, 12> kMasterAndCcPlugins{
				"Update.esm",
				"Dawnguard.esm",
				"Dragonborn.esm",
				"HearthFires.esm",
				"ccbgssse037-curios.esl",
				"ccbgssse025-advdsgs.esm",
				"ccbgssse001-fish.esm",
				"ccbgssse067-daedinv.esm",
				"ccbgssse003-zombies.esl",
				"ccbgssse040-advobgg.esl",
				"ccasvsse001-almsivi.esm",
				"ccvsvsse004-beaskpeg.esl"
			};
			for (const auto pName : kMasterAndCcPlugins) {
				if (EqualsIgnoreCase(GetFileStem(pName), stem)) {
					continue;
				}
				if (auto* f = LookupFormFlexible<T>(a_localFormID, pName)) {
					return f;
				}
			}
		}

		return nullptr;
	}
}
