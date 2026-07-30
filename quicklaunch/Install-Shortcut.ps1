# Desktop shortcut → pythonw (no cmd window). Falls back to run.bat.
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$main = Join-Path $here 'main.py'
if (-not (Test-Path $main)) { throw "Missing main.py at $main" }

$pyw = @(
    "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\pythonw.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

$desktop = [Environment]::GetFolderPath('Desktop')
$lnkPath = Join-Path $desktop 'BeamNG QuickLaunch.lnk'
$w = New-Object -ComObject WScript.Shell
$lnk = $w.CreateShortcut($lnkPath)

if ($pyw) {
    $lnk.TargetPath = $pyw
    $lnk.Arguments = "`"$main`""
    $lnk.WorkingDirectory = $here
    $lnk.WindowStyle = 7  # minimized — pythonw has no window anyway
} else {
    $bat = Join-Path $here 'run.bat'
    $lnk.TargetPath = $bat
    $lnk.WorkingDirectory = $here
    $lnk.WindowStyle = 7
}

$lnk.Description = 'Skip BeamNG menus — pick map/vehicle and spawn (no console)'
$icon = 'C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\icon-beamng.ico'
if (Test-Path $icon) { $lnk.IconLocation = $icon }
$lnk.Save()

Write-Host "Shortcut created: $lnkPath"
if ($pyw) { Write-Host "Target: pythonw (no console window)" }
else { Write-Host "Target: run.bat (pythonw not found)" }
