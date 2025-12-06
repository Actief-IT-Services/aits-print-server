# Windows Build - NSIS Troubleshooting

## Problem: "NSIS not found" Error

Even though you have NSIS installed, the build script can't find it.

### Solution 1: Use the Updated Script (Recommended)

The `build_complete_windows.bat` script now automatically checks these locations:
- `C:\Program Files (x86)\NSIS\makensis.exe` (32-bit NSIS on 64-bit Windows)
- `C:\Program Files\NSIS\makensis.exe` (64-bit NSIS)
- System PATH

**Just run the script again** - it should now find NSIS automatically!

### Solution 2: Add NSIS to Your PATH (Permanent Fix)

1. **Find your NSIS installation:**
   - Default location: `C:\Program Files (x86)\NSIS\`
   - Or: `C:\Program Files\NSIS\`

2. **Add to PATH:**
   - Press Windows key + R
   - Type: `sysdm.cpl` and press Enter
   - Go to "Advanced" tab
   - Click "Environment Variables"
   - Under "System variables", find and select "Path"
   - Click "Edit"
   - Click "New"
   - Add: `C:\Program Files (x86)\NSIS` (or your NSIS location)
   - Click "OK" on all windows

3. **Restart Command Prompt** and try again

### Solution 3: Manual Build with Full Path

If the script still doesn't work, build manually:

```batch
REM 1. Build the .exe first
cd aits_print_server\build_scripts
pyinstaller --clean build_windows.spec

REM 2. Build the installer manually with full NSIS path
cd build_scripts
"C:\Program Files (x86)\NSIS\makensis.exe" windows_installer.nsi

REM 3. Move the installer to dist folder
move AITS_Print_Server_Setup.exe ..\dist\
```

### Solution 4: Verify NSIS Installation

Check if NSIS is actually installed:

1. Open File Explorer
2. Navigate to: `C:\Program Files (x86)\NSIS\`
3. Look for `makensis.exe`

If it's not there:
- Check `C:\Program Files\NSIS\`
- If neither location has it, reinstall NSIS from https://nsis.sourceforge.io/

### Solution 5: Skip NSIS (Use Standalone .exe Only)

You don't actually need NSIS! The standalone .exe works perfectly:

```batch
REM Just build the standalone executable
cd aits_print_server\build_scripts
build_windows.bat
```

This creates `dist\AITS_Print_Server.exe` which works without installation.

**Standalone .exe vs Installer:**
- **Standalone .exe**: Portable, no installation, works immediately
- **Installer (.exe from NSIS)**: Professional installation wizard, Start Menu shortcuts, uninstaller

Both contain the same application!

---

## Still Having Issues?

### Check NSIS Version
Open Command Prompt:
```batch
"C:\Program Files (x86)\NSIS\makensis.exe" /VERSION
```

Should show: `v3.x.x` (any version 3.x or later is fine)

### Reinstall NSIS
1. Download from: https://nsis.sourceforge.io/Download
2. Run installer
3. Choose default installation location
4. Complete installation
5. Run build script again

---

## Quick Test

To test if NSIS is accessible:

```batch
where makensis
```

If it shows a path, NSIS is in your PATH ✓  
If it says "INFO: Could not find...", use Solution 2 above

---

**Most Common Issue:** NSIS is installed but not in PATH. The updated `build_complete_windows.bat` now handles this automatically by checking default installation locations!
