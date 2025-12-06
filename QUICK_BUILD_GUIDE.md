# 🚀 Quick Build Reference - Windows

## ✅ THE FIX IS APPLIED

The crash in `tray_app.py` has been fixed. The issue was a method signature mismatch.

---

## 🎯 Just Want to Build? Run This:

```batch
cd C:\path\to\aits_print_server\build_scripts
build_simple_windows.bat
```

**That's it!** The script will:
- ✓ Check prerequisites
- ✓ Clean old builds
- ✓ Build the .exe
- ✓ Create the installer (if NSIS is installed)

---

## 📋 Three Build Options

### 🏃 Fast Build (Recommended)
```batch
build_simple_windows.bat
```
- Assumes dependencies already installed
- Goes straight to building
- **Fastest option**

### 🔄 Complete Build
```batch
build_complete_windows.bat
```
- Installs dependencies first
- Then builds everything
- Use for first-time builds

### ⚡ Basic Build
```batch
build_windows.bat
```
- Just creates the .exe
- No installer
- For quick tests

---

## 🎁 What You Get

After successful build:

```
dist/
  ├── AITS_Print_Server.exe          ← Standalone app (25-35 MB)
  └── AITS_Print_Server_Setup.exe    ← Professional installer
```

---

## 🧪 Test Your Build

1. **Run it**:
   ```
   dist\AITS_Print_Server.exe
   ```

2. **Look for system tray icon** (printer symbol)

3. **Right-click icon** → "Open Configuration"

4. **Browser opens** to `http://localhost:8888/config`

5. **Success!** 🎉

---

## ❌ If Something Goes Wrong

### Check Prerequisites First
```batch
build_scripts\check_environment.bat
```

This tells you what's missing:
- Python
- pip  
- PyInstaller
- NSIS (optional, for installer)

### Common Issues

**"PyInstaller not found"**
```batch
pip install pyinstaller==6.3.0
```

**"NSIS not found"**
- Download: https://nsis.sourceforge.io/Download
- Install to: `C:\Program Files (x86)\NSIS\`

**".exe crashes immediately"**
- ✅ Already fixed! Rebuild with the updated code.

---

## 📦 Dependencies (Auto-installed by complete build)

```
pyinstaller==6.3.0
pystray==0.19.5
flask==3.0.0
flask-cors==4.0.0
pillow==10.1.0
pyyaml==6.0.1
waitress==2.1.2
pywin32==306
reportlab==4.0.7
```

---

## 🔍 Need More Details?

- **Complete guide**: `WINDOWS_BUILD_GUIDE.md`
- **Fix details**: `WINDOWS_BUILD_FIX.md`
- **User guide**: `WINDOWS_INSTALL_GUIDE.md`
- **Features**: `README_NEW_FEATURES.md`

---

## 💡 Pro Tips

1. **First time?** Run `check_environment.bat` first
2. **Already installed dependencies?** Use `build_simple_windows.bat`
3. **Want just the .exe?** Use `build_windows.bat`
4. **Need the installer?** Make sure NSIS is installed
5. **Still having issues?** Check `WINDOWS_BUILD_FIX.md`

---

**Status**: ✅ Ready to build  
**Last Fix**: November 5, 2025 - Fixed tray_app.py method signature
