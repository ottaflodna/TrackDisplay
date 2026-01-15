"""
Power Curve Viewer - Displays power curve data for tracks
Shows best average power over various durations
"""

from typing import List, Dict, Any, Optional
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from models.track import Track
from viewer.base_viewer import BaseViewer


class PowerCurveViewer(BaseViewer):
    """
    Display power curve data showing best average power over various durations
    """
    
    # Duration labels in order
    DURATION_LABELS = ['5s', '10s', '20s', '30s', '1min', '2min', '5min', 
                       '10min', '20min', '30min', '1h', '2h', '5h', 'Total']
    
    # Duration values in seconds for plotting
    DURATION_SECONDS = {
        '5s': 5,
        '10s': 10,
        '20s': 20,
        '30s': 30,
        '1min': 60,
        '2min': 120,
        '5min': 300,
        '10min': 600,
        '20min': 1200,
        '30min': 1800,
        '1h': 3600,
        '2h': 7200,
        '5h': 18000
    }
    
    def __init__(self):
        super().__init__()
        self.figure = None
        self.canvas = None
        self.toolbar = None
    
    def get_available_options(self) -> Dict[str, Any]:
        """Get available configuration options for power curve viewer"""
        return {
            'show_legend': {
                'type': 'checkbox',
                'default': True,
                'label': 'Show Legend'
            },
            'plot_style': {
                'type': 'combo',
                'values': ['Line', 'Bar'],
                'default': 'Line',
                'label': 'Plot Style'
            }
        }
    
    def get_default_options(self) -> Dict[str, Any]:
        """Get default options for power curve viewer"""
        return {
            'show_legend': True,
            'plot_style': 'Line'
        }
    
    def create_view(self, tracks: List[Track], options: Dict[str, Any] = None) -> tuple:
        """
        Create matplotlib figure and canvas for power curves
        Returns (canvas, toolbar) tuple
        """
        if not tracks:
            return self._create_empty_view()
        
        # Filter tracks that have power curve data
        tracks_with_power = [t for t in tracks if t.power_curve is not None]
        
        if not tracks_with_power:
            return self._create_no_power_view()
        
        # Get options
        opts = self.get_default_options()
        if options:
            opts.update(options)
        
        show_legend = opts.get('show_legend', True)
        plot_style = opts.get('plot_style', 'Line')
        
        # Create figure and canvas
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, None)
        
        # Create the plot
        ax = self.figure.add_subplot(111)
        
        # Get color map for multiple tracks
        colors = plt.cm.tab10(range(len(tracks_with_power)))
        
        for idx, track in enumerate(tracks_with_power):
            # Extract power curve data
            durations = []
            powers = []
            
            for label in self.DURATION_LABELS:
                if label in track.power_curve and track.power_curve[label] is not None:
                    if label == 'Total':
                        # Get actual total duration from track
                        if 'Total' in track.power_curve:
                            # Use the actual total time from the track
                            durations.append(self._calculate_total_duration(track))
                    else:
                        durations.append(self.DURATION_SECONDS[label])
                    powers.append(track.power_curve[label])
            
            if not durations or not powers:
                continue
            
            label = track.name if track.name else f"Track {idx + 1}"
            
            # Plot based on style
            if plot_style == 'Line':
                ax.plot(durations, powers, marker='o', label=label, 
                       color=colors[idx], linewidth=2, markersize=6)
            else:  # Bar
                # For bar plots, offset each track slightly
                offset = (idx - len(tracks_with_power) / 2) * 0.02
                bar_durations = [d * (1 + offset) for d in durations]
                ax.bar(bar_durations, powers, label=label, 
                      color=colors[idx], alpha=0.7, width=0.1)
        
        # Configure plot with log scale for x-axis
        ax.set_xscale('log')
        ax.set_xlabel('Duration (seconds)', fontsize=12)
        ax.set_ylabel('Power (W)', fontsize=12)
        ax.set_title('Power Curve - Best Average Power', fontsize=14, fontweight='bold')
        ax.minorticks_on()  # Enable minor ticks on both axes
        ax.xaxis.set_minor_locator(plt.NullLocator())  # Remove minor ticks from x-axis
        ax.grid(True, alpha=0.3, which='major')
        ax.grid(True, alpha=0.3, which='minor', linewidth=1.0)
        
        # Set x-axis tick labels
        tick_positions = [self.DURATION_SECONDS[label] for label in self.DURATION_LABELS[:-1]]
        tick_labels = self.DURATION_LABELS[:-1]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=45, ha='right')
        
        if show_legend and len(tracks_with_power) > 0:
            ax.legend(loc='best', framealpha=0.9)
        
        self.figure.tight_layout()
        
        return self.canvas, self.toolbar
    
    def _calculate_total_duration(self, track: Track) -> float:
        """Calculate total duration of track in seconds"""
        if len(track.points) < 2 or not track.points[0].timestamp or not track.points[-1].timestamp:
            return 3600  # Default to 1 hour if can't calculate
        
        total_seconds = (track.points[-1].timestamp - track.points[0].timestamp).total_seconds()
        return total_seconds if total_seconds > 0 else 3600
    
    def _create_empty_view(self) -> tuple:
        """Create an empty view when no tracks are loaded"""
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, None)
        
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'No Tracks Loaded\n\nUse "Add Tracks" to load GPS track files with power data',
                ha='center', va='center', fontsize=14, color='gray',
                transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        return self.canvas, self.toolbar
    
    def _create_no_power_view(self) -> tuple:
        """Create a view when no tracks have power data"""
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, None)
        
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'No Power Data Available\n\nLoaded tracks do not contain power measurements',
                ha='center', va='center', fontsize=14, color='gray',
                transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        return self.canvas, self.toolbar
    
    def get_required_track_attributes(self) -> List[str]:
        """Get list of required track point attributes"""
        return ['power', 'timestamp']  # Required for power curve calculation
