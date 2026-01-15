#!/usr/bin/env python3
"""
GPS Tracklog Combined Viewer - Application Entry Point
Displays both map and curve viewers in a single window
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


def main():
    """Main application entry point for the combined viewer"""
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    from apps.combined_app import CombinedWindow

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = CombinedWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
