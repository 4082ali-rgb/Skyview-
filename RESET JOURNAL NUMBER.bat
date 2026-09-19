@echo off
cd /d "%~dp0"
echo This clears the stored journal number. The next RUN will ask you for a new one
echo instead of counting up automatically.
set /p ok=Type YES to confirm:
if /I "%ok%"=="YES" (
  del /f /q skyview_je_state.json 2>nul
  echo Cleared. Next RUN will ask for the journal number.
) else (
  echo Cancelled - nothing changed.
)
echo.
pause
