#!/bin/bash
# AITS Print Server - Linux Installer
# Version: 1.0.0

set -e

INSTALL_DIR="/opt/aits-print-server"
SERVICE_NAME="aits-print-server"
USER="aits-print"

echo "========================================="
echo "AITS Print Server - Linux Installer"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: Please run as root (use sudo)"
    exit 1
fi

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
else
    echo "Error: Cannot detect Linux distribution"
    exit 1
fi

echo "Detected OS: $OS $OS_VERSION"
echo ""

# Install dependencies based on distribution
install_dependencies() {
    echo "Installing dependencies..."
    
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y python3 python3-pip python3-venv cups libcups2-dev
            ;;
        fedora|rhel|centos)
            dnf install -y python3 python3-pip cups cups-devel
            ;;
        arch)
            pacman -Sy --noconfirm python python-pip cups
            ;;
        *)
            echo "Warning: Unsupported distribution. Please install Python 3.8+, pip, and CUPS manually."
            read -p "Continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
    
    echo "✓ Dependencies installed"
}

# Create system user
create_user() {
    echo "Creating system user..."
    
    if id "$USER" &>/dev/null; then
        echo "User $USER already exists"
    else
        useradd -r -s /bin/false -d $INSTALL_DIR $USER
        echo "✓ User created: $USER"
    fi
}

# Install print server
install_server() {
    echo "Installing AITS Print Server..."
    
    # Create installation directory
    mkdir -p $INSTALL_DIR
    
    # Copy files
    cp -r ../server.py ../requirements.txt ../config.yaml.example $INSTALL_DIR/
    cp -r ../templates $INSTALL_DIR/ 2>/dev/null || true
    
    # Create config if not exists
    if [ ! -f "$INSTALL_DIR/config.yaml" ]; then
        cp $INSTALL_DIR/config.yaml.example $INSTALL_DIR/config.yaml
    fi
    
    # Create virtual environment
    cd $INSTALL_DIR
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    deactivate
    
    # Set permissions
    chown -R $USER:$USER $INSTALL_DIR
    chmod 755 $INSTALL_DIR
    
    echo "✓ Server installed to $INSTALL_DIR"
}

# Create systemd service
create_service() {
    echo "Creating systemd service..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=AITS Print Server
After=network.target cups.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}.service
    
    echo "✓ Systemd service created"
}

# Main installation
main() {
    install_dependencies
    create_user
    install_server
    create_service
    
    echo ""
    echo "========================================="
    echo "Installation completed successfully!"
    echo "========================================="
    echo ""
    echo "Configuration file: $INSTALL_DIR/config.yaml"
    echo ""
    echo "To start the service:"
    echo "  sudo systemctl start $SERVICE_NAME"
    echo ""
    echo "To check status:"
    echo "  sudo systemctl status $SERVICE_NAME"
    echo ""
    echo "To view logs:"
    echo "  sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "To enable autostart on boot:"
    echo "  sudo systemctl enable $SERVICE_NAME"
    echo ""
    echo "Server will be available at: http://localhost:8888"
    echo ""
}

main
