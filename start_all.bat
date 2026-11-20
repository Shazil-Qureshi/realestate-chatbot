@echo off
rem start_all.bat - starts everything the project needs on this laptop.
rem Double-click it, or run it from PowerShell with:  .\start_all.bat
rem Each service opens in its own window. Close a window to stop that service.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [FAIL] .venv not found. See docs\04_environment_setup.md
    pause
    exit /b 1
)

start "Bella - backend (port 8000)" cmd /k ".venv\Scripts\python.exe backend\main.py"
start "Bella - website (port 5500)" cmd /k ".venv\Scripts\python.exe -m http.server 5500 --directory web"
start "Bella - n8n (port 5678)" cmd /k "npx n8n@2.48.4"

echo.
echo Started three windows: backend, website and n8n.
echo   Website: http://localhost:5500
echo   Backend: http://127.0.0.1:8000/health
echo   n8n:     http://localhost:5678   (takes about a minute)
echo.
echo n8n is pinned to version 2.48.4 so it does not update itself on restart.
pause
