#!/bin/bash
# =============================================================================
# AITS Print Server - Linux/Raspberry Pi Installer
# =============================================================================
# This script installs the AITS Print Server on Linux systems.
# Tested on: Ubuntu 20.04+, Debian 11+, Raspberry Pi OS
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/laurensdecroix/odoo-dev/main/aits_print_server/install_linux.sh | sudo bash
#   
#   Or download and run:
#   chmod +x install_linux.sh
#   sudo ./install_linux.sh
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/aits-print-server"
SERVICE_NAME="aits-print-server"
SERVICE_USER="aits-print"
CONFIG_DIR="/etc/aits-print-server"
LOG_DIR="/var/log/aits-print-server"
GITHUB_REPO="https://raw.githubusercontent.com/laurensdecroix/odoo-dev/main/aits_print_server"

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║           AITS Print Server - Linux Installer                 ║"
    echo "║                  by Actief IT Services                        ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print message functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root (use sudo)"
    fi
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/debian_version ]; then
        OS="debian"
        VERSION=$(cat /etc/debian_version)
    else
        OS="unknown"
    fi
    
    info "Detected OS: $OS $VERSION"
    
    case $OS in
        ubuntu|debian|raspbian)
            PKG_MANAGER="apt-get"
            PKG_UPDATE="apt-get update"
            ;;
        fedora|centos|rhel)
            PKG_MANAGER="dnf"
            PKG_UPDATE="dnf check-update || true"
            ;;
        arch)
            PKG_MANAGER="pacman"
            PKG_UPDATE="pacman -Sy"
            ;;
        *)
            warning "Unknown OS, assuming Debian-based"
            PKG_MANAGER="apt-get"
            PKG_UPDATE="apt-get update"
            ;;
    esac
}

# Install system dependencies
install_dependencies() {
    info "Installing system dependencies..."
    
    $PKG_UPDATE
    
    case $PKG_MANAGER in
        apt-get)
            apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                cups \
                libcups2-dev \
                curl \
                git
            ;;
        dnf)
            dnf install -y \
                python3 \
                python3-pip \
                cups \
                cups-devel \
                curl \
                git
            ;;
        pacman)
            pacman -S --noconfirm \
                python \
                python-pip \
                cups \
                curl \
                git
            ;;
    esac
    
    success "System dependencies installed"
}

# Create service user
create_user() {
    info "Creating service user..."
    
    if id "$SERVICE_USER" &>/dev/null; then
        info "User $SERVICE_USER already exists"
    else
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        success "Created user: $SERVICE_USER"
    fi
    
    # Add user to lpadmin group for CUPS access
    usermod -a -G lpadmin "$SERVICE_USER" 2>/dev/null || true
}

# Create directories
create_directories() {
    info "Creating directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    
    success "Directories created"
}

# Download print server files
download_files() {
    info "Downloading print server files..."
    
    cd "$INSTALL_DIR"
    
    # Download main files
    FILES=(
        "server.py"
        "printer_manager.py"
        "job_queue.py"
        "auth.py"
        "odoo_client.py"
        "requirements.txt"
        "config.yaml.example"
    )
    
    for file in "${FILES[@]}"; do
        info "  Downloading $file..."
        curl -sSL "$GITHUB_REPO/$file" -o "$file" || warning "Could not download $file"
    done
    
    # Download static files
    mkdir -p static
    curl -sSL "$GITHUB_REPO/static/icon.ico" -o static/icon.ico 2>/dev/null || true
    
    success "Files downloaded"
}

# Setup Python virtual environment
setup_venv() {
    info "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    python3 -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install pycups for Linux
    pip install pycups
    
    deactivate
    
    success "Python environment configured"
}

# Create configuration file
create_config() {
    info "Creating configuration file..."
    
    if [ -f "$CONFIG_DIR/config.yaml" ]; then
        warning "Configuration file already exists, skipping..."
        return
    fi
    
    # Get Odoo URL from user
    echo ""
    echo -e "${YELLOW}Please enter your Odoo configuration:${NC}"
    echo ""
    
    read -p "Odoo URL (e.g., https://mycompany.odoo.com): " ODOO_URL
    read -p "Database name: " ODOO_DB
    read -p "API Key: " ODOO_API_KEY
    read -p "Server name (e.g., Warehouse Printer): " SERVER_NAME
    
    # Generate server config
    cat > "$CONFIG_DIR/config.yaml" << EOF
# AITS Print Server Configuration
# Generated by installer on $(date)

server:
  host: "0.0.0.0"
  port: 8888
  name: "${SERVER_NAME:-Linux Print Server}"

odoo:
  url: "${ODOO_URL}"
  database: "${ODOO_DB}"
  api_key: "${ODOO_API_KEY}"

polling:
  interval: 5
  batch_size: 10

logging:
  level: "INFO"
  file: "${LOG_DIR}/print_server.log"
  max_size: 10485760
  backup_count: 5

security:
  ssl_enabled: false
  # ssl_cert: "/etc/aits-print-server/cert.pem"
  # ssl_key: "/etc/aits-print-server/key.pem"
EOF
    
    # Create symlink to config
    ln -sf "$CONFIG_DIR/config.yaml" "$INSTALL_DIR/config.yaml"
    
    success "Configuration file created at $CONFIG_DIR/config.yaml"
}

# Create systemd service
create_service() {
    info "Creating systemd service..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=AITS Print Server
Documentation=https://github.com/laurensdecroix/odoo-dev
After=network.target cups.service
Wants=cups.service

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/server.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${LOG_DIR} ${CONFIG_DIR}
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    success "Systemd service created"
}

# Set permissions
set_permissions() {
    info "Setting permissions..."
    
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    
    chmod 750 "$INSTALL_DIR"
    chmod 750 "$CONFIG_DIR"
    chmod 640 "$CONFIG_DIR/config.yaml" 2>/dev/null || true
    chmod 750 "$LOG_DIR"
    
    success "Permissions set"
}

# Enable and start service
start_service() {
    info "Starting print server service..."
    
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"
    
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        success "Print server is running!"
    else
        warning "Service may not have started correctly. Check logs with:"
        echo "  journalctl -u $SERVICE_NAME -f"
    fi
}

# Print completion message
print_completion() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         AITS Print Server Installation Complete!              ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Installation Summary:${NC}"
    echo "  • Install directory: $INSTALL_DIR"
    echo "  • Configuration: $CONFIG_DIR/config.yaml"
    echo "  • Log files: $LOG_DIR/"
    echo "  • Service name: $SERVICE_NAME"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  • Check status:    sudo systemctl status $SERVICE_NAME"
    echo "  • View logs:       sudo journalctl -u $SERVICE_NAME -f"
    echo "  • Restart:         sudo systemctl restart $SERVICE_NAME"
    echo "  • Stop:            sudo systemctl stop $SERVICE_NAME"
    echo "  • Edit config:     sudo nano $CONFIG_DIR/config.yaml"
    echo ""
    echo -e "${BLUE}Web Interface:${NC}"
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    echo "  • http://${LOCAL_IP}:8888"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Ensure CUPS is configured with your printers"
    echo "  2. The server will auto-register with Odoo"
    echo "  3. Check Odoo → Direct Print → Printers to see discovered printers"
    echo ""
}

# Uninstall function
uninstall() {
    echo -e "${YELLOW}Uninstalling AITS Print Server...${NC}"
    
    # Stop and disable service
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    rm -f /etc/systemd/system/${SERVICE_NAME}.service
    systemctl daemon-reload
    
    # Remove files
    rm -rf "$INSTALL_DIR"
    rm -rf "$LOG_DIR"
    
    # Keep config for potential reinstall
    echo -e "${YELLOW}Configuration kept at $CONFIG_DIR${NC}"
    echo "To remove completely: sudo rm -rf $CONFIG_DIR"
    
    # Remove user
    userdel "$SERVICE_USER" 2>/dev/null || true
    
    success "Uninstallation complete"
}

# Main installation
main() {
    print_banner
    
    # Handle uninstall flag
    if [ "$1" = "--uninstall" ] || [ "$1" = "-u" ]; then
        check_root
        uninstall
        exit 0
    fi
    
    check_root
    detect_os
    install_dependencies
    create_user
    create_directories
    download_files
    setup_venv
    create_config
    create_service
    set_permissions
    start_service
    print_completion
}

# Run main function
main "$@"
