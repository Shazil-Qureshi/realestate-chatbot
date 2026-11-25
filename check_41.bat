@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" check_41.py
echo.
echo Finished. This window stays open so you can read it.
pause
