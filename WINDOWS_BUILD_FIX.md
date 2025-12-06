# Windows Build Issues - FIXED ✅

## Issue Discovered

The `.exe` file built with PyInstaller was crashing with this error:

```
Failed to execute script 'tray_app' due to unhandled exception:
PrintServerTray.get_status_text() missing 1 required positional argument: 'item'
```

## Root Cause

In `tray_app.py`, the method signature didn't match how it was being called:
- **Defined as**: `get_status_text(self, icon, item)` 
- **Called as**: `MenuItem(self.get_status_text, ...)` without parameters

When pystray calls the function to get the menu text, it doesn't pass parameters, causing the crash.

## Fix Applied ✅

Updated `tray_app.py`:

**Before:**
```python
def get_status_text(self, icon, item):
    """Get server status text"""
    if self.server_process and self.server_process.poll() is None:
        return "Status: Running"
    return "Status: Stopped"

def setup_menu(self):
    return Menu(
        MenuItem(
            self.get_status_text,  # ❌ Wrong - expects parameters
            lambda: None,
            enabled=False
        ),
        ...
    )
```

**After:**
```python
def get_status_text(self):  # ✅ No extra parameters
    """Get server status text"""
    if self.server_process and self.server_process.poll() is None:
        return "Status: Running"
    return "Status: Stopped"

def setup_menu(self):
    return Menu(
        MenuItem(
            self.get_status_text(),  # ✅ Call the method to get text
            lambda icon, item: None,  # ✅ Proper lambda signature
            enabled=False
        ),
        ...
    )
```

## How to Rebuild

### Option 1: Simple Build (Recommended)

```batch
cd aits_print_server\build_scripts
build_simple_windows.bat
```

### Option 2: Complete Build (if you want to reinstall dependencies)

```batch
cd aits_print_server\build_scripts
build_complete_windows.bat
```

### Option 3: Basic Build (just the .exe)

```batch
cd aits_print_server\build_scripts
build_windows.bat
```

## Testing the Fix

After rebuilding, test the `.exe`:

1. **Run the executable**:
   ```
   dist\AITS_Print_Server.exe
   ```

2. **Check system tray**: You should see the printer icon in the system tray

3. **Right-click the icon**: Menu should show:
   - Status: Running (grayed out)
   - Open Configuration
   - Restart Server
   - Quit

4. **Click "Open Configuration"**: Should open `http://localhost:8888/config` in your browser

5. **Test the web interface**: Try discovering printers and updating settings

## What Each Build Script Does

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `build_simple_windows.bat` | Fast build, skips dependency install | When deps already installed, fastest option |
| `build_complete_windows.bat` | Full automation, installs deps + builds | First-time build or after updating Python |
| `build_windows.bat` | Basic .exe only, no installer | Quick test builds |
| `check_environment.bat` | Verifies prerequisites | Before building to check setup |

## Expected Output Files

After a successful build:

```
dist/
  ├── AITS_Print_Server.exe         (25-35 MB standalone executable)
  └── AITS_Print_Server_Setup.exe   (Installer with NSIS, if available)
```

## Troubleshooting

### If the .exe still crashes:

1. **Run from command line** to see error messages:
   ```cmd
   cd dist
   AITS_Print_Server.exe
   ```

2. **Check if dependencies are missing**:
   - The .exe should be self-contained
   - Check that `static/config.html` was bundled

3. **Verify Python version**:
   ```cmd
   python --version
   ```
   Should be Python 3.8 or higher

### If NSIS installer isn't created:

1. **Check NSIS installation**:
   ```cmd
   "C:\Program Files (x86)\NSIS\makensis.exe" /VERSION
   ```

2. **Install NSIS** if missing:
   - Download from: https://nsis.sourceforge.io/Download
   - Install to default location

3. **Run environment check**:
   ```cmd
   build_scripts\check_environment.bat
   ```

## Files Modified

- ✅ `tray_app.py` - Fixed method signature
- ✅ `build_complete_windows.bat` - Enhanced error handling
- ✅ `build_simple_windows.bat` - Created new fast build script

## Next Steps

1. **Rebuild the .exe** with one of the scripts above
2. **Test the new .exe** to ensure the tray icon works
3. **Distribute** either:
   - `AITS_Print_Server.exe` (portable, no installation needed)
   - `AITS_Print_Server_Setup.exe` (professional installer)

---

**Last Updated**: November 5, 2025  
**Status**: ✅ Fixed and ready to rebuild
