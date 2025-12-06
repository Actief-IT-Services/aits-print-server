#!/bin/bash
# Build script for macOS application
# Creates a .app bundle and optionally a .dmg installer

echo "========================================="
echo "AITS Print Server - macOS Build Script"
echo "========================================="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    exit 1
fi

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo "Installing build dependencies..."
pip3 install pyinstaller pillow pystray flask flask-cors pyyaml

echo ""
echo "Building macOS application..."
cd "$(dirname "$0")"
pyinstaller --clean build_macos.spec

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "Build completed successfully!"
    echo "========================================="
    echo ""
    echo "Application location: dist/AITS Print Server.app"
    echo ""
    
    # Ask if user wants to create DMG
    read -p "Create DMG installer? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating DMG..."
        
        # Check for create-dmg
        if ! command -v create-dmg &> /dev/null; then
            echo "Installing create-dmg..."
            brew install create-dmg
        fi
        
        # Create DMG
        create-dmg \
            --volname "AITS Print Server" \
            --volicon "../static/icon.icns" \
            --window-pos 200 120 \
            --window-size 600 400 \
            --icon-size 100 \
            --icon "AITS Print Server.app" 175 120 \
            --hide-extension "AITS Print Server.app" \
            --app-drop-link 425 120 \
            "dist/AITS_Print_Server_Installer.dmg" \
            "dist/AITS Print Server.app"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "DMG created: dist/AITS_Print_Server_Installer.dmg"
        fi
    fi
    
    echo ""
    echo "You can now distribute the .app or .dmg file."
    echo "Users can drag the app to Applications folder."
    echo ""
else
    echo ""
    echo "Build failed! Check the errors above."
    echo ""
    exit 1
fi
