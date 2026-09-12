"""Build the legacy SKSE solution with optimized code and PDB symbols.

The requested SKSE checkout is organized around a Visual Studio solution rather
than a complete standalone CMake tree. The default ``Release_VC142|x64``
configuration is optimized and the SKSE project enables linker debug
information; the wrapper also requests compiler program-database information.
Build output is redirected to an externally configured SKSE build root and is
deployed to the configured Skyrim installation unless ``--no-deploy`` is specified.
The checkout's legacy property sheet emits the main target with an outdated
runtime suffix, so the wrapper normalizes that generated DLL and PDB to the
runtime targeted by the checkout. All generated output, MSBuild intermediates,
wrapper status, temporary properties, and logs are placed under the configured
external SKSE build root rather than the source checkout or repository root.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape


build_log = None
status_file = None

DEFAULT_CONFIGURATION = "Release_VC142"
DEFAULT_PLATFORM = "x64"
SOLUTION_RELATIVE_PATH = Path("src") / "skse64" / "skse64.sln"
TARGET_PROPERTIES_RELATIVE_PATH = Path("src") / "skse64" / "sheets" / "Common.props"
RUNTIME_DEFINITION_RELATIVE_PATH = Path("src") / "skse64" / "skse64" / "skse64.def"
NORMALIZED_TARGET_NAME = "skse64_1_6_1170"
LOADER_NAME = "skse64_loader"
RUNTIME_VERSION_DEFINE = "0x01064920"
RUNTIME_OVERRIDE_PROPS_NAME = ".skse-runtime-override.props"


def timestamp() -> str:
	return datetime.now().astimezone().isoformat(timespec="seconds")


def report(message: str) -> None:
	line = f"[{timestamp()}] {message}"
	print(line, flush=True)
	if build_log is not None:
		build_log.write(line + "\n")
		build_log.flush()


def absolute_path(path: Path, base_dir: Path) -> Path:
	if path.is_absolute():
		return path.resolve()
	return (base_dir / path).resolve()


def configured_build_log_path(repo_root: Path) -> Path:
	try:
		from config import SKSE_BUILD_DIR
	except ImportError:
		build_root = repo_root / "build-skse"
	else:
		build_root = absolute_path(Path(SKSE_BUILD_DIR), repo_root)
	return build_root / "build-skse.log"


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
				vswhere_paths.append(
					Path(program_files) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
				)
		for vswhere in vswhere_paths:
			if not vswhere.is_file():
				continue
			try:
				result = subprocess.run(
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
				install_path = result.stdout.strip()
				if install_path:
					candidate = Path(install_path) / "Common7" / "Tools" / "VsDevCmd.bat"
					if (candidate.parent.parent.parent / "VC" / "Tools" / "MSVC").is_dir() and candidate.is_file():
						vsdevcmd = candidate
						break
			except (OSError, subprocess.SubprocessError):
				pass

	if not vsdevcmd or not vsdevcmd.is_file():
		raise RuntimeError(
			"VsDevCmd.bat was not found; install the Visual Studio C++ tools or run from an x64 MSVC developer shell"
		)

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


def resolve_msbuild(msbuild: str, environment: dict[str, str]) -> str:
	candidate = Path(msbuild)
	if candidate.is_file():
		return str(candidate.resolve())
	found = shutil.which(msbuild, path=environment.get("PATH"))
	if found:
		return found
	raise RuntimeError(f"MSBuild executable was not found: {msbuild}")


def environment_value(environment: dict[str, str], name: str) -> str | None:
	for key, value in environment.items():
		if key.lower() == name.lower():
			return value
	return None


def infer_platform_toolset(environment: dict[str, str]) -> str | None:
	version = environment_value(environment, "VCToolsVersion")
	if not version:
		return None
	match = re.match(r"14\.(\d+)", version)
	if match and int(match.group(1)) >= 30:
		return "v143"
	if match and int(match.group(1)) >= 20:
		return "v142"
	return None


def add_checkout_include_path(environment: dict[str, str], source_dir: Path) -> dict[str, str]:
	include_dir = source_dir / "src" / "common"
	if not include_dir.is_dir():
		raise RuntimeError(f"SKSE common include directory does not exist: {include_dir}")
	result = environment.copy()
	include_key = next((key for key in result if key.lower() == "include"), "INCLUDE")
	existing = result.get(include_key, "")
	result[include_key] = str(include_dir) + (os.pathsep + existing if existing else "")
	cl_key = next((key for key in result if key.lower() == "cl"), "CL")
	existing_cl_options = result.get(cl_key, "").strip()
	result[cl_key] = f'{existing_cl_options} /I"{include_dir}"'.strip()
	report(f"Added the SKSE common include directory: {include_dir}")
	return result


def create_runtime_override_props(
	output_dir: Path, intermediate_root: Path, runtime_definition_file: Path
) -> Path:
	output_dir.mkdir(parents=True, exist_ok=True)
	props_path = output_dir / RUNTIME_OVERRIDE_PROPS_NAME
	definition_file = escape(str(runtime_definition_file.resolve()))
	intermediate_directory = escape(str(intermediate_root.resolve()) + os.sep + "$(MSBuildProjectName)" + os.sep)
	props_path.write_text(
		"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
		"<Project xmlns=\"http://schemas.microsoft.com/developer/msbuild/2003\">\n"
		"  <PropertyGroup>\n"
		f"    <IntDir>{intermediate_directory}</IntDir>\n"
		"  </PropertyGroup>\n"
		"  <ItemDefinitionGroup>\n"
		"    <ClCompile>\n"
		f"      <AdditionalOptions>/URUNTIME_VERSION /DRUNTIME_VERSION={RUNTIME_VERSION_DEFINE} %(AdditionalOptions)</AdditionalOptions>\n"
		"    </ClCompile>\n"
		"  </ItemDefinitionGroup>\n"
		"  <ItemDefinitionGroup Condition=\"'$(MSBuildProjectName)' == 'skse64'\">\n"
		"    <Link>\n"
		f"      <ModuleDefinitionFile>{definition_file}</ModuleDefinitionFile>\n"
		"    </Link>\n"
		"  </ItemDefinitionGroup>\n"
		"</Project>\n",
		encoding="utf-8",
	)
	report(
		f"Created temporary MSBuild runtime override: {props_path}; "
		f"IntDir={intermediate_directory}; RUNTIME_VERSION={RUNTIME_VERSION_DEFINE}; "
		f"ModuleDefinitionFile={runtime_definition_file}"
	)
	return props_path


def remove_runtime_override_props(props_path: Path) -> None:
	try:
		props_path.unlink()
	except FileNotFoundError:
		return
	except OSError as error:
		report(f"Unable to remove temporary MSBuild runtime override {props_path}: {error}")
	else:
		report(f"Removed temporary MSBuild runtime override: {props_path}")


def run_process(
	command: list[str],
	working_dir: Path,
	environment: dict[str, str],
) -> int:
	resolved_command = list(command)
	if environment.get("PATH") and not Path(resolved_command[0]).is_file():
		found_path = shutil.which(resolved_command[0], path=environment.get("PATH"))
		if found_path:
			resolved_command[0] = found_path
	report("Running: " + " ".join(resolved_command))
	process = subprocess.Popen(
		resolved_command,
		cwd=working_dir,
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
	while not output_closed or process.poll() is None:
		try:
			line = output.get(timeout=10)
		except queue.Empty:
			report("Build still running; waiting for MSBuild output...")
			continue
		if line is None:
			output_closed = True
			continue
		if line:
			report("[msbuild] " + line)
	return process.wait()


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


def validate_checkout(source_dir: Path, configuration: str, platform: str) -> tuple[Path, str]:
	if not source_dir.is_dir():
		raise RuntimeError(f"SKSE source directory does not exist: {source_dir}")
	solution = source_dir / SOLUTION_RELATIVE_PATH
	properties = source_dir / TARGET_PROPERTIES_RELATIVE_PATH
	common_project = source_dir / "src" / "common" / "common" / "common_vc14.vcxproj"
	for required_path in (solution, properties, common_project):
		if not required_path.is_file():
			raise RuntimeError(f"Required SKSE checkout file does not exist: {required_path}")

	solution_text = solution.read_text(encoding="utf-8", errors="replace")
	configuration_key = f"{configuration}|{platform}"
	if configuration_key not in solution_text:
		raise RuntimeError(f"SKSE solution does not define the requested configuration: {configuration_key}")

	properties_text = properties.read_text(encoding="utf-8", errors="replace")
	match = re.search(r"<TargetName>\s*([^<]+?)\s*</TargetName>", properties_text)
	if not match:
		raise RuntimeError(f"Unable to determine the SKSE target name from {properties}")
	target_name = match.group(1).strip().replace("$(ProjectName)", "skse64")
	if not target_name:
		raise RuntimeError(f"SKSE target name is empty in {properties}")
	return solution, target_name


def build_once(
	msbuild: str,
	solution: Path,
	source_dir: Path,
	output_dir: Path,
	intermediate_root: Path,
	configuration: str,
	platform: str,
	platform_toolset: str | None,
	windows_sdk_version: str,
	environment: dict[str, str],
	target_name: str,
	runtime_override_props: Path,
) -> tuple[int, int, Path, Path]:
	output_dir.mkdir(parents=True, exist_ok=True)
	intermediate_root.mkdir(parents=True, exist_ok=True)
	build_start_ns = time.time_ns()
	build_start = datetime.now().astimezone().isoformat(timespec="seconds")
	(output_dir / ".build-start.txt").write_text(build_start + "\n", encoding="utf-8")
	report(f"Build start: {build_start}")

	output_argument = str(output_dir)
	if not output_argument.endswith(("\\", "/")):
		output_argument += os.sep
	command = [
		msbuild,
		str(solution),
		"/t:Rebuild",
		"/m",
		"/nologo",
		"/v:minimal",
		f"/p:Configuration={configuration}",
		f"/p:Platform={platform}",
		f"/p:OutDir={output_argument}",
		f"/p:WindowsTargetPlatformVersion={windows_sdk_version}",
		f"/p:ForceImportBeforeCppTargets={runtime_override_props}",
		"/p:PostBuildEventUseInBuild=false",
		"/p:GenerateDebugInformation=true",
		"/p:DebugInformationFormat=ProgramDatabase",
	]
	if platform_toolset:
		command.append(f"/p:PlatformToolset={platform_toolset}")

	exit_code = run_process(command, source_dir, environment)
	dll = output_dir / f"{target_name}.dll"
	pdb = output_dir / f"{target_name}.pdb"
	for label, path in (("SKSE DLL", dll), ("SKSE PDB", pdb)):
		result = artifact_details(path)
		if result is None:
			report(f"Build exit={exit_code}; {label} is missing: {path}")
			continue
		freshness = "newer" if result[0] > build_start_ns else "not newer"
		report(f"Build exit={exit_code}; {label}={result[2]}; artifact is {freshness} than build start")
	return exit_code, build_start_ns, dll, pdb


def verify_fresh_artifact(path: Path, build_start_ns: int, label: str) -> bool:
	result = artifact_details(path)
	if result is None:
		report(f"{label} is missing: {path}")
		return False
	if result[0] <= build_start_ns:
		report(f"{label} is stale: {path}")
		return False
	report(f"Built {label}: timestamp={result[2]}; size={result[1]}; SHA-256={result[3]}")
	return True


def verify_runtime_export(path: Path, environment: dict[str, str]) -> bool:
	dumpbin = shutil.which("dumpbin.exe", path=environment.get("PATH")) or shutil.which(
		"dumpbin", path=environment.get("PATH")
	)
	if not dumpbin:
		report("dumpbin was not found; cannot verify the SKSE runtime StartSKSE export.")
		return False
	try:
		result = subprocess.run(
			[dumpbin, "/exports", str(path)],
			capture_output=True,
			text=True,
			encoding="utf-8",
			errors="replace",
			check=False,
			env=environment,
		)
	except OSError as error:
		report(f"Unable to inspect SKSE runtime exports with dumpbin: {error}")
		return False
	if result.returncode != 0:
		report(f"dumpbin failed while inspecting SKSE runtime exports (exit={result.returncode}).")
		return False
	if not re.search(r"\bStartSKSE\b", result.stdout):
		report(f"SKSE runtime is missing the required StartSKSE export: {path}")
		return False
	report(f"Verified SKSE runtime StartSKSE export: {path}")
	return True


def normalize_target_artifacts(
	output_dir: Path, target_name: str, build_start_ns: int
) -> tuple[Path, Path] | None:
	legacy_dll = output_dir / f"{target_name}.dll"
	legacy_pdb = output_dir / f"{target_name}.pdb"
	normalized_dll = output_dir / f"{NORMALIZED_TARGET_NAME}.dll"
	normalized_pdb = output_dir / f"{NORMALIZED_TARGET_NAME}.pdb"

	if legacy_dll.resolve() != normalized_dll.resolve():
		for source, destination in ((legacy_dll, normalized_dll), (legacy_pdb, normalized_pdb)):
			if not source.is_file():
				report(f"Cannot normalize missing SKSE artifact: {source}")
				return None
			if destination.exists():
				destination.unlink()
			source.replace(destination)
			report(f"Normalized {source.name} to {destination.name}.")

	if not verify_fresh_artifact(normalized_dll, build_start_ns, "SKSE DLL") or not verify_fresh_artifact(
		normalized_pdb, build_start_ns, "SKSE PDB"
	):
		return None
	return normalized_dll, normalized_pdb


def deploy_artifacts(artifacts: tuple[Path, ...], deploy_dir: Path) -> bool:
	try:
		deploy_dir.mkdir(parents=True, exist_ok=True)
		for source in artifacts:
			destination = deploy_dir / source.name
			if source.resolve() == destination.resolve():
				continue
			shutil.copyfile(source, destination)
			stat = source.stat()
			os.utime(destination, ns=(stat.st_atime_ns, stat.st_mtime_ns))
	except OSError as error:
		report(f"Unable to deploy SKSE artifacts to {deploy_dir}: {error}")
		return False

	for source in artifacts:
		destination = deploy_dir / source.name
		source_details = artifact_details(source)
		destination_details = artifact_details(destination)
		if source_details is None or destination_details is None or source_details[3] != destination_details[3]:
			report(f"Deployed SKSE artifact does not match its source: {destination}")
			return False
	report(f"Deployed {', '.join(source.name for source in artifacts)} to {deploy_dir}.")
	return True


def main() -> int:
	global status_file

	repo_root = Path(__file__).resolve().parent
	parser = argparse.ArgumentParser(description="Build the SKSE solution with optimized code and PDB symbols.")
	parser.add_argument("--source-dir", type=Path, default=None, help="SKSE checkout root; defaults to config.SKSE_SOURCE.")
	parser.add_argument(
		"--output-dir",
		type=Path,
		default=None,
		help="Directory for generated SKSE artifacts; defaults to SKSE_BUILD_DIR/<configuration>/<platform>.",
	)
	parser.add_argument("--configuration", default=DEFAULT_CONFIGURATION, help="Visual Studio solution configuration.")
	parser.add_argument("--platform", default=DEFAULT_PLATFORM, help="Visual Studio solution platform.")
	parser.add_argument(
		"--platform-toolset",
		default=None,
		help="Optional MSVC toolset override, such as v143, for machines without the solution's default toolset.",
	)
	parser.add_argument(
		"--windows-sdk-version",
		default=None,
		help="Windows SDK version override; defaults to the version selected by the x64 MSVC environment.",
	)
	parser.add_argument("--msbuild", default="MSBuild.exe", help="MSBuild executable or full path.")
	deployment_options = parser.add_mutually_exclusive_group()
	deployment_options.add_argument(
		"--deploy-dir",
		type=Path,
		default=None,
		help="Directory to receive the SKSE release payload and matching PDBs; defaults to config.SKYRIM.",
	)
	deployment_options.add_argument(
		"--no-deploy",
		action="store_true",
		help="Build and verify artifacts without copying them to the configured Skyrim installation.",
	)
	args = parser.parse_args()

	try:
		from config import SKSE_BUILD_DIR, SKSE_SOURCE, SKYRIM
	except ImportError as error:
		report(f"Missing or incomplete config.py; copy config.example.py and set local paths: {error}")
		return 2

	source_dir = absolute_path(args.source_dir or Path(SKSE_SOURCE), repo_root)
	build_root = absolute_path(Path(SKSE_BUILD_DIR), repo_root)
	output_dir = absolute_path(
		args.output_dir
		if args.output_dir is not None
		else build_root / args.configuration / args.platform,
		repo_root,
	)
	intermediate_root = build_root / "intermediate" / args.configuration / args.platform
	deploy_dir = None
	if not args.no_deploy:
		deploy_dir = absolute_path(args.deploy_dir or Path(SKYRIM), repo_root)
	status_file = build_root / ".build-status.txt"
	report(
		f"Build paths: source={source_dir}; solution={source_dir / SOLUTION_RELATIVE_PATH}; "
		f"build_root={build_root}; output={output_dir}; intermediate={intermediate_root}; "
		f"log={build_root / 'build-skse.log'}; status={status_file}"
	)
	if deploy_dir is not None:
		report(f"SKSE deployment enabled: {deploy_dir}")
	else:
		report("SKSE deployment disabled by --no-deploy")

	try:
		solution, target_name = validate_checkout(source_dir, args.configuration, args.platform)
		environment = x64_msvc_environment()
		environment = add_checkout_include_path(environment, source_dir)
		msbuild = resolve_msbuild(args.msbuild, environment)
		platform_toolset = args.platform_toolset or infer_platform_toolset(environment)
		windows_sdk_version = (args.windows_sdk_version or environment_value(environment, "WindowsSDKVersion") or "").strip(
			"\\/"
		)
		if not windows_sdk_version:
			raise RuntimeError(
				"Windows SDK version was not supplied and was not exposed by the x64 MSVC environment; "
				"pass --windows-sdk-version explicitly"
			)
	except (OSError, RuntimeError) as error:
		report(f"SKSE build setup failed: {error}")
		return 2

	report(
		f"Building target {target_name} with {args.configuration}|{args.platform}; "
		f"PlatformToolset={platform_toolset or 'project default'}; "
		f"compiler debug format=ProgramDatabase; linker debug information=enabled; "
		f"Windows SDK={windows_sdk_version}."
	)
	runtime_definition_file = source_dir / RUNTIME_DEFINITION_RELATIVE_PATH
	runtime_override_props = create_runtime_override_props(output_dir, intermediate_root, runtime_definition_file)
	try:
		exit_code, build_start_ns, dll, pdb = build_once(
			msbuild,
			solution,
			source_dir,
			output_dir,
			intermediate_root,
			args.configuration,
			args.platform,
			platform_toolset,
			windows_sdk_version,
			environment,
			target_name,
			runtime_override_props,
		)
		if exit_code != 0:
			report(f"SKSE build failed with exit={exit_code}")
			return exit_code

		normalized_artifacts = normalize_target_artifacts(output_dir, target_name, build_start_ns)
		if normalized_artifacts is None:
			report("SKSE DLL or PDB failed freshness validation; performing one clean rebuild.")
			exit_code, build_start_ns, dll, pdb = build_once(
				msbuild,
				solution,
				source_dir,
				output_dir,
				intermediate_root,
				args.configuration,
				args.platform,
				platform_toolset,
				windows_sdk_version,
				environment,
				target_name,
				runtime_override_props,
			)
			if exit_code != 0:
				report(f"SKSE clean rebuild failed with exit={exit_code}")
				return exit_code
			normalized_artifacts = normalize_target_artifacts(output_dir, target_name, build_start_ns)
			if normalized_artifacts is None:
				report("SKSE DLL or PDB failed freshness validation after the allowed rebuild.")
				return 3
		dll, pdb = normalized_artifacts
		if not verify_runtime_export(dll, environment):
			report("SKSE runtime export validation failed; refusing to deploy an unusable DLL.")
			return 3
		loader = output_dir / f"{LOADER_NAME}.exe"
		loader_pdb = output_dir / f"{LOADER_NAME}.pdb"
		release_artifacts = (dll, pdb, loader, loader_pdb)
		if not all(
			verify_fresh_artifact(path, build_start_ns, f"SKSE {path.name}")
			for path in (loader, loader_pdb)
		):
			report("A required SKSE release binary or matching PDB failed freshness validation.")
			return 3

		if deploy_dir is not None and not deploy_artifacts(release_artifacts, deploy_dir):
			return 4
		report("SKSE build completed with fresh optimized release binaries and matching PDBs.")
		return 0
	finally:
		remove_runtime_override_props(runtime_override_props)


if __name__ == "__main__":
	log_path = configured_build_log_path(Path(__file__).resolve().parent)
	log_path.parent.mkdir(parents=True, exist_ok=True)
	build_log = log_path.open("w", encoding="utf-8", buffering=1)
	exit_code = 1
	try:
		exit_code = main()
	except Exception as error:
		report(f"SKSE build wrapper failed: {error}")
		exit_code = 1
	finally:
		build_log.close()
		if status_file is not None:
			status_file.parent.mkdir(parents=True, exist_ok=True)
			status_file.write_text(f"exit_code={exit_code}\ntimestamp={timestamp()}\n", encoding="utf-8")
	sys.exit(exit_code)
