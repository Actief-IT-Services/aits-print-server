# Windows Installer - Quick Start

## 🎯 For the Person Building the .exe

### What You Need (on a Windows PC):
1. Python 3.8 or newer
2. Internet connection
3. (Optional) NSIS for professional installer

### Build Steps:

**Step 1:** Transfer this entire folder to your Windows machine

**Step 2:** Open Command Prompt (Windows key + R, type `cmd`, press Enter)

**Step 3:** Navigate to the folder:
```batch
cd path\to\aits_print_server
```

**Step 4:** Run the automated build:
```batch
build_scripts\build_complete_windows.bat
```

**Step 5:** Wait for completion (5-10 minutes)

**Step 6:** Find your files in the `dist\` folder:
- `AITS_Print_Server.exe` - Standalone application
- `AITS_Print_Server_Setup.exe` - Professional installer (if NSIS installed)

---

## 📤 For Distribution

Once built, distribute to users:

### Option 1: Professional Installer (Recommended)
**File:** `dist\AITS_Print_Server_Setup.exe`
- Give this to end users
- Include `WINDOWS_INSTALL_GUIDE.md`
- Users just run the installer

### Option 2: Portable Application
**File:** `dist\AITS_Print_Server.exe`
- Give this to users who want portable version
- No installation needed
- Just double-click to run

---

## ✅ Testing Your Build

Before distributing:

1. **Test on your Windows PC:**
   - Run `AITS_Print_Server.exe`
   - Check system tray for icon
   - Visit http://localhost:8888/config
   - Verify printers show up
   - Try a test print

2. **Test on a clean Windows PC (if possible):**
   - Run the installer
   - Verify installation works
   - Test printing
   - Test uninstallation

---

## 🆘 If Build Fails

### "Python not found"
- Install Python from https://www.python.org/
- Check "Add Python to PATH" during installation

### "NSIS not found"
- Don't worry! The standalone .exe will still be created
- To get installer, download NSIS from https://nsis.sourceforge.io/

### Other errors
- See `WINDOWS_BUILD_GUIDE.md` for detailed troubleshooting

---

## 📞 Questions?

See the full documentation:
- **WINDOWS_BUILD_GUIDE.md** - Complete build instructions
- **WINDOWS_INSTALL_GUIDE.md** - For end users
- **QUICK_REFERENCE.md** - Quick commands

---

**That's it! You're ready to create Windows installers!** 🎉
