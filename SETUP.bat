@echo off
cd /d "%~dp0"
echo Installing what the JE builder needs (one time only)...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Python was not found. Install it from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" in the installer, then run SETUP again.
)
echo.
pause
