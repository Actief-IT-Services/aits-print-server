#!/bin/bash
# AITS Print Server - macOS Installer
# Version: 1.0.0

set -e

INSTALL_DIR="/usr/local/aits-print-server"
PLIST_NAME="com.aits.print-server"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "========================================="
echo "AITS Print Server - macOS Installer"
echo "========================================="
echo ""

# Check for Homebrew
check_homebrew() {
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    echo "✓ Homebrew available"
}

# Install dependencies
install_dependencies() {
    echo "Installing dependencies..."
    
    # Install Python if not present
    if ! command -v python3 &> /dev/null; then
        brew install python@3.11
    fi
    
    echo "✓ Dependencies installed"
}

# Install print server
install_server() {
    echo "Installing AITS Print Server..."
    
    # Create installation directory
    sudo mkdir -p $INSTALL_DIR
    
    # Copy files
    sudo cp -r ../server.py ../requirements.txt ../config.yaml.example $INSTALL_DIR/
    sudo cp -r ../templates $INSTALL_DIR/ 2>/dev/null || true
    
    # Create config if not exists
    if [ ! -f "$INSTALL_DIR/config.yaml" ]; then
        sudo cp $INSTALL_DIR/config.yaml.example $INSTALL_DIR/config.yaml
    fi
    
    # Create virtual environment
    cd $INSTALL_DIR
    sudo python3 -m venv venv
    sudo venv/bin/pip install --upgrade pip
    sudo venv/bin/pip install -r requirements.txt
    
    # Set permissions
    sudo chown -R $USER:staff $INSTALL_DIR
    sudo chmod 755 $INSTALL_DIR
    
    echo "✓ Server installed to $INSTALL_DIR"
}

# Create LaunchAgent
create_launch_agent() {
    echo "Creating LaunchAgent..."
    
    mkdir -p "$HOME/Library/LaunchAgents"
    
    cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${INSTALL_DIR}/venv/bin/python3</string>
        <string>${INSTALL_DIR}/server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${INSTALL_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${INSTALL_DIR}/server.log</string>
    <key>StandardErrorPath</key>
    <string>${INSTALL_DIR}/server.error.log</string>
</dict>
</plist>
EOF

    # Load the LaunchAgent
    launchctl load "$PLIST_PATH"
    
    echo "✓ LaunchAgent created and loaded"
}

# Main installation
main() {
    check_homebrew
    install_dependencies
    install_server
    create_launch_agent
    
    echo ""
    echo "========================================="
    echo "Installation completed successfully!"
    echo "========================================="
    echo ""
    echo "Configuration file: $INSTALL_DIR/config.yaml"
    echo ""
    echo "To stop the service:"
    echo "  launchctl unload $PLIST_PATH"
    echo ""
    echo "To start the service:"
    echo "  launchctl load $PLIST_PATH"
    echo ""
    echo "To check if running:"
    echo "  launchctl list | grep aits"
    echo ""
    echo "To view logs:"
    echo "  tail -f $INSTALL_DIR/server.log"
    echo "  tail -f $INSTALL_DIR/server.error.log"
    echo ""
    echo "Server is now available at: http://localhost:8888"
    echo ""
}

main
