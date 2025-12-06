@echo off
REM Build script for Windows executable
REM Creates a standalone .exe file with system tray

echo =========================================
echo AITS Print Server - Windows Build Script
echo =========================================
echo.

REM Check for Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Python not found. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [1/4] Installing build dependencies...
pip install pyinstaller pillow pystray flask flask-cors pyyaml waitress pywin32 requests

echo.
echo [2/4] Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.
echo [3/4] Building executable...
cd /d "%~dp0"
pyinstaller --clean build_windows.spec

if %errorLevel% neq 0 (
    echo.
    echo Build failed! Check the errors above.
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Copying additional files...
copy "..\config.yaml.example" "dist\config.yaml.example" >nul
copy "..\README.md" "dist\README.md" >nul
copy "..\LICENSE.txt" "dist\LICENSE.txt" >nul

echo.
echo =========================================
echo Build completed successfully!
echo =========================================
echo.
echo Executable location: dist\AITS_Print_Server.exe
echo.
echo To create an installer, run: build_installer.bat
echo (Requires NSIS - https://nsis.sourceforge.io/)
echo.
echo Or distribute the dist folder as a portable version.
echo.

pause
