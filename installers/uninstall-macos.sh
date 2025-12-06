#!/bin/bash
# AITS Print Server - macOS Uninstaller

INSTALL_DIR="/usr/local/aits-print-server"
PLIST_NAME="com.aits.print-server"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "AITS Print Server - Uninstaller"
echo "==============================="
echo ""

# Unload LaunchAgent
echo "Stopping service..."
launchctl unload "$PLIST_PATH" 2>/dev/null || true

# Remove LaunchAgent
echo "Removing LaunchAgent..."
rm -f "$PLIST_PATH"

# Remove installation directory
echo "Removing installation directory..."
sudo rm -rf $INSTALL_DIR

echo ""
echo "Uninstallation completed!"
