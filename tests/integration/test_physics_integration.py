"""
Integration Tests for Physics Module
=====================================

End-to-end tests for NASAPowerService + PhysicsEngine integration.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from backend.services.weather.nasa_power_service import NASAPowerService
from backend.services.physics.physics_engine import PhysicsEngine
from backend.core.models import (
    SystemState,
    ComponentSpecs,
    SimulationStepInput
)


@pytest.fixture
def physics_engine():
    """Create PhysicsEngine instance."""
    return PhysicsEngine()


@pytest.fixture
def nasa_service():
    """Create NASAPowerService instance."""
    return NASAPowerService()


@pytest.fixture
def test_specs():
    """Create test component specifications."""
    return ComponentSpecs(
        pv_capacity_kw=10.0,
        battery_capacity_kwh=20.0,
        battery_power_kw=5.0,
        panel_efficiency=0.20,
        inverter_efficiency=0.96,
        battery_efficiency=0.95,
        temperature_coefficient=-0.004,
        min_soc=0.2,
        max_soc=0.9
    )


@pytest.fixture
def initial_state():
    """Create initial system state."""
    return SystemState(
        timestep=0,
        soc=0.5,
        pv_power=0.0,
        load_demand=0.0,
        battery_power=0.0,
        grid_power=0.0,
        total_cost=0.0,
        total_revenue=0.0,
        battery_cycles=0.0,
        unmet_load=0.0,
        excess_pv=0.0
    )


@pytest.fixture
def mock_weather_response():
    """Create mock NASA API response with realistic weather datafor 24 hours."""
    # Simulated hourly GHI and temperature for one day
    return {
        "properties": {
            "parameter": {
                "GHI": {
                    f"20240101{hour:02d}": [0, 0, 0, 0, 0, 0, 50, 150, 300, 500, 700, 850, 900, 850, 700, 500, 300, 150, 50, 0, 0, 0, 0, 0][hour]
                    for hour in range(24)
                },
                "T2M": {
                    f"20240101{hour:02d}": [15, 14, 13, 13, 12, 12, 13, 15, 18, 21, 24, 26, 28, 29, 28, 27, 25, 22, 19, 17, 16, 15, 15, 14][hour]
                    for hour in range(24)
                }
            }
        }
    }


class TestPhysicsModuleIntegration:
    """Integration tests for complete physics simulation."""
    
    @pytest.mark.asyncio
    async def test_daily_simulation_cycle(
        self,
        physics_engine,
        nasa_service,
        test_specs,
        initial_state,
        mock_weather_response
    ):
        """Test complete 24-hour simulation with weather data."""
        # Mock NASA API
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_weather_response)
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Fetch weather data
            weather_data = await nasa_service.fetch_hourly_data(
                latitude=40.7128,
                longitude=-74.0060,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 1, 23)
            )
            
            # Verify weather data
            assert len(weather_data.ghi_values) == 24
            assert len(weather_data.temperature_values) == 24
            
            # Run simulation for 24 hours
            state = initial_state
            load_profile = [2, 2, 2, 2, 2, 3, 5, 7, 6, 5, 5, 5, 6, 6, 5, 7, 8, 8, 6, 5, 4, 3, 2, 2]
            
            for hour in range(24):
                ghi, temp = weather_data.get_hour_data(hour)
                
                step_input = SimulationStepInput(
                    ghi=ghi,
                    temperature=temp,
                    load_demand=load_profile[hour],
                    control_action=0.0  # Neutral control
                )
                
                state = physics_engine.step(state, test_specs, step_input)
            
            # Verify final state
            assert state.timestep == 24
            assert 0.2 <= state.soc <= 0.9  # Within SoC limits
            assert state.total_cost >= 0  # Some cost incurred
    
    @pytest.mark.asyncio
    async def test_pv_generation_vs_load(self, physics_engine, test_specs, initial_state):
        """Test PV power generation under various load conditions."""
        # Morning scenario: Low GHI, moderate load
        morning_input = SimulationStepInput(
            ghi=200.0,
            temperature=15.0,
            load_demand=5.0,
            control_action=0.0
        )
        
        morning_state = physics_engine.step(initial_state, test_specs, morning_input)
        
        # PV should generate some power
        assert morning_state.pv_power > 0
        assert morning_state.pv_power < test_specs.pv_capacity_kw
        
        # Noon scenario: High GHI, high load
        noon_input = SimulationStepInput(
            ghi=1000.0,
            temperature=25.0,
            load_demand=3.0,
            control_action=0.0
        )
        
        noon_state = physics_engine.step(initial_state, test_specs, noon_input)
        
        # PV should generate near rated capacity
        assert noon_state.pv_power > 7.0
        
        # Night scenario: No GHI, low load
        night_input = SimulationStepInput(
            ghi=0.0,
            temperature=12.0,
            load_demand=2.0,
            control_action=0.0
        )
        
        night_state = physics_engine.step(initial_state, test_specs, night_input)
        
        # No PV generation
        assert night_state.pv_power == 0.0
        
        # Should import from grid at night
        assert night_state.grid_power > 0
    
    @pytest.mark.asyncio
    async def test_battery_charging_discharging_cycle(
        self,
        physics_engine,
        test_specs,
        initial_state
    ):
        """Test battery charge/discharge over a simulated cycle."""
        # Start with 50% SoC
        state = initial_state
        
        # Step 1: Excess PV → Charge battery
        charge_input = SimulationStepInput(
            ghi=800.0,
            temperature=20.0,
            load_demand=2.0,
            control_action=1.0  # Force charge
        )
        
        state = physics_engine.step(state, test_specs, charge_input)
        assert state.soc > initial_state.soc, "Battery should charge"
        
        # Step 2: No PV, high load → Discharge battery
        discharge_input = SimulationStepInput(
            ghi=0.0,
            temperature=15.0,
            load_demand=7.0,
            control_action=-1.0  # Force discharge
        )
        
        state = physics_engine.step(state, test_specs, discharge_input)
        # SoC should decrease (discharging)
        assert state.battery_power < 0, "Battery should be discharging"
    
    @pytest.mark.asyncio
    async def test_cost_calculation(self, physics_engine, test_specs, initial_state):
        """Test cost accumulation over multiple steps."""
        state = initial_state
        
        # Multiple steps with grid import
        for _ in range(10):
            step_input = SimulationStepInput(
                ghi=0.0,
                temperature=20.0,
                load_demand=5.0,
                control_action=0.0
            )
            
            state = physics_engine.step(state, test_specs, step_input)
        
        # Costs should accumulate
        assert state.total_cost > 0
        assert state.timestep == 10
    
    @pytest.mark.asyncio
    async def test_soc_limit_enforcement(self, physics_engine, test_specs):
        """Test that SoC stays within configured limits."""
        # Start near max SoC
        high_soc_state = SystemState(
            timestep=0,
            soc=0.88,
            pv_power=0.0,
            load_demand=0.0,
            battery_power=0.0,
            grid_power=0.0,
            total_cost=0.0,
            total_revenue=0.0,
            battery_cycles=0.0,
            unmet_load=0.0,
            excess_pv=0.0
        )
        
        # Try to charge further
        charge_input = SimulationStepInput(
            ghi=1000.0,
            temperature=20.0,
            load_demand=1.0,
            control_action=1.0
        )
        
        state = physics_engine.step(high_soc_state, test_specs, charge_input)
        assert state.soc <= test_specs.max_soc
        
        # Start near min SoC
        low_soc_state = SystemState(
            timestep=0,
            soc=0.22,
            pv_power=0.0,
            load_demand=0.0,
            battery_power=0.0,
            grid_power=0.0,
            total_cost=0.0,
            total_revenue=0.0,
            battery_cycles=0.0,
            unmet_load=0.0,
            excess_pv=0.0
        )
        
        # Try to discharge further
        discharge_input = SimulationStepInput(
            ghi=0.0,
            temperature=20.0,
            load_demand=10.0,
            control_action=-1.0
        )
        
        state = physics_engine.step(low_soc_state, test_specs, discharge_input)
        assert state.soc >= test_specs.min_soc
