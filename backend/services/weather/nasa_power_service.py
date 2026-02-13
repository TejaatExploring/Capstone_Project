"""
NASA POWER API Service
=======================

Implementation of IWeatherService using NASA POWER API.
Provides real-world solar irradiance and temperature data.

API Documentation: https://power.larc.nasa.gov/docs/
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import httpx
from functools import lru_cache

from ...core.interfaces import IWeatherService
from ...core.models import WeatherData
from ...core.exceptions import WeatherServiceError
from ...infrastructure.config import get_settings
from ...infrastructure.logging import get_logger

logger = get_logger(__name__)


class NASAPowerService(IWeatherService):
    """
    NASA POWER API service implementation.
    
    Fetches Global Horizontal Irradiance (GHI) and temperature (T2M) data
    from NASA's POWER (Prediction Of Worldwide Energy Resources) database.
    
    Features:
    - Async HTTP requests
    - Automatic retry on failure
    - Response validation
    - Simple in-memory caching
    - Comprehensive error handling
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3
    ):
        """
        Initialize NASA POWER service.
        
        Args:
            base_url: API base URL (defaults from settings)
            timeout: Request timeout in seconds (defaults from settings)
            max_retries: Maximum retry attempts (default: 3)
        """
        settings = get_settings()
        self.base_url = base_url or settings.NASA_API_BASE_URL
        self.timeout = timeout or settings.NASA_API_TIMEOUT
        self.max_retries = max_retries
        
        # In-memory cache: (lat, lon, start, end) -> WeatherData
        self._cache: Dict[tuple, WeatherData] = {}
        
        logger.info(
            f"NASAPowerService initialized: "
            f"base_url={self.base_url}, timeout={self.timeout}s"
        )
    
    async def fetch_hourly_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> WeatherData:
        """
        Fetch hourly weather data from NASA POWER API.
        
        Args:
            latitude: Location latitude (-90 to 90)
            longitude: Location longitude (-180 to 180)
            start_date: Start of data range
            end_date: End of data range
        
        Returns:
            WeatherData value object with GHI, temperature, and timestamps
            
        Raises:
            WeatherServiceError: If data retrieval fails
        """
        # Validate inputs
        if not -90 <= latitude <= 90:
            raise WeatherServiceError(f"Invalid latitude: {latitude}")
        if not -180 <= longitude <= 180:
            raise WeatherServiceError(f"Invalid longitude: {longitude}")
        if start_date >= end_date:
            raise WeatherServiceError("start_date must be before end_date")
        
        # Check cache
        cache_key = (latitude, longitude, start_date, end_date)
        if cache_key in self._cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key]
        
        logger.info(
            f"Fetching weather data: lat={latitude}, lon={longitude}, "
            f"from {start_date} to {end_date}"
        )
        
        # Fetch from API with retry logic
        raw_data = await self._fetch_with_retry(
            latitude, longitude, start_date, end_date
        )
        
        # Parse and validate response
        weather_data = self._parse_response(
            raw_data, latitude, longitude, start_date, end_date
        )
        
        # Cache result
        self._cache[cache_key] = weather_data
        
        logger.info(
            f"Successfully fetched {weather_data.num_hours} hours of data"
        )
        
        return weather_data
    
    async def validate_location(
        self,
        latitude: float,
        longitude: float
    ) -> bool:
        """
        Validate if the given location is supported by NASA POWER.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            True if location is valid, False otherwise
        """
        # NASA POWER supports global coverage with some exclusions
        # Basic validation
        if not -90 <= latitude <= 90:
            return False
        if not -180 <= longitude <= 180:
            return False
        
        # Try a small data fetch to verify
        try:
            test_start = datetime(2024, 1, 1)
            test_end = datetime(2024, 1, 2)
            await self.fetch_hourly_data(latitude, longitude, test_start, test_end)
            return True
        except WeatherServiceError:
            return False
    
    async def _fetch_with_retry(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Fetch data from API with retry logic.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start date
            end_date: End date
            
        Returns:
            Raw API response dictionary
            
        Raises:
            WeatherServiceError: If all retries fail
        """
        # Build API URL
        url = self._build_url(latitude, longitude, start_date, end_date)
        
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    data = await response.json()  # httpx Response.json() is async
                    
                    # Validate response structure
                    if "properties" not in data or "parameter" not in data["properties"]:
                        raise WeatherServiceError(
                            f"Invalid API response structure: {data}"
                        )
                    
                    return data
                    
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    f"Request timeout (attempt {attempt}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code >= 500 and attempt < self.max_retries:
                    # Retry on server errors
                    await asyncio.sleep(2 ** attempt)
                else:
                    # Don't retry on client errors
                    break
                    
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
        
        # All retries failed
        raise WeatherServiceError(
            f"Failed to fetch weather data after {self.max_retries} attempts: {last_error}"
        )
    
    def _build_url(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """
        Build NASA POWER API URL.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start date
            end_date: End date
            
        Returns:
            Full API URL
        """
        # Format dates as YYYYMMDD
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        # NASA POWER API parameters
        parameters = "GHI,T2M"  # Global Horizontal Irradiance, Temperature at 2m
        community = "RE"  # Renewable Energy community
        temporal_api = "hourly"
        output_format = "JSON"
        
        url = (
            f"{self.base_url}"
            f"?parameters={parameters}"
            f"&community={community}"
            f"&longitude={longitude}"
            f"&latitude={latitude}"
            f"&start={start_str}"
            f"&end={end_str}"
            f"&format={output_format}"
        )
        
        return url
    
    def _parse_response(
        self,
        raw_data: Dict[str, Any],
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> WeatherData:
        """
        Parse NASA POWER API response into WeatherData value object.
        
        Args:
            raw_data: Raw API response
            latitude: Requested latitude
            longitude: Requested longitude
            start_date: Requested start date
            end_date: Requested end date
            
        Returns:
            WeatherData value object
            
        Raises:
            WeatherServiceError: If parsing fails
        """
        try:
            parameters = raw_data["properties"]["parameter"]
            
            # Extract GHI and T2M dictionaries
            ghi_dict = parameters.get("GHI", {})
            t2m_dict = parameters.get("T2M", {})
            
            if not ghi_dict or not t2m_dict:
                raise WeatherServiceError(
                    "Missing GHI or T2M data in API response"
                )
            
            # Parse timestamps and values
            timestamps = []
            ghi_values = []
            temperature_values = []
            
            # NASA POWER returns data as: "YYYYMMDDHH": value
            for timestamp_str in sorted(ghi_dict.keys()):
                # Parse timestamp: "2024010100" -> datetime(2024, 1, 1, 0)
                year = int(timestamp_str[0:4])
                month = int(timestamp_str[4:6])
                day = int(timestamp_str[6:8])
                hour = int(timestamp_str[8:10])
                
                dt = datetime(year, month, day, hour)
                
                # Only include data within requested range
                if start_date <= dt <= end_date:
                    timestamps.append(dt)
                    
                    # Get values (handle missing data)
                    ghi = ghi_dict.get(timestamp_str, 0.0)
                    temp = t2m_dict.get(timestamp_str, 25.0)
                    
                    # Handle special values (-999 means no data)
                    if ghi == -999 or ghi < 0:
                        ghi = 0.0
                    if temp == -999:
                        temp = 25.0  # Default temperature
                    
                    ghi_values.append(float(ghi))
                    temperature_values.append(float(temp))
            
            # Create WeatherData value object
            weather_data = WeatherData(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                ghi_values=tuple(ghi_values),
                temperature_values=tuple(temperature_values),
                timestamps=tuple(timestamps)
            )
            
            return weather_data
            
        except Exception as e:
            raise WeatherServiceError(f"Failed to parse API response: {e}")
    
    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self._cache.clear()
        logger.info("Weather data cache cleared")
