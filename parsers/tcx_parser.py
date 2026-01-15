"""
TCX file parser for bike/run tracks with power, heart rate, cadence
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
from models.track import Track, TrackPoint


class TCXParser:
    """Parser for TCX format files (Garmin Training Center XML)"""
    
    def parse(self, file_path: str) -> Track:
        """
        Parse a TCX file and return a Track object
        
        Args:
            file_path: Path to the TCX file
            
        Returns:
            Track object containing parsed data
        """
        track_name = os.path.basename(file_path)
        track = Track(name=track_name, track_type='tcx')
        
        # Parse TCX XML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Define namespaces
        ns = {
            'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
            'ns3': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'
        }
        
        # Extract trackpoints from all laps
        for trackpoint in root.findall('.//tcx:Trackpoint', ns):
            # Get position data
            position = trackpoint.find('tcx:Position', ns)
            if position is None:
                continue
            
            lat_elem = position.find('tcx:LatitudeDegrees', ns)
            lon_elem = position.find('tcx:LongitudeDegrees', ns)
            
            if lat_elem is None or lon_elem is None:
                continue
            
            latitude = float(lat_elem.text)
            longitude = float(lon_elem.text)
            
            # Get altitude
            altitude = None
            alt_elem = trackpoint.find('tcx:AltitudeMeters', ns)
            if alt_elem is not None and alt_elem.text:
                altitude = float(alt_elem.text)
            
            # Get timestamp
            timestamp = None
            time_elem = trackpoint.find('tcx:Time', ns)
            if time_elem is not None and time_elem.text:
                timestamp = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
            
            # Create track point with basic data
            track_point = TrackPoint(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                timestamp=timestamp
            )
            
            # Get heart rate
            hr_elem = trackpoint.find('.//tcx:HeartRateBpm/tcx:Value', ns)
            if hr_elem is not None and hr_elem.text:
                track_point.heart_rate = int(hr_elem.text)
            
            # Get cadence
            cadence_elem = trackpoint.find('tcx:Cadence', ns)
            if cadence_elem is not None and cadence_elem.text:
                track_point.cadence = int(cadence_elem.text)
            
            # Get speed (in m/s, convert to km/h)
            speed_elem = trackpoint.find('.//tcx:Speed', ns)
            if speed_elem is not None and speed_elem.text:
                track_point.speed = float(speed_elem.text) * 3.6
            
            # Get power from extensions
            extensions = trackpoint.find('tcx:Extensions', ns)
            if extensions is not None:
                # Try to find power in the extensions
                power_elem = extensions.find('.//ns3:Watts', ns)
                if power_elem is not None and power_elem.text:
                    track_point.power = float(power_elem.text)
            
            track.add_point(track_point)
        
        # Calculate vertical speeds
        self._calculate_vertical_speeds(track)
        
        # Calculate speed if not present
        track.calculate_speed()
        
        # Apply window averaging for power and vertical speed
        track.apply_window_averaging()
        
        # Calculate power curve if power data is available
        track.calculate_power_curve()
        
        return track
    
    def _calculate_vertical_speeds(self, track: Track):
        """Calculate vertical speed between consecutive points"""
        for i in range(1, len(track.points)):
            p1 = track.points[i - 1]
            p2 = track.points[i]
            
            if p1.altitude is not None and p2.altitude is not None and \
               p1.timestamp is not None and p2.timestamp is not None:
                
                # Calculate time difference in seconds
                time_diff = (p2.timestamp - p1.timestamp).total_seconds()
                
                if time_diff > 0:
                    # Calculate vertical speed in m/s and m/h
                    alt_diff = p2.altitude - p1.altitude
                    p2.vertical_speed_ms = alt_diff / time_diff
                    p2.vertical_speed_mh = p2.vertical_speed_ms * 3600
