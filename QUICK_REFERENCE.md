# 🚀 AITS Print Server - Quick Reference Card

## ⚡ Quick Start (Choose One)

### 1️⃣ System Tray App (Recommended for Testing)
```bash
cd /home/ldcrx/odoo/shclients18/odoo-dev/aits_print_server
source venv/bin/activate
python3 tray_app.py
```
✅ Tray icon appears → Right-click → "Open Configuration"

### 2️⃣ Simple Server Only
```bash
cd /home/ldcrx/odoo/shclients18/odoo-dev/aits_print_server
source venv/bin/activate
python3 server_simple.py
```
✅ Open browser: http://localhost:8888/config

### 3️⃣ Windows Executable (On Windows)
```batch
cd aits_print_server
build_scripts\build_windows.bat
dist\AITS_Print_Server.exe
```
✅ Double-click .exe → Tray icon appears

### 4️⃣ macOS Application (On macOS)
```bash
cd aits_print_server
./build_scripts/build_macos.sh
open dist/AITS\ Print\ Server.app
```
✅ Menu bar icon appears

---

## 🌐 Web Interface Access

**URL**: http://localhost:8888/config

**Features**:
- ⚙️ Server Settings (host, port, debug mode)
- 🖨️ Printers (discover, select default)
- ℹ️ About (version info)

---

## 📡 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API info |
| `/config` | GET | Web UI |
| `/health` | GET | Health check |
| `/printers` | GET | List printers |
| `/print` | POST | Print PDF |
| `/api/config` | GET/POST | Settings |

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `tray_app.py` | System tray application |
| `server_simple.py` | Web server with config UI |
| `static/config.html` | Configuration interface |
| `config.yaml.example` | Configuration template |
| `generate_icons.py` | Icon generator |

---

## 🔨 Build Commands

### Windows
```batch
build_scripts\build_windows.bat
```
Output: `dist\AITS_Print_Server.exe`

### macOS
```bash
./build_scripts/build_macos.sh
```
Output: `dist/AITS Print Server.app`

---

## 🛠️ Install as Service

### Linux
```bash
sudo ./installers/install-linux.sh
```
Uninstall: `sudo ./installers/uninstall-linux.sh`

### macOS
```bash
sudo ./installers/install-macos.sh
```
Uninstall: `sudo ./installers/uninstall-macos.sh`

### Windows (as Administrator)
```batch
installers\install-windows.bat
```
Uninstall: `installers\uninstall-windows.bat`

---

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port is in use
sudo netstat -tulpn | grep 8888

# Check logs
tail -f printserver.log
```

### Printers not showing
```bash
# Linux/macOS
lpstat -p -d

# Windows (PowerShell)
Get-Printer
```

### Tray icon missing
```bash
# Install dependencies
pip install pystray pillow
```

### Build failed
```bash
# Install PyInstaller
pip install pyinstaller==6.3.0

# Windows: Install Visual C++ Redistributable
# macOS: brew install create-dmg
```

---

## 📚 Documentation

| Document | Size | Purpose |
|----------|------|---------|
| `DEPLOYMENT_COMPLETE.md` | 16KB | Complete deployment guide |
| `BUILD_GUIDE.md` | 7.2KB | Build executables guide |
| `README_NEW_FEATURES.md` | 8.3KB | Feature documentation |
| `NEW_FEATURES_SUMMARY.md` | 11KB | Comprehensive summary |
| `INSTALLATION.md` | 5.8KB | Installation instructions |
| `QUICKSTART.md` | 7.1KB | Quick start guide |

---

## ✅ Testing Checklist

- [ ] `python3 tray_app.py` starts without errors
- [ ] Tray/menu icon appears
- [ ] http://localhost:8888/config loads
- [ ] Status shows "Online" (green dot)
- [ ] Printers list populated
- [ ] Settings can be changed and saved
- [ ] Print test PDF works
- [ ] Quit from tray menu works

---

## 🔑 Default Settings

```yaml
Server:
  Host: 0.0.0.0
  Port: 8888
  Debug: false

Printing:
  Default Printer: (auto-detect)
  Max File Size: 50 MB
  Allowed: PDF only

Logging:
  Level: INFO
  File: printserver.log
```

---

## 📦 Dependencies

**Core**:
- Flask 3.0.0
- flask-cors
- PyYAML
- Requests
- ReportLab

**New Features**:
- pystray 0.19.5
- Pillow 10.1.0
- pyinstaller 6.3.0

**Platform**:
- Windows: pywin32, win32print
- Linux/macOS: pycups

---

## 🎯 Common Tasks

### Change Port
Edit `config.yaml`:
```yaml
server:
  port: 9000  # Change from 8888
```
Or use web interface → Server Settings → Port

### Regenerate Icons
```bash
python3 generate_icons.py
```

### View Logs
```bash
tail -f printserver.log
```

### Test API
```bash
# Health check
curl http://localhost:8888/health

# List printers
curl http://localhost:8888/printers

# Get config
curl http://localhost:8888/api/config
```

---

## 🚢 Distribution

### For End Users
✅ **Windows**: Distribute `AITS_Print_Server.exe`
✅ **macOS**: Distribute `AITS Print Server.app` or `.dmg`

**No Python required!**

### For Servers
✅ Use installer scripts in `installers/` folder
✅ Runs as system service
✅ Auto-starts on boot

### For Developers
✅ Clone repository
✅ `pip install -r requirements.txt`
✅ Run directly with Python

---

## 📞 Quick Help

**Web Interface Not Loading?**
→ Check server is running: `ps aux | grep server_simple`

**Can't Print?**
→ Check printer is online: `lpstat -p` (Linux/macOS)

**Tray Icon Missing?**
→ Install: `pip install pystray pillow`

**Build Failed?**
→ See `BUILD_GUIDE.md` troubleshooting section

---

## 🏆 Project Status

✅ **Web Configuration Interface** - Complete  
✅ **System Tray Application** - Complete  
✅ **Windows Executable Build** - Complete  
✅ **macOS Application Build** - Complete  
✅ **Linux Service Install** - Complete  
✅ **Icon Generation** - Complete  
✅ **Documentation** - Complete  
✅ **Testing Tools** - Complete  

**Status: Production Ready** 🎉

---

*Quick Reference v1.0 - AITS Direct Print Server*
