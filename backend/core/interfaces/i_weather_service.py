"""
Weather Service Interface
==========================

Defines the contract for external weather data providers (e.g., NASA POWER API).
Implementation: Phase 1
"""

from abc import ABC, abstractmethod
from datetime import datetime
from ..models.weather_data import WeatherData


class IWeatherService(ABC):
    """
    Abstract interface for weather data retrieval services.
    
    Principle: Dependency Inversion - high-level modules depend on abstractions,
    not concrete implementations.
    
    Design: Uses WeatherData value object to eliminate primitive obsession.
    """
    
    @abstractmethod
    async def fetch_hourly_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> WeatherData:
        """
        Fetch hourly weather data for a specific location and time range.
        
        Args:
            latitude: Location latitude (-90 to 90)
            longitude: Location longitude (-180 to 180)
            start_date: Start of data range
            end_date: End of data range
        
        Returns:
            WeatherData value object containing GHI, temperature, and timestamps
            
        Raises:
            WeatherServiceError: If data retrieval fails
        """
        pass
    
    @abstractmethod
    async def validate_location(self, latitude: float, longitude: float) -> bool:
        """
        Validate if the given location is supported by the service.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            True if location is valid, False otherwise
        """
        pass
