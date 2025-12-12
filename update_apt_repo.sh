#!/bin/bash
# Update APT Repository
# Run this script after building a new .deb package to update the repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APT_REPO_DIR="$SCRIPT_DIR/apt-repo"

# Find the latest .deb file
LATEST_DEB=$(ls -t "$SCRIPT_DIR"/*.deb 2>/dev/null | head -1)

if [ -z "$LATEST_DEB" ]; then
    echo "Error: No .deb file found in $SCRIPT_DIR"
    exit 1
fi

echo "=========================================="
echo "Updating APT Repository"
echo "=========================================="
echo "Latest package: $(basename $LATEST_DEB)"

# Create apt-repo directory if it doesn't exist
mkdir -p "$APT_REPO_DIR"

# Copy the latest .deb to apt-repo
cp "$LATEST_DEB" "$APT_REPO_DIR/"

# Remove old versions (keep only 2 latest)
cd "$APT_REPO_DIR"
ls -t *.deb 2>/dev/null | tail -n +3 | xargs -r rm -f

# Generate Packages file
echo "Generating Packages index..."
dpkg-scanpackages --multiversion . > Packages
gzip -k -f Packages

# Update Release file with date
cat > Release << EOF
Origin: Actief IT Services
Label: AITS Print Server
Suite: stable
Codename: stable
Architectures: all
Components: main
Description: AITS Print Server APT Repository
Date: $(date -R)
EOF

echo ""
echo "=========================================="
echo "✓ APT Repository updated!"
echo "=========================================="
echo ""
echo "Contents:"
ls -la "$APT_REPO_DIR"
echo ""
echo "Don't forget to commit and push to update the public repository:"
echo "  git add -A && git commit -m 'Update APT repository' && git push"
echo "  git subtree push --prefix=aits_print_server public main"
