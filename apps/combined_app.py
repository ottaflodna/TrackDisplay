"""
Combined Application - GPS Track Combined Viewer
Displays both map and curve viewers in a single window with shared track management
"""

from typing import List, Optional
import os
import json
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QDockWidget,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, QEventLoop, QTimer

from models.track import Track
from ui.track_manager_widget import TrackManagerWidget
from viewer.map_viewer import MapViewer
from viewer.curve_viewer import CurveViewer
from viewer.power_curve_viewer import PowerCurveViewer


class CombinedWindow(QMainWindow):
    """Main window combining map and curve viewers with shared track management"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPS Tracklog Combined Viewer")
        self.setMinimumSize(1200, 800)

        # Data
        self.tracks: List[Track] = []
        self.view_state: dict = {}

        # Viewers
        self.map_viewer = MapViewer()
        self.curve_viewer = CurveViewer()
        self.power_curve_viewer = PowerCurveViewer()

        # Map properties
        self.base_map = "OpenTopoMap"
        self.track_color_mode = "Plain"
        self.colormap_map = "Jet (Blue-Green-Yellow-Red)"
        self.show_start_stop = False
        self.show_legend_map = False
        self.show_zoom_controls = False
        self.color_min_map: Optional[float] = None
        self.color_max_map: Optional[float] = None

        # Curve properties
        self.x_data = "Distance (km)"
        self.y_data = "Altitude (m)"
        self.color_data = "None"
        self.colormap_curve = "viridis"
        self.color_min_curve: Optional[float] = None
        self.color_max_curve: Optional[float] = None
        self.show_legend_curve = True
        
        # Power curve properties
        self.show_legend_power = True

        # UI setup
        self._setup_ui()
        # Defer empty view initialization until window is shown
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._initialize_empty_views)
        self.statusBar().showMessage("Ready")

    def _setup_ui(self):
        """Setup central widget (stacked viewers) and docks for track manager and properties"""
        # Map tab
        # Curve tab
        # Track manager dock

    def _setup_ui(self):
        from PyQt5.QtWidgets import QDockWidget

        # Enable dock nesting to allow docks to fill the entire window
        self.setDockNestingEnabled(True)

        # Map viewer dock (will occupy center area)
        self.map_view = QWebEngineView()
        self.map_dock = QDockWidget("Map Viewer", self)
        self.map_dock.setWidget(self.map_view)
        self.map_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.RightDockWidgetArea, self.map_dock)

        # Curve viewer dock
        self.curve_container = QWidget()
        self.curve_container.setMinimumSize(400, 300)  # Set minimum size to prevent negative dimensions
        self.curve_layout = QVBoxLayout()
        self.curve_container.setLayout(self.curve_layout)
        self.curve_dock = QDockWidget("Curve Viewer", self)
        self.curve_dock.setWidget(self.curve_container)
        self.curve_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.RightDockWidgetArea, self.curve_dock)
        
        # Power curve viewer dock
        self.power_curve_container = QWidget()
        self.power_curve_container.setMinimumSize(400, 300)
        self.power_curve_layout = QVBoxLayout()
        self.power_curve_container.setLayout(self.power_curve_layout)
        self.power_curve_dock = QDockWidget("Power Curve", self)
        self.power_curve_dock.setWidget(self.power_curve_container)
        self.power_curve_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.RightDockWidgetArea, self.power_curve_dock)

        # Tabify viewers in the main area
        self.tabifyDockWidget(self.map_dock, self.curve_dock)
        self.tabifyDockWidget(self.curve_dock, self.power_curve_dock)
        self.map_dock.raise_()  # Show map tab by default

        # Track manager dock (left)
        self.track_manager = TrackManagerWidget("Active Tracklogs", self)
        self.track_manager.tracks_changed.connect(self.on_tracks_changed)
        self.track_manager.track_properties_changed.connect(self.on_track_properties_changed)
        self.track_manager.map_screenshot_requested.connect(self.on_map_screenshot_requested)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.track_manager)

        # Map properties dock (bottom left, below track manager)
        self.map_properties_dock = QDockWidget("Map Properties", self)
        self.map_properties_dock.setWidget(self._create_map_properties_widget())
        self.map_properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.map_properties_dock)

        # Curve properties dock (bottom left, tabbed with map properties)
        self.curve_properties_dock = QDockWidget("Curve Properties", self)
        self.curve_properties_dock.setWidget(self._create_curve_properties_widget())
        self.curve_properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.curve_properties_dock)

        # Tabify the two properties docks together
        self.tabifyDockWidget(self.map_properties_dock, self.curve_properties_dock)
        self.map_properties_dock.raise_()  # Show map properties by default

        # Split track manager and properties vertically
        self.splitDockWidget(self.track_manager, self.map_properties_dock, Qt.Vertical)

    # Remove _setup_properties_dock
    # (No reference to properties_dock here)

    def _create_map_properties_widget(self):
        properties_widget = QWidget()
        properties_layout = QFormLayout()
        properties_widget.setLayout(properties_layout)

        # Base map settings
        map_group = QGroupBox("Base map settings")
        map_layout = QFormLayout()
        map_group.setLayout(map_layout)
        properties_layout.addRow(map_group)

        self.base_map_combo = QComboBox()
        self.base_map_combo.addItems(MapViewer.AVAILABLE_BASE_MAPS)
        self.base_map_combo.setCurrentText(self.base_map)
        self.base_map_combo.currentTextChanged.connect(self.on_base_map_changed)
        map_layout.addRow("Base map:", self.base_map_combo)

        # Track color settings
        track_group = QGroupBox("Track color settings")
        track_layout = QFormLayout()
        track_group.setLayout(track_layout)
        properties_layout.addRow(track_group)

        self.track_color_combo = QComboBox()
        self.track_color_combo.addItems(MapViewer.COLOR_MODES)
        self.track_color_combo.setCurrentText(self.track_color_mode)
        self.track_color_combo.currentTextChanged.connect(self.on_track_color_changed)
        track_layout.addRow("Track color:", self.track_color_combo)

        self.colormap_combo_map = QComboBox()
        self.colormap_combo_map.addItems(MapViewer.AVAILABLE_COLORMAPS)
        self.colormap_combo_map.setCurrentText(self.colormap_map)
        self.colormap_combo_map.setEnabled(False)  # Enabled when color mode != Plain
        self.colormap_combo_map.currentTextChanged.connect(self.on_colormap_map_changed)
        track_layout.addRow("Colormap:", self.colormap_combo_map)

        self.color_min_spinbox_map = QDoubleSpinBox()
        self.color_min_spinbox_map.setRange(-999999, 999999)
        self.color_min_spinbox_map.setDecimals(2)
        self.color_min_spinbox_map.setEnabled(False)
        self.color_min_spinbox_map.editingFinished.connect(self.on_color_min_map_changed)
        track_layout.addRow("Color min:", self.color_min_spinbox_map)

        self.color_max_spinbox_map = QDoubleSpinBox()
        self.color_max_spinbox_map.setRange(-999999, 999999)
        self.color_max_spinbox_map.setDecimals(2)
        self.color_max_spinbox_map.setEnabled(False)
        self.color_max_spinbox_map.editingFinished.connect(self.on_color_max_map_changed)
        track_layout.addRow("Color max:", self.color_max_spinbox_map)

        # Display settings
        display_group = QGroupBox("Viewer display settings")
        display_layout = QFormLayout()
        display_group.setLayout(display_layout)
        properties_layout.addRow(display_group)

        self.show_start_stop_checkbox = QCheckBox()
        self.show_start_stop_checkbox.setChecked(self.show_start_stop)
        self.show_start_stop_checkbox.stateChanged.connect(self.on_show_start_stop_changed)
        display_layout.addRow("Show start and stop:", self.show_start_stop_checkbox)

        self.show_legend_checkbox_map = QCheckBox()
        self.show_legend_checkbox_map.setChecked(self.show_legend_map)
        self.show_legend_checkbox_map.stateChanged.connect(self.on_show_legend_map_changed)
        display_layout.addRow("Show legend:", self.show_legend_checkbox_map)

        self.show_zoom_controls_checkbox = QCheckBox()
        self.show_zoom_controls_checkbox.setChecked(self.show_zoom_controls)
        self.show_zoom_controls_checkbox.stateChanged.connect(self.on_show_zoom_controls_changed)
        display_layout.addRow("Show zoom controls:", self.show_zoom_controls_checkbox)

        return properties_widget

    def _create_curve_properties_widget(self):
        properties_widget = QWidget()
        properties_layout = QFormLayout()
        properties_widget.setLayout(properties_layout)

        # Data selection
        data_group = QGroupBox("Data Selection")
        data_layout = QFormLayout()
        data_group.setLayout(data_layout)
        properties_layout.addRow(data_group)

        self.x_data_combo = QComboBox()
        self.x_data_combo.addItems(CurveViewer.AVAILABLE_DATA)
        self.x_data_combo.setCurrentText(self.x_data)
        self.x_data_combo.currentTextChanged.connect(self.on_x_data_changed)
        data_layout.addRow("X-Axis:", self.x_data_combo)

        self.y_data_combo = QComboBox()
        self.y_data_combo.addItems(CurveViewer.AVAILABLE_DATA)
        self.y_data_combo.setCurrentText(self.y_data)
        self.y_data_combo.currentTextChanged.connect(self.on_y_data_changed)
        data_layout.addRow("Y-Axis:", self.y_data_combo)

        self.color_data_combo = QComboBox()
        self.color_data_combo.addItems(["None"] + CurveViewer.AVAILABLE_DATA)
        self.color_data_combo.setCurrentText(self.color_data)
        self.color_data_combo.currentTextChanged.connect(self.on_color_data_changed)
        data_layout.addRow("Color By:", self.color_data_combo)

        # Display settings
        display_group = QGroupBox("Display Settings")
        display_layout = QFormLayout()
        display_group.setLayout(display_layout)
        properties_layout.addRow(display_group)

        self.colormap_combo_curve = QComboBox()
        self.colormap_combo_curve.addItems(CurveViewer.AVAILABLE_COLORMAPS)
        self.colormap_combo_curve.setCurrentText(self.colormap_curve)
        self.colormap_combo_curve.setEnabled(False)  # until color data selected
        self.colormap_combo_curve.currentTextChanged.connect(self.on_colormap_curve_changed)
        display_layout.addRow("Colormap:", self.colormap_combo_curve)

        self.color_min_spinbox_curve = QDoubleSpinBox()
        self.color_min_spinbox_curve.setRange(-999999, 999999)
        self.color_min_spinbox_curve.setDecimals(2)
        self.color_min_spinbox_curve.setEnabled(False)
        self.color_min_spinbox_curve.editingFinished.connect(self.on_color_min_curve_changed)
        display_layout.addRow("Color min:", self.color_min_spinbox_curve)

        self.color_max_spinbox_curve = QDoubleSpinBox()
        self.color_max_spinbox_curve.setRange(-999999, 999999)
        self.color_max_spinbox_curve.setDecimals(2)
        self.color_max_spinbox_curve.setEnabled(False)
        self.color_max_spinbox_curve.editingFinished.connect(self.on_color_max_curve_changed)
        display_layout.addRow("Color max:", self.color_max_spinbox_curve)

        self.show_legend_checkbox_curve = QCheckBox()
        self.show_legend_checkbox_curve.setChecked(self.show_legend_curve)
        self.show_legend_checkbox_curve.stateChanged.connect(self.on_show_legend_curve_changed)
        display_layout.addRow("Show legend:", self.show_legend_checkbox_curve)

        return properties_widget
        properties_dock = QDockWidget("Map Properties", self)
        properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)

        properties_widget = QWidget()
        properties_layout = QFormLayout()
        properties_widget.setLayout(properties_layout)

        # Base map settings
        map_group = QGroupBox("Base map settings")
        map_layout = QFormLayout()
        map_group.setLayout(map_layout)
        properties_layout.addRow(map_group)

        self.base_map_combo = QComboBox()
        self.base_map_combo.addItems(MapViewer.AVAILABLE_BASE_MAPS)
        self.base_map_combo.setCurrentText(self.base_map)
        self.base_map_combo.currentTextChanged.connect(self.on_base_map_changed)
        map_layout.addRow("Base map:", self.base_map_combo)

        # Track color settings
        track_group = QGroupBox("Track color settings")
        track_layout = QFormLayout()
        track_group.setLayout(track_layout)
        properties_layout.addRow(track_group)

        self.track_color_combo = QComboBox()
        self.track_color_combo.addItems(MapViewer.COLOR_MODES)
        self.track_color_combo.setCurrentText(self.track_color_mode)
        self.track_color_combo.currentTextChanged.connect(self.on_track_color_changed)
        track_layout.addRow("Track color:", self.track_color_combo)

        self.colormap_combo_map = QComboBox()
        self.colormap_combo_map.addItems(MapViewer.AVAILABLE_COLORMAPS)
        self.colormap_combo_map.setCurrentText(self.colormap_map)
        self.colormap_combo_map.setEnabled(False)  # Enabled when color mode != Plain
        self.colormap_combo_map.currentTextChanged.connect(self.on_colormap_map_changed)
        track_layout.addRow("Colormap:", self.colormap_combo_map)

        self.color_min_spinbox_map = QDoubleSpinBox()
        self.color_min_spinbox_map.setRange(-999999, 999999)
        self.color_min_spinbox_map.setDecimals(2)
        self.color_min_spinbox_map.setEnabled(False)
        self.color_min_spinbox_map.editingFinished.connect(self.on_color_min_map_changed)
        track_layout.addRow("Color min:", self.color_min_spinbox_map)

        self.color_max_spinbox_map = QDoubleSpinBox()
        self.color_max_spinbox_map.setRange(-999999, 999999)
        self.color_max_spinbox_map.setDecimals(2)
        self.color_max_spinbox_map.setEnabled(False)
        self.color_max_spinbox_map.editingFinished.connect(self.on_color_max_map_changed)
        track_layout.addRow("Color max:", self.color_max_spinbox_map)

        # Display settings
        display_group = QGroupBox("Viewer display settings")
        display_layout = QFormLayout()
        display_group.setLayout(display_layout)
        properties_layout.addRow(display_group)

        self.show_start_stop_checkbox = QCheckBox()
        self.show_start_stop_checkbox.setChecked(self.show_start_stop)
        self.show_start_stop_checkbox.stateChanged.connect(self.on_show_start_stop_changed)
        display_layout.addRow("Show start and stop:", self.show_start_stop_checkbox)

        self.show_legend_checkbox_map = QCheckBox()
        self.show_legend_checkbox_map.setChecked(self.show_legend_map)
        self.show_legend_checkbox_map.stateChanged.connect(self.on_show_legend_map_changed)
        display_layout.addRow("Show legend:", self.show_legend_checkbox_map)

        self.show_zoom_controls_checkbox = QCheckBox()
        self.show_zoom_controls_checkbox.setChecked(self.show_zoom_controls)
        self.show_zoom_controls_checkbox.stateChanged.connect(self.on_show_zoom_controls_changed)
        display_layout.addRow("Show zoom controls:", self.show_zoom_controls_checkbox)

        properties_dock.setWidget(properties_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, properties_dock)
        self.splitDockWidget(self.track_manager, properties_dock, Qt.Vertical)

    def _setup_curve_properties_dock(self):
        properties_dock = QDockWidget("Curve Properties", self)
        properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)

        properties_widget = QWidget()
        properties_layout = QFormLayout()
        properties_widget.setLayout(properties_layout)

        # Data selection
        data_group = QGroupBox("Data Selection")
        data_layout = QFormLayout()
        data_group.setLayout(data_layout)
        properties_layout.addRow(data_group)

        self.x_data_combo = QComboBox()
        self.x_data_combo.addItems(CurveViewer.AVAILABLE_DATA)
        self.x_data_combo.setCurrentText(self.x_data)
        self.x_data_combo.currentTextChanged.connect(self.on_x_data_changed)
        data_layout.addRow("X-Axis:", self.x_data_combo)

        self.y_data_combo = QComboBox()
        self.y_data_combo.addItems(CurveViewer.AVAILABLE_DATA)
        self.y_data_combo.setCurrentText(self.y_data)
        self.y_data_combo.currentTextChanged.connect(self.on_y_data_changed)
        data_layout.addRow("Y-Axis:", self.y_data_combo)

        self.color_data_combo = QComboBox()
        self.color_data_combo.addItems(["None"] + CurveViewer.AVAILABLE_DATA)
        self.color_data_combo.setCurrentText(self.color_data)
        self.color_data_combo.currentTextChanged.connect(self.on_color_data_changed)
        data_layout.addRow("Color By:", self.color_data_combo)

        # Display settings
        display_group = QGroupBox("Display Settings")
        display_layout = QFormLayout()
        display_group.setLayout(display_layout)
        properties_layout.addRow(display_group)

        self.colormap_combo_curve = QComboBox()
        self.colormap_combo_curve.addItems(CurveViewer.AVAILABLE_COLORMAPS)
        self.colormap_combo_curve.setCurrentText(self.colormap_curve)
        self.colormap_combo_curve.setEnabled(False)  # until color data selected
        self.colormap_combo_curve.currentTextChanged.connect(self.on_colormap_curve_changed)
        display_layout.addRow("Colormap:", self.colormap_combo_curve)

        self.color_min_spinbox_curve = QDoubleSpinBox()
        self.color_min_spinbox_curve.setRange(-999999, 999999)
        self.color_min_spinbox_curve.setDecimals(2)
        self.color_min_spinbox_curve.setEnabled(False)
        self.color_min_spinbox_curve.editingFinished.connect(self.on_color_min_curve_changed)
        display_layout.addRow("Color min:", self.color_min_spinbox_curve)

        self.color_max_spinbox_curve = QDoubleSpinBox()
        self.color_max_spinbox_curve.setRange(-999999, 999999)
        self.color_max_spinbox_curve.setDecimals(2)
        self.color_max_spinbox_curve.setEnabled(False)
        self.color_max_spinbox_curve.editingFinished.connect(self.on_color_max_curve_changed)
        display_layout.addRow("Color max:", self.color_max_spinbox_curve)

        self.show_legend_checkbox_curve = QCheckBox()
        self.show_legend_checkbox_curve.setChecked(self.show_legend_curve)
        self.show_legend_checkbox_curve.stateChanged.connect(self.on_show_legend_curve_changed)
        display_layout.addRow("Show legend:", self.show_legend_checkbox_curve)

        properties_dock.setWidget(properties_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, properties_dock)
        self.splitDockWidget(self.track_manager, properties_dock, Qt.Vertical)


    def _initialize_empty_views(self):
        # Empty map centered on Lausanne
        lausanne_coords = [46.5197, 6.6323]
        m = self.map_viewer._create_base_map(lausanne_coords, self.base_map, zoom_control=self.show_zoom_controls)
        map_file = os.path.abspath('track_map.html')
        m.save(map_file)
        self.map_view.setUrl(QUrl.fromLocalFile(map_file))

        # Empty curve view
        canvas, toolbar = self.curve_viewer.create_view([], None)
        self._set_curve_content(canvas, toolbar)
        
        # Empty power curve view
        power_canvas, power_toolbar = self.power_curve_viewer.create_view([], None)
        self._set_power_curve_content(power_canvas, power_toolbar)

    def _set_curve_content(self, canvas, toolbar):
        # Clear and set new content
        while self.curve_layout.count():
            item = self.curve_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if toolbar:
            self.curve_layout.addWidget(toolbar)
        if canvas:
            self.curve_layout.addWidget(canvas)
    
    def _set_power_curve_content(self, canvas, toolbar):
        # Clear and set new content
        while self.power_curve_layout.count():
            item = self.power_curve_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if toolbar:
            self.power_curve_layout.addWidget(toolbar)
        if canvas:
            self.power_curve_layout.addWidget(canvas)

    # Track and property change handlers
    def on_tracks_changed(self, tracks: List[Track]):
        self.tracks = tracks
        if not self.tracks:
            self._initialize_empty_views()
            self.view_state = {}
        else:
            self._regenerate_views(fit_bounds=True)

    def on_track_properties_changed(self):
        # Preserve map view when only properties change
        self._regenerate_views(fit_bounds=False)
    
    def on_map_screenshot_requested(self):
        """Handle map screenshot request"""
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
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", "Failed to save screenshot")

    # Map property handlers
    def on_base_map_changed(self, value: str):
        self.base_map = value
        self.statusBar().showMessage(f"Base map set to: {value}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)
        else:
            self._initialize_empty_views()

    def on_track_color_changed(self, value: str):
        self.track_color_mode = value
        # Enable colormap + range when not Plain
        if value != "Plain" and self.tracks:
            computed_min, computed_max = self.map_viewer._get_value_range(self.tracks, value)
            self.color_min_map = computed_min
            self.color_max_map = computed_max
            # Update spinboxes
            self.color_min_spinbox_map.blockSignals(True)
            self.color_max_spinbox_map.blockSignals(True)
            self.color_min_spinbox_map.setValue(computed_min)
            self.color_max_spinbox_map.setValue(computed_max)
            self.color_min_spinbox_map.blockSignals(False)
            self.color_max_spinbox_map.blockSignals(False)
            self.color_min_spinbox_map.setEnabled(True)
            self.color_max_spinbox_map.setEnabled(True)
            self.colormap_combo_map.setEnabled(True)
        else:
            self.color_min_map = None
            self.color_max_map = None
            self.color_min_spinbox_map.setEnabled(False)
            self.color_max_spinbox_map.setEnabled(False)
            self.colormap_combo_map.setEnabled(False)
        self.statusBar().showMessage(f"Track color mode set to: {value}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_colormap_map_changed(self, value: str):
        self.colormap_map = value
        self.statusBar().showMessage(f"Colormap set to: {value}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_color_min_map_changed(self):
        self.color_min_map = self.color_min_spinbox_map.value()
        self.statusBar().showMessage(f"Color min set to: {self.color_min_map:.2f}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_color_max_map_changed(self):
        self.color_max_map = self.color_max_spinbox_map.value()
        self.statusBar().showMessage(f"Color max set to: {self.color_max_map:.2f}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_show_start_stop_changed(self, state: int):
        self.show_start_stop = (state == Qt.Checked)
        self.statusBar().showMessage(f"Start/stop markers: {'On' if self.show_start_stop else 'Off'}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_show_legend_map_changed(self, state: int):
        self.show_legend_map = (state == Qt.Checked)
        self.statusBar().showMessage(f"Legend (map): {'On' if self.show_legend_map else 'Off'}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_show_zoom_controls_changed(self, state: int):
        self.show_zoom_controls = (state == Qt.Checked)
        self.statusBar().showMessage(f"Zoom controls: {'On' if self.show_zoom_controls else 'Off'}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)
        else:
            self._initialize_empty_views()

    # Curve property handlers
    def on_x_data_changed(self, value: str):
        self.x_data = value
        self.statusBar().showMessage(f"X-axis set to: {value}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_y_data_changed(self, value: str):
        self.y_data = value
        self.statusBar().showMessage(f"Y-axis set to: {value}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_color_data_changed(self, value: str):
        self.color_data = value
        if value != "None" and self.tracks:
            # Compute range from data
            color_values = []
            for track in self.tracks:
                values = self.curve_viewer._get_data_values(track, value)
                color_values.extend([v for v in values if v is not None])
            if color_values:
                self.color_min_curve = min(color_values)
                self.color_max_curve = max(color_values)
                self.color_min_spinbox_curve.blockSignals(True)
                self.color_max_spinbox_curve.blockSignals(True)
                self.color_min_spinbox_curve.setValue(self.color_min_curve)
                self.color_max_spinbox_curve.setValue(self.color_max_curve)
                self.color_min_spinbox_curve.blockSignals(False)
                self.color_max_spinbox_curve.blockSignals(False)
                self.colormap_combo_curve.setEnabled(True)
                self.color_min_spinbox_curve.setEnabled(True)
                self.color_max_spinbox_curve.setEnabled(True)
        else:
            self.color_min_curve = None
            self.color_max_curve = None
            self.colormap_combo_curve.setEnabled(False)
            self.color_min_spinbox_curve.setEnabled(False)
            self.color_max_spinbox_curve.setEnabled(False)
        self.statusBar().showMessage(f"Color by: {value}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_colormap_curve_changed(self, value: str):
        self.colormap_curve = value
        self.statusBar().showMessage(f"Colormap (curve) set to: {value}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_color_min_curve_changed(self):
        self.color_min_curve = self.color_min_spinbox_curve.value()
        self.statusBar().showMessage(f"Color min (curve) set to: {self.color_min_curve:.2f}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_color_max_curve_changed(self):
        self.color_max_curve = self.color_max_spinbox_curve.value()
        self.statusBar().showMessage(f"Color max (curve) set to: {self.color_max_curve:.2f}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    def on_show_legend_curve_changed(self, state: int):
        self.show_legend_curve = (state == Qt.Checked)
        self.statusBar().showMessage(f"Legend (curve): {'On' if self.show_legend_curve else 'Off'}")
        if self.tracks:
            self._regenerate_views(fit_bounds=False)

    # View regeneration
    def _regenerate_views(self, fit_bounds: bool = False):
        # Capture current view before regenerating (if not fitting bounds)
        if not fit_bounds and self.tracks:
            self._capture_current_view()
        
        # Map view generation
        map_options = {
            'base_map': self.base_map,
            'color_mode': self.track_color_mode,
            'colormap': self.colormap_map,
            'show_start_stop': self.show_start_stop,
            'show_legend': self.show_legend_map,
            'zoom_control': self.show_zoom_controls,
            'color_min': self.color_min_map,
            'color_max': self.color_max_map,
            'fit_bounds': fit_bounds
        }
        # Preserve center/zoom if not fitting bounds
        if not fit_bounds and self.view_state:
            map_options.update(self.view_state)
        map_file, new_view_state = self.map_viewer.create_view(
            self.tracks,
            output_file='track_map.html',
            **map_options
        )
        self.view_state = new_view_state
        self.map_view.setUrl(QUrl.fromLocalFile(map_file))

        # Curve view generation
        curve_options = {
            'x_data': self.x_data,
            'y_data': self.y_data,
            'color_data': self.color_data,
            'colormap': self.colormap_curve,
            'color_min': self.color_min_curve,
            'color_max': self.color_max_curve,
            'show_legend': self.show_legend_curve
        }
        canvas, toolbar = self.curve_viewer.create_view(self.tracks, curve_options)
        self._set_curve_content(canvas, toolbar)
        
        # Power curve view generation
        power_curve_options = {
            'show_legend': self.show_legend_power
        }
        power_canvas, power_toolbar = self.power_curve_viewer.create_view(self.tracks, power_curve_options)
        self._set_power_curve_content(power_canvas, power_toolbar)
    
    def _capture_current_view(self):
        """Capture the current map center and zoom from the browser"""
        # JavaScript to extract Leaflet map's current view
        js_code = """
        (function() {
            try {
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
        QTimer.singleShot(200, loop.quit)
        loop.exec_()
        
        # Parse result and update view settings
        if result_holder['result']:
            try:
                view_data = json.loads(result_holder['result'])
                self.view_state = {
                    'current_center': [view_data['lat'], view_data['lng']],
                    'current_zoom': int(view_data['zoom'])
                }
            except:
                pass
