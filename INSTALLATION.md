# AITS Print Server - Installation Guide

## Overview

The AITS Print Server is a lightweight Flask-based server that enables direct printing from Odoo to local or network printers. It acts as a bridge between your Odoo instance and your printing infrastructure.

## Features

- ✅ Direct printing from Odoo to any printer
- ✅ PDF to printer conversion
- ✅ Support for CUPS (Linux/macOS) and Windows printing
- ✅ RESTful API for print job management
- ✅ Printer discovery and health monitoring
- ✅ Configurable via YAML
- ✅ Runs as a system service (auto-start on boot)

## System Requirements

### Linux
- Python 3.8 or higher
- CUPS (Common Unix Printing System)
- 50MB disk space
- Systemd (for service management)

### macOS
- macOS 10.14 (Mojave) or higher
- Python 3.8 or higher
- 50MB disk space
- CUPS is pre-installed on macOS

### Windows
- Windows 10 or higher / Windows Server 2016 or higher
- Python 3.8 or higher
- 50MB disk space
- Windows Print Spooler service

## Installation

### Linux

1. **Download the installer:**
   ```bash
   cd /path/to/aits_print_server/installers
   chmod +x install-linux.sh
   ```

2. **Run the installer:**
   ```bash
   sudo ./install-linux.sh
   ```

3. **Start the service:**
   ```bash
   sudo systemctl start aits-print-server
   ```

4. **Enable auto-start on boot:**
   ```bash
   sudo systemctl enable aits-print-server
   ```

5. **Check status:**
   ```bash
   sudo systemctl status aits-print-server
   ```

### macOS

1. **Download the installer:**
   ```bash
   cd /path/to/aits_print_server/installers
   chmod +x install-macos.sh
   ```

2. **Run the installer:**
   ```bash
   ./install-macos.sh
   ```
   
   The service will start automatically and run on login.

3. **Check if running:**
   ```bash
   launchctl list | grep aits
   ```

### Windows

1. **Download the installer:**
   - Right-click `install-windows.bat`
   - Select "Run as Administrator"

2. **Start the service:**
   ```
   net start AITSPrintServer
   ```
   
   OR double-click `C:\Program Files\AITS Print Server\start-service.bat`

3. **Enable auto-start on boot:**
   ```
   sc config AITSPrintServer start= auto
   ```

## Configuration

After installation, edit the configuration file:

- **Linux:** `/opt/aits-print-server/config.yaml`
- **macOS:** `/usr/local/aits-print-server/config.yaml`
- **Windows:** `C:\Program Files\AITS Print Server\config.yaml`

### Configuration Options

```yaml
server:
  host: 0.0.0.0        # Listen on all interfaces
  port: 8888           # Server port
  debug: false         # Debug mode

printing:
  default_printer: null  # Default printer name (null = system default)
  temp_dir: /tmp         # Directory for temporary files
  
logging:
  level: INFO          # Log level: DEBUG, INFO, WARNING, ERROR
  file: server.log     # Log file path
```

After editing, restart the service:

**Linux:**
```bash
sudo systemctl restart aits-print-server
```

**macOS:**
```bash
launchctl unload ~/Library/LaunchAgents/com.aits.print-server.plist
launchctl load ~/Library/LaunchAgents/com.aits.print-server.plist
```

**Windows:**
```
net stop AITSPrintServer
net start AITSPrintServer
```

## Uninstallation

### Linux
```bash
cd /path/to/aits_print_server/installers
sudo ./uninstall-linux.sh
```

### macOS
```bash
cd /path/to/aits_print_server/installers
./uninstall-macos.sh
```

### Windows
- Right-click `uninstall-windows.bat`
- Select "Run as Administrator"

## Testing the Installation

1. **Check if the server is running:**
   ```bash
   curl http://localhost:8888/health
   ```
   
   Expected response:
   ```json
   {
     "status": "ok",
     "version": "1.0.0"
   }
   ```

2. **List available printers:**
   ```bash
   curl http://localhost:8888/printers
   ```

3. **Test printing (from Odoo):**
   - Go to Odoo → Direct Print → Configuration → Settings
   - Set "Print Server URL" to `http://localhost:8888`
   - Click "Test Connection"

## Troubleshooting

### Service won't start

**Linux:**
```bash
# Check logs
sudo journalctl -u aits-print-server -f

# Check if port 8888 is in use
sudo lsof -i :8888
```

**macOS:**
```bash
# Check logs
tail -f /usr/local/aits-print-server/server.log
tail -f /usr/local/aits-print-server/server.error.log

# Check if port 8888 is in use
lsof -i :8888
```

**Windows:**
```
# Check Windows Event Viewer
eventvwr.msc

# Check if port 8888 is in use
netstat -ano | findstr :8888
```

### Cannot connect from Odoo

1. Check firewall settings - ensure port 8888 is open
2. If Odoo is on a different machine, change `host` in config.yaml to `0.0.0.0`
3. Verify the Print Server URL in Odoo settings

### Printer not found

**Linux/macOS:**
```bash
# List CUPS printers
lpstat -p -d

# Add a printer if needed
lpadmin -p PrinterName -v socket://printer-ip-address -m everywhere
```

**Windows:**
- Open "Devices and Printers" in Control Panel
- Ensure your printer is installed and set as default (if needed)

### Permission denied errors

**Linux:**
```bash
# Add user to lp (printer) group
sudo usermod -a -G lp aits-print
sudo systemctl restart aits-print-server
```

**macOS:**
- The service runs as your user account, so it should have access to your printers

**Windows:**
- Ensure the service is running as an account with printer access
- Or set the service to run as Local System with desktop interaction

## API Documentation

### Health Check
```
GET /health
```

### List Printers
```
GET /printers
```

### Submit Print Job
```
POST /print
Content-Type: application/json

{
  "printer": "printer_name",
  "document": "base64_encoded_pdf",
  "options": {
    "copies": 1,
    "color": true
  }
}
```

## Support

For issues and feature requests, please contact your system administrator or refer to the module documentation.

## Version

Current Version: 1.0.0

## License

Proprietary - AITS Direct Print Module
