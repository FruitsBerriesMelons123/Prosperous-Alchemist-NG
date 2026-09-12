"""Build and deploy the Release plugin without cleaning CommonLibSSE-NG artifacts.

The wrapper is intentionally Windows/x64-focused: it configures the standalone
``alchemist`` CMake consumer with Ninja, validates a fresh DLL, and copies that
DLL and the bundled locale resources to the local deployment path. With
``--package``, it also converts the user guide to a Nexus-ready BBCode text
file in ``dist`` before creating the release archive. Release builds deploy the
plugin PDB beside the DLL for local symbol-assisted diagnostics and include it
beside the DLL in the release archive.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import queue
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path


build_log = None
status_file = None

BUILD_TYPE = "Release"
GENERATOR = "Ninja"
TARGET = "alchemist"
NEXUS_BBCODE_FILENAME = "Prosperous-Alchemist-NG-nexus-description.bbcode.txt"
PLUGIN_CLEAN_RULES = (
	"CXX_SCAN__alchemist_Release",
	"CXX_DYNDEP__alchemist_Release",
	"CXX_COMPILER__alchemist_scanned_Release",
	"CXX_COMPILER__alchemist_unscanned_Release",
	"RC_COMPILER__alchemist_unscanned_Release",
	"CXX_SHARED_LIBRARY_LINKER__alchemist_Release",
)
# These rules remove only plugin outputs. CommonLibSSE-NG and its fetched dependencies
# are deliberately retained so routine plugin rebuilds do not trigger a full rebuild.


def timestamp() -> str:
	return datetime.now().astimezone().isoformat(timespec="seconds")


def source_public_version(repo_root: Path) -> str:
	version_header = repo_root / "alchemist" / "include" / "version.h"
	try:
		version_text = version_header.read_text(encoding="utf-8")
	except OSError as error:
		raise RuntimeError(f"Unable to read source version header: {version_header}: {error}") from error

	components = dict(
		re.findall(
			r"^\s*#define\s+MYFP_VERSION_(MAJOR|MINOR|PATCH)\s+([0-9]+)\s*$",
			version_text,
			re.MULTILINE,
		)
	)
	missing = [name for name in ("MAJOR", "MINOR", "PATCH") if name not in components]
	if missing:
		raise RuntimeError(
			f"Source version header is missing required public version macros ({', '.join(missing)}): {version_header}"
		)
	return ".".join(components[name] for name in ("MAJOR", "MINOR", "PATCH"))


def release_package_path(repo_root: Path) -> Path:
	return repo_root / "dist" / f"Prosperous-Alchemist-NG-v{source_public_version(repo_root)}.zip"


def report(message: str) -> None:
	line = f"[{timestamp()}] {message}"
	print(line, flush=True)
	if build_log is not None:
		build_log.write(line + "\n")
		build_log.flush()


def x64_msvc_environment() -> dict[str, str]:
	environment = os.environ.copy()
	environment_by_name = {key.upper(): value for key, value in environment.items()}
	if (
		environment.get("VSCMD_ARG_TGT_ARCH") == "x64"
		and environment.get("VSCMD_ARG_HOST_ARCH") == "x64"
		and any(
			(Path(include_path) / "string_view").is_file()
			for include_path in environment.get("INCLUDE", "").split(os.pathsep)
			if include_path
		)
	):
		return environment

	vsdevcmd = None
	vs_install_dir = environment_by_name.get("VSINSTALLDIR")
	if vs_install_dir:
		candidate = Path(vs_install_dir).resolve() / "Common7" / "Tools" / "VsDevCmd.bat"
		if (candidate.parent.parent.parent / "VC" / "Tools" / "MSVC").is_dir() and candidate.is_file():
			vsdevcmd = candidate

	vc_install_dir = environment_by_name.get("VCINSTALLDIR")
	if vsdevcmd is None and vc_install_dir:
		candidate = Path(vc_install_dir).resolve().parent / "Common7" / "Tools" / "VsDevCmd.bat"
		if (candidate.parent.parent.parent / "VC" / "Tools" / "MSVC").is_dir() and candidate.is_file():
			vsdevcmd = candidate

	if vsdevcmd is None:
		vswhere_paths = []
		for environment_name in ("ProgramFiles(x86)", "ProgramFiles"):
			program_files = environment_by_name.get(environment_name.upper())
			if program_files:
				vswhere_paths.append(Path(program_files) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe")
		for vswhere in vswhere_paths:
			if vswhere.is_file():
				try:
					res = subprocess.run(
						[
							str(vswhere),
							"-latest",
							"-products",
							"*",
							"-requires",
							"Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
							"-property",
							"installationPath",
						],
						capture_output=True,
						text=True,
						check=True,
					)
					install_path = res.stdout.strip()
					if install_path:
						candidate = Path(install_path) / "Common7" / "Tools" / "VsDevCmd.bat"
						if (candidate.parent.parent.parent / "VC" / "Tools" / "MSVC").is_dir() and candidate.is_file():
							vsdevcmd = candidate
							break
				except Exception:
					pass

	if not vsdevcmd or not vsdevcmd.is_file():
		raise RuntimeError("VsDevCmd.bat not found; ensure Visual Studio C++ tools are installed or run from an MSVC developer shell")

	stale_toolchain_names = {
		"VCINSTALLDIR",
		"VCToolsInstallDir",
		"VCToolsVersion",
		"DevEnvDir",
		"INCLUDE",
		"LIB",
		"LIBPATH",
		"UniversalCRTSdkDir",
		"UCRTVersion",
		"VSINSTALLDIR",
		"WindowsSdkDir",
	}
	toolchain_environment = {
		key: value
		for key, value in environment.items()
		if not key.upper().startswith("VSCMD_") and key.upper() not in stale_toolchain_names
	}
	command = f'call "{vsdevcmd}" -arch=x64 -host_arch=x64 >nul && set'
	result = subprocess.run(
		f"cmd.exe /d /c {command}",
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
		encoding="utf-8",
		errors="replace",
		env=toolchain_environment,
	)
	if result.returncode != 0:
		raise RuntimeError(f"x64 MSVC setup failed with exit={result.returncode}: {result.stdout.strip()}")
	environment = toolchain_environment
	for line in result.stdout.splitlines():
		key, separator, value = line.partition("=")
		if separator and key:
			environment[key] = value
	report("Configured the MSVC environment for x64.")
	return environment


def run_process(
	command: list[str],
	repo_root: Path,
	environment: dict[str, str] | None = None,
	dependency_name: str | None = None,
) -> int:
	resolved_command = list(command)
	if environment and "PATH" in environment and not Path(resolved_command[0]).is_file():
		found_path = shutil.which(resolved_command[0], path=environment.get("PATH"))
		if found_path:
			resolved_command[0] = found_path
	report("Running: " + " ".join(resolved_command))
	process = subprocess.Popen(
		resolved_command,
		cwd=repo_root,
		env=environment,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
		encoding="utf-8",
		errors="replace",
		bufsize=1,
	)
	output: queue.Queue[str | None] = queue.Queue()

	def read_output() -> None:
		assert process.stdout is not None
		for line in process.stdout:
			output.put(line.rstrip())
		output.put(None)

	reader = threading.Thread(target=read_output, daemon=True)
	reader.start()
	output_closed = False
	dependency_updated = False
	while not output_closed or process.poll() is None:
		try:
			line = output.get(timeout=10)
		except queue.Empty:
			if dependency_name is None:
				report("Build still running; waiting for compiler output...")
			continue
		if line is None:
			output_closed = True
			continue
		if line:
			if dependency_name is not None:
				dependency_status = re.match(r"^--\s+(Up-to-date|Installing):", line.lstrip())
				if dependency_status:
					dependency_updated = dependency_updated or dependency_status.group(1) != "Up-to-date"
					continue
			report("[cmake] " + line)

	exit_code = process.wait()
	if dependency_name is not None:
		status = "up-to-date" if exit_code == 0 and not dependency_updated else "not up-to-date"
		exit_suffix = "" if exit_code == 0 else f" (exit={exit_code})"
		report(f"{dependency_name}: {status}{exit_suffix}")
	return exit_code


def cache_value(path: Path, key: str) -> str | None:
	try:
		lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
	except FileNotFoundError:
		return None
	for line in lines:
		prefix = f"{key}:"
		if line.startswith(prefix):
			return line.partition("=")[2]
	return None


def validate_vcpkg_layout(
	repo_root: Path,
	vcpkg_root: Path,
	static_install_root: Path,
	static_dir: Path,
) -> None:
	if not vcpkg_root.is_dir():
		raise RuntimeError(f"Reusable vcpkg tool root does not exist: {vcpkg_root}")
	try:
		static_install_root.relative_to(vcpkg_root)
	except ValueError as error:
		raise RuntimeError(
			f"Manifest-specific vcpkg install root must be under the reusable tool root: {static_install_root}"
		) from error
	try:
		static_dir.relative_to(static_install_root)
	except ValueError as error:
		raise RuntimeError(
			f"Static vcpkg prefix must be under its manifest-specific install root: {static_dir}"
		) from error
	if repo_root == static_dir or repo_root in static_dir.parents:
		raise RuntimeError(f"Static vcpkg prefix must remain outside the repository: {static_dir}")


def configure_vcpkg_environment(
	environment: dict[str, str],
	vcpkg_root: Path,
	downloads_dir: Path,
	binary_cache_dir: Path,
) -> dict[str, str]:
	for cache_dir in (downloads_dir, binary_cache_dir):
		cache_dir.mkdir(parents=True, exist_ok=True)
	result = environment.copy()
	result["VCPKG_ROOT"] = str(vcpkg_root)
	result["VCPKG_DOWNLOADS"] = str(downloads_dir)
	result["VCPKG_DEFAULT_BINARY_CACHE"] = str(binary_cache_dir)
	return result


def validate_imgui_layout(
	repo_root: Path,
	source_dir: Path,
	build_dir: Path,
	install_dir: Path,
) -> None:
	if not source_dir.is_dir():
		raise RuntimeError(f"External ImGui source directory does not exist: {source_dir}")
	for label, path in (("build", build_dir), ("install", install_dir)):
		if path == repo_root or repo_root in path.parents:
			raise RuntimeError(f"External ImGui {label} directory must remain outside the repository: {path}")
	try:
		install_dir.relative_to(build_dir)
	except ValueError as error:
		raise RuntimeError(f"External ImGui install directory must be under its build directory: {install_dir}") from error


def validate_imgui_build_tree(build_dir: Path, source_dir: Path) -> None:
	cache = build_dir / "CMakeCache.txt"
	configured_source = cache_value(cache, "CMAKE_HOME_DIRECTORY")
	if not configured_source:
		return
	normalize_path = lambda value: value.replace("\\", "/").rstrip("/").casefold()
	if normalize_path(configured_source) != normalize_path(str(source_dir.resolve())):
		raise RuntimeError(
			f"External ImGui build directory is configured for another source tree ({configured_source}): {build_dir}"
		)


def configure_imgui(
	cmake: str,
	source_dir: Path,
	build_dir: Path,
	install_dir: Path,
	repo_root: Path,
	environment: dict[str, str],
) -> int:
	imgui_cmake_source = repo_root / "cmake" / "imgui-reusable"
	if not (imgui_cmake_source / "CMakeLists.txt").is_file():
		raise FileNotFoundError(f"Reusable ImGui CMake source does not exist: {imgui_cmake_source}")
	prepare_cmake_build_tree(build_dir, "reusable ImGui")
	validate_imgui_build_tree(build_dir, imgui_cmake_source)
	install_dir.mkdir(parents=True, exist_ok=True)
	return run_process(
		[
			cmake,
			"-S",
			str(imgui_cmake_source),
			"-B",
			str(build_dir),
			"-G",
			GENERATOR,
			f"-DCMAKE_BUILD_TYPE={BUILD_TYPE}",
			f"-DCMAKE_INSTALL_PREFIX={install_dir}",
			f"-DIMGUI_SOURCE_DIR={source_dir}",
			"-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded",
		],
		repo_root,
		environment,
	)


def build_imgui(
	cmake: str,
	build_dir: Path,
	install_dir: Path,
	repo_root: Path,
	environment: dict[str, str],
) -> int:
	exit_code = run_process(
		[cmake, "--build", str(build_dir), "--target", "install"],
		repo_root,
		environment,
		"Reusable ImGui",
	)
	if exit_code == 0 and not (install_dir / "lib" / "cmake" / "imgui" / "imguiConfig.cmake").is_file():
		raise RuntimeError(f"Reusable ImGui package was not installed: {install_dir}")
	return exit_code


def artifact_details(path: Path) -> tuple[int, int, str, str] | None:
	try:
		stat = path.stat()
	except FileNotFoundError:
		return None
	digest = hashlib.sha256()
	with path.open("rb") as stream:
		for chunk in iter(lambda: stream.read(1024 * 1024), b""):
			digest.update(chunk)
	return (
		stat.st_mtime_ns,
		stat.st_size,
		datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
		digest.hexdigest().upper(),
	)


def remove_tree(path: Path) -> None:
	def handle_remove_error(function, target, _exc_info) -> None:
		os.chmod(target, stat.S_IREAD | stat.S_IWRITE)
		function(target)

	shutil.rmtree(path, onerror=handle_remove_error)


def prepare_cmake_build_tree(build_dir: Path, description: str) -> None:
	build_dir.mkdir(parents=True, exist_ok=True)
	cache = build_dir / "CMakeCache.txt"
	if not cache.exists():
		return
	cache_text = cache.read_text(encoding="utf-8", errors="replace")
	configured_build_dir = next(
		(
			line.removeprefix("# For build in directory:").strip()
			for line in cache_text.splitlines()
			if line.startswith("# For build in directory:")
		),
		None,
	)
	normalize_path = lambda value: value.replace("\\", "/").rstrip("/").casefold()
	configured_generator = cache_value(cache, "CMAKE_GENERATOR")
	configured_pointer_size = cache_value(cache, "CMAKE_SIZEOF_VOID_P")
	configured_compiler = cache_value(cache, "CMAKE_CXX_COMPILER")
	configured_fetchcontent_dir = cache_value(cache, "FETCHCONTENT_BASE_DIR")
	configured_x86_compiler = configured_compiler and "hostx86/x86" in configured_compiler.lower().replace("\\", "/")
	invalid_reasons = []
	if configured_build_dir and normalize_path(configured_build_dir) != normalize_path(str(build_dir.resolve())):
		invalid_reasons.append(f"a different build directory ({configured_build_dir})")
	expected_fetchcontent_dir = build_dir / "_deps"
	if configured_fetchcontent_dir and normalize_path(configured_fetchcontent_dir) != normalize_path(str(expected_fetchcontent_dir.resolve())):
		invalid_reasons.append(f"a different FetchContent directory ({configured_fetchcontent_dir})")
	if configured_generator and configured_generator != GENERATOR:
		invalid_reasons.append(f"the {configured_generator} generator")
	if configured_pointer_size and configured_pointer_size != "8":
		invalid_reasons.append(f"{configured_pointer_size}-byte pointers")
	if configured_x86_compiler:
		invalid_reasons.append("an x86 compiler")
	if invalid_reasons:
		report(
			f"Replacing the existing {description} build tree configured for "
			f"{', '.join(invalid_reasons)}."
		)
		remove_tree(build_dir)
		build_dir.mkdir(parents=True, exist_ok=True)


def configure_commonlib(
	cmake: str,
	source_dir: Path,
	build_dir: Path,
	install_dir: Path,
	vcpkg_static_dir: Path,
	repo_root: Path,
	environment: dict[str, str],
) -> int:
	prepare_cmake_build_tree(build_dir, "CommonLibSSE-NG")
	install_dir.mkdir(parents=True, exist_ok=True)
	return run_process(
		[
			cmake,
			"-S",
			str(source_dir),
			"-B",
			str(build_dir),
			"-G",
			GENERATOR,
			f"-DCMAKE_BUILD_TYPE={BUILD_TYPE}",
			f"-DCMAKE_INSTALL_PREFIX={install_dir}",
			f"-DCMAKE_PREFIX_PATH={vcpkg_static_dir}",
			f"-DFETCHCONTENT_BASE_DIR={build_dir / '_deps'}",
			"-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded",
			"-DBUILD_TESTS=OFF",
			"-DREX_OPTION_INI=ON",
			"-DENABLE_SKYRIM_SE=ON",
			"-DENABLE_SKYRIM_AE=ON",
			"-DENABLE_SKYRIM_VR=ON",
		"-U",
		"RAPIDCSV_INCLUDE_DIRS",
		"-U",
		"directxmath_DIR",
		"-U",
		"directxtk_DIR",
		"-U",
		"fmt_DIR",
		"-U",
		"spdlog_DIR",
		],
		repo_root,
		environment,
	)


def build_commonlib(
	cmake: str,
	source_dir: Path,
	build_dir: Path,
	install_dir: Path,
	repo_root: Path,
	environment: dict[str, str],
) -> int:
	exit_code = run_process(
		[cmake, "--build", str(build_dir), "--target", "CommonLibSSE"],
		repo_root,
		environment,
	)
	if exit_code != 0:
		return exit_code
	install_exit = run_process(
		[cmake, "--install", str(build_dir)],
		repo_root,
		environment,
		"CommonLibSSE-NG",
	)
	if install_exit != 0:
		return install_exit

	helper_source = source_dir / "cmake" / "CommonLibSSE.cmake"
	helper_destination = install_dir / "lib" / "cmake" / "CommonLibSSE" / helper_source.name
	if not helper_source.is_file():
		raise FileNotFoundError(f"CommonLibSSE consumer helper does not exist: {helper_source}")
	helper_destination.parent.mkdir(parents=True, exist_ok=True)
	shutil.copyfile(helper_source, helper_destination)
	report(f"Installed the CommonLibSSE consumer helper: {helper_destination}")
	return 0


def configure_build(
	cmake: str,
	source_dir: Path,
	build_dir: Path,
	commonlib_source_dir: Path,
	commonlib_install_dir: Path,
	vcpkg_static_dir: Path,
	imgui_install_dir: Path,
	deploy_dir: Path,
	repo_root: Path,
	environment: dict[str, str],
) -> int:
	prepare_cmake_build_tree(build_dir, "alchemist")
	cmake_arguments = [
		cmake,
		"-S",
		str(source_dir),
		"-B",
		str(build_dir),
		"-G",
		GENERATOR,
		f"-DCMAKE_BUILD_TYPE={BUILD_TYPE}",
		f"-DCOMMONLIBSSE_DIR={commonlib_source_dir}",
		f"-DCOMMONLIBSSE_INSTALL_DIR={commonlib_install_dir}",
		f"-DVCPKG_STATIC_DIR={vcpkg_static_dir}",
		f"-DIMGUI_INSTALL_DIR={imgui_install_dir}",
		f"-DALCHEMIST_DEPLOY_DIR={deploy_dir}",
		"-U",
		"RAPIDCSV_INCLUDE_DIRS",
		"-U",
		"directxmath_DIR",
		"-U",
		"directxtk_DIR",
		"-U",
		"fmt_DIR",
		"-U",
		"nlohmann_json_DIR",
		"-U",
		"spdlog_DIR",
	]

	return run_process(
		cmake_arguments,
		repo_root,
		environment,
	)


def clean_plugin_outputs(
	ninja: str,
	build_dir: Path,
	repo_root: Path,
	environment: dict[str, str],
) -> int:
	report("Cleaning alchemist outputs while preserving the external CommonLibSSE-NG package and cached ImGui targets.")
	return run_process(
		[ninja, "-C", str(build_dir), "-t", "clean", "-r", *PLUGIN_CLEAN_RULES],
		repo_root,
		environment,
	)


def remove_legacy_commonlib_outputs(build_dir: Path) -> None:
	legacy_paths = [
		build_dir / "CommonLibSSE",
		build_dir / "_deps" / "hde64-src",
		build_dir / "_deps" / "hde64-build",
		build_dir / "_deps" / "hde64-subbuild",
	]
	for path in legacy_paths:
		if path.is_dir():
			report(f"Removing the obsolete in-tree CommonLibSSE-NG output: {path}")
			remove_tree(path)


def build_once(
	cmake: str,
	build_dir: Path,
	artifact: Path,
	symbol_artifact: Path,
	repo_root: Path,
	environment: dict[str, str],
) -> tuple[int, int]:
	# Capture the timestamp immediately before the one allowed build attempt so a stale
	# incremental artifact can be detected and retried at most once by main().
	build_start_ns = time.time_ns()
	build_start = datetime.now().astimezone().isoformat(timespec="seconds")
	start_file = Path(os.environ.get("TEMP", repo_root)) / "prosperous-alchemist-build-start.txt"
	start_file.write_text(build_start + "\n", encoding="utf-8")
	report(f"Build start: {build_start}")
	exit_code = run_process(
		[cmake, "--build", str(build_dir), "--target", TARGET],
		repo_root,
		environment,
	)
	result = artifact_details(artifact)
	symbol_result = artifact_details(symbol_artifact)
	if result is None:
		report(f"Build exit={exit_code}; artifact missing: {artifact}")
	if symbol_result is None:
		report(f"Build exit={exit_code}; symbol artifact missing: {symbol_artifact}")
	if result is not None:
		artifact_ns, _, artifact_timestamp, _ = result
		freshness = "newer" if artifact_ns > build_start_ns else "not newer"
		report(f"Build exit={exit_code}; artifact={artifact_timestamp}; artifact is {freshness} than build start")
	if symbol_result is not None:
		symbol_ns, _, symbol_timestamp, _ = symbol_result
		freshness = "newer" if symbol_ns > build_start_ns else "not newer"
		report(f"Build exit={exit_code}; symbols={symbol_timestamp}; symbols are {freshness} than build start")
	return exit_code, build_start_ns


def deploy_locale_resources(repo_root: Path, deployed: Path) -> bool:
	source_directory = repo_root / "locales"
	destination_directory = deployed.parent / "locales"
	locale_files = sorted(source_directory.glob("alchemist.*.json"))
	if not locale_files:
		report(f"No locale resources found to deploy from {source_directory}.")
		return False
	try:
		destination_directory.mkdir(parents=True, exist_ok=True)
		for source_path in locale_files:
			shutil.copy2(source_path, destination_directory / source_path.name)
	except OSError as error:
		report(f"Unable to deploy locale resources to {destination_directory}: {error}")
		return False
	report(f"Deployed {len(locale_files)} locale resources to {destination_directory}.")
	return True


def deploy_artifact(artifact: Path, symbol_artifact: Path, deployed: Path, repo_root: Path) -> bool:
	deployed_symbol = deployed.with_suffix(".pdb")
	# Preserve the built timestamps; verify_deployment() separately checks timestamps and hashes.
	try:
		deployed.parent.mkdir(parents=True, exist_ok=True)
		shutil.copyfile(artifact, deployed)
		artifact_stat = artifact.stat()
		os.utime(deployed, ns=(artifact_stat.st_atime_ns, artifact_stat.st_mtime_ns))
		shutil.copyfile(symbol_artifact, deployed_symbol)
		symbol_stat = symbol_artifact.stat()
		os.utime(deployed_symbol, ns=(symbol_stat.st_atime_ns, symbol_stat.st_mtime_ns))
	except OSError as error:
		report(f"Unable to deploy {artifact} and {symbol_artifact} to {deployed.parent}: {error}")
		return False
	report(f"Deployed {artifact} and {symbol_artifact} to {deployed.parent} with the built file timestamps.")
	return deploy_locale_resources(repo_root, deployed)


def verify_deployment(artifact: Path, symbol_artifact: Path, deployed: Path) -> bool:
	deployed_symbol = deployed.with_suffix(".pdb")
	built = artifact_details(artifact)
	built_symbol = artifact_details(symbol_artifact)
	deployed_details = artifact_details(deployed)
	deployed_symbol_details = artifact_details(deployed_symbol)
	if built is None:
		report(f"Built artifact is missing: {artifact}")
		return False
	if built_symbol is None:
		report(f"Built symbol artifact is missing: {symbol_artifact}")
		return False
	if deployed_details is None:
		report(f"Deployed artifact is missing: {deployed}")
		return False
	if deployed_symbol_details is None:
		report(f"Deployed symbol artifact is missing: {deployed_symbol}")
		return False

	report(
		f"Built DLL: timestamp={built[2]}; size={built[1]}; SHA-256={built[3]}"
	)
	report(
		f"Deployed DLL: timestamp={deployed_details[2]}; size={deployed_details[1]}; "
		f"SHA-256={deployed_details[3]}"
	)
	report(
		f"Built PDB: timestamp={built_symbol[2]}; size={built_symbol[1]}; SHA-256={built_symbol[3]}"
	)
	report(
		f"Deployed PDB: timestamp={deployed_symbol_details[2]}; size={deployed_symbol_details[1]}; "
		f"SHA-256={deployed_symbol_details[3]}"
	)
	if built[0] != deployed_details[0] or built[3] != deployed_details[3]:
		report("Built and deployed DLLs differ in timestamp or contents.")
		return False
	if built_symbol[0] != deployed_symbol_details[0] or built_symbol[3] != deployed_symbol_details[3]:
		report("Built and deployed PDBs differ in timestamp or contents.")
		return False
	report("Built and deployed DLLs and PDBs match.")
	return True


def convert_user_readme_to_bbcode(repo_root: Path, md2nexus: Path, output_path: Path) -> Path:
	source_path = repo_root / "docs" / "USER_README.md"
	if not source_path.is_file():
		raise FileNotFoundError(f"User readme does not exist: {source_path}")
	if not md2nexus.is_file():
		raise FileNotFoundError(f"md2nexus executable does not exist: {md2nexus}")

	output_path.parent.mkdir(parents=True, exist_ok=True)
	try:
		output_path.unlink()
	except FileNotFoundError:
		pass

	report(f"Generating Nexus BBCode from {source_path} to {output_path}.")
	exit_code = run_process(
		[
			str(md2nexus),
			"--input",
			str(source_path),
			"--output",
			str(output_path),
		],
		repo_root,
	)
	if exit_code != 0:
		raise RuntimeError(f"md2nexus failed with exit={exit_code}")
	if not output_path.is_file() or output_path.stat().st_size == 0:
		raise RuntimeError(f"md2nexus did not create a non-empty output file: {output_path}")
	report(f"Nexus BBCode created successfully: {output_path} ({output_path.stat().st_size} bytes)")
	return output_path


def package_release(
	repo_root: Path,
	artifact: Path,
	symbol_artifact: Path,
	md2nexus: Path,
	package_path: Path | None = None,
) -> Path:
	if package_path is None:
		package_path = release_package_path(repo_root)
	package_path.parent.mkdir(parents=True, exist_ok=True)
	if not symbol_artifact.is_file():
		raise FileNotFoundError(f"Release PDB does not exist: {symbol_artifact}")

	convert_user_readme_to_bbcode(
		repo_root,
		md2nexus,
		repo_root / "dist" / NEXUS_BBCODE_FILENAME,
	)

	ini_path = repo_root / "alchemist.ini"

	report(f"Packaging release distribution archive: {package_path}")
	with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
		zf.write(artifact, "SKSE/Plugins/alchemist.dll")
		zf.write(symbol_artifact, "SKSE/Plugins/alchemist.pdb")
		if ini_path.is_file():
			zf.write(ini_path, "SKSE/Plugins/alchemist.ini")
		for resource_directory_name in ("locales", "fonts"):
			resource_directory = repo_root / resource_directory_name
			if resource_directory.is_dir():
				for resource_path in sorted(resource_directory.rglob("*")):
					if resource_path.is_file():
						relative_path = resource_path.relative_to(resource_directory).as_posix()
						zf.write(resource_path, f"SKSE/Plugins/{resource_directory_name}/{relative_path}")
		if (repo_root / "COPYING").is_file():
			zf.write(repo_root / "COPYING", "COPYING")
		if (repo_root / "EXCEPTIONS.md").is_file():
			zf.write(repo_root / "EXCEPTIONS.md", "EXCEPTIONS.md")
		if (repo_root / "docs" / "USER_README.md").is_file():
			zf.write(repo_root / "docs" / "USER_README.md", "docs/USER_README.md")
		licenses_dir = repo_root / "licenses"
		if licenses_dir.is_dir():
			for lic_file in sorted(licenses_dir.glob("*")):
				if lic_file.is_file():
					zf.write(lic_file, f"licenses/{lic_file.name}")

	report(f"Package created successfully: size={package_path.stat().st_size} bytes")
	return package_path


def main() -> int:
	global status_file

	parser = argparse.ArgumentParser(description="Build the Prosperous Alchemist plugin with live progress output.")
	parser.add_argument("--build-dir", default="build-alchemist")
	parser.add_argument("--cmake", default="cmake")
	parser.add_argument("--package", action="store_true", help="Create a release distribution zip archive.")
	args = parser.parse_args()

	repo_root = Path(__file__).resolve().parent
	# The standalone consumer is the canonical CMake source root. Visual Studio settings
	# may point at this directory only to avoid an IDE warning; build.py remains the
	# supported entry point and controls the Release/Ninja/deployment contract.
	source_dir = repo_root / "alchemist"
	build_dir = (repo_root / args.build_dir).resolve()
	status_file = build_dir / ".build-status.txt"
	try:
		from config import (
			CMAKE_DIR,
			COMMONLIBSSE_BUILD_DIR,
			COMMONLIBSSE_INSTALL_DIR,
			COMMONLIBSSE_SOURCE,
			DLL_DEPLOY,
			MD2NEXUS,
			NINJA_DIR,
			VCPKG_BINARY_CACHE_DIR,
			VCPKG_DOWNLOADS_DIR,
			VCPKG_ROOT,
			VCPKG_STATIC_DIR,
			VCPKG_STATIC_INSTALL_ROOT,
			IMGUI_BUILD_DIR,
			IMGUI_INSTALL_DIR,
			IMGUI_SOURCE_DIR,
		)
	except ImportError as error:
		report(f"Missing config.py; copy config.example.py and set local paths: {error}")
		return 2
	if args.cmake == "cmake" and Path(CMAKE_DIR).is_dir():
		args.cmake = str(Path(CMAKE_DIR) / "cmake.exe")
	os.environ["PATH"] = str(NINJA_DIR) + os.pathsep + os.environ.get("PATH", "")
	commonlib_source_dir = Path(COMMONLIBSSE_SOURCE).resolve()
	commonlib_build_dir = Path(COMMONLIBSSE_BUILD_DIR).resolve()
	commonlib_install_dir = Path(COMMONLIBSSE_INSTALL_DIR).resolve()
	vcpkg_root = Path(VCPKG_ROOT).resolve()
	vcpkg_downloads_dir = Path(VCPKG_DOWNLOADS_DIR).resolve()
	vcpkg_binary_cache_dir = Path(VCPKG_BINARY_CACHE_DIR).resolve()
	vcpkg_static_install_root = Path(VCPKG_STATIC_INSTALL_ROOT).resolve()
	vcpkg_static_dir = Path(VCPKG_STATIC_DIR).resolve()
	imgui_source_dir = Path(IMGUI_SOURCE_DIR).resolve()
	imgui_build_dir = Path(IMGUI_BUILD_DIR).resolve()
	imgui_install_dir = Path(IMGUI_INSTALL_DIR).resolve()
	deployed = Path(DLL_DEPLOY).resolve()
	md2nexus = Path(MD2NEXUS).resolve()
	artifact = build_dir / f"{TARGET}.dll"
	symbol_artifact = build_dir / f"{TARGET}.pdb"
	if not source_dir.is_dir():
		report(f"CMake source directory does not exist: {source_dir}")
		return 2
	if not (commonlib_source_dir / "CMakeLists.txt").is_file():
		report(f"CommonLibSSE-NG source directory does not exist: {commonlib_source_dir}")
		return 2
	try:
		validate_vcpkg_layout(repo_root, vcpkg_root, vcpkg_static_install_root, vcpkg_static_dir)
		validate_imgui_layout(repo_root, imgui_source_dir, imgui_build_dir, imgui_install_dir)
	except RuntimeError as error:
		report(f"Invalid external dependency path configuration: {error}")
		return 2
	if not vcpkg_static_dir.is_dir():
		report(f"Manifest-specific static vcpkg directory does not exist: {vcpkg_static_dir}")
		return 2
	try:
		environment = x64_msvc_environment()
		environment = configure_vcpkg_environment(
			environment,
			vcpkg_root,
			vcpkg_downloads_dir,
			vcpkg_binary_cache_dir,
		)
	except RuntimeError as error:
		report(f"Unable to configure the x64 MSVC environment: {error}")
		return 2
	ninja = shutil.which("ninja", path=environment.get("PATH"))
	if not ninja:
		report("Ninja executable was not found on PATH")
		return 2
	report(
		f"Build paths: commonlib_source={commonlib_source_dir}; commonlib_build={commonlib_build_dir}; "
		f"commonlib_install={commonlib_install_dir}; vcpkg_root={vcpkg_root}; "
		f"vcpkg_downloads={vcpkg_downloads_dir}; vcpkg_binary_cache={vcpkg_binary_cache_dir}; "
		f"vcpkg_static_install_root={vcpkg_static_install_root}; vcpkg_static_dir={vcpkg_static_dir}; "
		f"imgui_source={imgui_source_dir}; imgui_build={imgui_build_dir}; imgui_install={imgui_install_dir}; "
		f"source={source_dir}; build={build_dir}; deploy={deployed}"
	)

	report(f"Configuring reusable ImGui at {imgui_build_dir} with {GENERATOR} and {BUILD_TYPE}.")
	imgui_configure_exit = configure_imgui(
		args.cmake,
		imgui_source_dir,
		imgui_build_dir,
		imgui_install_dir,
		repo_root,
		environment,
	)
	if imgui_configure_exit != 0:
		report(f"Reusable ImGui configure failed with exit={imgui_configure_exit}")
		return imgui_configure_exit
	imgui_build_exit = build_imgui(
		args.cmake,
		imgui_build_dir,
		imgui_install_dir,
		repo_root,
		environment,
	)
	if imgui_build_exit != 0:
		report(f"Reusable ImGui build or install failed with exit={imgui_build_exit}")
		return imgui_build_exit

	report(f"Configuring external CommonLibSSE-NG at {commonlib_source_dir} with {GENERATOR} and {BUILD_TYPE}.")
	commonlib_configure_exit = configure_commonlib(
		args.cmake,
		commonlib_source_dir,
		commonlib_build_dir,
		commonlib_install_dir,
		vcpkg_static_dir,
		repo_root,
		environment,
	)
	if commonlib_configure_exit != 0:
		report(f"CommonLib configure failed with exit={commonlib_configure_exit}")
		return commonlib_configure_exit
	commonlib_build_exit = build_commonlib(
		args.cmake,
		commonlib_source_dir,
		commonlib_build_dir,
		commonlib_install_dir,
		repo_root,
		environment,
	)
	if commonlib_build_exit != 0:
		report(f"CommonLib build or install failed with exit={commonlib_build_exit}")
		return commonlib_build_exit
	remove_legacy_commonlib_outputs(build_dir)

	report(f"Configuring {source_dir} with {GENERATOR} and {BUILD_TYPE}.")
	configure_exit = configure_build(
		args.cmake,
		source_dir,
		build_dir,
		commonlib_source_dir,
		commonlib_install_dir,
		vcpkg_static_dir,
		imgui_install_dir,
		deployed.parent,
		repo_root,
		environment,
	)
	if configure_exit != 0:
		report(f"Configure failed with exit={configure_exit}")
		return configure_exit

	clean_exit = clean_plugin_outputs(
		ninja,
		build_dir,
		repo_root,
		environment,
	)
	if clean_exit != 0:
		report(f"Plugin clean failed with exit={clean_exit}")
		return clean_exit

	exit_code, build_start_ns = build_once(
		args.cmake,
		build_dir,
		artifact,
		symbol_artifact,
		repo_root,
		environment,
	)

	if exit_code != 0:
		return exit_code
	artifact_result = artifact_details(artifact)
	symbol_result = artifact_details(symbol_artifact)
	if (
		artifact_result is None
		or artifact_result[0] <= build_start_ns
		or symbol_result is None
		or symbol_result[0] <= build_start_ns
	):
		report("Build artifact or PDB failed freshness validation; performing one clean rebuild.")
		retry_clean_exit = clean_plugin_outputs(
			ninja,
			build_dir,
			repo_root,
			environment,
		)
		if retry_clean_exit != 0:
			report(f"Retry plugin clean failed with exit={retry_clean_exit}")
			return retry_clean_exit
		exit_code, build_start_ns = build_once(
			args.cmake,
			build_dir,
			artifact,
			symbol_artifact,
			repo_root,
			environment,
		)
		if exit_code != 0:
			return exit_code
		artifact_result = artifact_details(artifact)
		symbol_result = artifact_details(symbol_artifact)
		if (
			artifact_result is None
			or artifact_result[0] <= build_start_ns
			or symbol_result is None
			or symbol_result[0] <= build_start_ns
		):
			report("Build DLL or PDB failed freshness validation after the allowed rebuild.")
			return 3
	if not deploy_artifact(artifact, symbol_artifact, deployed, repo_root):
		return 4
	if not verify_deployment(artifact, symbol_artifact, deployed):
		return 4
	if args.package:
		package_release(repo_root, artifact, symbol_artifact, md2nexus)
	report("Build completed with a fresh artifact.")
	return 0


if __name__ == "__main__":
	build_log = (Path(__file__).resolve().parent / "build.log").open("w", encoding="utf-8", buffering=1)
	exit_code = 1
	try:
		exit_code = main()
	except Exception as error:
		report(f"Build wrapper failed: {error}")
		exit_code = 1
	finally:
		build_log.close()
		if status_file is not None:
			status_file.parent.mkdir(parents=True, exist_ok=True)
			status_file.write_text(f"exit_code={exit_code}\ntimestamp={timestamp()}\n", encoding="utf-8")
	sys.exit(exit_code)
