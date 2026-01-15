"""
GPX file parser for bike tracks
"""

import gpxpy
import os
from models.track import Track, TrackPoint


class GPXParser:
    """Parser for GPX format files"""
    
    def parse(self, file_path: str) -> Track:
        """
        Parse a GPX file and return a Track object
        
        Args:
            file_path: Path to the GPX file
            
        Returns:
            Track object containing parsed data
        """
        with open(file_path, 'r', encoding='utf-8') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
        
        # Use filename as track name
        track_name = os.path.basename(file_path)
        track = Track(name=track_name, track_type='gpx')
        
        # Extract points from all tracks and segments
        for gpx_track in gpx.tracks:
            for segment in gpx_track.segments:
                for point in segment.points:
                    track_point = self._create_track_point(point)
                    track.add_point(track_point)
        
        # If no tracks, try routes
        if len(track) == 0:
            for route in gpx.routes:
                for point in route.points:
                    track_point = self._create_track_point(point)
                    track.add_point(track_point)
        
        # If still no points, try waypoints
        if len(track) == 0:
            for point in gpx.waypoints:
                track_point = self._create_track_point(point)
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
    
    def _create_track_point(self, gpx_point) -> TrackPoint:
        """Create TrackPoint from gpxpy point with all available extensions"""
        track_point = TrackPoint(
            latitude=gpx_point.latitude,
            longitude=gpx_point.longitude,
            altitude=gpx_point.elevation,
            timestamp=gpx_point.time,
            speed=gpx_point.speed
        )
        
        # Extract extension data if available
        if hasattr(gpx_point, 'extensions') and gpx_point.extensions:
            for ext in gpx_point.extensions:
                # Try different approaches to find extension elements
                
                # Approach 1: Direct child elements with namespace
                power_elem = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}power')
                if power_elem is None:
                    power_elem = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}power')
                
                # Approach 2: Search in TrackPointExtension wrapper
                if power_elem is None:
                    tpe = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}TrackPointExtension')
                    if tpe is None:
                        tpe = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}TrackPointExtension')
                    if tpe is not None:
                        power_elem = tpe.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}power')
                        if power_elem is None:
                            power_elem = tpe.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}power')
                
                if power_elem is not None:
                    try:
                        track_point.power = float(power_elem.text)
                    except (ValueError, AttributeError):
                        pass
                
                # Heart rate
                hr_elem = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}hr')
                if hr_elem is None:
                    hr_elem = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}hr')
                if hr_elem is None:
                    tpe = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}TrackPointExtension')
                    if tpe is None:
                        tpe = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}TrackPointExtension')
                    if tpe is not None:
                        hr_elem = tpe.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}hr')
                        if hr_elem is None:
                            hr_elem = tpe.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}hr')
                
                if hr_elem is not None:
                    try:
                        track_point.heart_rate = int(hr_elem.text)
                    except (ValueError, AttributeError):
                        pass
                
                # Cadence
                cad_elem = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}cad')
                if cad_elem is None:
                    cad_elem = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}cad')
                if cad_elem is None:
                    tpe = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}TrackPointExtension')
                    if tpe is None:
                        tpe = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}TrackPointExtension')
                    if tpe is not None:
                        cad_elem = tpe.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}cad')
                        if cad_elem is None:
                            cad_elem = tpe.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}cad')
                
                if cad_elem is not None:
                    try:
                        track_point.cadence = int(cad_elem.text)
                    except (ValueError, AttributeError):
                        pass
                
                # Temperature
                temp_elem = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}atemp')
                if temp_elem is None:
                    temp_elem = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}atemp')
                if temp_elem is None:
                    tpe = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}TrackPointExtension')
                    if tpe is None:
                        tpe = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}TrackPointExtension')
                    if tpe is not None:
                        temp_elem = tpe.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}atemp')
                        if temp_elem is None:
                            temp_elem = tpe.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v2}atemp')
                
                if temp_elem is not None:
                    try:
                        track_point.temperature = float(temp_elem.text)
                    except (ValueError, AttributeError):
                        pass
        
        # Set default values for power and cadence if not found
        if track_point.power is None:
            track_point.power = 0.0
        if track_point.cadence is None:
            track_point.cadence = 0
        
        return track_point
    
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
