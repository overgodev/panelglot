@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  Manga Image Translator - Web Server
echo ============================================================
echo.
echo  Make sure LM Studio is running with a Sugoi model loaded
echo  before translating (Server tab, "Status: Running").
echo.
echo  Web UI will be available at:
echo    http://localhost:8000
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set "LANIP=%%a"
    setlocal enabledelayedexpansion
    echo    http://!LANIP: =!:8000
    endlocal
)
echo.
echo  Close this window to stop the server.
echo ============================================================
echo.

cd server
"%~dp0venv\Scripts\python.exe" main.py --start-instance --host 0.0.0.0 --use-gpu

pause
