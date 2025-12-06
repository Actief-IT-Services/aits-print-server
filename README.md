# AITS Print Server

A professional print server application that bridges Odoo with physical printers.

## Features

- **REST API** for print job submission
- **Multi-platform support** (Linux with CUPS, Windows with win32print)
- **Printer discovery** and capability detection
- **Job queue management** with retry logic
- **API key authentication**
- **Real-time status monitoring**
- **Comprehensive logging**

## Installation

### Prerequisites

**Linux (Ubuntu/Debian):**
```bash
# Install CUPS
sudo apt-get update
sudo apt-get install cups cups-client python3-cups

# Install Python dependencies
pip install -r requirements.txt
```

**Windows:**
```bash
# Install Python dependencies (win32print comes with pywin32)
pip install -r requirements.txt
```

### Setup

1. Clone or copy this directory
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `config.example.yaml` to `config.yaml`
4. Edit `config.yaml` with your settings
5. Generate an API key: `python generate_api_key.py`
6. Run the server: `python server.py`

## Configuration

Edit `config.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8888
  debug: false
  workers: 4

security:
  api_keys:
    - "your-generated-api-key-here"
  
printer:
  default_timeout: 30
  max_retries: 3
  retry_delay: 5

logging:
  level: INFO
  file: logs/print_server.log
```

## API Endpoints

### Health Check
```
GET /api/health
```

### List Printers
```
GET /api/printers
Headers: X-API-Key: your-api-key
```

### Print Document
```
POST /api/print
Headers: 
  X-API-Key: your-api-key
  Content-Type: application/json
Body:
{
  "printer_name": "HP_LaserJet",
  "document": "base64_encoded_pdf",
  "document_name": "invoice.pdf",
  "copies": 1,
  "options": {
    "paper_size": "A4",
    "duplex": true,
    "color": false
  }
}
```

### Get Job Status
```
GET /api/jobs/{job_id}
Headers: X-API-Key: your-api-key
```

### List Jobs
```
GET /api/jobs
Headers: X-API-Key: your-api-key
Query params: ?status=pending&limit=50
```

## Running as a Service

### Linux (systemd)

Create `/etc/systemd/system/aits-print-server.service`:

```ini
[Unit]
Description=AITS Print Server
After=network.target cups.service

[Service]
Type=simple
User=printserver
WorkingDirectory=/opt/aits_print_server
ExecStart=/usr/bin/python3 /opt/aits_print_server/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable aits-print-server
sudo systemctl start aits-print-server
sudo systemctl status aits-print-server
```

### Windows (NSSM)

Use NSSM (Non-Sucking Service Manager):
```cmd
nssm install AITSPrintServer "C:\Python39\python.exe" "C:\aits_print_server\server.py"
nssm start AITSPrintServer
```

## Docker Support

Build and run with Docker:

```bash
docker build -t aits-print-server .
docker run -d -p 8888:8888 -v $(pwd)/config.yaml:/app/config.yaml aits-print-server
```

## Connecting to Odoo

In Odoo, go to **Direct Print > Configuration > Print Servers**:

1. Click **New**
2. Set **Server URL**: `http://your-server-ip:8888`
3. Set **API Key**: (copy from config.yaml)
4. Click **Test Connection**
5. Save

## Troubleshooting

### Linux - Printer not found
```bash
# List available printers
lpstat -p -d

# Check CUPS status
systemctl status cups
```

### Windows - Permission denied
Run the server as Administrator or grant printer access to the user account.

### Connection refused
- Check firewall settings
- Verify the server is running: `curl http://localhost:8888/api/health`
- Check logs in `logs/print_server.log`

## License

LGPL-3
