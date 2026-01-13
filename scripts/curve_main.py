#!/usr/bin/env python3
"""
GPS Tracklog Curve Viewer - Application Entry Point
Demonstrates the new curve viewer using refactored architecture
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


def main():
    """Main application entry point for the curve viewer"""
    # Required for QtWebEngineWidgets - MUST be set before any imports that use it
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    # Import after setting the attribute
    from apps.curve_app import CurveWindow
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    # Create and show main window
    window = CurveWindow()
    window.showMaximized()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
