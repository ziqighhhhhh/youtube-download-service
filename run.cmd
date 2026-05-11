@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo Stop old service on port 9000
echo ============================================
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo Killed PID %%a
)

echo.
echo ============================================
echo Starting server...
echo ============================================
echo URL: http://127.0.0.1:9000
echo Press Ctrl+C to stop
echo ============================================
echo.

start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:9000"

python -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Server failed to start
    pause
    exit /b 1
)

pause