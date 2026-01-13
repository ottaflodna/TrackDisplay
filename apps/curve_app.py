"""
Curve Application - GPS Track Curve/Chart Viewer
Demonstrates reuse of base components for a different visualization type
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout,
                             QComboBox, QCheckBox, QFileDialog, QMessageBox, QPushButton,
                             QDoubleSpinBox)
from PyQt5.QtCore import Qt
from typing import List
import os
from datetime import datetime

from ui.base_window import BaseWindow
from viewer.base_viewer import BaseViewer
from viewer.curve_viewer import CurveViewer
from models.track import Track


class CurveWindow(BaseWindow):
    """Main window for GPS tracklog curve/chart viewer"""
    
    def __init__(self):
        # Initialize curve-specific properties before calling super().__init__()
        self.x_data = "Distance (km)"
        self.y_data = "Altitude (m)"
        self.color_data = "None"
        self.colormap = "viridis"
        self.color_min = None
        self.color_max = None
        self.show_legend = True
        self.canvas = None
        self.toolbar = None
        
        super().__init__()
        self.setWindowTitle("GPS Tracklog Curve Viewer")
        
        # Add screenshot button to track manager (after it's created)
        screenshot_btn = QPushButton("Screenshot")
        screenshot_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        screenshot_btn.clicked.connect(self.take_screenshot)
        self.track_manager.widget().layout().addWidget(screenshot_btn)
    
    def create_viewer(self) -> BaseViewer:
        """Create and return the curve viewer instance"""
        return CurveViewer()
    
    def setup_viewer_widget(self):
        """Setup the curve display as central widget"""
        central_widget = QWidget()
        self.curve_layout = QVBoxLayout()
        central_widget.setLayout(self.curve_layout)
        
        # Set as central widget
        self.setCentralWidget(central_widget)
    
    def setup_viewer_properties_dock(self):
        """Setup the curve properties dock widget"""
        from PyQt5.QtWidgets import QDockWidget
        
        # Create dock widget
        properties_dock = QDockWidget("Curve Properties", self)
        properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        
        # Create properties widget
        properties_widget = QWidget()
        properties_layout = QFormLayout()
        properties_widget.setLayout(properties_layout)
        
        # Data selection group
        data_groupbox = QGroupBox("Data Selection")
        data_layout = QFormLayout()
        data_groupbox.setLayout(data_layout)
        properties_layout.addRow(data_groupbox)
        
        # X-axis data selector
        self.x_data_combo = QComboBox()
        self.x_data_combo.addItems(CurveViewer.AVAILABLE_DATA)
        self.x_data_combo.setCurrentText(self.x_data)
        self.x_data_combo.currentTextChanged.connect(self.on_x_data_changed)
        data_layout.addRow("X-Axis:", self.x_data_combo)
        
        # Y-axis data selector
        self.y_data_combo = QComboBox()
        self.y_data_combo.addItems(CurveViewer.AVAILABLE_DATA)
        self.y_data_combo.setCurrentText(self.y_data)
        self.y_data_combo.currentTextChanged.connect(self.on_y_data_changed)
        data_layout.addRow("Y-Axis:", self.y_data_combo)
        
        # Color data selector
        self.color_data_combo = QComboBox()
        self.color_data_combo.addItems(['None'] + CurveViewer.AVAILABLE_DATA)
        self.color_data_combo.setCurrentText(self.color_data)
        self.color_data_combo.currentTextChanged.connect(self.on_color_data_changed)
        data_layout.addRow("Color By:", self.color_data_combo)
        
        # Display settings group
        display_groupbox = QGroupBox("Display Settings")
        display_layout = QFormLayout()
        display_groupbox.setLayout(display_layout)
        properties_layout.addRow(display_groupbox)
        
        # Colormap selector
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(CurveViewer.AVAILABLE_COLORMAPS)
        self.colormap_combo.setCurrentText(self.colormap)
        self.colormap_combo.setEnabled(False)  # Disabled until color data is selected
        self.colormap_combo.currentTextChanged.connect(self.on_colormap_changed)
        display_layout.addRow("Colormap:", self.colormap_combo)
        
        # Color scale min/max inputs
        self.color_min_spinbox = QDoubleSpinBox()
        self.color_min_spinbox.setRange(-999999, 999999)
        self.color_min_spinbox.setDecimals(2)
        self.color_min_spinbox.setEnabled(False)
        self.color_min_spinbox.editingFinished.connect(self.on_color_min_changed)
        display_layout.addRow("Color min:", self.color_min_spinbox)
        
        self.color_max_spinbox = QDoubleSpinBox()
        self.color_max_spinbox.setRange(-999999, 999999)
        self.color_max_spinbox.setDecimals(2)
        self.color_max_spinbox.setEnabled(False)
        self.color_max_spinbox.editingFinished.connect(self.on_color_max_changed)
        display_layout.addRow("Color max:", self.color_max_spinbox)
        
        # Show legend checkbox
        self.show_legend_checkbox = QCheckBox()
        self.show_legend_checkbox.setChecked(self.show_legend)
        self.show_legend_checkbox.stateChanged.connect(self.on_show_legend_changed)
        display_layout.addRow("Show legend:", self.show_legend_checkbox)
        
        # Set widget to dock
        properties_dock.setWidget(properties_widget)
        
        # Add dock to main window on left side, below tracks dock
        self.addDockWidget(Qt.LeftDockWidgetArea, properties_dock)
        self.splitDockWidget(self.track_manager, properties_dock, Qt.Vertical)
    
    def on_x_data_changed(self, value: str):
        """Handle X-axis data selection change"""
        self.x_data = value
        self.statusBar().showMessage(f"X-axis set to: {value}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_y_data_changed(self, value: str):
        """Handle Y-axis data selection change"""
        self.y_data = value
        self.statusBar().showMessage(f"Y-axis set to: {value}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_color_data_changed(self, value: str):
        """Handle color data selection change"""
        self.color_data = value
        
        # Enable/disable colormap and color range controls
        if value != "None" and self.tracks:
            # Compute min/max values for the selected color data
            color_values = []
            for track in self.tracks:
                values = self.viewer._get_data_values(track, value)
                color_values.extend([v for v in values if v is not None])
            
            if color_values:
                computed_min = min(color_values)
                computed_max = max(color_values)
                self.color_min = computed_min
                self.color_max = computed_max
                
                # Update spinboxes
                self.color_min_spinbox.blockSignals(True)
                self.color_max_spinbox.blockSignals(True)
                self.color_min_spinbox.setValue(computed_min)
                self.color_max_spinbox.setValue(computed_max)
                self.color_min_spinbox.blockSignals(False)
                self.color_max_spinbox.blockSignals(False)
                
                # Enable controls
                self.colormap_combo.setEnabled(True)
                self.color_min_spinbox.setEnabled(True)
                self.color_max_spinbox.setEnabled(True)
        else:
            self.color_min = None
            self.color_max = None
            self.colormap_combo.setEnabled(False)
            self.color_min_spinbox.setEnabled(False)
            self.color_max_spinbox.setEnabled(False)
        
        self.statusBar().showMessage(f"Color by: {value}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_colormap_changed(self, value: str):
        """Handle colormap selection change"""
        self.colormap = value
        self.statusBar().showMessage(f"Colormap set to: {value}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_color_min_changed(self):
        """Handle color min value change"""
        self.color_min = self.color_min_spinbox.value()
        self.statusBar().showMessage(f"Color min set to: {self.color_min:.2f}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_color_max_changed(self):
        """Handle color max value change"""
        self.color_max = self.color_max_spinbox.value()
        self.statusBar().showMessage(f"Color max set to: {self.color_max:.2f}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_show_legend_changed(self, state: int):
        """Handle show legend checkbox change"""
        self.show_legend = (state == Qt.Checked)
        self.statusBar().showMessage(f"Legend: {'On' if self.show_legend else 'Off'}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_viewer_properties_changed(self, fit_bounds: bool = False):
        """Handle viewer property changes and regenerate curves"""
        self.regenerate_view(fit_bounds)
    
    def get_viewer_options(self) -> dict:
        """Get current viewer options from UI controls"""
        return {
            'x_data': self.x_data,
            'y_data': self.y_data,
            'color_data': self.color_data,
            'colormap': self.colormap,
            'color_min': self.color_min,
            'color_max': self.color_max,
            'show_legend': self.show_legend
        }
    
    def regenerate_view(self, fit_bounds: bool = True):
        """Override base class method to handle matplotlib canvas directly"""
        try:
            if not self.viewer:
                return
            
            if not self.tracks:
                # No tracks - show empty view
                self.initialize_empty_view()
                self.statusBar().showMessage("View reset (no tracks)")
                return
            
            self.statusBar().showMessage("Generating view...")
            
            # Get viewer options
            options = self.get_viewer_options()
            
            # Load view in widget (which creates the canvas)
            self.load_view_in_widget()
            
            self.statusBar().showMessage(f"View generated with {len(self.tracks)} track(s)")
            
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, 
                "Error", 
                f"Error generating view:\n{str(e)}"
            )
            self.statusBar().showMessage("Error generating view")
    
    def load_view_in_widget(self, view_file: str = None):
        """Load the matplotlib canvas in the widget"""
        # Clear previous canvas and toolbar
        while self.curve_layout.count():
            item = self.curve_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if self.tracks:
            # Create view with current tracks
            options = self.get_viewer_options()
            canvas, toolbar = self.viewer.create_view(self.tracks, options)
            
            # Add toolbar and canvas to layout
            self.curve_layout.addWidget(toolbar)
            self.curve_layout.addWidget(canvas)
            
            # Store references
            self.canvas = canvas
            self.toolbar = toolbar
        else:
            # Show empty view
            self.initialize_empty_view()
    
    def initialize_empty_view(self):
        """Initialize an empty view with a message"""
        # Clear layout
        while self.curve_layout.count():
            item = self.curve_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create empty view
        canvas, toolbar = self.viewer.create_view([], None)
        self.curve_layout.addWidget(toolbar)
        self.curve_layout.addWidget(canvas)
        
        self.canvas = canvas
        self.toolbar = toolbar
    
    def get_default_output_file(self) -> str:
        """Get default output filename for the curves"""
        return "track_curves.png"
    
    def take_screenshot(self):
        """Save the current matplotlib figure to a file"""
        if not self.canvas or not self.viewer.figure:
            QMessageBox.warning(self, "Error", "No chart to save")
            return
        
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"curves_screenshot_{timestamp}.png"
        
        # Ask user where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Chart",
            default_filename,
            "PNG Images (*.png);;JPEG Images (*.jpg);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)"
        )
        
        if file_path:
            try:
                self.viewer.figure.savefig(file_path, dpi=150, bbox_inches='tight')
                self.statusBar().showMessage(f"Chart saved: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save chart: {str(e)}")

