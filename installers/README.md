# AITS Print Server - Installers

This directory contains installation and uninstallation scripts for the AITS Print Server on different operating systems.

## Available Installers

### Linux
- **install-linux.sh** - Installer for Linux (Ubuntu, Debian, Fedora, RHEL, CentOS, Arch)
- **uninstall-linux.sh** - Uninstaller for Linux

**Usage:**
```bash
sudo ./install-linux.sh
sudo ./uninstall-linux.sh
```

### macOS
- **install-macos.sh** - Installer for macOS 10.14+
- **uninstall-macos.sh** - Uninstaller for macOS

**Usage:**
```bash
./install-macos.sh
./uninstall-macos.sh
```

### Windows
- **install-windows.bat** - Installer for Windows 10+/Server 2016+
- **uninstall-windows.bat** - Uninstaller for Windows

**Usage:**
- Right-click the file
- Select "Run as Administrator"

## What the Installers Do

### Linux
1. Installs Python 3 and CUPS (if not present)
2. Creates system user `aits-print`
3. Installs server to `/opt/aits-print-server`
4. Creates Python virtual environment
5. Installs all dependencies
6. Creates systemd service
7. Configures auto-start on boot

### macOS
1. Checks/installs Homebrew
2. Installs Python 3 (if needed)
3. Installs server to `/usr/local/aits-print-server`
4. Creates Python virtual environment
5. Installs all dependencies
6. Creates LaunchAgent for auto-start
7. Starts the service

### Windows
1. Checks for Python 3 installation
2. Creates installation directory in Program Files
3. Creates Python virtual environment
4. Installs all dependencies including pywin32
5. Creates Windows service
6. Provides batch files for service management

## Post-Installation

After installation, the print server will be:
- **Running on:** `http://localhost:8888`
- **Auto-starting:** On system boot (if enabled)
- **Logging to:** 
  - Linux: `journalctl -u aits-print-server -f`
  - macOS: `/usr/local/aits-print-server/server.log`
  - Windows: Windows Event Viewer

## Configuration

Edit the configuration file after installation:
- **Linux:** `/opt/aits-print-server/config.yaml`
- **macOS:** `/usr/local/aits-print-server/config.yaml`
- **Windows:** `C:\Program Files\AITS Print Server\config.yaml`

See `../INSTALLATION.md` for detailed configuration options.

## Troubleshooting

If installation fails:

1. **Check Python version:**
   ```
   python3 --version  # Linux/macOS
   python --version   # Windows
   ```
   Must be 3.8 or higher

2. **Check permissions:**
   - Linux/macOS: Must run with `sudo`
   - Windows: Must "Run as Administrator"

3. **Check network:**
   - Port 8888 must be available
   - Check with: `lsof -i :8888` (Linux/macOS) or `netstat -ano | findstr :8888` (Windows)

4. **Check logs:**
   - Installation logs are shown in the terminal
   - Service logs available after installation (see Post-Installation section)

## Support

For detailed installation instructions and troubleshooting, see:
- `../INSTALLATION.md` - Complete installation guide
- `../README.md` - Server documentation

## Requirements

Before running installers, ensure you have:

### Linux
- Root/sudo access
- Internet connection (for package downloads)
- 50MB free disk space

### macOS
- Administrator account
- Internet connection
- 50MB free disk space
- Xcode Command Line Tools (will be installed if needed)

### Windows
- Administrator privileges
- Python 3.8+ installed with "Add to PATH" option
- Internet connection
- 50MB free disk space

## Version

Installer Version: 1.0.0
Compatible with: AITS Print Server 1.0.0
