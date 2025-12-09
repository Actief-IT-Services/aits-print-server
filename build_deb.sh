#!/bin/bash
# =============================================================================
# AITS Print Server - Debian Package Builder
# =============================================================================
# This script creates a .deb package for easy installation
#
# Usage: ./build_deb.sh
# Output: aits-print-server_1.0.0_all.deb
# =============================================================================

set -e

# Configuration
PACKAGE_NAME="aits-print-server"
VERSION="1.0.0"
MAINTAINER="Actief IT Services <info@actief-it.be>"
DESCRIPTION="AITS Print Server for Odoo Direct Printing"
ARCH="all"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="/tmp/${PACKAGE_NAME}_${VERSION}_${ARCH}"

echo "=========================================="
echo "Building ${PACKAGE_NAME} v${VERSION}"
echo "=========================================="

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create directory structure
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/aits-print-server"
mkdir -p "$BUILD_DIR/etc/systemd/system"
mkdir -p "$BUILD_DIR/usr/local/bin"

# Copy application files
echo "Copying application files..."
cp "$SCRIPT_DIR/server.py" "$BUILD_DIR/opt/aits-print-server/"
cp "$SCRIPT_DIR/printer_manager.py" "$BUILD_DIR/opt/aits-print-server/"
cp "$SCRIPT_DIR/job_queue.py" "$BUILD_DIR/opt/aits-print-server/"
cp "$SCRIPT_DIR/auth.py" "$BUILD_DIR/opt/aits-print-server/"
cp "$SCRIPT_DIR/generate_api_key.py" "$BUILD_DIR/opt/aits-print-server/"
cp "$SCRIPT_DIR/requirements.txt" "$BUILD_DIR/opt/aits-print-server/"
cp "$SCRIPT_DIR/config.example.yaml" "$BUILD_DIR/opt/aits-print-server/"

# Copy odoo_client if exists
if [ -f "$SCRIPT_DIR/odoo_client.py" ]; then
    cp "$SCRIPT_DIR/odoo_client.py" "$BUILD_DIR/opt/aits-print-server/"
fi

# Copy static files if they exist
if [ -d "$SCRIPT_DIR/static" ]; then
    cp -r "$SCRIPT_DIR/static" "$BUILD_DIR/opt/aits-print-server/"
fi

# Create systemd service file
echo "Creating systemd service..."
cat > "$BUILD_DIR/etc/systemd/system/aits-print-server.service" << 'EOF'
[Unit]
Description=AITS Print Server for Odoo Direct Printing
Documentation=https://github.com/laurensdecroix/odoo-dev
After=network.target cups.service
Wants=cups.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/aits-print-server
ExecStart=/usr/bin/python3 /opt/aits-print-server/server.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aits-print-server

# Security
NoNewPrivileges=false
ProtectSystem=false
ProtectHome=false

[Install]
WantedBy=multi-user.target
EOF

# Create control file
echo "Creating DEBIAN/control..."
cat > "$BUILD_DIR/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.8), python3-pip, python3-venv, cups, libcups2-dev, python3-flask, python3-yaml, python3-requests
Recommends: python3-cups
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 AITS Print Server enables direct printing from Odoo to local printers.
 Features:
  - REST API for print job management
  - CUPS integration for Linux printing
  - Auto-discovery of network printers
  - Systemd service for auto-start
  - Web configuration interface
Homepage: https://www.actief-it.be
EOF

# Create postinst script (runs after installation)
echo "Creating post-install script..."
cat > "$BUILD_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo "=========================================="
echo "AITS Print Server - Post Installation"
echo "=========================================="

# Install Python packages system-wide
echo "Installing Python dependencies..."
pip3 install flask flask-cors pyyaml requests pycups 2>/dev/null || \
python3 -m pip install flask flask-cors pyyaml requests pycups 2>/dev/null || \
apt-get install -y python3-flask python3-yaml python3-requests 2>/dev/null || true

# Create config if it doesn't exist
if [ ! -f /opt/aits-print-server/config.yaml ]; then
    echo "Creating default configuration..."
    cp /opt/aits-print-server/config.example.yaml /opt/aits-print-server/config.yaml
    
    # Generate API key
    API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
    sed -i "s/CHANGE-ME-GENERATE-A-SECURE-API-KEY/$API_KEY/" /opt/aits-print-server/config.yaml 2>/dev/null || true
    
    echo ""
    echo "=========================================="
    echo "Generated API Key: $API_KEY"
    echo "=========================================="
    echo "Save this key! You'll need it to configure Odoo."
    echo ""
fi

# Create logs directory
mkdir -p /opt/aits-print-server/logs
chmod 755 /opt/aits-print-server/logs

# Set permissions
chmod 755 /opt/aits-print-server
chmod 644 /opt/aits-print-server/*.py
chmod 644 /opt/aits-print-server/config.yaml 2>/dev/null || true

# Reload systemd and enable service
echo "Enabling systemd service..."
systemctl daemon-reload
systemctl enable aits-print-server

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start aits-print-server"
echo "  Stop:    sudo systemctl stop aits-print-server"
echo "  Status:  sudo systemctl status aits-print-server"
echo "  Logs:    journalctl -u aits-print-server -f"
echo ""
echo "Config:    /opt/aits-print-server/config.yaml"
echo "Server:    http://localhost:8888"
echo ""
echo "To start now, run:"
echo "  sudo systemctl start aits-print-server"
echo ""

exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# Create prerm script (runs before removal)
echo "Creating pre-remove script..."
cat > "$BUILD_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

echo "Stopping AITS Print Server..."
systemctl stop aits-print-server 2>/dev/null || true
systemctl disable aits-print-server 2>/dev/null || true

exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/prerm"

# Create postrm script (runs after removal)
echo "Creating post-remove script..."
cat > "$BUILD_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

if [ "$1" = "purge" ]; then
    echo "Removing configuration and logs..."
    rm -rf /opt/aits-print-server
fi

systemctl daemon-reload

exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# Create conffiles (config files that should be preserved on upgrade)
# Note: Only list files that exist in the package
echo "Creating conffiles..."
cat > "$BUILD_DIR/DEBIAN/conffiles" << 'EOF'
/opt/aits-print-server/config.example.yaml
EOF

# Set permissions
find "$BUILD_DIR" -type d -exec chmod 755 {} \;
find "$BUILD_DIR/opt" -type f -exec chmod 644 {} \;
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/prerm"
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# Build the package
echo "Building .deb package..."
DEB_FILE="${SCRIPT_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
dpkg-deb --root-owner-group --build "$BUILD_DIR" "$DEB_FILE"

# Clean up
rm -rf "$BUILD_DIR"

echo ""
echo "=========================================="
echo "Package built successfully!"
echo "=========================================="
echo ""
echo "Output: $DEB_FILE"
echo ""
echo "To install:"
echo "  sudo dpkg -i $DEB_FILE"
echo "  sudo apt-get install -f  # Fix any missing dependencies"
echo ""
echo "Or use apt directly:"
echo "  sudo apt install ./$DEB_FILE"
echo ""
