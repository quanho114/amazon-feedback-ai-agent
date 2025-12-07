@echo off
REM One-click start: Backend + Frontend

echo ========================================
echo  Amazon Feedback AI Agent
echo  Starting Backend + Frontend...
echo ========================================
echo.

REM Start Backend in new window
start "Backend (Port 8000)" cmd /k "cd /d %~dp0 && python api.py"

REM Wait 3 seconds for backend to start
timeout /t 3 /nobreak >nul

REM Start Frontend in new window
start "Frontend (Port 3000)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo  Servers Starting...
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to open browser...
pause >nul

REM Open browser
start http://localhost:3000

exit
