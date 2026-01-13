"""
Curve Viewer - Displays track data as interactive matplotlib charts
Example of reusing the base architecture for a different visualization
"""

import os
from typing import List, Dict, Any, Optional
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from models.track import Track
from viewer.base_viewer import BaseViewer


class CurveViewer(BaseViewer):
    """
    Create and display interactive matplotlib charts with GPS track data
    Shows altitude, speed, power, heart rate, etc. over time/distance
    """
    
    # Available data attributes
    AVAILABLE_DATA = [
        'Distance (km)',
        'Time (min)',
        'Point Index',
        'Altitude (m)',
        'Speed (km/h)',
        'Heart Rate (bpm)',
        'Power (W)',
        'Cadence (rpm)',
        'Temperature (°C)',
        'Vertical Speed (m/s)'
    ]
    
    # Sequential data types (for line plots)
    SEQUENTIAL_DATA = ['Distance (km)', 'Time (min)', 'Point Index']
    
    # Available colormaps
    AVAILABLE_COLORMAPS = [
        'viridis',
        'plasma',
        'inferno',
        'magma',
        'cividis',
        'turbo',
        'jet',
        'rainbow',
        'hot',
        'cool',
        'spring',
        'summer',
        'autumn',
        'winter'
    ]
    
    def __init__(self):
        super().__init__()
        self.figure = None
        self.canvas = None
        self.toolbar = None
    
    def get_available_options(self) -> Dict[str, Any]:
        """Get available configuration options for curve viewer"""
        return {
            'x_data': {
                'type': 'combo',
                'values': self.AVAILABLE_DATA,
                'label': 'X-Axis Data'
            },
            'y_data': {
                'type': 'combo',
                'values': self.AVAILABLE_DATA,
                'label': 'Y-Axis Data'
            },
            'color_data': {
                'type': 'combo',
                'values': ['None'] + self.AVAILABLE_DATA,
                'label': 'Color Data'
            },
            'colormap': {
                'type': 'combo',
                'values': self.AVAILABLE_COLORMAPS,
                'label': 'Colormap'
            },
            'show_legend': {
                'type': 'checkbox',
                'default': True,
                'label': 'Show Legend'
            }
        }
    
    def get_default_options(self) -> Dict[str, Any]:
        """Get default options for curve viewer"""
        return {
            'x_data': 'Distance (km)',
            'y_data': 'Altitude (m)',
            'color_data': 'None',
            'colormap': 'viridis',
            'color_min': None,
            'color_max': None,
            'show_legend': True
        }
    
    def create_view(self, tracks: List[Track], options: Dict[str, Any] = None) -> tuple:
        """
        Create matplotlib figure and canvas for the tracks
        Returns (canvas, toolbar) tuple
        """
        if not tracks:
            return self._create_empty_view()
        
        # Get options
        opts = self.get_default_options()
        if options:
            opts.update(options)
        
        x_data = opts.get('x_data', 'Distance (km)')
        y_data = opts.get('y_data', 'Altitude (m)')
        color_data = opts.get('color_data', 'None')
        colormap = opts.get('colormap', 'viridis')
        color_min = opts.get('color_min', None)
        color_max = opts.get('color_max', None)
        show_legend = opts.get('show_legend', True)
        
        # Create figure and canvas
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, None)
        
        # Create the plot
        ax = self.figure.add_subplot(111)
        
        # Determine plot type based on X-axis data
        use_line_plot = x_data in self.SEQUENTIAL_DATA
        
        # Get color map for multiple tracks
        colors = plt.cm.tab10(range(len(tracks)))
        
        for idx, track in enumerate(tracks):
            # Get data values
            x_values = self._get_data_values(track, x_data)
            y_values = self._get_data_values(track, y_data)
            
            if not x_values or not y_values:
                continue
            
            # Ensure both have same length
            min_len = min(len(x_values), len(y_values))
            x_values = x_values[:min_len]
            y_values = y_values[:min_len]
            
            label = track.name if track.name else f"Track {idx + 1}"
            
            # Handle color data
            if color_data != 'None':
                color_values = self._get_data_values(track, color_data)
                if color_values:
                    color_values = color_values[:min_len]
                    # Create scatter plot with color mapping
                    scatter = ax.scatter(x_values, y_values, c=color_values, 
                                       label=label, cmap=colormap, s=10 if use_line_plot else 50,
                                       vmin=color_min, vmax=color_max)
                    # Add colorbar for color data
                    if idx == len(tracks) - 1:  # Add colorbar only once
                        cbar = self.figure.colorbar(scatter, ax=ax)
                        cbar.set_label(color_data)
                else:
                    # Fallback to standard plot if color data not available
                    if use_line_plot:
                        ax.plot(x_values, y_values, label=label, color=colors[idx], linewidth=2)
                    else:
                        ax.scatter(x_values, y_values, label=label, color=colors[idx], s=50)
            else:
                # Standard plot without color mapping
                if use_line_plot:
                    ax.plot(x_values, y_values, label=label, color=colors[idx], linewidth=2)
                else:
                    ax.scatter(x_values, y_values, label=label, color=colors[idx], s=50)
        
        # Configure plot
        ax.set_xlabel(x_data, fontsize=12)
        ax.set_ylabel(y_data, fontsize=12)
        ax.set_title(f'{y_data} vs {x_data}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        if show_legend and len(tracks) > 0:
            ax.legend(loc='best', framealpha=0.9)
        
        self.figure.tight_layout()
        
        return self.canvas, self.toolbar
    
    def _create_empty_view(self) -> tuple:
        """Create an empty view when no tracks are loaded"""
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, None)
        
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'No Tracks Loaded\n\nUse "Add Tracks" to load GPS track files',
                ha='center', va='center', fontsize=14, color='gray',
                transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        return self.canvas, self.toolbar
    
    def _get_data_values(self, track: Track, data_type: str) -> List:
        """Get data values based on data type selection"""
        if data_type == 'Distance (km)':
            # Calculate cumulative distance
            from math import radians, cos, sin, asin, sqrt
            distances = [0.0]
            for i in range(1, len(track.points)):
                p1 = track.points[i - 1]
                p2 = track.points[i]
                
                lon1, lat1, lon2, lat2 = map(radians, [p1.longitude, p1.latitude, 
                                                         p2.longitude, p2.latitude])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                r = 6371  # Earth radius in km
                distances.append(distances[-1] + c * r)
            return distances
            
        elif data_type == 'Time (min)':
            if not track.points[0].timestamp:
                return []
            start_time = track.points[0].timestamp
            return [(p.timestamp - start_time).total_seconds() / 60 for p in track.points if p.timestamp]
            
        elif data_type == 'Point Index':
            return list(range(len(track.points)))
            
        elif data_type == 'Altitude (m)':
            return [p.altitude if p.altitude is not None else 0 for p in track.points]
            
        elif data_type == 'Speed (km/h)':
            speeds = []
            for i in range(1, len(track.points)):
                p1 = track.points[i - 1]
                p2 = track.points[i]
                if p1.timestamp and p2.timestamp:
                    from math import radians, cos, sin, asin, sqrt
                    lon1, lat1, lon2, lat2 = map(radians, [p1.longitude, p1.latitude,
                                                             p2.longitude, p2.latitude])
                    dlon = lon2 - lon1
                    dlat = lat2 - lat1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a))
                    distance = 6371 * c  # km
                    time_diff = (p2.timestamp - p1.timestamp).total_seconds() / 3600  # hours
                    if time_diff > 0:
                        speeds.append(distance / time_diff)
                    else:
                        speeds.append(0)
            # Add first point with same speed as second
            if speeds:
                speeds.insert(0, speeds[0])
            return speeds
            
        elif data_type == 'Heart Rate (bpm)':
            return [p.heart_rate if p.heart_rate is not None else 0 for p in track.points]
            
        elif data_type == 'Power (W)':
            return [p.power if p.power is not None else 0 for p in track.points]
            
        elif data_type == 'Cadence (rpm)':
            return [p.cadence if p.cadence is not None else 0 for p in track.points]
            
        elif data_type == 'Temperature (°C)':
            return [p.temperature if p.temperature is not None else 0 for p in track.points]
            
        elif data_type == 'Vertical Speed (m/s)':
            vert_speeds = []
            for i in range(1, len(track.points)):
                p1 = track.points[i - 1]
                p2 = track.points[i]
                if p1.altitude is not None and p2.altitude is not None and p1.timestamp and p2.timestamp:
                    alt_diff = p2.altitude - p1.altitude
                    time_diff = (p2.timestamp - p1.timestamp).total_seconds()
                    if time_diff > 0:
                        vert_speeds.append(alt_diff / time_diff)
                    else:
                        vert_speeds.append(0)
                else:
                    vert_speeds.append(0)
            # Add first point with zero vertical speed
            vert_speeds.insert(0, 0)
            return vert_speeds
        
        return []
    
    def save_view(self, tracks: List[Track], output_file: str, options: Dict[str, Any] = None):
        """Save the matplotlib figure to a file"""
        if self.figure is None:
            # Create view if not already created
            self.create_view(tracks, options)
        
        if self.figure:
            # Determine format from file extension
            _, ext = os.path.splitext(output_file)
            if ext.lower() in ['.png', '.jpg', '.jpeg', '.pdf', '.svg']:
                self.figure.savefig(output_file, dpi=150, bbox_inches='tight')
            else:
                # Default to PNG
                self.figure.savefig(output_file + '.png', dpi=150, bbox_inches='tight')
    
    def get_required_track_attributes(self) -> List[str]:
        """Get list of required track point attributes"""
        return ['altitude', 'timestamp']  # Minimum required for curve viewing

