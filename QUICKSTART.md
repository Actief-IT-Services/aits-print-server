# AITS Print Server - Quick Start Guide

## Installation

### Linux (Ubuntu/Debian)

```bash
# 1. Navigate to print server directory
cd /home/ldcrx/odoo/shclients18/odoo-dev/aits_print_server

# 2. Install system dependencies
sudo apt-get update
sudo apt-get install -y cups libcups2-dev gcc python3-dev python3-venv

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Generate API key
python generate_api_key.py
# Copy the generated API key - you'll need it for configuration

# 6. Create configuration file
cp config.example.yaml config.yaml

# 7. Edit config.yaml and add your API key
nano config.yaml
# Replace 'your-secret-api-key-here' with the generated key
# Update other settings as needed (host, port, etc.)

# 8. Test the server
python server.py
```

### Windows

```powershell
# 1. Navigate to print server directory
cd C:\path\to\aits_print_server

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Generate API key
python generate_api_key.py
# Copy the generated API key

# 5. Create configuration file
copy config.example.yaml config.yaml

# 6. Edit config.yaml and add your API key
notepad config.yaml
# Replace 'your-secret-api-key-here' with the generated key

# 7. Test the server
python server.py
```

## Configuration

Edit `config.yaml`:

```yaml
server:
  host: 0.0.0.0  # Listen on all interfaces
  port: 8888     # Port number
  debug: false   # Set to true for development
  workers: 4     # Number of worker processes

security:
  api_keys:
    - 'YOUR_GENERATED_API_KEY_HERE'  # Replace with actual key

printer:
  timeout: 30           # Print job timeout (seconds)
  max_retries: 3        # Maximum retry attempts
  retention_days: 7     # Keep job history for 7 days

logging:
  level: INFO
  file: logs/print_server.log
```

## Testing

Test the server connection and printer discovery:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux
# or
venv\Scripts\activate     # Windows

# Run test script
python test_server.py --api-key YOUR_API_KEY
```

## Running the Server

### Development Mode

```bash
# Linux
source venv/bin/activate
python server.py

# Windows
venv\Scripts\activate
python server.py
```

### Production (Linux with systemd)

```bash
# 1. Create user for print server
sudo useradd -r -s /bin/false printserver

# 2. Install to /opt
sudo mkdir -p /opt/aits_print_server
sudo cp -r * /opt/aits_print_server/
sudo chown -R printserver:printserver /opt/aits_print_server

# 3. Set up virtual environment
cd /opt/aits_print_server
sudo -u printserver python3 -m venv venv
sudo -u printserver venv/bin/pip install -r requirements.txt

# 4. Install systemd service
sudo cp aits-print-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aits-print-server
sudo systemctl start aits-print-server

# 5. Check status
sudo systemctl status aits-print-server
sudo journalctl -u aits-print-server -f
```

### Production (Windows with NSSM)

```powershell
# 1. Download NSSM from https://nssm.cc/download
# 2. Extract nssm.exe to a folder

# 3. Install service
nssm install AITSPrintServer "C:\path\to\aits_print_server\venv\Scripts\python.exe" "C:\path\to\aits_print_server\server.py"

# 4. Configure service
nssm set AITSPrintServer AppDirectory "C:\path\to\aits_print_server"
nssm set AITSPrintServer DisplayName "AITS Print Server"
nssm set AITSPrintServer Description "Direct printing service for Odoo"
nssm set AITSPrintServer Start SERVICE_AUTO_START

# 5. Start service
nssm start AITSPrintServer

# 6. Check status
nssm status AITSPrintServer
```

### Docker

```bash
# 1. Create config.yaml from example
cp config.example.yaml config.yaml
# Edit config.yaml and add your API key

# 2. Build and run with docker-compose
docker-compose up -d

# 3. Check logs
docker-compose logs -f

# 4. Stop
docker-compose down
```

## Connecting to Odoo

1. **Start Print Server** on the machine with printer access

2. **Generate API Key**:
   ```bash
   python generate_api_key.py
   ```

3. **Configure in Odoo**:
   - Go to: Settings > Technical > Print Servers
   - Click "New"
   - Fill in:
     - Name: "Office Print Server"
     - URL: `http://your-server-ip:8888`
     - API Key: (paste generated key)
     - Timeout: 30
   - Click "Test Connection"
   - Click "Discover Printers"

4. **Configure Printers**:
   - Go to: Settings > Technical > Printers
   - Your discovered printers should appear
   - Configure each printer's settings

5. **Create Print Rules**:
   - Go to: Settings > Technical > Print Rules
   - Create rules to automatically route documents to printers

## API Endpoints

### Health Check
```bash
curl http://localhost:8888/api/health
```

### List Printers
```bash
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8888/api/printers
```

### Submit Print Job
```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "printer_name": "HP_LaserJet",
    "document": "BASE64_ENCODED_PDF",
    "document_name": "invoice_001.pdf",
    "copies": 1
  }' \
  http://localhost:8888/api/print
```

### Get Job Status
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8888/api/jobs/JOB_ID
```

### List Jobs
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8888/api/jobs?status=completed&limit=50
```

## Troubleshooting

### Server won't start

**Check if port is already in use:**
```bash
# Linux
sudo netstat -tulpn | grep 8888

# Windows
netstat -ano | findstr :8888
```

**Check logs:**
```bash
tail -f logs/print_server.log
```

### No printers found

**Linux:**
```bash
# Check CUPS is running
sudo systemctl status cups

# List printers via command line
lpstat -p -d

# Restart CUPS
sudo systemctl restart cups
```

**Windows:**
```powershell
# List printers
Get-Printer

# Check Print Spooler service
Get-Service -Name Spooler
Start-Service -Name Spooler
```

### Authentication errors

- Verify API key in `config.yaml` matches Odoo configuration
- Check that API key doesn't have extra spaces or quotes
- Regenerate API key if needed

### Print jobs failing

- Check printer is online and has paper
- Verify document format (PDF works best)
- Check printer permissions
- Review error message in job details

## Security Recommendations

1. **Use HTTPS** in production (set up nginx/apache reverse proxy)
2. **Firewall**: Only allow connections from Odoo server IP
3. **Strong API Keys**: Use the provided generator (32+ characters)
4. **Regular Updates**: Keep dependencies updated
5. **Log Monitoring**: Monitor logs for suspicious activity

## Next Steps

1. Set up print rules in Odoo for automatic routing
2. Configure print scenarios for different document types
3. Set up backup printers for failover
4. Configure HTTPS for production use
5. Set up monitoring and alerting

## Support

For issues or questions:
1. Check logs: `logs/print_server.log`
2. Run test script: `python test_server.py --api-key YOUR_KEY`
3. Check printer status in Odoo
4. Review job queue: `/api/jobs`
