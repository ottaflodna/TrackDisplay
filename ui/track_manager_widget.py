"""
Reusable track management dock widget
Can be used by any application that needs track loading/management
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QDockWidget,
                             QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import List, Optional
import os

from models.track import Track
from ui.track_list_item import TrackListItem
from ui.file_selector import FileSelector
from parsers.gpx_parser import GPXParser
from parsers.igc_parser import IGCParser
from parsers.tcx_parser import TCXParser


class TrackManagerWidget(QDockWidget):
    """
    Reusable dock widget for managing GPS tracklogs
    
    Signals:
        tracks_changed: Emitted when tracks are added, removed, or cleared
        track_properties_changed: Emitted when a track's properties are modified
        map_screenshot_requested: Emitted when user wants to capture map screenshot
    """
    
    tracks_changed = pyqtSignal(list)  # List of all current tracks
    track_properties_changed = pyqtSignal()
    map_screenshot_requested = pyqtSignal()
    
    # Color palette for tracks (can be overridden by applications)
    COLORS = [
        '#457B9D', '#2A9D8F', '#F4A261', '#E76F51', '#264653',
        '#A8DADC', '#F77F00', '#06FFA5', '#9B59B6', '#FF6B9D',
        '#3498DB', '#F39C12', '#1ABC9C', '#E74C3C', '#95E1D3',
        '#F38181', '#AA96DA', '#FCBAD3', '#A8E6CF', '#E63946',
    ]
    
    def __init__(self, title: str = "Active Tracklogs", parent=None):
        super().__init__(title, parent)
        self.tracks: List[Track] = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI for the dock widget"""
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        
        # Create main widget
        main_widget = QWidget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Track list widget
        self.track_list = QListWidget()
        self.track_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
                padding: 5px;
            }
        """)
        layout.addWidget(self.track_list)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Tracks")
        add_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        add_btn.clicked.connect(self.add_tracks)
        button_layout.addWidget(add_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        clear_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        # Screenshot button
        screenshot_layout = QHBoxLayout()
        
        screenshot_btn = QPushButton("Map Screenshot")
        screenshot_btn.setStyleSheet("padding: 8px; font-size: 12px; background-color: #457B9D; color: white;")
        screenshot_btn.clicked.connect(self.request_map_screenshot)
        screenshot_layout.addWidget(screenshot_btn)
        
        layout.addLayout(screenshot_layout)
        
        self.setWidget(main_widget)
    
    def add_tracks(self):
        """Add new tracks via file selection"""
        selector = FileSelector()
        file_paths = selector.select_files()
        
        if not file_paths:
            return
        
        # Show loading message
        if self.parent():
            self.parent().statusBar().showMessage(f"Loading {len(file_paths)} track(s)...")
            QApplication.processEvents()
        
        gpx_parser = GPXParser()
        igc_parser = IGCParser()
        tcx_parser = TCXParser()
        added_count = 0
        
        for i, file_path in enumerate(file_paths):
            # Update progress message
            if self.parent():
                self.parent().statusBar().showMessage(
                    f"Loading track {i+1}/{len(file_paths)}: {os.path.basename(file_path)}"
                )
                QApplication.processEvents()
            
            try:
                if file_path.lower().endswith('.gpx'):
                    track = gpx_parser.parse(file_path)
                elif file_path.lower().endswith('.igc'):
                    track = igc_parser.parse(file_path)
                elif file_path.lower().endswith('.tcx'):
                    track = tcx_parser.parse(file_path)
                else:
                    continue
                
                if track:
                    # Assign fixed color from palette
                    track.color = self.COLORS[len(self.tracks) % len(self.COLORS)]
                    
                    # Set default line width
                    if not hasattr(track, 'line_width'):
                        track.line_width = 5
                    
                    self.tracks.append(track)
                    self.add_track_to_list(track)
                    added_count += 1
                    
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Error loading {file_path}:\n{str(e)}"
                )
        
        if added_count > 0:
            if self.parent():
                self.parent().statusBar().showMessage(
                    f"Added {added_count} track(s). Total: {len(self.tracks)}"
                )
            # Emit signal with updated track list
            self.tracks_changed.emit(self.tracks)
        else:
            if self.parent():
                self.parent().statusBar().showMessage("No tracks added")
    
    def add_track_to_list(self, track: Track):
        """Add a track to the list widget"""
        item = QListWidgetItem(self.track_list)
        track_widget = TrackListItem(track)
        track_widget.properties_changed.connect(self.on_track_properties_changed)
        track_widget.remove_requested.connect(self.remove_track)
        
        item.setSizeHint(track_widget.sizeHint())
        self.track_list.addItem(item)
        self.track_list.setItemWidget(item, track_widget)
    
    def remove_track(self, track_widget: TrackListItem):
        """Remove a track from the list"""
        reply = QMessageBox.question(
            self,
            "Remove Track",
            f"Remove track '{track_widget.track.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Find and remove the track
            self.tracks.remove(track_widget.track)
            
            # Remove from list widget
            for i in range(self.track_list.count()):
                item = self.track_list.item(i)
                widget = self.track_list.itemWidget(item)
                if widget == track_widget:
                    self.track_list.takeItem(i)
                    break
            
            if self.parent():
                self.parent().statusBar().showMessage(
                    f"Removed track. Total: {len(self.tracks)}"
                )
            
            # Emit signal with updated track list
            self.tracks_changed.emit(self.tracks)
    
    def clear_all(self):
        """Clear all tracks"""
        if not self.tracks:
            return
        
        reply = QMessageBox.question(
            self,
            "Clear All",
            f"Remove all {len(self.tracks)} track(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tracks.clear()
            self.track_list.clear()
            
            if self.parent():
                self.parent().statusBar().showMessage("All tracks cleared")
            
            # Emit signal with empty track list
            self.tracks_changed.emit(self.tracks)
    
    def on_track_properties_changed(self):
        """Handle track property changes"""
        if self.parent():
            self.parent().statusBar().showMessage("Track properties updated")
        self.track_properties_changed.emit()
    
    def request_map_screenshot(self):
        """Request a screenshot of the map viewer"""
        if self.parent():
            self.parent().statusBar().showMessage("Capturing map screenshot...")
        self.map_screenshot_requested.emit()
    
    def get_tracks(self) -> List[Track]:
        """Get the current list of tracks"""
        return self.tracks.copy()
    
    def set_tracks(self, tracks: List[Track]):
        """Set the track list (useful for initialization)"""
        self.tracks = tracks.copy()
        self.track_list.clear()
        
        for track in self.tracks:
            # Ensure color and line_width are set
            if not track.color:
                idx = self.tracks.index(track)
                track.color = self.COLORS[idx % len(self.COLORS)]
            
            if not hasattr(track, 'line_width'):
                track.line_width = 5
            
            self.add_track_to_list(track)
        
        # Emit signal
        if self.tracks:
            self.tracks_changed.emit(self.tracks)
