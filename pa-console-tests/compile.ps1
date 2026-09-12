$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

$caprica = "E:\Projects\games\skyrim\utils\Caprica.v0.3.0\Caprica.exe"
$flags = "E:\Projects\games\skyrim\utils\CreationKit\Data\Source\Scripts\TESV_Papyrus_Flags.flg"
$importSKSE = "E:\Projects\games\skyrim\1.6.1170\mods\skse64_1_6_1170 scripts\Scripts\Source"
$import2 = "E:\Projects\games\skyrim\utils\CreationKit\Data\Source\Scripts"
$import3 = "E:\Projects\games\skyrim\git\powerof3-PapyrusExtenderSSE\Papyrus\Source\scripts"
$import4 = "E:\Projects\games\skyrim\git\KrisV-777-ConsoleUtil-Extended\dist\Source\Scripts"

# Destination directories in the live mod profile
$output = "E:\Projects\games\skyrim\1.6.1170\mods\Prosperous Alchemist NG\Scripts"
$customConsoleDir = "E:\Projects\games\skyrim\1.6.1170\mods\Prosperous Alchemist NG\SKSE\CustomConsole"

if (-not (Test-Path $output)) { New-Item -ItemType Directory -Force -Path $output | Out-Null }
if (-not (Test-Path $customConsoleDir)) { New-Item -ItemType Directory -Force -Path $customConsoleDir | Out-Null }

Write-Host "Deploying pa-tests.yaml to SKSE\CustomConsole..."
Copy-Item -Path ".\SKSE\CustomConsole\pa-tests.yaml" -Destination $customConsoleDir -Force

Write-Host "Compiling ProsperousAlchemistTests.psc with Caprica..."
Push-Location "Source\Scripts"
try {
    & $caprica --game skyrim --flags $flags -i "." -i ".." -i $importSKSE -i $import2 -i $import3 -i $import4 "ProsperousAlchemistTests.psc" -o $output
} finally {
    Pop-Location
}

Write-Host "Done! Test scripts are compiled and deployed to your MO2 profile."
