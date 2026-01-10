#!/bin/bash

# TrackDisplay - Dependency Installation Script for Ubuntu
# This script installs required Python modules via apt

set -e  # Exit on any error

echo "================================================"
echo "TrackDisplay Dependency Installation"
echo "================================================"
echo ""

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install Python modules via apt
echo ""
echo "Installing Python modules via apt..."
sudo apt-get install -y \
    python3-folium \
    python3-gpxpy \
    python3-pyqt5 \
    python3-pyqt5.qtwebengine

echo ""
echo "================================================"
echo "Installation completed successfully!"
echo "================================================"
echo ""
echo "You can now run the application with:"
echo "  python3 main.py"
echo ""
