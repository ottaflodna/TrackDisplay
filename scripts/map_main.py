#!/usr/bin/env python3
"""
GPS Tracklog Map Viewer - Refactored Application Entry Point
Uses the new refactored architecture with reusable components
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


def main():
    """Main application entry point for the map viewer"""
    # Required for QtWebEngineWidgets - MUST be set before any imports that use it
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    # Import after setting the attribute
    from apps.map_app import MapWindow
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    # Create and show main window
    window = MapWindow()
    window.showMaximized()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
