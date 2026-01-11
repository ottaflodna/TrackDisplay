"""
Main PyQt5 window for tracklog management
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QLabel, QLineEdit, QSpinBox, QColorDialog,
                             QGroupBox, QFormLayout, QMessageBox, QDockWidget,
                             QComboBox, QCheckBox, QApplication, QDoubleSpinBox)
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
        self.base_map = "OpenTopoMap"
        self.track_color_mode = "Plain"
        self.show_start_stop = False  # Default: show start/stop markers
        self.show_legend = False  # Default: don't show legend
        self.show_zoom_controls = False  # Default: show zoom controls
        self.color_min: Optional[float] = None  # Min value for color scale
        self.color_max: Optional[float] = None  # Max value for color scale
        
        # Track map state for preservation
        self.map_center: Optional[List[float]] = None
        self.map_zoom: Optional[int] = None
        
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
        
        tracks_layout.addLayout(button_layout)
        
        # Screenshot button
        screenshot_btn = QPushButton("Screenshot")
        screenshot_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        screenshot_btn.clicked.connect(self.take_screenshot)
        tracks_layout.addWidget(screenshot_btn)
        
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
        from viewer.map_viewer import MapViewer
        self.base_map_combo = QComboBox()
        self.base_map_combo.addItems(MapViewer.AVAILABLE_BASE_MAPS)
        self.base_map_combo.setCurrentText(self.base_map)
        self.base_map_combo.currentTextChanged.connect(self.on_base_map_changed)

        map_groupbox = QGroupBox()
        map_groupbox.setTitle("Base map settings")
        map_layout = QFormLayout()
        map_groupbox.setLayout(map_layout)
        map_layout.addRow("Base map:", self.base_map_combo)
        properties_layout.addRow(map_groupbox)

        # Add a separator
        track_groupbox = QGroupBox()
        track_groupbox.setTitle("Track color settings")
        track_layout = QFormLayout()
        track_groupbox.setLayout(track_layout)
        properties_layout.addRow(track_groupbox)

        # Track color mode selector
        self.track_color_combo = QComboBox()
        self.track_color_combo.addItems([
            "Plain",
            "Altitude (m)",
            "Vertical Speed (m/s)",
            "Vertical Speed (m/h)",
            "Power (W)",
            "Heart Rate (bpm)",
            "Cadence (rpm)",
            'Speed (km/h)',
            'Temperature (°C)'
        ])
        self.track_color_combo.setCurrentText(self.track_color_mode)
        self.track_color_combo.currentTextChanged.connect(self.on_track_color_changed)
        track_layout.addRow("Track color:", self.track_color_combo)
               
        # Color scale min/max inputs
        self.color_min_spinbox = QDoubleSpinBox()
        self.color_min_spinbox.setRange(-999999, 999999)
        self.color_min_spinbox.setDecimals(2)
        self.color_min_spinbox.setEnabled(False)
        self.color_min_spinbox.editingFinished.connect(self.on_color_min_changed)
        track_layout.addRow("Color min:", self.color_min_spinbox)
        
        self.color_max_spinbox = QDoubleSpinBox()
        self.color_max_spinbox.setRange(-999999, 999999)
        self.color_max_spinbox.setDecimals(2)
        self.color_max_spinbox.setEnabled(False)
        self.color_max_spinbox.editingFinished.connect(self.on_color_max_changed)
        track_layout.addRow("Color max:", self.color_max_spinbox)
        
        # Add a separator
        display_groupbox = QGroupBox()
        display_groupbox.setTitle("Viewer display settings")
        display_layout = QFormLayout()
        display_groupbox.setLayout(display_layout)
        properties_layout.addRow(display_groupbox)

        # Show start/stop checkbox
        self.show_start_stop_checkbox = QCheckBox()
        self.show_start_stop_checkbox.setChecked(self.show_start_stop)
        self.show_start_stop_checkbox.stateChanged.connect(self.on_show_start_stop_changed)
        display_layout.addRow("Show start and stop:", self.show_start_stop_checkbox)
        
        # Show legend checkbox
        self.show_legend_checkbox = QCheckBox()
        self.show_legend_checkbox.setChecked(self.show_legend)
        self.show_legend_checkbox.stateChanged.connect(self.on_show_legend_changed)
        display_layout.addRow("Show legend:", self.show_legend_checkbox)
        
        # Show zoom controls checkbox
        self.show_zoom_controls_checkbox = QCheckBox()
        self.show_zoom_controls_checkbox.setChecked(self.show_zoom_controls)
        self.show_zoom_controls_checkbox.stateChanged.connect(self.on_show_zoom_controls_changed)
        display_layout.addRow("Show zoom controls:", self.show_zoom_controls_checkbox)


        # Set widget to dock
        properties_dock.setWidget(properties_widget)
        
        # Add dock to main window on left side, below tracks dock
        self.addDockWidget(Qt.LeftDockWidgetArea, properties_dock)
        self.splitDockWidget(self.tracks_dock, properties_dock, Qt.Vertical)
    
    def on_base_map_changed(self, value: str):
        """Handle base map selection change"""
        self.base_map = value
        self.statusBar().showMessage(f"Base map set to: {value}")
        # Auto-regenerate map with new base layer (preserve zoom/center)
        if self.tracks:
            self.regenerate_map(fit_bounds=False)
        else:
            self.initialize_empty_map()
    
    def on_track_color_changed(self, value: str):
        """Handle track color mode change"""
        self.track_color_mode = value
        
        # Compute min/max values for the selected color mode
        if value != "Plain" and self.tracks:
            from viewer.map_viewer import MapViewer
            viewer = MapViewer()
            computed_min, computed_max = viewer._get_value_range(self.tracks, value)
            self.color_min = computed_min
            self.color_max = computed_max
            
            # Update spinboxes
            self.color_min_spinbox.blockSignals(True)
            self.color_max_spinbox.blockSignals(True)
            self.color_min_spinbox.setValue(computed_min)
            self.color_max_spinbox.setValue(computed_max)
            self.color_min_spinbox.blockSignals(False)
            self.color_max_spinbox.blockSignals(False)
            
            # Enable spinboxes for manual adjustment
            self.color_min_spinbox.setEnabled(True)
            self.color_max_spinbox.setEnabled(True)
        else:
            # Disable spinboxes for Plain mode
            self.color_min = None
            self.color_max = None
            self.color_min_spinbox.setEnabled(False)
            self.color_max_spinbox.setEnabled(False)
        
        self.statusBar().showMessage(f"Track color mode set to: {value}")
        # Auto-regenerate map when option changes (preserve zoom/center)
        if self.tracks:
            self.regenerate_map(fit_bounds=False)
    
    def on_color_min_changed(self):
        """Handle color min value change"""
        self.color_min = self.color_min_spinbox.value()
        self.statusBar().showMessage(f"Color min set to: {self.color_min:.2f}")
        if self.tracks:
            self.regenerate_map(fit_bounds=False)
    
    def on_color_max_changed(self):
        """Handle color max value change"""
        self.color_max = self.color_max_spinbox.value()
        self.statusBar().showMessage(f"Color max set to: {self.color_max:.2f}")
        if self.tracks:
            self.regenerate_map(fit_bounds=False)
    
    def on_show_start_stop_changed(self, state: int):
        """Handle show start/stop checkbox change"""
        self.show_start_stop = (state == Qt.Checked)
        self.statusBar().showMessage(f"Start/stop markers: {'On' if self.show_start_stop else 'Off'}")
        # Auto-regenerate map when option changes (preserve zoom/center)
        if self.tracks:
            self.regenerate_map(fit_bounds=False)
    
    def on_show_legend_changed(self, state: int):
        """Handle show legend checkbox change"""
        self.show_legend = (state == Qt.Checked)
        self.statusBar().showMessage(f"Legend: {'On' if self.show_legend else 'Off'}")
        # Auto-regenerate map when option changes (preserve zoom/center)
        if self.tracks:
            self.regenerate_map(fit_bounds=False)
    
    def on_show_zoom_controls_changed(self, state: int):
        """Handle show zoom controls checkbox change"""
        self.show_zoom_controls = (state == Qt.Checked)
        self.statusBar().showMessage(f"Zoom controls: {'On' if self.show_zoom_controls else 'Off'}")
        # Auto-regenerate map when option changes (preserve zoom/center)
        if self.tracks:
            self.regenerate_map(fit_bounds=False)
        else:
            self.initialize_empty_map()
    
    def take_screenshot(self):
        """Capture a screenshot of the map view"""
        from PyQt5.QtWidgets import QFileDialog
        from PyQt5.QtCore import QTimer
        from datetime import datetime
        
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"map_screenshot_{timestamp}.png"
        
        # Ask user where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            default_filename,
            "PNG Images (*.png);;JPEG Images (*.jpg);;All Files (*)"
        )
        
        if file_path:
            # Capture the screenshot
            pixmap = self.map_view.grab()
            
            # Save the screenshot
            if pixmap.save(file_path):
                self.statusBar().showMessage(f"Screenshot saved: {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save screenshot")
    
    def setup_map_central_widget(self):
        """Setup the map display as central widget"""
        central_widget = QWidget()
        map_layout = QVBoxLayout()
        central_widget.setLayout(map_layout)
        
        # Web view for map
        self.map_view = QWebEngineView()
        map_layout.addWidget(self.map_view)
        
        # Set as central widget
        self.setCentralWidget(central_widget)
    
    def add_tracks(self):
        """Add new tracks via file selection"""
        from ui.file_selector import FileSelector
        from parsers.gpx_parser import GPXParser
        from parsers.igc_parser import IGCParser
        from parsers.tcx_parser import TCXParser
        
        selector = FileSelector()
        file_paths = selector.select_files()
        
        if not file_paths:
            return
        
        # Show loading message
        self.statusBar().showMessage(f"Loading {len(file_paths)} track(s)...")
        QApplication.processEvents()  # Force UI update
        
        gpx_parser = GPXParser()
        igc_parser = IGCParser()
        tcx_parser = TCXParser()
        added_count = 0
        
        for i, file_path in enumerate(file_paths):
            # Update progress message
            self.statusBar().showMessage(f"Loading track {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
            QApplication.processEvents()  # Force UI update
            
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
            self.statusBar().showMessage(f"Added {added_count} track(s). Total: {len(self.tracks)}. Generating map...")
            QApplication.processEvents()  # Force UI update
            # Auto-regenerate map with zoom recalculation
            self.regenerate_map(fit_bounds=True)
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
            # Auto-regenerate map with zoom recalculation
            self.regenerate_map(fit_bounds=True)
    
    def load_map_in_view(self, map_file: str):
        """Load the map HTML file in the web view"""
        if os.path.exists(map_file):
            url = QUrl.fromLocalFile(os.path.abspath(map_file))
            self.map_view.setUrl(url)
            # Force reload to bypass cache
            self.map_view.reload()
    
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
        """Handle track property changes (name, color, width)"""
        self.statusBar().showMessage("Track properties updated. Regenerating map...")
        # Preserve zoom/center when only properties change
        self.regenerate_map(fit_bounds=False)
    
    def _capture_current_view(self):
        """Capture the current map center and zoom from the browser"""
        from PyQt5.QtCore import QEventLoop
        
        # JavaScript to extract Leaflet map's current view
        js_code = """
        (function() {
            try {
                // Find the Leaflet map object
                var map = null;
                for (var key in window) {
                    if (window[key] && window[key]._layers) {
                        map = window[key];
                        break;
                    }
                }
                if (map) {
                    var center = map.getCenter();
                    var zoom = map.getZoom();
                    return JSON.stringify({
                        lat: center.lat,
                        lng: center.lng,
                        zoom: zoom
                    });
                }
                return null;
            } catch(e) {
                return null;
            }
        })();
        """
        
        # Use event loop to wait for JavaScript result
        loop = QEventLoop()
        result_holder = {'result': None}
        
        def handle_result(result):
            result_holder['result'] = result
            loop.quit()
        
        # Execute JavaScript
        self.map_view.page().runJavaScript(js_code, handle_result)
        
        # Wait for result (max 200ms timeout)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(200, loop.quit)
        loop.exec_()
        
        # Parse result and update view settings
        if result_holder['result']:
            try:
                import json
                view_data = json.loads(result_holder['result'])
                self.map_center = [view_data['lat'], view_data['lng']]
                self.map_zoom = int(view_data['zoom'])
            except:
                pass  # Keep existing values if capture fails
    
    def initialize_empty_map(self):
        """Initialize an empty map centered on Lausanne"""
        import folium
        from viewer.map_viewer import MapViewer
        
        # Lausanne coordinates
        lausanne_coords = [46.5197, 6.6323]
        
        # Create map viewer instance
        viewer = MapViewer()
        
        # Create empty map with selected base layer
        m = viewer._create_base_map(lausanne_coords, self.base_map, zoom_control=self.show_zoom_controls)
        
        # Save map
        map_file = os.path.abspath('track_map.html')
        m.save(map_file)
        self.current_map_file = map_file
        
        # Load in view
        self.load_map_in_view(map_file)
    
    def regenerate_map(self, fit_bounds: bool = False):
        """Regenerate the map with current track data and settings
        
        Args:
            fit_bounds: If True, recalculates zoom to fit all tracks (used when adding tracks)
        """
        try:
            from viewer.map_viewer import MapViewer
            
            # Capture current view settings from the browser before regenerating
            if not fit_bounds and self.current_map_file and self.tracks:
                self._capture_current_view()
            
            self.statusBar().showMessage("Generating map...")
            
            if not self.tracks:
                # No tracks - show empty Lausanne map
                self.initialize_empty_map()
                self.map_center = None
                self.map_zoom = None
                self.statusBar().showMessage("Map reset (no tracks)")
            else:
                # Extract current map state if not fitting bounds and first time
                if not fit_bounds and self.map_center is None:
                    # First time - calculate from tracks
                    viewer = MapViewer()
                    self.map_center = viewer._calculate_center(self.tracks)
                    self.map_zoom = 13
                
                # Generate map with current tracks and settings
                viewer = MapViewer()
                
                # Pass current center/zoom if not fitting bounds
                kwargs = {
                    'show_start_stop': self.show_start_stop,
                    'base_map': self.base_map,
                    'fit_bounds': fit_bounds,
                    'color_mode': self.track_color_mode,
                    'show_legend': self.show_legend,
                    'color_min': self.color_min,
                    'color_max': self.color_max,
                    'zoom_control': self.show_zoom_controls
                }
                
                if not fit_bounds:
                    kwargs['current_center'] = self.map_center
                    kwargs['current_zoom'] = self.map_zoom
                
                # create_map returns (file_path, center, zoom)
                map_file, center, zoom = viewer.create_map(self.tracks, **kwargs)
                self.current_map_file = map_file
                
                # Always update stored center/zoom with the values actually used
                # This preserves the view for subsequent setting changes
                self.map_center = center
                self.map_zoom = zoom
                
                # Load map in web view
                self.load_map_in_view(map_file)
                
                zoom_msg = " (zoom adjusted)" if fit_bounds else " (view preserved)"
                self.statusBar().showMessage(f"Map generated with {len(self.tracks)} track(s){zoom_msg}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating map:\n{str(e)}")
            self.statusBar().showMessage("Error generating map")
    
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
        
        # Auto-regenerate map with initial tracks (with zoom fit)
        if self.tracks:
            self.regenerate_map(fit_bounds=True)
        
        self.statusBar().showMessage(f"Loaded {len(self.tracks)} track(s)")
