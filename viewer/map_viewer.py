"""
Map viewer using Folium with OpenTopoMap base layer
"""

import folium
import os
import webbrowser
from typing import List
from models.track import Track


class MapViewer:
    """Create and display interactive maps with GPS tracks"""
    
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
    
    def create_map(self, tracks: List[Track], output_file: str = 'track_map.html', show_start_stop: bool = True) -> str:
        """
        Create an interactive map with all tracks
        
        Args:
            tracks: List of Track objects to display
            output_file: Output HTML filename
            show_start_stop: Whether to show start/stop markers
            
        Returns:
            Path to the generated HTML file
        """
        if not tracks:
            raise ValueError("No tracks provided")
        
        # Calculate center point from all tracks
        center = self._calculate_center(tracks)
        
        # Create map with OpenTopoMap
        m = folium.Map(
            location=center,
            zoom_start=13,
            tiles='OpenTopoMap',
            attr='Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap'
        )
        
        # Add each track with a different color
        for idx, track in enumerate(tracks):
            color = self.COLORS[idx % len(self.COLORS)]
            track.color = color
            self._add_track_to_map(m, track, color, show_start_stop)
        
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
    
    def _add_track_to_map(self, m: folium.Map, track: Track, color: str, show_start_stop: bool = True):
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
    
    def _add_legend(self, m: folium.Map, tracks: List[Track]):
        """Add a legend showing track names and colors"""
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
        m.get_root().html.add_child(folium.Element(legend_html))
    
    def open_in_browser(self, file_path: str):
        """Open the HTML file in the default browser"""
        webbrowser.open('file://' + file_path)
