"""
Weather Data Value Object
==========================

Immutable value object representing weather data for a location and time period.
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass(frozen=True)
class WeatherData:
    """
    Immutable value object for weather data.
    
    Eliminates primitive obsession by encapsulating weather parameters
    in a well-defined domain object.
    
    Attributes:
        latitude: Location latitude (-90 to 90)
        longitude: Location longitude (-180 to 180)
        start_date: Start of data period
        end_date: End of data period
        ghi_values: Global Horizontal Irradiance (W/m²) - hourly
        temperature_values: Ambient temperature (°C) - hourly
        timestamps: Timestamps for each data point
    """
    latitude: float
    longitude: float
    start_date: datetime
    end_date: datetime
    ghi_values: tuple[float, ...]  # Immutable sequence
    temperature_values: tuple[float, ...]
    timestamps: tuple[datetime, ...]
    
    def __post_init__(self):
        """Validate weather data consistency."""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}")
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        
        # Ensure all sequences have same length
        length = len(self.ghi_values)
        if len(self.temperature_values) != length:
            raise ValueError("All weather data arrays must have same length")
        if len(self.timestamps) != length:
            raise ValueError("Timestamps must match data length")
        
        # Validate GHI values (cannot be negative)
        if any(ghi < 0 for ghi in self.ghi_values):
            raise ValueError("GHI values cannot be negative")
    
    @property
    def num_hours(self) -> int:
        """Get number of hourly data points."""
        return len(self.ghi_values)
    
    def get_hour_data(self, hour_index: int) -> tuple[float, float]:
        """
        Get weather data for a specific hour.
        
        Args:
            hour_index: Index of the hour (0 to num_hours-1)
            
        Returns:
            Tuple of (ghi, temperature) for that hour
        """
        if not 0 <= hour_index < self.num_hours:
            raise IndexError(f"Hour index {hour_index} out of range [0, {self.num_hours})")
        return (self.ghi_values[hour_index], self.temperature_values[hour_index])
