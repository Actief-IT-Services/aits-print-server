# 🪟 AITS Print Server - Windows Installation

## Quick Start for Windows Users

### Option 1: Using the Installer (Recommended) ⭐

1. **Download** `AITS_Print_Server_Setup.exe`
2. **Run** the installer (may need administrator rights)
3. **Follow** the installation wizard
4. **Launch** from Start Menu → "AITS Print Server"
5. **System tray icon** appears
6. **Configure** by right-clicking tray icon → "Open Configuration"

### Option 2: Portable Version

1. **Download** `AITS_Print_Server.exe`
2. **Place** in any folder (e.g., Desktop, Documents)
3. **Double-click** to run
4. **System tray icon** appears
5. **Configure** by right-clicking tray icon → "Open Configuration"

---

## 🎯 What Gets Installed?

### With Installer:
- Main application in `C:\Program Files\AITS Print Server\`
- Start Menu shortcuts
- Desktop shortcut
- Configuration interface shortcut
- Uninstaller

### With Portable .exe:
- Single executable file
- Config file created on first run (same folder)
- Log file created on use (same folder)

---

## 🌐 Accessing the Configuration

After starting the application:

1. **System tray icon** appears (printer icon)
2. **Right-click** the tray icon
3. **Click** "Open Configuration"
4. **Browser opens** to http://localhost:8888/config

**Or manually visit:** http://localhost:8888/config

---

## ⚙️ Configuration Options

The web interface allows you to configure:

- **Server Settings**
  - Host address
  - Port number
  - Debug mode
  
- **Printer Settings**
  - Select default printer
  - View available printers
  - Test printing
  
- **Advanced Settings**
  - Max file size
  - Log level
  - Auto-start options

---

## 🖨️ How to Print

### From Odoo:
1. Open an invoice in Odoo
2. Click "Print" or "Direct Print"
3. Document sends to print server
4. Prints automatically to default printer

### From API:
```bash
curl -X POST http://localhost:8888/print \
  -F "file=@document.pdf" \
  -F "printer=Your Printer Name"
```

---

## 🔧 System Requirements

- **OS:** Windows 10 or later (64-bit)
- **RAM:** Minimum 2 GB, Recommended 4 GB
- **Disk:** 100 MB free space
- **Network:** For Odoo integration
- **Printer:** Any Windows-compatible printer

---

## 🚀 First Run Checklist

- [ ] Install or run the application
- [ ] Check system tray for printer icon
- [ ] Open configuration interface
- [ ] Verify printers are detected
- [ ] Select default printer
- [ ] Test print with sample document
- [ ] Configure Odoo connection (if needed)

---

## ❓ Troubleshooting

### Application won't start

**Problem:** Double-clicking does nothing

**Solutions:**
1. Check Windows Defender/Antivirus - may have blocked it
2. Right-click → "Run as Administrator"
3. Install Visual C++ Redistributable: [Download](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### No system tray icon

**Problem:** App runs but no tray icon

**Solutions:**
1. Check Windows taskbar settings
2. Enable "Show all icons" in system tray settings
3. Restart the application

### Port already in use

**Problem:** "Port 8888 already in use"

**Solutions:**
1. Close other applications using port 8888
2. Change port in configuration
3. Kill process: `netstat -ano | findstr :8888` then `taskkill /PID <pid> /F`

### Printers not showing

**Problem:** No printers in list

**Solutions:**
1. Check printer is installed in Windows
2. Open Settings → Devices → Printers
3. Restart print spooler: `net stop spooler && net start spooler`
4. Restart the application

### Can't access web interface

**Problem:** Browser can't connect to http://localhost:8888/config

**Solutions:**
1. Check application is running (tray icon should be visible)
2. Check firewall isn't blocking port 8888
3. Try `http://127.0.0.1:8888/config` instead
4. Restart application

---

## 🔄 Updating

### With Installer:
1. Download new version of `AITS_Print_Server_Setup.exe`
2. Run installer (will upgrade automatically)
3. Restart application

### With Portable:
1. Download new version of `AITS_Print_Server.exe`
2. Close running application (right-click tray → Quit)
3. Replace old .exe with new one
4. Start application

**Note:** Configuration files are preserved during updates

---

## 🗑️ Uninstalling

### If installed with installer:
1. **Start Menu** → Settings → Apps
2. Find **"AITS Print Server"**
3. Click **Uninstall**

**OR**

1. **Start Menu** → AITS Print Server → **Uninstall**

### If using portable .exe:
1. Right-click tray icon → **Quit**
2. Delete the .exe file
3. Delete `config.yaml` and `printserver.log` if present

---

## 🔐 Security & Privacy

- **Local only:** Server binds to localhost by default
- **No data collection:** No telemetry or analytics
- **Configuration:** Stored locally in config.yaml
- **Logs:** Stored locally in printserver.log
- **Network:** Only opens port 8888 on localhost

### For network access (advanced):
Edit config.yaml:
```yaml
server:
  host: "0.0.0.0"  # Listen on all interfaces
  port: 8888
```

**Warning:** This exposes the server to your network. Use firewall rules to restrict access.

---

## 📖 Additional Help

- **Quick Reference:** See `QUICK_REFERENCE.md`
- **Full Documentation:** See `README.md`
- **Build Guide:** See `WINDOWS_BUILD_GUIDE.md`
- **Feature Guide:** See `README_NEW_FEATURES.md`

---

## 🆘 Getting Support

If you encounter issues:

1. **Check the log file:** `printserver.log` in installation/application folder
2. **Review troubleshooting** section above
3. **Check documentation** files
4. **Contact:** your IT administrator or AITS support

---

## 🎉 You're Ready!

The AITS Print Server is now ready to use. Enjoy direct printing from Odoo to your local printers!

**Quick Access:**
- System Tray Icon → Right-click for menu
- Web Config → http://localhost:8888/config
- Documentation → Start Menu → AITS Print Server → Documentation

---

*Windows Installation Guide v1.0*
*For technical users, see WINDOWS_BUILD_GUIDE.md*
