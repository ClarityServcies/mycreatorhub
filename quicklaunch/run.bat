@echo off
setlocal
REM No lingering console: prefer pythonw, start detached, exit this window immediately.
set "PYW="
set "PY="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
if not defined PYW if defined PY (
  for %%I in ("%PY%") do set "PYW=%%~dpIpythonw.exe"
)
if not defined PYW (
  where pythonw >nul 2>&1 && for /f "delims=" %%I in ('where pythonw') do set "PYW=%%I" & goto :have_pyw
)
:have_pyw
if not defined PYW if not defined PY (
  echo Python not found. Install Python 3.10+ and retry.
  pause
  exit /b 1
)
cd /d "%~dp0"
if defined PYW if exist "%PYW%" (
  start "" "%PYW%" "%~dp0main.py" %*
  exit /b 0
)
REM Fallback: hide console via start /min then exit
start "" /min "%PY%" "%~dp0main.py" %*
exit /b 0
