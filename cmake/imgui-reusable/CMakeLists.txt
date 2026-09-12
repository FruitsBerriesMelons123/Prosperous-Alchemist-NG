cmake_minimum_required(VERSION 3.21)

project(imgui_reusable LANGUAGES CXX)

set(IMGUI_SOURCE_DIR "" CACHE PATH "Path to the pinned Dear ImGui source checkout")
if(NOT IS_DIRECTORY "${IMGUI_SOURCE_DIR}")
	message(FATAL_ERROR "IMGUI_SOURCE_DIR must point to the pinned Dear ImGui source checkout: ${IMGUI_SOURCE_DIR}")
endif()

set(IMGUI_REQUIRED_SOURCES
	imgui.cpp
	imgui_draw.cpp
	imgui_tables.cpp
	imgui_widgets.cpp
	backends/imgui_impl_dx11.cpp
)
foreach(relative_path IN LISTS IMGUI_REQUIRED_SOURCES)
	if(NOT EXISTS "${IMGUI_SOURCE_DIR}/${relative_path}")
		message(FATAL_ERROR "The configured Dear ImGui source checkout is missing ${relative_path}: ${IMGUI_SOURCE_DIR}")
	endif()
endforeach()

include(CMakePackageConfigHelpers)
include(GNUInstallDirs)

add_library(imgui STATIC
	"${IMGUI_SOURCE_DIR}/imgui.cpp"
	"${IMGUI_SOURCE_DIR}/imgui_draw.cpp"
	"${IMGUI_SOURCE_DIR}/imgui_tables.cpp"
	"${IMGUI_SOURCE_DIR}/imgui_widgets.cpp"
	"${IMGUI_SOURCE_DIR}/backends/imgui_impl_dx11.cpp"
)

add_library(imgui::imgui ALIAS imgui)

target_compile_features(imgui PUBLIC cxx_std_11)
target_include_directories(imgui PUBLIC
	$<BUILD_INTERFACE:${IMGUI_SOURCE_DIR}>
	$<BUILD_INTERFACE:${IMGUI_SOURCE_DIR}/backends>
	$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/imgui>
	$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/imgui/backends>
)
target_link_libraries(imgui PUBLIC d3d11 dxgi)
set_target_properties(imgui PROPERTIES OUTPUT_NAME imgui)

install(TARGETS imgui
	EXPORT imguiTargets
	ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
	LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
	RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
	INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)
install(FILES
	"${IMGUI_SOURCE_DIR}/imconfig.h"
	"${IMGUI_SOURCE_DIR}/imgui.h"
	"${IMGUI_SOURCE_DIR}/imgui_internal.h"
	"${IMGUI_SOURCE_DIR}/imstb_rectpack.h"
	"${IMGUI_SOURCE_DIR}/imstb_textedit.h"
	"${IMGUI_SOURCE_DIR}/imstb_truetype.h"
	DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/imgui
)
install(FILES
	"${IMGUI_SOURCE_DIR}/backends/imgui_impl_dx11.h"
	DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/imgui/backends
)
install(FILES "${IMGUI_SOURCE_DIR}/LICENSE.txt" DESTINATION ${CMAKE_INSTALL_DATADIR}/imgui)
install(EXPORT imguiTargets
	FILE imguiTargets.cmake
	NAMESPACE imgui::
	DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/imgui
)

configure_package_config_file(
	"${CMAKE_CURRENT_SOURCE_DIR}/imguiConfig.cmake.in"
	"${CMAKE_CURRENT_BINARY_DIR}/imguiConfig.cmake"
	INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/imgui
)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/imguiConfig.cmake"
	DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/imgui
)
