@echo off
setlocal
set GAME=c:\program files (x86)\steam\steamapps\common\BeamNG.drive\Bin64\BeamNG.drive.x64.exe
set ARGS=-gfx d3d11
if not "%LEVEL%"=="" set ARGS=%ARGS% -level %LEVEL%

echo === Killing existing BeamNG processes ===
taskkill /F /IM BeamNG.drive.exe 2>nul
taskkill /F /IM BeamNG.drive.x64.exe 2>nul
timeout /t 3 /nobreak >nul

echo === Instance 1 (affinity FF, userpath C:\BNG1) ===
if not exist "C:\BNG1" mkdir "C:\BNG1"
start "BNG1" /affinity FF %GAME% %ARGS% -userpath "C:\BNG1"
timeout /t 10 /nobreak >nul
echo === Instance 2 (affinity FF00, userpath C:\BNG2) ===
if not exist "C:\BNG2" mkdir "C:\BNG2"
start "BNG2" /affinity FF00 %GAME% %ARGS% -userpath "C:\BNG2"
timeout /t 10 /nobreak >nul
echo === Instance 3 (affinity FF0000, userpath C:\BNG3) ===
if not exist "C:\BNG3" mkdir "C:\BNG3"
start "BNG3" /affinity FF0000 %GAME% %ARGS% -userpath "C:\BNG3"

timeout /t 10 /nobreak >nul
echo === OBS ===
start "OBS" /affinity F000000 "C:\Program Files\obs-studio\bin\64bit\obs64.exe"
echo === Rig up ===
pause
