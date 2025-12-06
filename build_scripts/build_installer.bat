@echo off
REM Build NSIS installer for AITS Print Server
REM Requires NSIS to be installed: https://nsis.sourceforge.io/

echo =========================================
echo AITS Print Server - Installer Builder
echo =========================================
echo.

REM Check if executable exists
if not exist "dist\AITS_Print_Server.exe" (
    echo Error: Executable not found!
    echo Please run build_windows.bat first.
    pause
    exit /b 1
)

REM Check for NSIS
where makensis >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: NSIS not found in PATH
    echo.
    echo Please install NSIS from: https://nsis.sourceforge.io/
    echo And add it to your PATH, or run:
    echo   "C:\Program Files (x86)\NSIS\makensis.exe" windows_installer.nsi
    echo.
    pause
    exit /b 1
)

echo Building installer...
cd /d "%~dp0"
makensis windows_installer.nsi

if %errorLevel% equ 0 (
    echo.
    echo =========================================
    echo Installer created successfully!
    echo =========================================
    echo.
    echo Installer: AITS_Print_Server_Setup.exe
    echo.
) else (
    echo.
    echo Installer build failed!
    echo.
)

pause
