@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM AITS Print Server - Simple Windows Build (Skip Dependency Install)
REM ============================================================================
REM This script skips dependency installation and goes straight to building
REM Use this if dependencies are already installed or if pip is causing issues
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║        AITS Print Server - Simple Build (No Dependency Install)         ║
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
    echo    Current directory: %CD%
    pause
    cd /d "%ORIGINAL_DIR%"
    exit /b 1
)

REM ============================================================================
REM Check Prerequisites
REM ============================================================================

echo Checking prerequisites...
echo.

REM Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ ERROR: Python not found!
    pause
    cd /d "%ORIGINAL_DIR%"
    exit /b 1
)
echo ✓ Python found
python --version

REM Check PyInstaller
pyinstaller --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ❌ ERROR: PyInstaller not found!
    echo.
    echo Please install it first:
    echo    pip install pyinstaller==6.3.0
    echo.
    echo OR run: build_complete_windows.bat
    echo (which installs dependencies automatically)
    pause
    cd /d "%ORIGINAL_DIR%"
    exit /b 1
)
echo ✓ PyInstaller found
pyinstaller --version

REM Check NSIS
echo.
set NSIS_EXE=
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    set NSIS_EXE=C:\Program Files (x86)\NSIS\makensis.exe
) else if exist "C:\Program Files\NSIS\makensis.exe" (
    set NSIS_EXE=C:\Program Files\NSIS\makensis.exe
)

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
    set NSIS_AVAILABLE=0
)

echo.
echo ============================================================================
echo.
echo Press any key to start building...
pause >nul

REM ============================================================================
REM Clean Previous Builds
REM ============================================================================

echo.
echo Cleaning previous builds...
echo.

if exist "dist" (
    echo Removing old dist folder...
    rmdir /s /q "dist" 2>nul
)

if exist "build" (
    echo Removing old build folder...
    rmdir /s /q "build" 2>nul
)

if exist "AITS_Print_Server.spec" (
    del /q "AITS_Print_Server.spec" 2>nul
)

echo ✓ Cleanup complete
echo.

REM ============================================================================
REM Build Standalone Executable
REM ============================================================================

echo.
echo Building standalone executable with PyInstaller...
echo.
echo This may take a few minutes - please wait...
echo.

pyinstaller --clean build_scripts\build_windows.spec
set BUILD_ERROR=%errorLevel%

if %BUILD_ERROR% neq 0 (
    echo.
    echo ❌ ERROR: PyInstaller build failed! (Error code: %BUILD_ERROR%)
    echo.
    echo Check the error messages above.
    echo Common issues:
    echo   - Missing dependencies: pip install -r requirements.txt
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

REM ============================================================================
REM Create Installer (if NSIS available)
REM ============================================================================

if %NSIS_AVAILABLE% equ 1 (
    echo.
    echo Creating professional installer with NSIS...
    echo.
    
    REM Save current directory
    pushd "%~dp0"
    
    REM Run NSIS from the build_scripts directory
    echo Running NSIS...
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
            )
        )
    ) else (
        echo.
        echo ⚠ Warning: NSIS installer creation failed
        echo   You can still use the standalone .exe
    )
    
    REM Return to previous directory
    popd
)

REM ============================================================================
REM Build Complete Summary
REM ============================================================================

echo.
echo ============================================================================
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
)

if exist "dist\AITS_Print_Server_Setup.exe" (
    echo    ✓ Professional Installer:
    echo      dist\AITS_Print_Server_Setup.exe
    echo.
)

echo ============================================================================
echo.
echo 🚀 Next Steps:
echo.
echo    1. Test: dist\AITS_Print_Server.exe
echo    2. Visit: http://localhost:8888/config
echo.

if exist "dist\AITS_Print_Server_Setup.exe" (
    echo    3. Distribute: AITS_Print_Server_Setup.exe or AITS_Print_Server.exe
) else (
    echo    3. Distribute: AITS_Print_Server.exe
)

echo.
echo ============================================================================
echo.

REM Restore original directory
cd /d "%ORIGINAL_DIR%"

pause
endlocal
exit /b 0
