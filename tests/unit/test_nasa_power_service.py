"""
Unit Tests for NASAPowerService
=================================

Tests for NASA POWER API integration service.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import httpx

from backend.services.weather.nasa_power_service import NASAPowerService
from backend.core.models import WeatherData
from backend.core.exceptions import WeatherServiceError


@pytest.fixture
def nasa_service():
    """Create NASAPowerService instance."""
    return NASAPowerService()


@pytest.fixture
def mock_nasa_response():
    """Create mock successful NASA API response."""
    return {
        "properties": {
            "parameter": {
                "GHI": {
                    "2023010100": 0.0,
                    "2023010101": 0.0,
                    "2023010102": 150.5,
                    "2023010103": 800.2,
                    "2023010104": 600.0,
                },
                "T2M": {
                    "2023010100": 10.0,
                    "2023010101": 12.5,
                    "2023010102": 15.0,
                    "2023010103": 20.0,
                    "2023010104": 18.5,
                }
            }
        }
    }


class TestNASAPowerService:
    """Test suite for NASAPowerService."""
    
    @pytest.mark.asyncio
    async def test_fetch_hourly_data_success(self, nasa_service, mock_nasa_response):
        """Test successful data fetching."""
        # Mock async context manager and httpx response
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_nasa_response)
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Execute
            result = await nasa_service.fetch_hourly_data(
                latitude=40.7128,
                longitude=-74.0060,
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 1, 4)
            )
            
            # Verify
            assert isinstance(result, WeatherData)
            assert len(result.ghi_values) == 5
            assert len(result.temperature_values) == 5
            assert result.ghi_values[0] == 0.0
            assert result.ghi_values[3] == 800.2
            assert result.temperature_values[2] == 15.0
            mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_build_url(self, nasa_service):
        """Test URL construction."""
        url = nasa_service._build_url(
            latitude=40.7128,
            longitude=-74.0060,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31)
        )
        
        assert "power.larc.nasa.gov" in url
        assert "latitude=40.7128" in url
        assert "longitude=-74.006" in url
        assert "start=20230101" in url
        assert "end=20230131" in url
        assert "parameters=GHI,T2M" in url
        assert "community=RE" in url
        assert "format=JSON" in url
    
    @pytest.mark.asyncio
    async def test_parse_response(self, nasa_service, mock_nasa_response):
        """Test response parsing."""
        weather_data = nasa_service._parse_response(
            mock_nasa_response,
            latitude=40.7128,
            longitude=-74.0060,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 1, 4)
        )
        
        assert isinstance(weather_data, WeatherData)
        assert len(weather_data.ghi_values) == 5
        assert len(weather_data.temperature_values) == 5
        
        # Check values
        assert weather_data.ghi_values == (0.0, 0.0, 150.5, 800.2, 600.0)
        assert weather_data.temperature_values == (10.0, 12.5, 15.0, 20.0, 18.5)
    
    @pytest.mark.asyncio
    async def test_parse_response_missing_data(self, nasa_service):
        """Test parsing with missing data (-999 values)."""
        response_with_missing = {
            "properties": {
                "parameter": {
                    "GHI": {
                        "2023010100": 100.0,
                        "2023010101": -999.0,
                        "2023010102": 200.0,
                    },
                    "T2M": {
                        "2023010100": 15.0,
                        "2023010101": -999.0,
                        "2023010102": 18.0,
                    }
                }
            }
        }
        
        weather_data = nasa_service._parse_response(
            response_with_missing,
            latitude=40.0,
            longitude=-74.0,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 1, 2)
        )
        
        # -999 values should be replaced with defaults
        assert weather_data.ghi_values == (100.0, 0.0, 200.0)
        assert weather_data.temperature_values == (15.0, 25.0, 18.0)
    
    @pytest.mark.asyncio
    async def test_caching(self, nasa_service, mock_nasa_response):
        """Test in-memory caching."""
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_nasa_response)
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            # First call - should hit API
            result1 = await nasa_service.fetch_hourly_data(
                latitude=40.7128,
                longitude=-74.0060,
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 1, 4)
            )
            
            # Second call - should use cache
            result2 = await nasa_service.fetch_hourly_data(
                latitude=40.7128,
                longitude=-74.0060,
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 1, 4)
            )
            
            # Verify only one API call made
            assert mock_client.get.call_count == 1
            
            # Results should be identical
            assert result1.ghi_values == result2.ghi_values
            assert result1.temperature_values == result2.temperature_values
    
    @pytest.mark.asyncio
    async def test_http_error_handling(self, nasa_service):
        """Test handling of HTTP errors."""
        # Mock HTTP error
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404, text="Not Found")
        )
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Should raise WeatherServiceError
            with pytest.raises(WeatherServiceError) as exc_info:
                await nasa_service.fetch_hourly_data(
                    latitude=40.7128,
                    longitude=-74.0060,
                    start_date=datetime(2023, 1, 1),
                    end_date=datetime(2023, 1, 5)
                )
            
            assert "Failed to fetch weather data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, nasa_service):
        """Test handling of request timeouts."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(WeatherServiceError) as exc_info:
                await nasa_service.fetch_hourly_data(
                    latitude=40.7128,
                    longitude=-74.0060,
                    start_date=datetime(2023, 1, 1),
                    end_date=datetime(2023, 1, 5)
                )
            
            assert "Failed to fetch weather data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, nasa_service, mock_nasa_response):
        """Test retry logic on transient failures."""
        mock_success_response = AsyncMock()
        mock_success_response.json = AsyncMock(return_value=mock_nasa_response)
        mock_success_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        # First two calls fail, third succeeds
        mock_client.get = AsyncMock(side_effect=[
            httpx.RequestError("Connection failed"),
            httpx.RequestError("Connection failed"),
            mock_success_response
        ])
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Should succeed after retries
            result = await nasa_service.fetch_hourly_data(
                latitude=40.7128,
                longitude=-74.0060,
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 1, 4)
            )
            
            assert isinstance(result, WeatherData)
            assert mock_client.get.call_count == 3
    
    @pytest.mark.asyncio
    async def test_invalid_response_format(self, nasa_service):
        """Test handling of malformed API response."""
        invalid_response = {
            "properties": {
                "parameter": {
                    # Missing GHI
                    "T2M": {"2023010100": 15.0}
                }
            }
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=invalid_response)
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(WeatherServiceError) as exc_info:
                await nasa_service.fetch_hourly_data(
                    latitude=40.7128,
                    longitude=-74.0060,
                    start_date=datetime(2023, 1, 1),
                    end_date=datetime(2023, 1, 5)
                )
            
            assert "Missing GHI or T2M data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_coordinate_precision(self, nasa_service):
        """Test coordinate rounding in URL."""
        url = nasa_service._build_url(
            latitude=40.71280001,
            longitude=-74.00600001,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        # NASA API expects 4 decimal places
        assert "latitude=40.7128" in url
        assert "longitude=-74.006" in url
