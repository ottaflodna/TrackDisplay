# GPS Tracklog Viewer

A Python application to view multiple GPS tracklogs (GPX for biking, IGC for paragliding, and TCX for training data) on an interactive map with OpenTopoMap base layer.

## Features

- ✅ Support for GPX files (bike tracks)
- ✅ Support for IGC files (paragliding tracks)
- ✅ Support for TCX files (training data with power, heart rate, cadence)
- ✅ Multi-file selection
- ✅ Interactive map with OpenTopoMap
- ✅ Color-coded tracks with legend
- ✅ Start/end markers
- ✅ Track statistics (distance, points)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

1. A file dialog will open - select one or more GPX/IGC files
2. The app will parse the files and generate an interactive map
3. The map opens automatically in your default browser

## Project Structure

```
TrackDisplay/
├── main.py              # Application entry point
├── models/              # Data models
│   └── track.py         # Track and TrackPoint classes
├── parsers/             # File parsers
│   ├── gpx_parser.py    # GPX format parser
│   └── igc_parser.py    # IGC format parser
├── ui/                  # User interface
│   └── file_selector.py # File selection dialog
├── viewer/              # Map visualization
│   └── map_viewer.py    # Folium-based map viewer
└── requirements.txt     # Python dependencies
```

## Supported Formats

- **GPX**: Standard GPS Exchange Format (cycling, hiking, etc.)
- **IGC**: International Gliding Commission format (paragliding, gliding)
- **TCX**: Training Center XML format (Garmin devices, includes power, heart rate, cadence)

## Map Features

- OpenTopoMap base layer with topographic details
- Color-coded tracks (up to 10 different colors)
- Start markers (green) and end markers (red)
- Interactive legend with track names
- Popup information on track lines
- Auto-centering based on all track bounds
