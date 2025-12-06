# 🪟 Windows Installer Build Guide

## Overview

This guide explains how to build Windows installers for the AITS Print Server. You'll create:

1. **Standalone .exe** - Portable executable (no installation needed)
2. **Setup .exe** - Professional installer with Windows integration

---

## 📋 Prerequisites

### Required

1. **Windows 10 or later** (64-bit)
2. **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
   - ✅ During installation, check "Add Python to PATH"

### Optional (for installer)

3. **NSIS** (Nullsoft Scriptable Install System)
   - [Download from nsis.sourceforge.io](https://nsis.sourceforge.io/Download)
   - Install with default settings
   - NSIS creates professional Windows installers

---

## 🚀 Quick Build (Recommended)

### Method 1: Automated Build Script

This is the **easiest method** - everything is automated:

```batch
cd aits_print_server\build_scripts
build_complete_windows.bat
```

The script will:
- ✅ Check all prerequisites
- ✅ Install Python dependencies
- ✅ Clean previous builds
- ✅ Build standalone .exe with PyInstaller
- ✅ Create installer .exe with NSIS (if available)
- ✅ Show summary and file locations

**Output files:**
- `dist\AITS_Print_Server.exe` - Standalone executable (~30MB)
- `dist\AITS_Print_Server_Setup.exe` - Installer (~30MB) *[if NSIS installed]*

---

## 🔧 Manual Build Instructions

### Step 1: Prepare Environment

Open Command Prompt or PowerShell:

```batch
cd path\to\aits_print_server
```

### Step 2: Install Dependencies

```batch
pip install --upgrade pip
pip install pyinstaller==6.3.0
pip install pillow==10.1.0
pip install pystray==0.19.5
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install pyyaml==6.0.1
pip install waitress==2.1.2
pip install pywin32==306
pip install reportlab==4.0.7
pip install requests==2.31.0
```

### Step 3: Build Standalone Executable

```batch
cd build_scripts
pyinstaller --clean build_windows.spec
```

This creates: `dist\AITS_Print_Server.exe`

### Step 4: Build Installer (Optional)

**Requirements:** NSIS must be installed

```batch
cd build_scripts
makensis windows_installer.nsi
```

This creates: `build_scripts\AITS_Print_Server_Setup.exe`

Move to dist folder:
```batch
move AITS_Print_Server_Setup.exe ..\dist\
```

---

## 📦 Build Output

### Standalone Executable

**File:** `dist\AITS_Print_Server.exe`

**Size:** ~25-35 MB

**Features:**
- ✅ No installation required
- ✅ Portable - can run from USB drive
- ✅ System tray integration
- ✅ Web configuration interface
- ✅ All dependencies bundled

**Usage:**
- Double-click to run
- System tray icon appears
- Right-click tray icon → "Open Configuration"
- Access web UI: http://localhost:8888/config

### Professional Installer

**File:** `dist\AITS_Print_Server_Setup.exe`

**Size:** ~30-40 MB

**Features:**
- ✅ Standard Windows installer wizard
- ✅ Start Menu shortcuts
- ✅ Desktop shortcut
- ✅ Uninstaller in Control Panel
- ✅ Proper Windows integration
- ✅ Installation directory choice

**Installation includes:**
- Main executable
- Configuration files
- Documentation
- Static assets
- Shortcuts

**Uninstallation:**
- Control Panel → Programs → Uninstall
- Or: Start Menu → AITS Print Server → Uninstall

---

## 🧪 Testing Your Build

### Test Standalone .exe

1. Navigate to `dist` folder
2. Double-click `AITS_Print_Server.exe`
3. Check system tray for printer icon
4. Right-click icon → "Open Configuration"
5. Verify web interface loads
6. Test printer discovery
7. Try a test print

### Test Installer

1. Run `AITS_Print_Server_Setup.exe`
2. Follow installation wizard
3. Check Start Menu for shortcuts
4. Launch from Start Menu
5. Verify system tray icon appears
6. Test web interface
7. Try uninstalling from Control Panel

---

## 🛠️ Customization

### Change Application Icon

1. Replace `static\icon.ico` with your custom icon
2. Rebuild the executable

### Change Installer Settings

Edit `build_scripts\windows_installer.nsi`:

```nsis
!define PRODUCT_NAME "Your Company Print Server"
!define PRODUCT_VERSION "2.0.0"
!define PRODUCT_PUBLISHER "Your Company"
!define PRODUCT_WEB_SITE "http://www.yourcompany.com"
```

### Modify Build Settings

Edit `build_scripts\build_windows.spec`:

```python
# Change executable name
exe = EXE(
    name='YourPrintServer',  # Change this
    ...
)

# Add/remove files
datas=[
    ('config.yaml.example', '.'),
    ('static', 'static'),
    ('your_file.txt', '.'),  # Add custom files
],
```

---

## 📊 File Size Optimization

### Current size: ~30MB

**To reduce size:**

1. **Remove unused dependencies:**
   ```python
   # In build_windows.spec
   excludes=['tkinter', 'matplotlib', 'numpy', ...],
   ```

2. **Compress with UPX:**
   ```batch
   pip install pyinstaller[encryption]
   # Add to spec file:
   upx=True,
   upx_exclude=['vcruntime140.dll'],
   ```

3. **One-file mode** (already enabled):
   ```python
   onefile=True,
   ```

### To increase compatibility:

1. **Bundle runtime libraries:**
   ```batch
   # Install Visual C++ Redistributable
   # Include in installer
   ```

---

## 🐛 Troubleshooting

### Build Fails: "Python not found"

**Solution:**
- Reinstall Python
- Check "Add Python to PATH" during installation
- Or manually add to PATH:
  ```batch
  setx PATH "%PATH%;C:\Python311;C:\Python311\Scripts"
  ```

### Build Fails: "PyInstaller error"

**Solution:**
```batch
pip uninstall pyinstaller
pip install pyinstaller==6.3.0
pip install --upgrade setuptools
```

### .exe doesn't run: "Missing DLL"

**Solution:**
- Install Visual C++ Redistributable:
  - [Download from Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Antivirus blocks .exe

**Solution:**
- Add exception in antivirus
- Sign the executable (requires code signing certificate)
- Use installer instead of standalone .exe

### NSIS not found

**Solution:**
```batch
# Download and install NSIS
# Add to PATH (default: C:\Program Files (x86)\NSIS)
setx PATH "%PATH%;C:\Program Files (x86)\NSIS"
```

### "Failed to execute script"

**Solution:**
```batch
# Add debug flag to see errors
# Edit build_windows.spec:
console=True,  # Change from False
# Rebuild and check console output
```

---

## 🔐 Code Signing (Optional)

To prevent "Unknown Publisher" warnings:

### 1. Get Code Signing Certificate

- Purchase from Digicert, Sectigo, etc. (~$100-400/year)
- Or use self-signed for testing

### 2. Sign the Executable

```batch
# Using signtool (Windows SDK)
signtool sign /f "certificate.pfx" /p "password" /t http://timestamp.digicert.com "dist\AITS_Print_Server.exe"
```

### 3. Verify Signature

```batch
signtool verify /pa "dist\AITS_Print_Server.exe"
```

---

## 📝 Build Checklist

Before building:
- [ ] Updated version number in code
- [ ] Updated version in `windows_installer.nsi`
- [ ] Tested application functionality
- [ ] Updated documentation
- [ ] Generated fresh icons

After building:
- [ ] Test standalone .exe on clean Windows VM
- [ ] Test installer on clean Windows VM
- [ ] Verify all features work
- [ ] Test uninstaller
- [ ] Check file sizes
- [ ] Scan with antivirus
- [ ] Document any issues

---

## 📤 Distribution

### For End Users (Recommended)

**Option 1:** Professional Installer
```
Distribute: AITS_Print_Server_Setup.exe
Size: ~30-40 MB
Advantages: Easy installation, Windows integration, uninstaller
```

**Option 2:** Standalone Executable
```
Distribute: AITS_Print_Server.exe
Size: ~25-35 MB
Advantages: No installation, portable, simple
```

### Distribution Methods

1. **Direct Download**
   - Host on company website
   - Use download manager

2. **Network Share**
   - Place on company network drive
   - Users can copy and run

3. **USB Drive**
   - Copy to USB
   - Distribute to users

4. **Email** (not recommended for large files)
   - Zip the executable
   - Send via email

### Required Files for Users

**Minimum:**
- `AITS_Print_Server_Setup.exe` OR `AITS_Print_Server.exe`

**Recommended:**
- Installer/executable
- `README.md` or user guide
- `QUICK_REFERENCE.md`
- Installation instructions

---

## 🎯 Performance Notes

### Startup Time
- First launch: 3-5 seconds
- Subsequent launches: 2-3 seconds
- PyInstaller extracts files on first run

### Memory Usage
- Idle: ~50-80 MB RAM
- Active printing: ~100-150 MB RAM
- System tray: ~10-20 MB RAM

### Disk Space
- Installed size: ~40-50 MB
- Config/logs: ~1-5 MB
- Total: ~50-60 MB

---

## 🆘 Support

### Common Questions

**Q: Do users need Python installed?**
A: No, everything is bundled in the .exe

**Q: Will it work on Windows 7?**
A: Recommended Windows 10+, may work on Windows 7 with updates

**Q: Can multiple instances run?**
A: Only one instance can bind to port 8888

**Q: How to change the port?**
A: Use web configuration interface or edit config.yaml

**Q: Does it require admin rights?**
A: No for standalone .exe, Yes for installer

---

## 📚 Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [NSIS Documentation](https://nsis.sourceforge.io/Docs/)
- [Python Windows FAQ](https://docs.python.org/3/faq/windows.html)
- [Code Signing Guide](https://learn.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)

---

## 🎉 Success!

If you've made it this far, you should have:

✅ Working Windows installer
✅ Standalone portable .exe
✅ Professional installation experience
✅ Easy distribution package

**Ready to distribute your Windows Print Server!** 🚀

---

*Build Guide v1.0 - Last Updated: November 2024*
