$ErrorActionPreference = "Stop"

$Data = Join-Path $env:LOCALAPPDATA "BangladeshBhasha"
$Uninstaller = Join-Path $Data "uninstall.py"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Local = Join-Path $Here "uninstall.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = "py"
    $Args = @("-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
    $Args = @()
} else {
    throw "Python পাওয়া যায়নি।"
}

if (Test-Path $Local) {
    $Uninstaller = $Local
}
if (-not (Test-Path $Uninstaller)) {
    throw "Uninstaller পাওয়া যায়নি।"
}

& $Python @Args $Uninstaller
if ($LASTEXITCODE -ne 0) {
    throw "Uninstallation failed."
}
