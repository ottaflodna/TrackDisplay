"""
Map viewer using Folium with OpenTopoMap base layer
"""

import folium
import os
import webbrowser
from typing import List, Optional
from models.track import Track


class MapViewer:
    """Create and display interactive maps with GPS tracks"""
    
    # Available base map options
    AVAILABLE_BASE_MAPS = [
        'OpenTopoMap',
        'Satellite',
        'OpenCycleMap',
        'SwissTopo'
    ]
    
    # Extended color palette for multiple tracks (20 colors)
    COLORS = [
        '#FF0000',  # Red
        '#0000FF',  # Blue
        '#00FF00',  # Lime Green
        '#FF00FF',  # Magenta
        '#FFA500',  # Orange
        '#00FFFF',  # Cyan
        '#FFFF00',  # Yellow
        '#800080',  # Purple
        '#FFC0CB',  # Pink
        '#A52A2A',  # Brown
        '#FF6347',  # Tomato
        '#4169E1',  # Royal Blue
        '#32CD32',  # Lime
        '#FF1493',  # Deep Pink
        '#FF8C00',  # Dark Orange
        '#00CED1',  # Dark Turquoise
        '#FFD700',  # Gold
        '#9370DB',  # Medium Purple
        '#FF69B4',  # Hot Pink
        '#8B4513',  # Saddle Brown
    ]
    
    def create_map(self, tracks: List[Track], output_file: str = 'track_map.html', 
                   show_start_stop: bool = True, base_map: str = 'OpenTopoMap',
                   fit_bounds: bool = False, current_center: List[float] = None,
                   current_zoom: int = None, color_mode: str = 'Plain',
                   show_legend: bool = False, color_min: Optional[float] = None,
                   color_max: Optional[float] = None, zoom_control: bool = True) -> str:
        """
        Create an interactive map with all tracks
        
        Args:
            tracks: List of Track objects to display
            output_file: Output HTML filename
            show_start_stop: Whether to show start/stop markers
            base_map: Base map type ('OpenTopoMap', 'Satellite', 'OpenCycleMap', 'SwissTopo')
            fit_bounds: Whether to automatically adjust zoom to fit all tracks
            current_center: Current map center to preserve (if not fitting bounds)
            current_zoom: Current zoom level to preserve (if not fitting bounds)
            color_mode: How to color tracks ('Plain', 'Altitude', 'Vertical Speed (m/s)', etc.)
            show_legend: Whether to show the legend
            
        Returns:
            Path to the generated HTML file
        """
        if not tracks:
            raise ValueError("No tracks provided")
        
        # Use provided center/zoom or calculate from tracks
        if fit_bounds or current_center is None:
            center = self._calculate_center(tracks)
        else:
            center = current_center
        
        if current_zoom is None:
            zoom = 13
        else:
            zoom = current_zoom
        
        # Create map with selected base layer
        m = self._create_base_map(center, base_map, zoom, zoom_control)
        
        # Add each track with appropriate coloring
        if color_mode == 'Plain':
            # Use solid colors for each track
            for idx, track in enumerate(tracks):
                color = self.COLORS[idx % len(self.COLORS)]
                track.color = color
                self._add_track_to_map(m, track, color, show_start_stop, color_mode)
        else:
            # Use gradient coloring based on attribute
            for idx, track in enumerate(tracks):
                color = self.COLORS[idx % len(self.COLORS)]
                track.color = color
                self._add_colored_track_to_map(m, track, color, show_start_stop, color_mode, color_min, color_max)
        
        # Add legend if requested
        if show_legend:
            self._add_legend(m, tracks, color_mode, color_min, color_max)
        
        # Fit bounds to encompass all tracks if requested
        if fit_bounds:
            bounds = self._calculate_bounds(tracks)
            m.fit_bounds(bounds, padding=[50, 50])
        
        # Save map
        m.save(output_file)
        
        return os.path.abspath(output_file)
    
    def _calculate_center(self, tracks: List[Track]) -> List[float]:
        """Calculate center point of all tracks"""
        all_lats = []
        all_lngs = []
        
        for track in tracks:
            for point in track.points:
                all_lats.append(point.latitude)
                all_lngs.append(point.longitude)
        
        center_lat = sum(all_lats) / len(all_lats)
        center_lng = sum(all_lngs) / len(all_lngs)
        
        return [center_lat, center_lng]
    
    def _calculate_bounds(self, tracks: List[Track]) -> List[List[float]]:
        """Calculate bounding box encompassing all tracks"""
        all_lats = []
        all_lngs = []
        
        for track in tracks:
            for point in track.points:
                all_lats.append(point.latitude)
                all_lngs.append(point.longitude)
        
        # Return [[min_lat, min_lng], [max_lat, max_lng]]
        return [[min(all_lats), min(all_lngs)], [max(all_lats), max(all_lngs)]]
    
    def _create_base_map(self, center: List[float], base_map: str, zoom: int = 13, zoom_control: bool = True) -> folium.Map:
        """Create a folium map with the specified base layer"""
        
        if base_map == 'Satellite':
            m = folium.Map(
                location=center,
                zoom_start=zoom,
                zoom_control=zoom_control,
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Satellite'
            )
        
        elif base_map == 'OpenCycleMap':
            # Note: OpenCycleMap requires an API key from Thunderforest
            # You can get one free at https://www.thunderforest.com/docs/apikeys/
            api_key = 'cc077151fbf641f79c9c42eeebf1a2d9'  # Replace with your API key
            m = folium.Map(
                location=center,
                zoom_start=zoom,
                zoom_control=zoom_control,
                tiles=f'https://tile.thunderforest.com/cycle/{{z}}/{{x}}/{{y}}.png?apikey={api_key}',
                attr='Maps © Thunderforest, Data © OpenStreetMap contributors',
                name='OpenCycleMap'
            )
        
        elif base_map == 'SwissTopo':
            m = folium.Map(
                location=center,
                zoom_start=zoom,
                zoom_control=zoom_control,
                tiles='https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg',
                attr='© swisstopo',
                name='SwissTopo'
            )
        
        else:  # Default to OpenTopoMap
            m = folium.Map(
                location=center,
                zoom_start=zoom,
                zoom_control=zoom_control,
                tiles='OpenTopoMap',
                attr='Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap'
            )
        
        return m
    
    def _add_track_to_map(self, m: folium.Map, track: Track, color: str, show_start_stop: bool = True, color_mode: str = 'Plain'):
        """Add a single track to the map"""
        if len(track) == 0:
            return
        
        # Convert points to [lat, lng] format
        locations = [point.to_latlng() for point in track.points]
        
        # Get line width (default to 3 if not set)
        line_width = getattr(track, 'line_width', 3)
        
        # Add track line
        folium.PolyLine(
            locations=locations,
            color=color,
            weight=line_width,
            opacity=0.7,
            popup=self._create_popup_text(track)
        ).add_to(m)
        
        # Add start and end markers if enabled
        if show_start_stop:
            # Add start marker (green)
            folium.Marker(
                location=locations[0],
                popup=f"Start: {track.name}",
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)
            
            # Add end marker (red)
            folium.Marker(
                location=locations[-1],
                popup=f"End: {track.name}",
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(m)
    
    def _create_popup_text(self, track: Track) -> str:
        """Create popup text with track information"""
        distance = track.get_total_distance()
        
        html = f"""
        <div style="font-family: Arial; font-size: 12px;">
            <b>{track.name}</b><br>
            Type: {track.track_type.upper()}<br>
            Points: {len(track)}<br>
            Distance: {distance:.2f} km
        </div>
        """
        return html
    
    def _add_legend(self, m: folium.Map, tracks: List[Track], color_mode: str = 'Plain',
                    color_min: Optional[float] = None, color_max: Optional[float] = None):
        """Add a legend showing track names and colors or color scale"""
        if color_mode == 'Plain':
            # Show track names and colors
            legend_html = '''
            <div style="position: fixed; 
                        top: 10px; right: 10px; 
                        width: 250px; 
                        background-color: white; 
                        border:2px solid grey; 
                        z-index:9999; 
                        font-size:14px;
                        padding: 10px;
                        border-radius: 5px;
                        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
                <h4 style="margin-top:0;">GPS Tracks</h4>
            '''
            
            for track in tracks:
                legend_html += f'''
                <p style="margin: 5px 0;">
                    <span style="background-color:{track.color}; 
                                width: 20px; 
                                height: 3px; 
                                display: inline-block; 
                                margin-right: 5px;"></span>
                    {track.name} ({track.track_type.upper()})
                </p>
                '''
            
            legend_html += '</div>'
        else:
            # Show color scale for attribute
            if color_min is not None and color_max is not None:
                min_val, max_val = color_min, color_max
            else:
                min_val, max_val = self._get_value_range(tracks, color_mode)
            legend_html = f'''
            <div style="position: fixed; 
                        top: 10px; right: 10px; 
                        width: 200px; 
                        background-color: white; 
                        border:2px solid grey; 
                        z-index:9999; 
                        font-size:14px;
                        padding: 10px;
                        border-radius: 5px;
                        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
                <h4 style="margin-top:0; margin-bottom:10px;">{color_mode}</h4>
                <div style="display: flex; align-items: stretch;">
                    <div style="background: linear-gradient(to top, #0000FF, #00FF00, #FFFF00, #FF0000); 
                                height: 150px; 
                                width: 30px;"></div>
                    <div style="display: flex; 
                                flex-direction: column; 
                                justify-content: space-between; 
                                margin-left: 10px; 
                                height: 150px;">
                        <div style="margin-top: 0;">{max_val:.1f}</div>
                        <div>{(min_val + max_val) / 2:.1f}</div>
                        <div style="margin-bottom: 0;">{min_val:.1f}</div>
                    </div>
                </div>
            </div>
            '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
    
    def _add_colored_track_to_map(self, m: folium.Map, track: Track, base_color: str, 
                                   show_start_stop: bool, color_mode: str,
                                   color_min: Optional[float] = None,
                                   color_max: Optional[float] = None):
        """Add a track to the map with gradient coloring based on attribute"""
        if len(track) == 0:
            return
        
        # Get the attribute values for coloring
        values = self._get_track_values(track, color_mode)
        if not values or all(v is None for v in values):
            # Fallback to plain color if no values available
            self._add_track_to_map(m, track, base_color, show_start_stop, color_mode)
            return
        
        # Calculate value range
        valid_values = [v for v in values if v is not None]
        if not valid_values:
            self._add_track_to_map(m, track, base_color, show_start_stop, color_mode)
            return
        
        # Use provided min/max or calculate from data
        if color_min is not None and color_max is not None:
            min_val = color_min
            max_val = color_max
        else:
            min_val = min(valid_values)
            max_val = max(valid_values)
        
        # Create colored segments
        for i in range(len(track.points) - 1):
            if values[i] is not None:
                # Normalize value to 0-1 range
                if max_val > min_val:
                    normalized = (values[i] - min_val) / (max_val - min_val)
                else:
                    normalized = 0.5
                
                # Get color from gradient (blue -> green -> yellow -> red)
                color = self._value_to_color(normalized)
                
                # Add segment
                locations = [track.points[i].to_latlng(), track.points[i + 1].to_latlng()]
                folium.PolyLine(
                    locations=locations,
                    color=color,
                    weight=3,
                    opacity=0.8
                ).add_to(m)
        
        # Add start and end markers if enabled
        if show_start_stop:
            locations = [point.to_latlng() for point in track.points]
            folium.Marker(
                location=locations[0],
                popup=f"Start: {track.name}",
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)
            
            folium.Marker(
                location=locations[-1],
                popup=f"End: {track.name}",
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(m)
    
    def _get_track_values(self, track: Track, color_mode: str):
        """Extract values from track points based on color mode"""
        values = []
        for point in track.points:
            if color_mode == 'Altitude (m)':
                values.append(point.altitude)
            elif color_mode == 'Vertical Speed (m/s)':
                values.append(point.vertical_speed_ms)
            elif color_mode == 'Vertical Speed (m/h)':
                values.append(point.vertical_speed_mh)
            elif color_mode == 'Power (W)':
                values.append(point.power)
            elif color_mode == 'Heart Rate (bpm)':
                values.append(point.heart_rate)
            elif color_mode == 'Cadence (rpm)':
                values.append(point.cadence)
            elif color_mode == 'Temperature (°C)':
                values.append(point.temperature)
            elif color_mode == 'Speed (km/h)':
                values.append(point.speed)
            else:
                values.append(None)
        return values
    
    def _get_value_range(self, tracks: List[Track], color_mode: str):
        """Get min and max values across all tracks for a given attribute"""
        all_values = []
        for track in tracks:
            values = self._get_track_values(track, color_mode)
            all_values.extend([v for v in values if v is not None])
        
        if not all_values:
            return 0, 0
        
        return min(all_values), max(all_values)
    
    def _value_to_color(self, normalized: float) -> str:
        """Convert a normalized value (0-1) to a color (blue -> green -> yellow -> red)"""
        # Clamp value
        normalized = max(0, min(1, normalized))
        
        if normalized < 0.33:
            # Blue to green
            factor = normalized / 0.33
            r = 0
            g = int(255 * factor)
            b = int(255 * (1 - factor))
        elif normalized < 0.66:
            # Green to yellow
            factor = (normalized - 0.33) / 0.33
            r = int(255 * factor)
            g = 255
            b = 0
        else:
            # Yellow to red
            factor = (normalized - 0.66) / 0.34
            r = 255
            g = int(255 * (1 - factor))
            b = 0
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def open_in_browser(self, file_path: str):
        """Open the HTML file in the default browser"""
        webbrowser.open('file://' + file_path)
