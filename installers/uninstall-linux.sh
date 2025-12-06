#!/bin/bash
# AITS Print Server - Linux Uninstaller

INSTALL_DIR="/opt/aits-print-server"
SERVICE_NAME="aits-print-server"
USER="aits-print"

echo "AITS Print Server - Uninstaller"
echo "==============================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: Please run as root (use sudo)"
    exit 1
fi

# Stop and disable service
echo "Stopping service..."
systemctl stop ${SERVICE_NAME}.service 2>/dev/null || true
systemctl disable ${SERVICE_NAME}.service 2>/dev/null || true

# Remove service file
echo "Removing service file..."
rm -f /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload

# Remove installation directory
echo "Removing installation directory..."
rm -rf $INSTALL_DIR

# Remove user (optional)
read -p "Remove system user '$USER'? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    userdel $USER 2>/dev/null || true
    echo "User removed"
fi

echo ""
echo "Uninstallation completed!"
