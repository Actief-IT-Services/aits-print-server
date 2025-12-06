@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM AITS Print Server - Complete Windows Build & Installer Script
REM ============================================================================
REM This script:
REM 1. Builds the standalone .exe with PyInstaller
REM 2. Creates a professional installer .exe with NSIS
REM
REM Requirements:
REM - Python 3.8+ with pip
REM - NSIS (Nullsoft Scriptable Install System) - Download from: https://nsis.sourceforge.io/
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║           AITS Print Server - Windows Build System v1.0                 ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

REM Save original directory and change to script's parent directory
set ORIGINAL_DIR=%CD%
cd /d "%~dp0"
cd ..
set PROJECT_ROOT=%CD%

echo Project root: %PROJECT_ROOT%
echo.

REM Verify we're in the correct directory
if not exist "tray_app.py" (
    echo ❌ ERROR: Cannot find tray_app.py
    echo    Make sure you're running this script from the build_scripts folder
    echo    Current directory: %CD%
    pause
    exit /b 1
)

if not exist "build_scripts\windows_installer.nsi" (
    echo ❌ ERROR: Cannot find windows_installer.nsi
    echo    Make sure the build_scripts folder contains all necessary files
    pause
    exit /b 1
)

REM ============================================================================
REM Step 1: Check Prerequisites
REM ============================================================================

echo [1/5] Checking prerequisites...
echo.

REM Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ ERROR: Python not found!
    echo    Please install Python 3.8 or later from https://www.python.org/
    echo.
    pause
    exit /b 1
)
echo ✓ Python found
python --version

REM Check pip
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ ERROR: pip not found!
    pause
    exit /b 1
)
echo ✓ pip found

REM Check NSIS (optional but recommended)
REM Try common NSIS installation paths
set NSIS_EXE=
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    set NSIS_EXE=C:\Program Files (x86)\NSIS\makensis.exe
) else if exist "C:\Program Files\NSIS\makensis.exe" (
    set NSIS_EXE=C:\Program Files\NSIS\makensis.exe
)

REM Also check if it's in PATH
where makensis >nul 2>&1
if %errorLevel% equ 0 (
    set NSIS_EXE=makensis
)

if defined NSIS_EXE (
    echo ✓ NSIS found - Full installer will be created
    echo   Location: %NSIS_EXE%
    set NSIS_AVAILABLE=1
) else (
    echo ⚠ NSIS not found - Only standalone .exe will be created
    echo.
    echo   To create a professional installer:
    echo   1. Download NSIS from: https://nsis.sourceforge.io/
    echo   2. Install NSIS (default location is fine)
    echo   3. Either add NSIS to PATH, or run this script again
    echo      (it will auto-detect NSIS in default locations)
    echo.
    set NSIS_AVAILABLE=0
)

echo.
echo ============================================================================
pause

REM ============================================================================
REM Step 2: Install Dependencies
REM ============================================================================

echo.
echo [2/5] Installing Python dependencies...
echo.
echo This may take a few minutes - please wait...
echo.

echo Upgrading pip...
pip install --upgrade pip 2>&1
if %errorLevel% neq 0 (
    echo ⚠ Warning: pip upgrade failed, continuing anyway...
)

echo.
echo Installing PyInstaller...
pip install pyinstaller==6.3.0 2>&1
if %errorLevel% neq 0 (
    echo ❌ ERROR: Failed to install PyInstaller
    echo.
    echo Try running: pip install --user pyinstaller==6.3.0
    pause
    cd /d "%ORIGINAL_DIR%"
    exit /b 1
)

echo Installing Pillow...
pip install pillow==10.1.0 2>&1

echo Installing pystray...
pip install pystray==0.19.5 2>&1

echo Installing Flask...
pip install flask==3.0.0 2>&1

echo Installing flask-cors...
pip install flask-cors==4.0.0 2>&1

echo Installing PyYAML...
pip install pyyaml==6.0.1 2>&1

echo Installing waitress...
pip install waitress==2.1.2 2>&1

echo Installing pywin32...
pip install pywin32==306 2>&1
if %errorLevel% neq 0 (
    echo ⚠ Warning: pywin32 installation may have issues
    echo    This is normal on some systems, continuing...
)

echo Installing ReportLab...
pip install reportlab==4.0.7 2>&1

echo Installing requests...
pip install requests==2.31.0 2>&1

echo.
echo Verifying PyInstaller installation...
pyinstaller --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ❌ ERROR: PyInstaller installation verification failed!
    echo.
    echo PyInstaller was installed but cannot be run.
    echo Possible causes:
    echo   1. Scripts folder not in PATH
    echo   2. Antivirus blocking PyInstaller
    echo   3. Python installation corrupted
    echo.
    echo Try:
    echo   - Close and reopen Command Prompt
    echo   - Add Python Scripts folder to PATH
    echo   - Run as Administrator
    echo.
    pause
    cd /d "%ORIGINAL_DIR%"
    exit /b 1
)

echo.
echo ✓ All dependencies installed and verified successfully
echo.
echo ============================================================================
echo.
echo Press any key to continue with the build...
pause >nul

REM ============================================================================
REM Step 3: Clean Previous Builds
REM ============================================================================

echo.
echo [3/5] Cleaning previous builds...
echo.

if exist "dist" (
    echo Removing old dist folder...
    rmdir /s /q "dist"
)

if exist "build" (
    echo Removing old build folder...
    rmdir /s /q "build"
)

if exist "AITS_Print_Server.spec" (
    echo Removing old spec file...
    del /q "AITS_Print_Server.spec"
)

echo ✓ Cleanup complete
echo.
echo ============================================================================
pause

REM ============================================================================
REM Step 4: Build Standalone Executable
REM ============================================================================

echo.
echo [4/5] Building standalone executable with PyInstaller...
echo.
echo This may take a few minutes...
echo.

pyinstaller --clean build_scripts\build_windows.spec
set BUILD_ERROR=%errorLevel%

if %BUILD_ERROR% neq 0 (
    echo.
    echo ❌ ERROR: PyInstaller build failed! (Error code: %BUILD_ERROR%)
    echo.
    echo Possible causes:
    echo   - Missing dependencies (run: pip install -r requirements.txt)
    echo   - Antivirus blocking PyInstaller
    echo   - Insufficient disk space
    echo.
    pause
    cd /d "%ORIGINAL_DIR%"
    exit /b 1
)

echo.
echo ✓ Standalone executable created successfully!
echo   Location: dist\AITS_Print_Server.exe
echo.

REM Check file size
for %%I in ("dist\AITS_Print_Server.exe") do set SIZE=%%~zI
set /a SIZE_MB=%SIZE%/1048576
echo   File size: %SIZE_MB% MB
echo.
echo ============================================================================
pause

REM ============================================================================
REM Step 5: Create Installer (if NSIS available)
REM ============================================================================

if %NSIS_AVAILABLE% equ 1 (
    echo.
    echo [5/5] Creating professional installer with NSIS...
    echo.
    
    REM Save current directory
    pushd "%~dp0"
    
    REM Run NSIS from the build_scripts directory
    echo Running: "%NSIS_EXE%" windows_installer.nsi
    echo.
    "%NSIS_EXE%" windows_installer.nsi
    set NSIS_ERROR=%errorLevel%
    
    if %NSIS_ERROR% equ 0 (
        echo.
        echo ✓ Installer created successfully!
        echo.
        
        REM Move installer to root dist folder
        if exist "AITS_Print_Server_Setup.exe" (
            if not exist "..\dist\" mkdir "..\dist"
            move /y "AITS_Print_Server_Setup.exe" "..\dist\" >nul
            if exist "..\dist\AITS_Print_Server_Setup.exe" (
                echo   ✓ Installer location: dist\AITS_Print_Server_Setup.exe
            ) else (
                echo   ⚠ Warning: Failed to move installer, check build_scripts folder
            )
        ) else (
            echo   ⚠ Warning: Installer file not found after build
        )
    ) else (
        echo.
        echo ⚠ Warning: NSIS installer creation failed (Error code: %NSIS_ERROR%)
        echo   Check the output above for errors
        echo   You can still use the standalone .exe in dist folder
        echo.
    )
    
    REM Return to previous directory
    popd
) else (
    echo.
    echo [5/5] Skipping installer creation (NSIS not available)
    echo.
    echo To create a professional installer:
    echo 1. Download NSIS from https://nsis.sourceforge.io/
    echo 2. Install NSIS
    echo 3. Add NSIS to your PATH
    echo 4. Run this script again
)

echo.
echo ============================================================================

REM ============================================================================
REM Build Complete Summary
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                         BUILD COMPLETED! ✅                              ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo 📦 Output Files:
echo.

if exist "dist\AITS_Print_Server.exe" (
    echo    ✓ Standalone Executable:
    echo      dist\AITS_Print_Server.exe
    echo.
    echo      Usage: Double-click to run with system tray
    echo             No installation required
    echo             Can be distributed as-is
    echo.
)

if exist "dist\AITS_Print_Server_Setup.exe" (
    echo    ✓ Professional Installer:
    echo      dist\AITS_Print_Server_Setup.exe
    echo.
    echo      Usage: Run to install with:
    echo             - Start Menu shortcuts
    echo             - Desktop shortcut
    echo             - Uninstaller
    echo             - Windows integration
    echo.
) else (
    echo    ⚠ No installer created (NSIS not available)
    echo.
)

echo ============================================================================
echo.
echo 🚀 Next Steps:
echo.
echo    1. Test the executable:
echo       dist\AITS_Print_Server.exe
echo.
echo    2. Test the web interface:
echo       http://localhost:8888/config
echo.

if exist "dist\AITS_Print_Server_Setup.exe" (
    echo    3. Distribute either file:
    echo       - AITS_Print_Server_Setup.exe (recommended for end users)
    echo       - AITS_Print_Server.exe (portable version)
) else (
    echo    3. Distribute the file:
    echo       - AITS_Print_Server.exe
)

echo.
echo ============================================================================
echo.

REM Restore original directory
cd /d "%ORIGINAL_DIR%"

pause
endlocal
exit /b 0
