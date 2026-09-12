@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 goto :error
".venv\Scripts\python.exe" main.py
goto :eof
:error
echo.
echo Klarte ikke aa starte NM-verktoyet. Kontroller at Python 3 er installert.
pause

