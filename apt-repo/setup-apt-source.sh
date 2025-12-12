#!/bin/bash
# Setup AITS Print Server APT Repository
# Run this once on the print server to enable automatic updates

set -e

echo "Setting up AITS Print Server APT repository..."

# Add the repository source
echo "deb [trusted=yes] https://raw.githubusercontent.com/Actief-IT-Services/aits-print-server/main/apt-repo ./" | sudo tee /etc/apt/sources.list.d/aits-print-server.list

# Update package lists
echo "Updating package lists..."
sudo apt update

echo ""
echo "=========================================="
echo "✓ APT repository configured successfully!"
echo "=========================================="
echo ""
echo "You can now install/update the print server with:"
echo "  sudo apt install aits-print-server"
echo ""
echo "To check for updates:"
echo "  sudo apt update && sudo apt upgrade"
echo ""
