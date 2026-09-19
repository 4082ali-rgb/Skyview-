@echo off
cd /d "%~dp0"
set BASE=https://raw.githubusercontent.com/4082ali-rgb/Skyview-/claude/modest-hamilton-ce205v
echo Getting the latest version of the JE builder and its buttons...
for %%F in ("skyview_je.py" "RUN.bat" "SETUP.bat" "ADD ACCOUNT.bat" "SET JOURNAL NUMBER.bat" "RESET JOURNAL NUMBER.bat" "README.md") do (
  set "N=%%~F"
  setlocal enabledelayedexpansion
  curl -sSL -o "!N!.new" "%BASE%/!N: =%%20!" && move /y "!N!.new" "!N!" >nul && echo   updated !N! || echo   FAILED !N!
  endlocal
)
curl -sSL -o UPDATE.bat.new "%BASE%/UPDATE.bat" >nul 2>&1
if not exist inbox mkdir inbox
if not exist output mkdir output
echo Done. Your PDFs, journal number and saved accounts are untouched.
echo.
pause
if exist UPDATE.bat.new move /y UPDATE.bat.new UPDATE.bat >nul
