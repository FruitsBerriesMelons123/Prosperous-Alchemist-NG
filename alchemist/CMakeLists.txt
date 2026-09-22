cmake_minimum_required(VERSION 3.21)

# This consumer project builds the plugin from the alchemist directory and expects an
# independently managed CommonLibSSE-NG checkout plus a static vcpkg installation.
project(
	alchemist
	LANGUAGES CXX
	VERSION 1.3.2.0
)

set(COMMONLIBSSE_DIR "" CACHE PATH "Path to the external CommonLibSSE-NG checkout")
set(COMMONLIBSSE_INSTALL_DIR "" CACHE PATH "Path to the installed CommonLibSSE package")
get_filename_component(COMMONLIBSSE_PATH "${COMMONLIBSSE_DIR}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_LIST_DIR}")
if(NOT EXISTS "${COMMONLIBSSE_PATH}/CMakeLists.txt")
	message(FATAL_ERROR "COMMONLIBSSE_DIR must point to a CommonLibSSE-NG checkout: ${COMMONLIBSSE_PATH}")
endif()
get_filename_component(COMMONLIBSSE_INSTALL_PATH "${COMMONLIBSSE_INSTALL_DIR}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_LIST_DIR}")
if(NOT EXISTS "${COMMONLIBSSE_INSTALL_PATH}/lib/cmake/CommonLibSSE/CommonLibSSEConfig.cmake")
	message(FATAL_ERROR "COMMONLIBSSE_INSTALL_DIR must contain an installed CommonLibSSE package: ${COMMONLIBSSE_INSTALL_PATH}")
endif()

# CommonLibSSE-NG requires the static package configuration so the shipped DLL does not
# depend on dynamic vcpkg or MSVC runtime libraries beside the plugin.
set(VCPKG_STATIC_DIR "" CACHE PATH "Path to the static vcpkg installed directory")
if(NOT EXISTS "${VCPKG_STATIC_DIR}/share/spdlog/spdlogConfig.cmake")
	message(FATAL_ERROR "VCPKG_STATIC_DIR must point to a static vcpkg installed directory: ${VCPKG_STATIC_DIR}")
endif()
set(IMGUI_INSTALL_DIR "" CACHE PATH "Path to the installed reusable Dear ImGui package")
get_filename_component(IMGUI_INSTALL_PATH "${IMGUI_INSTALL_DIR}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_LIST_DIR}")
if(NOT EXISTS "${IMGUI_INSTALL_PATH}/lib/cmake/imgui/imguiConfig.cmake")
	message(FATAL_ERROR "IMGUI_INSTALL_DIR must contain an installed Dear ImGui package: ${IMGUI_INSTALL_PATH}")
endif()
set(CMAKE_PREFIX_PATH "${COMMONLIBSSE_INSTALL_PATH};${VCPKG_STATIC_DIR}" CACHE STRING "External CommonLib and static vcpkg package prefixes" FORCE)
find_package(spdlog CONFIG REQUIRED)
find_package(directxtk CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)
find_package(zstd CONFIG REQUIRED)
find_package(imgui CONFIG REQUIRED PATHS "${IMGUI_INSTALL_PATH}" NO_DEFAULT_PATH)
find_package(
	CommonLibSSE
	CONFIG
	REQUIRED
	PATHS "${COMMONLIBSSE_INSTALL_PATH}/lib/cmake/CommonLibSSE"
	NO_DEFAULT_PATH
)
set(CommonLibSSE_INCLUDE_DIRS
	"${COMMONLIBSSE_INSTALL_PATH}/include"
	"${COMMONLIBSSE_PATH}/extern/openvr/headers"
)
include("${COMMONLIBSSE_PATH}/cmake/CommonLibSSE.cmake")

# The wrapper and release packaging support Release only; keep multi-config generators
# from silently producing an unsupported Debug or RelWithDebInfo plugin.
set(CMAKE_CONFIGURATION_TYPES "Release" CACHE STRING "Supported build configurations" FORCE)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded" CACHE STRING "Use the static MSVC runtime" FORCE)

set(BUILD_TESTS OFF CACHE BOOL "Disable CommonLibSSE-NG tests for the plugin build" FORCE)
set(REX_OPTION_INI ON CACHE BOOL "Enable REX INI support" FORCE)
set(ENABLE_SKYRIM_SE ON CACHE BOOL "Enable Skyrim SE support" FORCE)
set(ENABLE_SKYRIM_AE ON CACHE BOOL "Enable Skyrim AE support" FORCE)
set(ENABLE_SKYRIM_VR ON CACHE BOOL "Enable Skyrim VR support" FORCE)

add_commonlibsse_plugin(
	alchemist
	NAME "alchemist"
	AUTHOR "FruitsBerriesMelons123"
	VERSION "1.3.2.0"
	USE_ADDRESS_LIBRARY
	SOURCES
		AlchemyPlus/AlchemyPlus.cpp
		AlchemyPlus/AlchemyPlus.h
		CACO/CACO.cpp
		CACO/CACO.h
		src/IngredientTracker.cpp
		include/IngredientTracker.h
		src/ProfileManager.cpp
		include/ProfileManager.h
		src/Localization.cpp
		src/PluginPaths.cpp
		src/main.cpp
		src/AlchemistEngine.cpp
		src/AlchemistWindow.cpp
		src/DeveloperTestHub.cpp
		src/MenuHandler.cpp
		src/ModSettings.cpp
		src/PotionConfirmation.cpp
		src/RenderHook.cpp
		include/ZstdWriter.h
		version.rc
)

target_include_directories(alchemist PRIVATE include ${CMAKE_CURRENT_SOURCE_DIR})
target_include_directories(alchemist PRIVATE "${COMMONLIBSSE_PATH}/extern/openvr/headers")
target_compile_definitions(alchemist PRIVATE NOMINMAX)
target_compile_features(alchemist PRIVATE cxx_std_23)
target_precompile_headers(alchemist PRIVATE include/AlchemistPCH.h)
target_link_libraries(alchemist PRIVATE imgui::imgui nlohmann_json::nlohmann_json zstd::libzstd d3d11 dxgi user32)

if(MSVC)
	target_compile_options(alchemist PRIVATE "$<$<CONFIG:Release>:/Zi>")
	target_link_options(alchemist PRIVATE "$<$<CONFIG:Release>:/DEBUG>")
	set_target_properties(alchemist PROPERTIES
		COMPILE_PDB_NAME alchemist
		COMPILE_PDB_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
		PDB_NAME alchemist
		PDB_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
	)
endif()

set(ALCHEMIST_DEPLOY_DIR "" CACHE PATH "Optional directory for the post-build plugin deployment")
# Deployment is intentionally opt-in so a configure/build does not overwrite an unrelated
# Skyrim profile. build.py supplies this directory from the local DLL_DEPLOY setting.
if(ALCHEMIST_DEPLOY_DIR)
	add_custom_command(
		TARGET alchemist
		POST_BUILD
		COMMAND ${CMAKE_COMMAND} -E make_directory "${ALCHEMIST_DEPLOY_DIR}"
		COMMAND ${CMAKE_COMMAND} -E copy
			"$<TARGET_FILE:alchemist>"
			"${ALCHEMIST_DEPLOY_DIR}/$<TARGET_FILE_NAME:alchemist>"
		VERBATIM
	)
	if(MSVC)
		add_custom_command(
			TARGET alchemist
			POST_BUILD
			COMMAND ${CMAKE_COMMAND} -E copy_if_different
				"$<TARGET_PDB_FILE:alchemist>"
				"${ALCHEMIST_DEPLOY_DIR}/$<TARGET_PDB_FILE_NAME:alchemist>"
			VERBATIM
		)
	endif()
endif()
