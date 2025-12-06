@echo off
REM AITS Print Server - Windows Installer
REM Version: 1.0.0

echo =========================================
echo AITS Print Server - Windows Installer
echo =========================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Please run as Administrator
    pause
    exit /b 1
)

set INSTALL_DIR=C:\Program Files\AITS Print Server
set SERVICE_NAME=AITSPrintServer

echo Installing AITS Print Server...
echo.

REM Check for Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Python 3.8+ is required but not found
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found
echo.

REM Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy files
echo Copying files...
xcopy /E /I /Y ..\server.py "%INSTALL_DIR%\"
xcopy /E /I /Y ..\requirements.txt "%INSTALL_DIR%\"
xcopy /E /I /Y ..\config.yaml.example "%INSTALL_DIR%\"
if exist ..\templates xcopy /E /I /Y ..\templates "%INSTALL_DIR%\templates\"

REM Create config if not exists
if not exist "%INSTALL_DIR%\config.yaml" (
    copy "%INSTALL_DIR%\config.yaml.example" "%INSTALL_DIR%\config.yaml"
)

REM Create virtual environment
echo Creating virtual environment...
cd /d "%INSTALL_DIR%"
python -m venv venv

REM Install dependencies
echo Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
call venv\Scripts\deactivate.bat

echo.
echo Installing Windows service...

REM Create service wrapper Python script
echo import sys > "%INSTALL_DIR%\service.py"
echo import servicemanager >> "%INSTALL_DIR%\service.py"
echo import win32serviceutil >> "%INSTALL_DIR%\service.py"
echo import win32service >> "%INSTALL_DIR%\service.py"
echo import win32event >> "%INSTALL_DIR%\service.py"
echo import socket >> "%INSTALL_DIR%\service.py"
echo import subprocess >> "%INSTALL_DIR%\service.py"
echo import os >> "%INSTALL_DIR%\service.py"
echo. >> "%INSTALL_DIR%\service.py"
echo class AITSPrintServer(win32serviceutil.ServiceFramework): >> "%INSTALL_DIR%\service.py"
echo     _svc_name_ = '%SERVICE_NAME%' >> "%INSTALL_DIR%\service.py"
echo     _svc_display_name_ = 'AITS Print Server' >> "%INSTALL_DIR%\service.py"
echo     _svc_description_ = 'AITS Direct Print Server for Odoo' >> "%INSTALL_DIR%\service.py"
echo. >> "%INSTALL_DIR%\service.py"
echo     def __init__(self, args): >> "%INSTALL_DIR%\service.py"
echo         win32serviceutil.ServiceFramework.__init__(self, args) >> "%INSTALL_DIR%\service.py"
echo         self.hWaitStop = win32event.CreateEvent(None, 0, 0, None) >> "%INSTALL_DIR%\service.py"
echo         socket.setdefaulttimeout(60) >> "%INSTALL_DIR%\service.py"
echo         self.process = None >> "%INSTALL_DIR%\service.py"
echo. >> "%INSTALL_DIR%\service.py"
echo     def SvcStop(self): >> "%INSTALL_DIR%\service.py"
echo         self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING) >> "%INSTALL_DIR%\service.py"
echo         win32event.SetEvent(self.hWaitStop) >> "%INSTALL_DIR%\service.py"
echo         if self.process: >> "%INSTALL_DIR%\service.py"
echo             self.process.terminate() >> "%INSTALL_DIR%\service.py"
echo. >> "%INSTALL_DIR%\service.py"
echo     def SvcDoRun(self): >> "%INSTALL_DIR%\service.py"
echo         servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, >> "%INSTALL_DIR%\service.py"
echo                               servicemanager.PYS_SERVICE_STARTED, >> "%INSTALL_DIR%\service.py"
echo                               (self._svc_name_, '')) >> "%INSTALL_DIR%\service.py"
echo         self.main() >> "%INSTALL_DIR%\service.py"
echo. >> "%INSTALL_DIR%\service.py"
echo     def main(self): >> "%INSTALL_DIR%\service.py"
echo         python_exe = r'%INSTALL_DIR%\venv\Scripts\python.exe' >> "%INSTALL_DIR%\service.py"
echo         server_py = r'%INSTALL_DIR%\server.py' >> "%INSTALL_DIR%\service.py"
echo         os.chdir(r'%INSTALL_DIR%') >> "%INSTALL_DIR%\service.py"
echo         self.process = subprocess.Popen([python_exe, server_py]) >> "%INSTALL_DIR%\service.py"
echo         self.process.wait() >> "%INSTALL_DIR%\service.py"
echo. >> "%INSTALL_DIR%\service.py"
echo if __name__ == '__main__': >> "%INSTALL_DIR%\service.py"
echo     win32serviceutil.HandleCommandLine(AITSPrintServer) >> "%INSTALL_DIR%\service.py"

REM Install pywin32 for service support
call venv\Scripts\activate.bat
pip install pywin32
call venv\Scripts\deactivate.bat

REM Install the service
"%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\service.py" install

REM Create a batch file to start/stop service
echo @echo off > "%INSTALL_DIR%\start-service.bat"
echo net start %SERVICE_NAME% >> "%INSTALL_DIR%\start-service.bat"

echo @echo off > "%INSTALL_DIR%\stop-service.bat"
echo net stop %SERVICE_NAME% >> "%INSTALL_DIR%\stop-service.bat"

echo.
echo =========================================
echo Installation completed successfully!
echo =========================================
echo.
echo Installation directory: %INSTALL_DIR%
echo Configuration file: %INSTALL_DIR%\config.yaml
echo.
echo To start the service:
echo   net start %SERVICE_NAME%
echo   OR double-click: %INSTALL_DIR%\start-service.bat
echo.
echo To stop the service:
echo   net stop %SERVICE_NAME%
echo   OR double-click: %INSTALL_DIR%\stop-service.bat
echo.
echo To set service to start automatically:
echo   sc config %SERVICE_NAME% start= auto
echo.
echo Server will be available at: http://localhost:8888
echo.

pause
