@echo off
echo ========================================================
echo   AgentOps Local Development Launcher (Windows)
echo ========================================================
echo.

set SCRIPT_DIR=%~dp0
set PYTHONPATH=%SCRIPT_DIR%services\api;%SCRIPT_DIR%packages\python-sdk

echo [1/2] Starting Backend API on http://localhost:8000 ...
start "AgentOps Backend API" cmd /k "cd /d %SCRIPT_DIR%services\api && py -m uvicorn agentops_api.main:app --reload --port 8000"

echo [2/2] Starting Frontend Next.js on http://localhost:3000 ...
start "AgentOps Frontend" cmd /k "cd /d %SCRIPT_DIR%apps\web && npm run dev"

echo.
echo ========================================================
echo   Services Launched!
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000/docs
echo ========================================================
pause
