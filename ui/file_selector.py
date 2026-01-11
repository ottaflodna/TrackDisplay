"""
File selection dialog for choosing GPS track files
"""

import tkinter as tk
from tkinter import filedialog
from typing import List


class FileSelector:
    """Handle file selection dialog"""
    
    def select_files(self) -> List[str]:
        """
        Open file dialog to select multiple GPX/IGC/TCX files
        
        Returns:
            List of selected file paths
        """
        # Create hidden root window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Open file dialog
        file_paths = filedialog.askopenfilenames(
            title='Select GPS Track Files',
            filetypes=[
                ('GPS Track Files', '*.gpx *.igc *.tcx'),
                ('GPX Files', '*.gpx'),
                ('IGC Files', '*.igc'),
                ('TCX Files', '*.tcx'),
                ('All Files', '*.*')
            ]
        )
        
        root.destroy()
        
        return list(file_paths) if file_paths else []
