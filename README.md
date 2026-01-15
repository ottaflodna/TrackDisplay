# GPS Tracklog Viewer

A modular Python application to visualize GPS tracklogs (GPX, IGC, and TCX formats) with multiple visualization modes: interactive maps and altitude/data curve charts.

## Features

### Track Format Support
- ✅ **GPX** files (bike tracks, hiking, etc.)
- ✅ **IGC** files (paragliding/gliding tracks)
- ✅ **TCX** files (training data with power, heart rate, cadence)

### Visualization Modes
- ✅ **Map Viewer** - Interactive map with multiple base layers
- ✅ **Curve Viewer** - Altitude, speed, power, and heart rate profiles

### User Interface
- ✅ Multi-file selection with drag & drop support
- ✅ Track management with statistics (distance, duration, points)
- ✅ Color-coded tracks with customizable color modes
- ✅ Configurable viewer properties
- ✅ Screenshot capture functionality
- ✅ Export/import track collections

### Map Features
- ✅ Multiple base maps (OpenTopoMap, Satellite, OpenCycleMap, SwissTopo)
- ✅ Color modes: Plain, Altitude, Speed, Heart Rate, Power, Cadence
- ✅ Start/stop markers with customizable visibility
- ✅ Interactive legend
- ✅ Zoom controls

### Curve/Chart Features
- ✅ Altitude, Speed, Heart Rate, Power, Cadence, Temperature profiles
- ✅ X-axis options: Distance, Time, Point Index
- ✅ Multi-view mode (all charts at once)
- ✅ Grid and legend toggles
- ✅ Data smoothing option

## Installation

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Map Viewer
Run the map viewer application:
```bash
python scripts/map_main.py
```

### Curve Viewer
Run the curve/chart viewer application:
```bash
python scripts/curve_main.py
```

### Combined Viewer
Run the combined map + curve viewer application:
```bash
python scripts/display_main.py
```

### Workflow
1. Select files using the "Add Tracks" button or drag & drop
2. Loaded tracks appear in the track manager with statistics
3. Configure visualization options in the properties panel
4. Click "Generate View" to create the visualization
5. View opens automatically in the integrated browser

## Project Structure

The application follows a modular, object-oriented architecture with clear separation of concerns:

```
TrackDisplay/
├── map_main.py                  # Map viewer application entry point
├── curve_main.py                # Curve viewer application entry point
├── requirements.txt             # Python dependencies
│
├── apps/                        # Application implementations
│   ├── map_app.py              # Map viewer application (MapWindow)
│   └── curve_app.py            # Curve viewer application (CurveWindow)
│
├── models/                      # Data models
│   └── track.py                # Track and TrackPoint classes
│
├── parsers/                     # File format parsers
│   ├── gpx_parser.py           # GPX format parser
│   ├── igc_parser.py           # IGC format parser
│   └── tcx_parser.py           # TCX format parser
│
├── ui/                          # User interface components
│   ├── base_window.py          # Abstract base window class
│   ├── file_selector.py        # File selection dialog
│   ├── track_manager_widget.py # Track list management
│   └── track_list_item.py      # Individual track item widget
│
├── viewer/                      # Visualization engines
│   ├── base_viewer.py          # Abstract base viewer interface
│   ├── map_viewer.py           # Folium-based map viewer
│   └── curve_viewer.py         # Plotly-based curve/chart viewer
│
└── tracklogs/                   # Sample track files
```

### Architecture Highlights

- **Base Classes**: `BaseWindow` and `BaseViewer` provide abstract interfaces for easy extension
- **App Layer**: `MapWindow` and `CurveWindow` implement specific applications by extending `BaseWindow`
- **Viewer Layer**: `MapViewer` and `CurveViewer` implement specific visualizations by extending `BaseViewer`
- **Reusable Components**: Track management, file selection, and parsing are shared across applications

## Supported Formats

- **GPX**: Standard GPS Exchange Format (cycling, hiking, etc.)
- **IGC**: International Gliding Commission format (paragliding, gliding)
- **TCX**: Training Center XML format (Garmin devices, includes power, heart rate, cadence)

## Technical Details

### Dependencies
- **PyQt5**: GUI framework and WebEngine for HTML rendering
- **folium**: Interactive map generation (Leaflet.js wrapper)
- **plotly**: Interactive chart generation
- **gpxpy**: GPX file parsing
- Standard library: xml.etree, datetime, pathlib

### Color Modes (Map Viewer)
Track segments can be colored by various metrics:
- Plain (solid color per track)
- Altitude (elevation gradient)
- Vertical Speed (climb/descent rate in m/s or m/h)
- Speed (km/h)
- Power (watts) - from TCX files
- Heart Rate (bpm) - from TCX files
- Cadence (rpm) - from TCX files
- Temperature (°C)

### Chart Types (Curve Viewer)
- Altitude Profile
- Speed Profile
- Heart Rate Profile
- Power Profile
- Cadence Profile
- Temperature Profile
- Multi-View (all charts simultaneously)

## Extending the Application

The refactored architecture makes it easy to add new viewers or applications:

1. **Create a new viewer**: Extend `BaseViewer` and implement `create_view()`, `get_available_options()`, and `get_default_options()`
2. **Create a new application**: Extend `BaseWindow` and implement `create_viewer()`, `setup_viewer_widget()`, and `setup_viewer_properties_dock()`
3. **Add a new entry point**: Create a new main file that instantiates your application window

Example: Adding a 3D terrain viewer would require creating `viewer/terrain_viewer.py` and `apps/terrain_app.py`, plus a simple `terrain_main.py` entry point.
