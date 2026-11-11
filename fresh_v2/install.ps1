$ErrorActionPreference = "Stop"

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command py -ErrorAction SilentlyContinue
if ($Python) {
    $PythonExe = "py"
    $PythonArgs = @("-3")
} else {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $Python) {
        throw "Python 3.10+ ইনস্টল করুন।"
    }
    $PythonExe = "python"
    $PythonArgs = @()
}

$Installer = Join-Path $Here "install.py"
$TempInstaller = $null

if (-not (Test-Path $Installer)) {
    $TempInstaller = Join-Path ([IO.Path]::GetTempPath()) "bhasha-install.py"
    Invoke-WebRequest `
      -Uri "https://raw.githubusercontent.com/utpalmohonto078-ship-it/bangladesh-bhasha/main/install.py" `
      -OutFile $TempInstaller
    $Installer = $TempInstaller
}

try {
    & $PythonExe @PythonArgs $Installer
    if ($LASTEXITCODE -ne 0) {
        throw "BANGLADESH BHASHA installation failed."
    }
} finally {
    if ($TempInstaller -and (Test-Path $TempInstaller)) {
        Remove-Item $TempInstaller -Force
    }
}
