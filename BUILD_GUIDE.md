# Building Standalone Installers

This guide explains how to build standalone executables with system tray support for Windows and macOS.

## Overview

The build process creates:
- **Windows**: `AITS_Print_Server.exe` - Single executable file with system tray icon
- **macOS**: `AITS Print Server.app` - Application bundle with system tray icon
- **macOS** (optional): `.dmg` installer file for easy distribution

## Features

✅ System tray icon on both platforms  
✅ No installation required (portable)  
✅ Web-based configuration interface  
✅ Auto-start/stop server  
✅ Easy access to configuration  

## Prerequisites

### Windows
- Python 3.8 or higher
- pip (Python package installer)
- ~500MB free disk space

### macOS
- Python 3.8 or higher
- Homebrew (will be installed automatically if missing)
- Xcode Command Line Tools
- ~500MB free disk space

## Building on Windows

1. **Open Command Prompt as Administrator**

2. **Navigate to build_scripts directory:**
   ```cmd
   cd aits_print_server\build_scripts
   ```

3. **Run the build script:**
   ```cmd
   build_windows.bat
   ```

4. **Wait for completion** (5-10 minutes)

5. **Find the executable:**
   ```
   dist\AITS_Print_Server.exe
   ```

### Distributing on Windows

The `.exe` file is completely portable. Users can:
1. Copy `AITS_Print_Server.exe` anywhere
2. Double-click to run
3. System tray icon will appear
4. Right-click icon for options

**Optional**: Create an installer using Inno Setup:
```
# Install Inno Setup from https://jrsoftware.org/isinfo.php
# Then compile the installer script (create one based on your needs)
```

## Building on macOS

1. **Open Terminal**

2. **Navigate to build_scripts directory:**
   ```bash
   cd aits_print_server/build_scripts
   ```

3. **Run the build script:**
   ```bash
   ./build_macos.sh
   ```

4. **Choose DMG creation when prompted**
   - Press `y` to create a .dmg installer
   - Press `n` to skip (just create .app)

5. **Wait for completion** (5-10 minutes)

6. **Find the output:**
   - Application: `dist/AITS Print Server.app`
   - DMG (if created): `dist/AITS_Print_Server_Installer.dmg`

### Distributing on macOS

**Option 1: Distribute .app directly**
Users can:
1. Copy `AITS Print Server.app` to Applications folder
2. Double-click to run
3. Grant permissions if prompted
4. System tray icon will appear

**Option 2: Distribute .dmg installer (Recommended)**
Users can:
1. Double-click the .dmg file
2. Drag app to Applications folder
3. Eject the disk image
4. Run from Applications

### Code Signing (macOS - Optional but Recommended)

For distribution outside your organization:

1. **Get an Apple Developer account** ($99/year)

2. **Request a Developer ID certificate**

3. **Sign the application:**
   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" "dist/AITS Print Server.app"
   ```

4. **Notarize with Apple:**
   ```bash
   xcrun altool --notarize-app --primary-bundle-id com.aits.printserver \
       --username "your@email.com" --password "@keychain:AC_PASSWORD" \
       --file "dist/AITS_Print_Server_Installer.dmg"
   ```

## System Tray Features

### Windows & macOS

Right-click the system tray icon to access:

- **Status** - Shows if server is running
- **Open Configuration** - Opens web interface in browser
- **Restart Server** - Restart the print server
- **Quit** - Stop server and exit application

### Web Configuration

When running, access the configuration interface at:
```
http://localhost:8888/config
```

Features:
- Configure server settings (host, port)
- Set default printer
- Adjust logging levels
- View available printers
- Test connection

## Troubleshooting Build Issues

### Windows

**Error: "Python not found"**
- Install Python from https://www.python.org/
- Make sure "Add Python to PATH" is checked

**Error: "pip is not recognized"**
- Reinstall Python with pip option enabled

**Error: "pywin32 import failed"**
```cmd
pip install --upgrade pywin32
python Scripts/pywin32_postinstall.py -install
```

### macOS

**Error: "command not found: python3"**
```bash
brew install python@3.11
```

**Error: "xcrun: error: invalid active developer path"**
```bash
xcode-select --install
```

**Error: "create-dmg: command not found"**
```bash
brew install create-dmg
```

**Permission denied**
```bash
chmod +x build_macos.sh
```

## File Structure After Build

### Windows
```
dist/
└── AITS_Print_Server.exe    (Standalone executable)
```

### macOS
```
dist/
├── AITS Print Server.app/   (Application bundle)
└── AITS_Print_Server_Installer.dmg  (Optional installer)
```

## Customization

### Change Icon

1. **Windows**: Replace `static/icon.ico` with your icon (256x256 recommended)
2. **macOS**: Replace `static/icon.icns` with your icon

### Change Application Name

Edit the spec files:
- `build_windows.spec` - Change `name='AITS_Print_Server'`
- `build_macos.spec` - Change `name='AITS Print Server.app'`

### Add Files to Bundle

Edit the `datas` list in spec files:
```python
datas=[
    ('../server_simple.py', '.'),
    ('../static', 'static'),
    ('../config.yaml.example', '.'),
    ('../your_file.txt', '.'),  # Add this
],
```

## Size Optimization

To reduce executable size:

1. **Remove unnecessary imports** in code
2. **Exclude modules** in spec file:
   ```python
   excludes=['tkinter', 'matplotlib', 'numpy'],
   ```
3. **Use UPX compression** (already enabled)

Typical sizes:
- Windows .exe: ~25-35 MB
- macOS .app: ~30-40 MB
- macOS .dmg: ~20-30 MB

## Testing the Build

### Windows
1. Copy .exe to different location
2. Double-click to run
3. Check system tray for icon
4. Open http://localhost:8888/config
5. Test printing functionality

### macOS
1. Copy .app to different Mac (or use VMware/Parallels)
2. Double-click to run
3. Grant permissions if requested
4. Check menu bar for icon
5. Open http://localhost:8888/config
6. Test printing functionality

## Automated Build (CI/CD)

### GitHub Actions Example

```yaml
name: Build Installers

on: [push]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: cd build_scripts && build_windows.bat
      - uses: actions/upload-artifact@v2
        with:
          name: windows-installer
          path: build_scripts/dist/AITS_Print_Server.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: cd build_scripts && ./build_macos.sh
      - uses: actions/upload-artifact@v2
        with:
          name: macos-installer
          path: build_scripts/dist/AITS_Print_Server_Installer.dmg
```

## Support

For build issues:
1. Check Python version: `python --version` (should be 3.8+)
2. Update pip: `pip install --upgrade pip`
3. Clear build cache: Delete `build/` and `dist/` directories
4. Reinstall dependencies: `pip install -r requirements.txt`

## Version Information

- PyInstaller: 6.3.0
- Python: 3.8+
- Supported OS:
  - Windows 10/11, Server 2016+
  - macOS 10.14 (Mojave) or later

---

**Build Version**: 1.0.0  
**Last Updated**: November 5, 2025
