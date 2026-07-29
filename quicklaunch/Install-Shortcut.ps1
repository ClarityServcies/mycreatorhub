# Creates a Desktop shortcut to BeamNG QuickLaunch (run.bat).
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $here 'run.bat'
if (-not (Test-Path $bat)) { throw "Missing run.bat at $bat" }

$desktop = [Environment]::GetFolderPath('Desktop')
$lnkPath = Join-Path $desktop 'BeamNG QuickLaunch.lnk'

$w = New-Object -ComObject WScript.Shell
$lnk = $w.CreateShortcut($lnkPath)
$lnk.TargetPath = $bat
$lnk.WorkingDirectory = $here
$lnk.WindowStyle = 1
$lnk.Description = 'Skip BeamNG menus — pick map/vehicle and spawn'
$icon = 'C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\icon-beamng.ico'
if (Test-Path $icon) { $lnk.IconLocation = $icon }
$lnk.Save()

Write-Host "Shortcut created: $lnkPath"
Write-Host "Double-click it (or run.bat) to open QuickLaunch."
