@echo off
REM Simple test script to verify build environment
REM Run this before build_complete_windows.bat to check if everything is ready

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                    Build Environment Check                               ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

REM Change to project root
cd /d "%~dp0"
cd ..

echo Checking build environment...
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ FAIL: Python not found
    echo    Install from: https://www.python.org/
    set HAS_ERRORS=1
) else (
    python --version
    echo ✓ PASS
)
echo.

REM Check pip
echo [2/5] Checking pip...
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ FAIL: pip not found
    set HAS_ERRORS=1
) else (
    pip --version
    echo ✓ PASS
)
echo.

REM Check PyInstaller
echo [3/5] Checking PyInstaller...
pyinstaller --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠ WARNING: PyInstaller not installed
    echo    Will be installed during build
) else (
    pyinstaller --version
    echo ✓ PASS
)
echo.

REM Check NSIS
echo [4/5] Checking NSIS...
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
    echo ✓ PASS: NSIS found
    echo    Location: %NSIS_EXE%
) else (
    echo ⚠ WARNING: NSIS not found
    echo    Standalone .exe will work, but no installer will be created
    echo    Download from: https://nsis.sourceforge.io/
)
echo.

REM Check required files
echo [5/5] Checking project files...
set FILES_OK=1

if not exist "tray_app.py" (
    echo ❌ FAIL: tray_app.py not found
    set FILES_OK=0
    set HAS_ERRORS=1
)

if not exist "server_simple.py" (
    echo ❌ FAIL: server_simple.py not found
    set FILES_OK=0
    set HAS_ERRORS=1
)

if not exist "build_scripts\build_windows.spec" (
    echo ❌ FAIL: build_windows.spec not found
    set FILES_OK=0
    set HAS_ERRORS=1
)

if not exist "build_scripts\windows_installer.nsi" (
    echo ❌ FAIL: windows_installer.nsi not found
    set FILES_OK=0
    set HAS_ERRORS=1
)

if not exist "static\icon.ico" (
    echo ⚠ WARNING: static\icon.ico not found
    echo    Icon will use default
)

if %FILES_OK% equ 1 (
    echo ✓ PASS: All required files found
)
echo.

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

if defined HAS_ERRORS (
    echo ╔══════════════════════════════════════════════════════════════════════════╗
    echo ║                         ❌ ERRORS FOUND                                  ║
    echo ╚══════════════════════════════════════════════════════════════════════════╝
    echo.
    echo Please fix the errors above before running the build script.
    echo.
) else (
    echo ╔══════════════════════════════════════════════════════════════════════════╗
    echo ║                    ✅ ENVIRONMENT READY                                  ║
    echo ╚══════════════════════════════════════════════════════════════════════════╝
    echo.
    echo You can now run: build_complete_windows.bat
    echo.
)

pause
