# 🚨 EMERGENCY: Stop All Running Instances

## You Have 144+ Instances Running!

### ⚡ QUICK FIX - Windows Task Manager

1. **Press**: `Ctrl` + `Shift` + `Esc`

2. **Click**: "Details" tab (or "Processes" tab)

3. **Find**: `AITS_Print_Server.exe`

4. **Right-click** → **"End process tree"**

5. **Repeat** until ALL instances are gone

---

### 💻 QUICK FIX - Command Line (FASTEST!)

**Open Command Prompt as Administrator:**
- Press `Win` + `X`
- Choose "Command Prompt (Admin)"

**Run this command:**
```cmd
taskkill /F /IM AITS_Print_Server.exe
```

**You should see:**
```
SUCCESS: The process "AITS_Print_Server.exe" with PID 1234 has been terminated.
SUCCESS: The process "AITS_Print_Server.exe" with PID 1235 has been terminated.
...
(repeated 144 times)
```

---

### 🔄 If That Doesn't Work - REBOOT

Sometimes processes get stuck. Just reboot your computer:
- Save your work
- Restart Windows
- All instances will be killed on shutdown

---

## ✅ FIXED FOR NEXT TIME!

The app has been updated with **single-instance protection**:

### What Changed:

1. **Lock File**: App creates a lock file to prevent multiple instances

2. **Port Check**: Verifies port 8888 isn't already in use

3. **User Warning**: Shows clear message if already running:
   ```
   =======================================================================
   AITS Print Server is already running!
   =======================================================================
   
   Look for the printer icon in your system tray.
   Right-click the icon to:
     - Open Configuration
     - Restart Server
     - Quit
   
   Press Enter to exit...
   ```

4. **Auto-Exit**: New instance exits instead of creating duplicate tray icons

---

## 🔨 Rebuild Required

After stopping all instances, rebuild the .exe:

```batch
cd aits_print_server\build_scripts
build_simple_windows.bat
```

This creates a new `.exe` with single-instance protection.

---

## 🎯 Testing the Fix

1. **Stop all instances** (using steps above)

2. **Rebuild the .exe** (see above)

3. **Run it once**:
   ```
   dist\AITS_Print_Server.exe
   ```

4. **Try running it again** (to test):
   - You should see: "AITS Print Server is already running!"
   - Press Enter to exit
   - NO new tray icon created ✅

5. **Success!** Only ONE instance can run now

---

## 📋 What You'll See Now

### First Instance (runs normally):
- ✅ Server starts
- ✅ Tray icon appears  
- ✅ Port 8888 opens
- ✅ Configuration available at http://localhost:8888/config

### Second Instance (blocked):
```
======================================================================
AITS Print Server is already running!
======================================================================

Look for the printer icon in your system tray.
Right-click the icon to:
  - Open Configuration
  - Restart Server
  - Quit

If you don't see the icon, check Task Manager for
running instances of AITS_Print_Server.exe
======================================================================
Press Enter to exit...
```

---

## 🎉 No More Multiple Instances!

After rebuilding with this fix:
- ✅ Can't accidentally start multiple instances
- ✅ Clear message if already running
- ✅ No more 100+ tray icons
- ✅ Safe to double-click by mistake

---

**Created**: November 5, 2025  
**Status**: 🔴 URGENT - Stop instances NOW, then rebuild with fix
