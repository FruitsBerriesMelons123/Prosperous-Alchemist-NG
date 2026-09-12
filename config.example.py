"""Machine-specific paths used by repository Python scripts."""

from pathlib import Path
from typing import Final


CMAKE_DIR: Final = Path(r"D:\Apps\CMake\bin")
MD2NEXUS: Final = Path(r"D:\Apps\md2nexus\md2nexus.exe")
NINJA_DIR: Final = Path(r"D:\Apps\ninja")
MO2_PROFILE: Final = Path(r"E:\Projects\games\skyrim\1.6.1170")
MO2_EXECUTABLE: Final = Path(r"E:\Projects\games\skyrim\Mod.Organizer-1.6.1170\ModOrganizer.exe")
MO2_SKSE_SHORTCUT: Final = "moshortcut://:SKSE"
SKSE_SOURCE: Final = Path(r"E:\Projects\games\skyrim\skse\skse64_2_02_06")
SKSE_BUILD_DIR: Final = Path(r"E:\Projects\games\skyrim\skse\skse64_2_02_06-build")
SKYUI_SOURCE: Final = Path(r"E:\Projects\games\skyrim\skyui\SkyUI-Community")
SSEEDIT: Final = Path(r"E:\Projects\games\skyrim\SSEEdit")
SKYRIM_LOGS: Final = Path(r"D:\Documents\My Games\Skyrim Special Edition\SKSE")
SKYRIM: Final = Path(r"D:\Steam\steamapps\common\Skyrim Special Edition")
VCPKG_ROOT: Final = Path(r"D:\Apps\vcpkg")
VCPKG_DOWNLOADS_DIR: Final = VCPKG_ROOT / "downloads"
VCPKG_BINARY_CACHE_DIR: Final = VCPKG_ROOT / "binary-cache"
VCPKG_STATIC_INSTALL_ROOT: Final = VCPKG_ROOT / "installed" / "prosperous-alchemist-commonlib"
VCPKG_STATIC_DIR: Final = VCPKG_STATIC_INSTALL_ROOT / "x64-windows-static"
IMGUI_SOURCE_DIR: Final = Path(r"D:\Apps\imgui\v1.91.9b")
IMGUI_BUILD_DIR: Final = Path(r"D:\Apps\imgui\v1.91.9b-build")
IMGUI_INSTALL_DIR: Final = IMGUI_BUILD_DIR / "install"
COMMONLIBSSE_SOURCE: Final = Path(r"E:\Projects\games\skyrim\git\alandtse-CommonLibSSE-NG")
COMMONLIBSSE_BUILD_DIR: Final = COMMONLIBSSE_SOURCE / "build"
COMMONLIBSSE_INSTALL_DIR: Final = COMMONLIBSSE_SOURCE / "install"
DLL_DEPLOY: Final = Path(
	r"E:\Projects\games\skyrim\1.6.1170\mods\Prosperous Alchemist NG\SKSE\Plugins\alchemist.dll"
)
PA_NG_MOD_DIR: Final = DLL_DEPLOY.parents[2]
ALCHEMY_PLUS_SOURCE: Final = Path(r"E:\Projects\games\skyrim\git\Exit-9B-AlchemyPlus")
ALCHEMY_PLUS_MOD_DIR: Final = Path(r"E:\Projects\games\skyrim\1.6.1170\mods\Alchemy Plus")
CACO_SOURCE: Final = Path(r"E:\Projects\games\skyrim\utils\caco\scripts\source")
CACO_MOD_DIR: Final = Path(r"E:\Projects\games\skyrim\1.6.1170\mods\Complete Alchemy & Cooking Overhaul")
KRYPTOPYR_PATCHES_MOD_DIR: Final = Path(r"E:\Projects\games\skyrim\1.6.1170\mods\kryptopyr's Automated Patches")
CACO_SETTINGS: Final = Path(r"E:\Projects\games\skyrim\1.6.1170\mods\Alchemy Plus\SKSE\Plugins\AlchemyPlus.json")
MO2_DEFAULT_PROFILE_DIR: Final = MO2_PROFILE / "profiles" / "Default"
MO2_SAVES_DIR: Final = MO2_DEFAULT_PROFILE_DIR / "saves"
BACKUP_LOCKEDORDER: Final = MO2_DEFAULT_PROFILE_DIR / "lockedorder.txt.2026_09_16_19_51_00"
BACKUP_LOADORDER: Final = MO2_DEFAULT_PROFILE_DIR / "loadorder.txt.2026_09_16_19_51_00"
BACKUP_PLUGINS: Final = MO2_DEFAULT_PROFILE_DIR / "plugins.txt.2026_09_16_19_51_00"
QUEST_TRACKER_SOURCE: Final = Path(r"E:\Projects\games\skyrim\git\wtarking-cell-QuestTrackerNG")
CONSOLEUTIL_EXTENDED_SOURCE: Final = Path(r"E:\Projects\games\skyrim\git\KrisV-777-ConsoleUtil-Extended")
EXTENDED_CONSOLE_SOURCE: Final = Path(r"E:\Projects\games\skyrim\git\KrisV-777-Extended-Console")
PAPYRUS_EXTENDER_SOURCE: Final = Path(r"E:\Projects\games\skyrim\git\powerof3-PapyrusExtenderSSE")
PO3_TWEAKS_SOURCE: Final = Path(r"E:\Projects\games\skyrim\git\powerof3-po3-Tweaks")
CAPRICA_DIR: Final = Path(r"E:\Projects\games\skyrim\utils\Caprica.v0.3.0")
CREATION_KIT_DIR: Final = Path(r"E:\Projects\games\skyrim\utils\CreationKit")


PATHS: Final = {
	"cmake_dir": CMAKE_DIR,
	"md2nexus": MD2NEXUS,
	"ninja_dir": NINJA_DIR,
	"mo2_profile": MO2_PROFILE,
	"mo2_executable": MO2_EXECUTABLE,
	"mo2_saves_dir": MO2_SAVES_DIR,
	"skse_source": SKSE_SOURCE,
	"skse_build_dir": SKSE_BUILD_DIR,
	"skyui_source": SKYUI_SOURCE,
	"sseedit": SSEEDIT,
	"skyrim_logs": SKYRIM_LOGS,
	"skyrim": SKYRIM,
	"vcpkg_root": VCPKG_ROOT,
	"vcpkg_downloads_dir": VCPKG_DOWNLOADS_DIR,
	"vcpkg_binary_cache_dir": VCPKG_BINARY_CACHE_DIR,
	"vcpkg_static_install_root": VCPKG_STATIC_INSTALL_ROOT,
	"vcpkg_static_dir": VCPKG_STATIC_DIR,
	"imgui_source_dir": IMGUI_SOURCE_DIR,
	"imgui_build_dir": IMGUI_BUILD_DIR,
	"imgui_install_dir": IMGUI_INSTALL_DIR,
	"commonlibsse_source": COMMONLIBSSE_SOURCE,
	"commonlibsse_build_dir": COMMONLIBSSE_BUILD_DIR,
	"commonlibsse_install_dir": COMMONLIBSSE_INSTALL_DIR,
	"dll_deploy": DLL_DEPLOY,
	"pa_ng_mod_dir": PA_NG_MOD_DIR,
	"alchemy_plus_source": ALCHEMY_PLUS_SOURCE,
	"alchemy_plus_mod_dir": ALCHEMY_PLUS_MOD_DIR,
	"caco_source": CACO_SOURCE,
	"caco_mod_dir": CACO_MOD_DIR,
	"kryptopyr_patches_mod_dir": KRYPTOPYR_PATCHES_MOD_DIR,
	"caco_settings": CACO_SETTINGS,
	"mo2_default_profile_dir": MO2_DEFAULT_PROFILE_DIR,
	"backup_lockedorder": BACKUP_LOCKEDORDER,
	"backup_loadorder": BACKUP_LOADORDER,
	"backup_plugins": BACKUP_PLUGINS,
	"quest_tracker_source": QUEST_TRACKER_SOURCE,
	"consoleutil_extended_source": CONSOLEUTIL_EXTENDED_SOURCE,
	"extended_console_source": EXTENDED_CONSOLE_SOURCE,
	"papyrus_extender_source": PAPYRUS_EXTENDER_SOURCE,
	"po3_tweaks_source": PO3_TWEAKS_SOURCE,
	"caprica_dir": CAPRICA_DIR,
	"creation_kit_dir": CREATION_KIT_DIR,
}

__all__ = [
	"CMAKE_DIR",
	"CACO_SETTINGS",
	"CACO_SOURCE",
	"CACO_MOD_DIR",
	"KRYPTOPYR_PATCHES_MOD_DIR",
	"ALCHEMY_PLUS_MOD_DIR",
	"PA_NG_MOD_DIR",
	"MO2_DEFAULT_PROFILE_DIR",
	"BACKUP_LOCKEDORDER",
	"BACKUP_LOADORDER",
	"BACKUP_PLUGINS",
	"DLL_DEPLOY",
	"MD2NEXUS",
	"MO2_PROFILE",
	"MO2_EXECUTABLE",
	"MO2_SKSE_SHORTCUT",
	"MO2_SAVES_DIR",
	"NINJA_DIR",
	"PATHS",
	"SKSE_SOURCE",
	"SKSE_BUILD_DIR",
	"SKYRIM",
	"SKYRIM_LOGS",
	"SKYUI_SOURCE",
	"SSEEDIT",
	"ALCHEMY_PLUS_SOURCE",
	"QUEST_TRACKER_SOURCE",
	"CONSOLEUTIL_EXTENDED_SOURCE",
	"EXTENDED_CONSOLE_SOURCE",
	"PAPYRUS_EXTENDER_SOURCE",
	"PO3_TWEAKS_SOURCE",
	"CAPRICA_DIR",
	"CREATION_KIT_DIR",
	"VCPKG_STATIC_DIR",
	"VCPKG_STATIC_INSTALL_ROOT",
	"VCPKG_ROOT",
	"VCPKG_DOWNLOADS_DIR",
	"VCPKG_BINARY_CACHE_DIR",
	"IMGUI_SOURCE_DIR",
	"IMGUI_BUILD_DIR",
	"IMGUI_INSTALL_DIR",
	"COMMONLIBSSE_SOURCE",
	"COMMONLIBSSE_BUILD_DIR",
	"COMMONLIBSSE_INSTALL_DIR",
]
