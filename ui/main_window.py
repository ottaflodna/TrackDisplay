"""
Main PyQt5 window for tracklog management
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QLabel, QLineEdit, QSpinBox, QColorDialog,
                             QGroupBox, QFormLayout, QMessageBox, QDockWidget,
                             QComboBox, QCheckBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QColor
from typing import List, Optional
import os
from models.track import Track


class TrackListItem(QWidget):
    """Custom widget for track list item with editable properties"""
    
    properties_changed = pyqtSignal()
    remove_requested = pyqtSignal(object)
    
    def __init__(self, track: Track, parent=None):
        super().__init__(parent)
        self.track = track
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for track item"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Color display (non-clickable)
        self.color_label = QLabel()
        self.color_label.setFixedSize(30, 30)
        self.color_label.setStyleSheet(f"background-color: {self.track.color or '#FF0000'}; border: 2px solid #666; border-radius: 3px;")
        layout.addWidget(self.color_label)
        
        # Name input
        self.name_input = QLineEdit(self.track.name)
        self.name_input.textChanged.connect(self.update_name)
        layout.addWidget(self.name_input, stretch=3)
        
        # Line width spinner
        width_label = QLabel("Width:")
        layout.addWidget(width_label)
        
        self.width_spinner = QSpinBox()
        self.width_spinner.setMinimum(1)
        self.width_spinner.setMaximum(10)
        self.width_spinner.setValue(getattr(self.track, 'line_width', 3))
        self.width_spinner.valueChanged.connect(self.update_width)
        layout.addWidget(self.width_spinner)
        
        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(30, 30)
        remove_btn.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold;")
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        layout.addWidget(remove_btn)
        
        self.setLayout(layout)
    
    def update_name(self, name: str):
        """Update track name"""
        self.track.name = name
        self.properties_changed.emit()
    
    def update_width(self, width: int):
        """Update line width"""
        self.track.line_width = width
        self.properties_changed.emit()


class MainWindow(QMainWindow):
    """Main window for GPS tracklog viewer"""
    
    def __init__(self):
        super().__init__()
        self.tracks: List[Track] = []
        self.current_map_file: Optional[str] = None
        
        # Map properties
        self.base_map = "Opentopomap"
        self.track_color_mode = "Plain"
        self.show_start_stop = True  # Default: show start/stop markers
        
        self.setup_ui()
        self.initialize_empty_map()
        
    def setup_ui(self):
        """Setup the main window UI"""
        self.setWindowTitle("GPS Tracklog Viewer")
        self.setMinimumSize(1000, 700)
        
        # Create central widget for map
        self.setup_map_central_widget()
        
        # Create dock widgets
        self.setup_tracks_dock()
        self.setup_map_properties_dock()
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def setup_tracks_dock(self):
        """Setup the tracks management dock widget"""
        # Create dock widget
        tracks_dock = QDockWidget("Active Tracklogs", self)
        tracks_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        
        # Create tracks widget
        tracks_widget = QWidget()
        tracks_layout = QVBoxLayout()
        tracks_widget.setLayout(tracks_layout)
        
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
        tracks_layout.addWidget(self.track_list)
        
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
        
        update_btn = QPushButton("Update Map")
        update_btn.setStyleSheet("padding: 8px; font-size: 12px; background-color: #4CAF50; color: white; font-weight: bold;")
        update_btn.clicked.connect(self.update_map)
        button_layout.addWidget(update_btn)
        
        tracks_layout.addLayout(button_layout)
        
        # Set widget to dock
        tracks_dock.setWidget(tracks_widget)
        
        # Add dock to main window (default: left side)
        self.addDockWidget(Qt.LeftDockWidgetArea, tracks_dock)
        
        # Store reference for positioning other docks
        self.tracks_dock = tracks_dock
    
    def setup_map_properties_dock(self):
        """Setup the map properties dock widget"""
        # Create dock widget
        properties_dock = QDockWidget("Map Properties", self)
        properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        
        # Create properties widget
        properties_widget = QWidget()
        properties_layout = QFormLayout()
        properties_widget.setLayout(properties_layout)
        
        # Base map selector
        self.base_map_combo = QComboBox()
        self.base_map_combo.addItems(["Opentopomap"])
        self.base_map_combo.setCurrentText(self.base_map)
        self.base_map_combo.currentTextChanged.connect(self.on_base_map_changed)
        properties_layout.addRow("Base map:", self.base_map_combo)
        
        # Track color mode selector
        self.track_color_combo = QComboBox()
        self.track_color_combo.addItems(["Plain"])
        self.track_color_combo.setCurrentText(self.track_color_mode)
        self.track_color_combo.currentTextChanged.connect(self.on_track_color_changed)
        properties_layout.addRow("Track color:", self.track_color_combo)
        
        # Show start/stop checkbox
        self.show_start_stop_checkbox = QCheckBox()
        self.show_start_stop_checkbox.setChecked(self.show_start_stop)
        self.show_start_stop_checkbox.stateChanged.connect(self.on_show_start_stop_changed)
        properties_layout.addRow("Show start and stop:", self.show_start_stop_checkbox)
        
        # Set widget to dock
        properties_dock.setWidget(properties_widget)
        
        # Add dock to main window on left side, below tracks dock
        self.addDockWidget(Qt.LeftDockWidgetArea, properties_dock)
        self.splitDockWidget(self.tracks_dock, properties_dock, Qt.Vertical)
    
    def on_base_map_changed(self, value: str):
        """Handle base map selection change"""
        self.base_map = value
        self.statusBar().showMessage(f"Base map set to: {value}")
    
    def on_track_color_changed(self, value: str):
        """Handle track color mode change"""
        self.track_color_mode = value
        self.statusBar().showMessage(f"Track color mode set to: {value}")
    
    def on_show_start_stop_changed(self, state: int):
        """Handle show start/stop checkbox change"""
        self.show_start_stop = (state == Qt.Checked)
        self.statusBar().showMessage(f"Start/stop markers: {'On' if self.show_start_stop else 'Off'}")
        # Auto-update map when option changes
        if self.tracks:
            self.update_map()
    
    def setup_map_central_widget(self):
        """Setup the map display as central widget"""
        central_widget = QWidget()
        map_layout = QVBoxLayout()
        central_widget.setLayout(map_layout)
        
        # Web view for map
        self.map_view = QWebEngineView()
        map_layout.addWidget(self.map_view)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Map")
        refresh_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        refresh_btn.clicked.connect(self.refresh_map)
        map_layout.addWidget(refresh_btn)
        
        # Set as central widget
        self.setCentralWidget(central_widget)
    
    def add_tracks(self):
        """Add new tracks via file selection"""
        from ui.file_selector import FileSelector
        from parsers.gpx_parser import GPXParser
        from parsers.igc_parser import IGCParser
        
        selector = FileSelector()
        file_paths = selector.select_files()
        
        if not file_paths:
            return
        
        gpx_parser = GPXParser()
        igc_parser = IGCParser()
        added_count = 0
        
        for file_path in file_paths:
            try:
                if file_path.lower().endswith('.gpx'):
                    track = gpx_parser.parse(file_path)
                elif file_path.lower().endswith('.igc'):
                    track = igc_parser.parse(file_path)
                else:
                    continue
                
                if track:
                    # Assign fixed color from cycler based on current track count
                    from viewer.map_viewer import MapViewer
                    track.color = MapViewer.COLORS[len(self.tracks) % len(MapViewer.COLORS)]
                    
                    # Set default line width
                    if not hasattr(track, 'line_width'):
                        track.line_width = 3
                    
                    self.tracks.append(track)
                    self.add_track_to_list(track)
                    added_count += 1
                    
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error loading {file_path}:\n{str(e)}")
        
        if added_count > 0:
            self.statusBar().showMessage(f"Added {added_count} track(s). Total: {len(self.tracks)}")
            # Auto-update map
            self.update_map()
        else:
            self.statusBar().showMessage("No tracks added")
    
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
            
            self.statusBar().showMessage(f"Removed track. Total: {len(self.tracks)}")
            # Auto-update map
            if self.tracks:
                self.update_map()
            else:
                self.initialize_empty_map()
    
    def load_map_in_view(self, map_file: str):
        """Load the map HTML file in the web view"""
        if os.path.exists(map_file):
            url = QUrl.fromLocalFile(os.path.abspath(map_file))
            self.map_view.setUrl(url)
    
    def refresh_map(self):
        """Refresh the current map"""
        if self.current_map_file:
            self.load_map_in_view(self.current_map_file)
            self.statusBar().showMessage("Map refreshed", 2000)
        else:
            self.update_map()
    
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
            self.statusBar().showMessage("All tracks cleared")
            # Reset map to Lausanne
            self.initialize_empty_map()
    
    def on_track_properties_changed(self):
        """Handle track property changes"""
        self.statusBar().showMessage("Track properties updated. Updating map...")
        self.update_map()
    
    def initialize_empty_map(self):
        """Initialize an empty map centered on Lausanne"""
        import folium
        
        # Lausanne coordinates
        lausanne_coords = [46.5197, 6.6323]
        
        # Create empty map
        m = folium.Map(
            location=lausanne_coords,
            zoom_start=9,
            tiles='OpenTopoMap',
            attr='Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap'
        )
        
        # Save map
        map_file = os.path.abspath('track_map.html')
        m.save(map_file)
        self.current_map_file = map_file
        
        # Load in view
        self.load_map_in_view(map_file)
    
    def update_map(self):
        """Update the map with current tracks"""
        try:
            from viewer.map_viewer import MapViewer
            import folium
            
            self.statusBar().showMessage("Updating map...")
            
            if not self.tracks:
                # No tracks - show empty Lausanne map
                self.initialize_empty_map()
                self.statusBar().showMessage("Map reset to Lausanne (no tracks)")
            else:
                # Generate map with tracks
                viewer = MapViewer()
                map_file = viewer.create_map(self.tracks, show_start_stop=self.show_start_stop)
                self.current_map_file = map_file
                
                # Load map in web view and force reload to bypass cache
                self.load_map_in_view(map_file)
                self.map_view.reload()
                
                self.statusBar().showMessage(f"Map updated with {len(self.tracks)} track(s)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error updating map:\n{str(e)}")
            self.statusBar().showMessage("Error updating map")
    
    def set_initial_tracks(self, tracks: List[Track]):
        """Set initial tracks (called from main.py)"""
        self.tracks = tracks.copy()
        self.track_list.clear()
        
        for track in self.tracks:
            # Ensure color and line_width are set
            if not track.color:
                from viewer.map_viewer import MapViewer
                idx = self.tracks.index(track)
                track.color = MapViewer.COLORS[idx % len(MapViewer.COLORS)]
            
            if not hasattr(track, 'line_width'):
                track.line_width = 3
            
            self.add_track_to_list(track)
        
        # Auto-update map with initial tracks
        if self.tracks:
            self.update_map()
        
        self.statusBar().showMessage(f"Loaded {len(self.tracks)} track(s)")
