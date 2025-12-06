# 🛑 Too Many System Tray Icons? - FIX GUIDE

## Problem: Multiple Printer Icons in System Tray

If you see dozens or hundreds of printer icons in your system tray, it means multiple instances of `AITS_Print_Server.exe` are running.

---

## ⚠️ STOP ALL INSTANCES IMMEDIATELY

### Method 1: Task Manager (Easiest)

1. **Open Task Manager**: Press `Ctrl + Shift + Esc`

2. **Find AITS_Print_Server.exe**: Look under "Processes" or "Details" tab

3. **Select the process**: Click on `AITS_Print_Server.exe`

4. **End all instances**:
   - Right-click → "End Task" (do this for EACH instance)
   - OR select the process and click "End Task" button repeatedly

5. **Verify**: All printer icons should disappear from system tray

### Method 2: Command Line (Faster for many instances)

1. **Open Command Prompt as Administrator**:
   - Press `Win + X`
   - Choose "Command Prompt (Admin)" or "Windows PowerShell (Admin)"

2. **Kill all instances**:
   ```cmd
   taskkill /F /IM AITS_Print_Server.exe
   ```

3. **Verify**: Check Task Manager to confirm all instances are gone

---

## 🔍 Why This Happened

### Common Causes:

1. **Double-clicking multiple times**
   - Each double-click starts a new instance
   - Each instance creates its own tray icon

2. **Crashes and auto-restarts**
   - If the app crashes but keeps restarting
   - Creates new instances in a loop

3. **Multiple shortcuts/startup entries**
   - App in Startup folder
   - App in Task Scheduler
   - App pinned to taskbar (accidentally clicked multiple times)

4. **Network drive or slow storage**
   - App takes time to start
   - User clicks again thinking it didn't work
   - Creates multiple instances

---

## ✅ HOW TO PREVENT THIS

### Solution 1: Add Single Instance Check

The app should be updated to only allow one instance at a time. Here's how:

**Update `tray_app.py`** to check for existing instances:

```python
import win32event
import win32api
from winerror import ERROR_ALREADY_EXISTS

# At the start of PrintServerTray.__init__():
def __init__(self):
    # Create a mutex to ensure only one instance runs
    self.mutex = win32event.CreateMutex(None, False, 'AITS_Print_Server_Mutex')
    self.last_error = win32api.GetLastError()
    
    if self.last_error == ERROR_ALREADY_EXISTS:
        print("AITS Print Server is already running!")
        sys.exit(0)
    
    # ... rest of __init__ code
```

### Solution 2: Check Port Before Starting

The app already tries to start on port 8888. We can check if it's in use:

```python
import socket

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except OSError:
            return True

# In start_server():
if is_port_in_use(self.server_port):
    print(f"Port {self.server_port} is already in use.")
    print("AITS Print Server may already be running.")
    return False
```

### Solution 3: User Instructions

**Add to installer/documentation:**

> ⚠️ **IMPORTANT**: Only run ONE instance of AITS Print Server
> 
> - Check system tray for existing printer icon before running
> - If icon exists, right-click it to open configuration
> - Don't double-click the .exe multiple times
> - The app takes 2-3 seconds to start

---

## 🚀 SAFE WAY TO USE THE APP

### First Time Setup:

1. **Install** using `AITS_Print_Server_Setup.exe`
   - This creates shortcuts in Start Menu
   - Optionally adds to Startup folder

2. **Launch ONCE**:
   - Use Start Menu shortcut
   - OR double-click desktop shortcut (if created)
   - OR run the .exe directly

3. **Verify it's running**:
   - Look for printer icon in system tray
   - It may take 2-3 seconds to appear

4. **Use the tray icon**:
   - Right-click → "Open Configuration"
   - Right-click → "Restart Server" (if needed)
   - Right-click → "Quit" (to stop)

### Daily Use:

- **Don't re-run the .exe** if it's already running
- **Check system tray first** for the printer icon
- **Use the tray icon menu** to control the server

### Stopping the Server:

- **Right-click tray icon** → "Quit"
- **OR** use Task Manager to end the process

---

## 🔧 IMMEDIATE FIX (For Current Situation)

**If you have 100+ instances running right now:**

1. **Open Task Manager** (`Ctrl + Shift + Esc`)

2. **Go to Details tab**

3. **Sort by Name** (click "Name" column header)

4. **Find AITS_Print_Server.exe**

5. **Right-click** → **End process tree**
   - This kills the process and any child processes

6. **Repeat** until all instances are gone

7. **Reboot** if Task Manager won't kill them all

---

## 📝 FOR DEVELOPERS

### Add Single Instance Lock:

I'll create an updated version of `tray_app.py` with single-instance protection:

**File: `tray_app_single_instance.py`**

```python
import sys
import os
import tempfile
import fcntl  # Linux/macOS
import platform

class SingleInstance:
    """Ensure only one instance of the app runs at a time"""
    
    def __init__(self, app_name="AITS_Print_Server"):
        self.app_name = app_name
        self.lock_file = None
        
        if platform.system() == 'Windows':
            # Windows: Use mutex
            import win32event
            import win32api
            from winerror import ERROR_ALREADY_EXISTS
            
            self.mutex = win32event.CreateMutex(None, False, f'{app_name}_Mutex')
            if win32api.GetLastError() == ERROR_ALREADY_EXISTS:
                raise RuntimeError(f"{app_name} is already running!")
        else:
            # Linux/macOS: Use file lock
            lock_path = os.path.join(tempfile.gettempdir(), f'{app_name}.lock')
            self.lock_file = open(lock_path, 'w')
            try:
                fcntl.lockf(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                raise RuntimeError(f"{app_name} is already running!")
```

---

## 🎯 SUMMARY

**Current Issue**: 144 instances running = 144 tray icons

**Immediate Fix**: 
1. Open Task Manager
2. Kill all `AITS_Print_Server.exe` processes
3. Reboot if necessary

**Long-term Fix**:
1. Update app with single-instance check
2. Add user instructions
3. Test before distributing

**Prevention**:
- Only run one instance
- Check tray for existing icon
- Use Start Menu shortcut (not .exe directly)
- Don't click multiple times

---

**Status**: 🔴 Critical - Need to add single-instance protection  
**Priority**: High - Users can accidentally create hundreds of instances  
**Solution**: Ready - See updated code above
