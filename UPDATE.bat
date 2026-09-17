@echo off
cd /d "%~dp0"
echo Getting the latest version of the JE builder...
curl -sSL -o skyview_je.py.new "https://raw.githubusercontent.com/4082ali-rgb/Skyview-/claude/modest-hamilton-ce205v/skyview_je.py" && move /y skyview_je.py.new skyview_je.py >nul && echo Updated. || echo Update failed. Check your internet connection.
echo.
pause
