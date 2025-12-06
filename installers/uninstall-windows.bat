@echo off
REM AITS Print Server - Windows Uninstaller

set INSTALL_DIR=C:\Program Files\AITS Print Server
set SERVICE_NAME=AITSPrintServer

echo AITS Print Server - Uninstaller
echo ===============================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Please run as Administrator
    pause
    exit /b 1
)

REM Stop service
echo Stopping service...
net stop %SERVICE_NAME% 2>nul

REM Uninstall service
echo Uninstalling service...
"%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\service.py" remove 2>nul

REM Remove installation directory
echo Removing installation directory...
rd /s /q "%INSTALL_DIR%"

echo.
echo Uninstallation completed!
echo.
pause
