# AITS Print Server - Complete Guide

## 🎉 New Features

### ✨ Web-Based Configuration Interface
Access a beautiful web interface to configure your print server at `http://localhost:8888/config`

**Features:**
- Real-time server status monitoring
- Configure server settings (host, port, debug mode)
- Set default printer
- View all available printers
- Adjust logging levels
- Test server connection
- Modern, responsive design

### 🖥️ System Tray Application
Run the print server with a convenient system tray icon on Windows and macOS!

**Features:**
- Runs in background
- System tray icon for quick access
- Right-click menu:
  - View server status
  - Open web configuration
  - Restart server
  - Quit application
- No console window (clean experience)
- Auto-starts server when launched

### 📦 Standalone Installers

**Windows (.exe)**
- Single executable file
- No installation required
- Portable - run from anywhere
- Includes system tray icon
- Built with PyInstaller

**macOS (.app + .dmg)**
- Native macOS application
- Drag-and-drop installation
- Menu bar icon
- DMG installer for easy distribution
- Built with PyInstaller

## 🚀 Quick Start

### Option 1: Run with System Tray (Recommended)

**Requirements:**
```bash
pip install pystray pillow
```

**Start:**
```bash
python3 tray_app.py
```

The server will start automatically and a system tray icon will appear!

### Option 2: Run Standalone Server

**Start:**
```bash
python3 server_simple.py
```

Then open `http://localhost:8888/config` in your browser.

### Option 3: Use Standalone Executable (Windows/macOS)

1. Build the executable (see BUILD_GUIDE.md)
2. Double-click the .exe (Windows) or .app (macOS)
3. System tray icon appears automatically!

## 📖 Documentation

### Main Documentation Files

1. **INSTALLATION.md** - Installation guide for all platforms
2. **BUILD_GUIDE.md** - How to build standalone executables
3. **README.md** - This file
4. **config.yaml.example** - Configuration template

### Web Interface Guide

Access the web configuration at: `http://localhost:8888/config`

#### Server Settings Tab
- **Host**: IP address to listen on
  - `0.0.0.0` = All interfaces (remote access)
  - `127.0.0.1` = Localhost only (local access)
- **Port**: Server port (default: 8888)
- **Debug Mode**: Enable for troubleshooting

#### Printers Tab
- View all available printers
- See printer status
- Identify default printer
- Refresh printer list

#### About Tab
- Server version information
- API endpoint documentation
- Platform information

### System Tray Menu

**Windows (System Tray):**
- Right-click the icon in system tray (bottom-right)

**macOS (Menu Bar):**
- Click the icon in menu bar (top-right)

**Menu Options:**
- **Status** - Shows if server is running
- **Open Configuration** - Opens web interface
- **Restart Server** - Restart the print server
- **Quit** - Stop and exit

## 🔧 Configuration

### Configuration File

Location: `config.yaml`

```yaml
server:
  host: 0.0.0.0      # Listen address
  port: 8888         # Server port
  debug: false       # Debug mode

printing:
  default_printer: null         # Default printer name
  temp_dir: /tmp                # Temp directory
  auto_cleanup: true            # Auto-delete temp files
  max_file_size: 50             # Max PDF size (MB)

logging:
  level: INFO                   # Log level
  file: server.log              # Log file
  max_size: 10                  # Max log size (MB)
  backup_count: 5               # Log rotation count
```

### Environment Variables

You can override config with environment variables:

```bash
export AITS_SERVER_HOST=0.0.0.0
export AITS_SERVER_PORT=8888
export AITS_DEFAULT_PRINTER="HP LaserJet"
```

## 🏗️ Building Executables

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for complete instructions.

### Quick Build Commands

**Windows:**
```cmd
cd build_scripts
build_windows.bat
```

**macOS:**
```bash
cd build_scripts
./build_macos.sh
```

## 📡 API Endpoints

### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "platform": "linux"
}
```

### List Printers
```
GET /printers
```

**Response:**
```json
{
  "success": true,
  "printers": [
    {
      "name": "HP LaserJet",
      "status": "Available",
      "default": true
    }
  ]
}
```

### Submit Print Job
```
POST /print
Content-Type: application/json

{
  "printer": "HP LaserJet",
  "document": "base64_encoded_pdf_data",
  "copies": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Print job submitted successfully"
}
```

### Get Configuration
```
GET /api/config
```

### Update Configuration
```
POST /api/config
Content-Type: application/json

{
  "server": {...},
  "printing": {...},
  "logging": {...}
}
```

## 🎨 Customization

### Change Icon

1. Replace `static/icon.ico` (Windows)
2. Replace `static/icon.icns` (macOS)
3. Or run `python3 generate_icons.py` to create new ones

### Change Branding

Edit `static/config.html`:
- Update title and headers
- Change color scheme (CSS variables)
- Add your logo

### Change Port

Edit `config.yaml`:
```yaml
server:
  port: 9999  # Your custom port
```

## 🐛 Troubleshooting

### Web Interface Not Loading

1. Check if server is running:
   ```bash
   curl http://localhost:8888/health
   ```

2. Check firewall settings
3. Verify port 8888 is not in use:
   ```bash
   lsof -i :8888  # Linux/macOS
   netstat -ano | findstr :8888  # Windows
   ```

### System Tray Icon Not Appearing

**Windows:**
- Check if icon is hidden in "Show hidden icons"
- Look in bottom-right corner of taskbar

**macOS:**
- Check if app has accessibility permissions
- Look in top-right menu bar

### Printer Not Found

**Windows:**
- Open "Devices and Printers"
- Ensure printer is installed
- Check printer name matches exactly

**Linux/macOS:**
- Run `lpstat -p -d` to list printers
- Ensure CUPS is running

### Build Errors

See [BUILD_GUIDE.md](BUILD_GUIDE.md) troubleshooting section.

## 📊 File Structure

```
aits_print_server/
├── server_simple.py          # Main server (simplified)
├── tray_app.py               # System tray application
├── config.yaml               # Configuration file
├── config.yaml.example       # Configuration template
├── requirements.txt          # Python dependencies
├── generate_icons.py         # Icon generator script
├── INSTALLATION.md           # Installation guide
├── BUILD_GUIDE.md           # Build guide
├── README.md                 # This file
├── static/
│   ├── config.html          # Web configuration interface
│   ├── icon.ico             # Windows icon
│   ├── icon.icns            # macOS icon
│   └── icon.png             # PNG icon
├── build_scripts/
│   ├── build_windows.spec   # PyInstaller spec (Windows)
│   ├── build_windows.bat    # Build script (Windows)
│   ├── build_macos.spec     # PyInstaller spec (macOS)
│   └── build_macos.sh       # Build script (macOS)
└── installers/
    ├── install-linux.sh     # Linux installer
    ├── install-macos.sh     # macOS installer
    ├── install-windows.bat  # Windows installer
    └── README.md            # Installer documentation
```

## 🔐 Security Notes

- Web interface has no authentication by default
- Only allow localhost access in production:
  ```yaml
  server:
    host: 127.0.0.1  # Localhost only
  ```
- For remote access, use a reverse proxy with authentication
- Consider using HTTPS for remote access

## 📝 License

Proprietary - AITS Direct Print Module

## 🤝 Support

For issues and questions:
1. Check documentation files
2. Review troubleshooting sections
3. Check server logs (`server.log`)
4. Contact your system administrator

## 🎯 Version

**Current Version:** 1.0.0  
**Release Date:** November 5, 2025  
**Python Required:** 3.8+  
**Supported Platforms:** Windows 10+, macOS 10.14+, Linux

## ✨ What's New

### Version 1.0.0
- ✅ Web-based configuration interface
- ✅ System tray application for Windows and macOS
- ✅ Standalone executable builds (.exe and .app)
- ✅ DMG installer for macOS
- ✅ Icon generation script
- ✅ Simplified server implementation
- ✅ Real-time printer discovery
- ✅ Configuration management via web UI
- ✅ Comprehensive build and deployment guides

---

**Enjoy your new print server with system tray! 🎉**
