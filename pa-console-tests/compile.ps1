$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir
$pathsFile = Join-Path $scriptDir "compile-paths.ps1"
if (-not (Test-Path $pathsFile)) {
    Write-Error "Could not find 'compile-paths.ps1'. Copy 'compile-paths.example.ps1' to 'compile-paths.ps1' and update your machine paths."
    exit 1
}

. $pathsFile

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
