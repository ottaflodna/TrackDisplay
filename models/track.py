"""
Track data model - common structure for GPX and IGC tracks
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class TrackPoint:
    """Single point in a GPS track"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    # IGC-specific fields
    pressure_altitude: Optional[float] = None
    
    # Calculated fields (available for both IGC and GPX)
    vertical_speed_ms: Optional[float] = None  # m/s, calculated from altitude changes
    vertical_speed_mh: Optional[float] = None  # m/h, calculated from altitude changes
    
    # GPX-specific fields (from extensions)
    power: Optional[float] = None  # watts
    heart_rate: Optional[int] = None  # bpm
    cadence: Optional[int] = None  # rpm
    temperature: Optional[float] = None  # celsius
    speed: Optional[float] = None  # m/s
    
    def to_latlng(self):
        """Return as [lat, lng] for mapping libraries"""
        return [self.latitude, self.longitude]


class Track:
    """GPS Track containing multiple points"""
    
    def __init__(self, name: str, track_type: str = "unknown"):
        """
        Initialize a track
        
        Args:
            name: Track name (usually filename)
            track_type: Type of track ('gpx', 'igc')
        """
        self.name = name
        self.track_type = track_type
        self.points: List[TrackPoint] = []
        self.color: Optional[str] = None
        self.power_curve: Optional[dict] = None  # Power curve data
    
    def add_point(self, point: TrackPoint):
        """Add a point to the track"""
        self.points.append(point)
    
    def get_bounds(self):
        """Calculate bounding box of the track"""
        if not self.points:
            return None
        
        lats = [p.latitude for p in self.points]
        lngs = [p.longitude for p in self.points]
        
        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lng': min(lngs),
            'max_lng': max(lngs)
        }
    
    def get_center(self):
        """Calculate center point of the track"""
        bounds = self.get_bounds()
        if not bounds:
            return None
        
        center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
        center_lng = (bounds['min_lng'] + bounds['max_lng']) / 2
        return [center_lat, center_lng]
    
    def get_total_distance(self):
        """Calculate total distance in kilometers (simplified)"""
        if len(self.points) < 2:
            return 0.0
        
        from math import radians, cos, sin, asin, sqrt
        
        total = 0.0
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            
            # Haversine formula
            lon1, lat1, lon2, lat2 = map(radians, [p1.longitude, p1.latitude, 
                                                     p2.longitude, p2.latitude])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Radius of earth in kilometers
            total += c * r
        
        return total
    
    def calculate_speed(self):
        """Calculate speed for points that don't have it, using Haversine formula"""
        if len(self.points) < 2:
            return
        
        from math import radians, cos, sin, asin, sqrt
        
        # Check if any points need speed calculation
        needs_calculation = any(p.speed is None and p.timestamp is not None 
                               for p in self.points)
        
        if not needs_calculation:
            return
        
        # Calculate speed between consecutive points
        for i in range(1, len(self.points)):
            p1 = self.points[i - 1]
            p2 = self.points[i]
            
            # Only calculate if speed is missing and we have timestamps
            if p2.speed is None and p1.timestamp is not None and p2.timestamp is not None:
                # Calculate time difference in seconds
                time_diff = (p2.timestamp - p1.timestamp).total_seconds()
                
                if time_diff > 0:
                    # Haversine formula for distance
                    lon1, lat1, lon2, lat2 = map(radians, [p1.longitude, p1.latitude, 
                                                             p2.longitude, p2.latitude])
                    dlon = lon2 - lon1
                    dlat = lat2 - lat1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a))
                    r = 6371000  # Radius of earth in meters
                    distance = c * r
                    
                    # Speed in m/s, then convert to km/h
                    speed_ms = distance / time_diff
                    p2.speed = speed_ms * 3.6  # Convert to km/h
        
        # Set first point's speed to second point's speed if available
        if self.points[0].speed is None and len(self.points) > 1 and self.points[1].speed is not None:
            self.points[0].speed = self.points[1].speed
    
    def apply_window_averaging(self):
        """Apply window averaging to vertical speed field only"""
        if len(self.points) < 2:
            return
        
        # Average vertical speed over 15 seconds
        self._average_vertical_speed(window_seconds=15)
    
    def _average_power(self, window_seconds: float):
        """Average power values over a time window using efficient sliding window"""
        if not self.points or not any(p.power is not None and p.timestamp is not None for p in self.points):
            return
        
        # Store original values
        original_powers = [p.power for p in self.points]
        half_window = window_seconds / 2
        
        for i, point in enumerate(self.points):
            if point.power is None or point.timestamp is None:
                continue
            
            # Find window boundaries using binary search-like approach
            window_sum = 0.0
            window_count = 0
            
            # Search backward from current point
            for j in range(i, -1, -1):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_powers[j] is not None:
                    window_sum += original_powers[j]
                    window_count += 1
            
            # Search forward from current point (skip current point to avoid double counting)
            for j in range(i + 1, len(self.points)):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_powers[j] is not None:
                    window_sum += original_powers[j]
                    window_count += 1
            
            # Calculate average
            if window_count > 0:
                point.power = window_sum / window_count
    
    def _average_vertical_speed(self, window_seconds: float):
        """Average vertical speed values over a time window using efficient sliding window"""
        if not self.points or not any(p.vertical_speed_mh is not None and p.timestamp is not None for p in self.points):
            return
        
        # Store original values
        original_vspeeds = [p.vertical_speed_mh for p in self.points]
        half_window = window_seconds / 2
        
        for i, point in enumerate(self.points):
            if point.vertical_speed_mh is None or point.timestamp is None:
                continue
            
            # Find window boundaries
            window_sum = 0.0
            window_count = 0
            
            # Search backward from current point
            for j in range(i, -1, -1):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_vspeeds[j] is not None:
                    window_sum += original_vspeeds[j]
                    window_count += 1
            
            # Search forward from current point
            for j in range(i + 1, len(self.points)):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_vspeeds[j] is not None:
                    window_sum += original_vspeeds[j]
                    window_count += 1
            
            # Calculate average
            if window_count > 0:
                point.vertical_speed_mh = window_sum / window_count
                # Also update m/s value
                point.vertical_speed_ms = point.vertical_speed_mh / 3600
    
    def _average_speed(self, window_seconds: float):
        """Average speed values over a time window using efficient sliding window"""
        if not self.points or not any(p.speed is not None and p.timestamp is not None for p in self.points):
            return
        
        # Store original values
        original_speeds = [p.speed for p in self.points]
        half_window = window_seconds / 2
        
        for i, point in enumerate(self.points):
            if point.speed is None or point.timestamp is None:
                continue
            
            # Find window boundaries
            window_sum = 0.0
            window_count = 0
            
            # Search backward from current point
            for j in range(i, -1, -1):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_speeds[j] is not None:
                    window_sum += original_speeds[j]
                    window_count += 1
            
            # Search forward from current point
            for j in range(i + 1, len(self.points)):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_speeds[j] is not None:
                    window_sum += original_speeds[j]
                    window_count += 1
            
            # Calculate average
            if window_count > 0:
                point.speed = window_sum / window_count
    
    def calculate_power_curve(self, pause_threshold_seconds: float = 900.0):
        """
        Calculate power curve (best average power) over various durations.
        Pauses (gaps > pause_threshold_seconds) are ignored.
        
        Args:
            pause_threshold_seconds: Time gap to consider as a pause (default 5s)
        """
        # Check if track has power data
        if not any(p.power is not None and p.power > 0 and p.timestamp is not None 
                   for p in self.points):
            self.power_curve = None
            return
        
        # Define durations to evaluate (in seconds)
        durations = {
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
        
        # Calculate total activity duration (excluding pauses)
        total_duration = self._calculate_moving_time(pause_threshold_seconds)
        if total_duration > 0:
            durations['Total'] = total_duration
        
        # Initialize power curve dictionary
        self.power_curve = {}
        
        # Build list of valid segments (excluding pauses)
        segments = self._build_moving_segments(pause_threshold_seconds)
        
        if not segments:
            self.power_curve = {key: None for key in durations.keys()}
            return
        
        # Calculate best average power for each duration
        for label, duration_seconds in durations.items():
            if total_duration < duration_seconds and label != 'Total':
                self.power_curve[label] = None
            else:
                best_avg = self._find_best_average_power(segments, duration_seconds)
                self.power_curve[label] = best_avg
    
    def _calculate_moving_time(self, pause_threshold_seconds: float) -> float:
        """Calculate total moving time (excluding pauses)"""
        if len(self.points) < 2:
            return 0.0
        
        total_time = 0.0
        for i in range(1, len(self.points)):
            p1 = self.points[i - 1]
            p2 = self.points[i]
            
            if p1.timestamp is None or p2.timestamp is None:
                continue
            
            time_diff = (p2.timestamp - p1.timestamp).total_seconds()
            if 0 < time_diff <= pause_threshold_seconds:
                total_time += time_diff
        
        return total_time
    
    def _build_moving_segments(self, pause_threshold_seconds: float) -> list:
        """
        Build list of continuous moving segments (point indices).
        Each segment is a list of consecutive point indices without pauses.
        """
        segments = []
        current_segment = []
        
        for i, point in enumerate(self.points):
            if point.power is None or point.timestamp is None:
                # Save current segment if not empty
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []
                continue
            
            # Check if this is a continuation or start of new segment
            if current_segment:
                prev_idx = current_segment[-1]
                prev_point = self.points[prev_idx]
                time_diff = (point.timestamp - prev_point.timestamp).total_seconds()
                
                if time_diff > pause_threshold_seconds:
                    # Pause detected - save current segment and start new one
                    segments.append(current_segment)
                    current_segment = [i]
                else:
                    # Continue current segment
                    current_segment.append(i)
            else:
                # Start new segment
                current_segment.append(i)
        
        # Add final segment
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def _find_best_average_power(self, segments: list, 
                                  target_duration: float) -> Optional[float]:
        """
        Find the best (highest) average power over the target duration.
        Uses an efficient sliding window approach with O(n) complexity per duration.
        
        Args:
            segments: List of moving segments (lists of point indices)
            target_duration: Target duration in seconds
            
        Returns:
            Best average power or None if no valid window found
        """
        best_avg = None
        
        for segment in segments:
            if len(segment) < 2:
                continue
            
            # Use sliding window with two pointers
            window_start = 0
            window_power_time = 0.0  # Sum of (power * time) in window
            window_duration = 0.0     # Total time in window
            
            # Precompute time differences and power-time products for efficiency
            intervals = []
            for i in range(len(segment) - 1):
                curr_idx = segment[i]
                next_idx = segment[i + 1]
                curr_point = self.points[curr_idx]
                next_point = self.points[next_idx]
                
                time_diff = (next_point.timestamp - curr_point.timestamp).total_seconds()
                avg_power = (curr_point.power + next_point.power) / 2
                power_time = avg_power * time_diff
                
                intervals.append((time_diff, power_time))
            
            # Slide the window through the segment
            for window_end in range(len(intervals)):
                # Add current interval to window
                time_diff, power_time = intervals[window_end]
                window_duration += time_diff
                window_power_time += power_time
                
                # Shrink window from the left if it exceeds target duration
                while window_duration > target_duration and window_start <= window_end:
                    window_duration -= intervals[window_start][0]
                    window_power_time -= intervals[window_start][1]
                    window_start += 1
                
                # Check if window meets or is close to target duration
                # We accept windows that are at least 95% of target duration
                if window_duration >= target_duration * 0.95:
                    window_avg = window_power_time / window_duration
                    if best_avg is None or window_avg > best_avg:
                        best_avg = window_avg
        
        return best_avg
    
    def __len__(self):
        """Return number of points"""
        return len(self.points)
    
    def __repr__(self):
        return f"Track(name='{self.name}', type='{self.track_type}', points={len(self.points)})"
