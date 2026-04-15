@echo off
title Timer Power Control System
color 0A

echo ========================================
echo    TIMER FAST/SLOW POWER SYSTEM
echo ========================================
echo.

echo [1] Starting WebSocket Server...
start "WebSocket Server" cmd /k "cd /d C:\Users\HP\epic-1-backend\WebSocket && .venv\Scripts\activate && echo ✅ Server Starting... && python websocket_server.py"

timeout /t 3 /nobreak > nul

echo [2] Starting CO Timer UI...
start "CO Timer UI" cmd /k "cd /d C:\Users\HP\epic-1-backend\WebSocket\CO && ..\.venv\Scripts\activate && echo ✅ CO UI Starting... && python timer_ui.py"

echo.
echo ========================================
echo    BOTH SERVICES STARTED!
echo    Close windows to stop
echo ========================================
echo.
pause
