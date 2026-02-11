"""
Test: Value Objects
===================

Unit tests for domain value objects introduced to eliminate primitive obsession.
Tests validation, immutability, and domain logic.
"""

import pytest
from datetime import datetime
from backend.core.models import (
    WeatherData,
    BatterySimulationResult,
    PVCalculationInput,
    BatterySimulationInput,
    SimulationStepInput
)


class TestWeatherData:
    """Test WeatherData value object."""
    
    def test_valid_weather_data(self):
        """Test creating valid weather data."""
        weather = WeatherData(
            latitude=40.7128,
            longitude=-74.0060,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            ghi_values=(800.0, 850.0, 900.0),
            temperature_values=(20.0, 22.0, 25.0),
            timestamps=(
                datetime(2024, 1, 1, 10),
                datetime(2024, 1, 1, 11),
                datetime(2024, 1, 1, 12)
            )
        )
        
        assert weather.num_hours == 3
        assert weather.get_hour_data(0) == (800.0, 20.0)
        assert weather.get_hour_data(1) == (850.0, 22.0)
    
    def test_immutability(self):
        """Test that WeatherData is immutable."""
        weather = WeatherData(
            latitude=40.7128,
            longitude=-74.0060,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            ghi_values=(800.0,),
            temperature_values=(20.0,),
            timestamps=(datetime(2024, 1, 1),)
        )
        
        with pytest.raises(AttributeError):
            weather.latitude = 50.0  # Should fail - frozen dataclass
    
    def test_invalid_latitude(self):
        """Test that invalid latitude raises ValueError."""
        with pytest.raises(ValueError, match="Invalid latitude"):
            WeatherData(
                latitude=100.0,  # Invalid
                longitude=-74.0060,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2),
                ghi_values=(800.0,),
                temperature_values=(20.0,),
                timestamps=(datetime(2024, 1, 1),)
            )
    
    def test_mismatched_array_lengths(self):
        """Test that mismatched array lengths raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            WeatherData(
                latitude=40.7128,
                longitude=-74.0060,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2),
                ghi_values=(800.0, 850.0),
                temperature_values=(20.0,),  # Mismatched length
                timestamps=(datetime(2024, 1, 1), datetime(2024, 1, 2))
            )
    
    def test_negative_ghi(self):
        """Test that negative GHI values raise ValueError."""
        with pytest.raises(ValueError, match="GHI values cannot be negative"):
            WeatherData(
                latitude=40.7128,
                longitude=-74.0060,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2),
                ghi_values=(800.0, -100.0),  # Negative GHI
                temperature_values=(20.0, 22.0),
                timestamps=(datetime(2024, 1, 1), datetime(2024, 1, 2))
            )


class TestBatterySimulationResult:
    """Test BatterySimulationResult value object."""
    
    def test_valid_result(self):
        """Test creating valid battery simulation result."""
        result = BatterySimulationResult(
            new_soc=0.6,
            actual_power_flow=5.0,
            grid_power=0.0,
            energy_stored=5.0,
            energy_discharged=0.0,
            efficiency_loss=0.25
        )
        
        assert result.new_soc == 0.6
        assert result.is_charging
        assert not result.is_discharging
        assert not result.is_idle
    
    def test_discharging_state(self):
        """Test discharging battery state."""
        result = BatterySimulationResult(
            new_soc=0.4,
            actual_power_flow=-3.0,
            grid_power=0.0,
            energy_stored=0.0,
            energy_discharged=3.0,
            efficiency_loss=0.15
        )
        
        assert result.is_discharging
        assert not result.is_charging
    
    def test_invalid_soc(self):
        """Test that invalid SoC raises ValueError."""
        with pytest.raises(ValueError, match="SoC must be between 0 and 1"):
            BatterySimulationResult(
                new_soc=1.5,  # Invalid
                actual_power_flow=5.0,
                grid_power=0.0,
                energy_stored=5.0,
                energy_discharged=0.0,
                efficiency_loss=0.25
            )
    
    def test_importing_from_grid(self):
        """Test grid import detection."""
        result = BatterySimulationResult(
            new_soc=0.5,
            actual_power_flow=0.0,
            grid_power=2.0,  # Importing
            energy_stored=0.0,
            energy_discharged=0.0,
            efficiency_loss=0.0
        )
        
        assert result.is_importing
        assert not result.is_exporting


class TestPVCalculationInput:
    """Test PVCalculationInput value object."""
    
    def test_valid_input(self):
        """Test creating valid PV calculation input."""
        pv_input = PVCalculationInput(
            ghi=800.0,
            temperature=25.0,
            pv_capacity_kw=10.0,
            panel_efficiency=0.20,
            temperature_coefficient=-0.004
        )
        
        assert pv_input.ghi == 800.0
        assert pv_input.pv_capacity_kw == 10.0
    
    def test_negative_ghi(self):
        """Test that negative GHI raises ValueError."""
        with pytest.raises(ValueError, match="GHI cannot be negative"):
            PVCalculationInput(
                ghi=-100.0,  # Invalid
                temperature=25.0,
                pv_capacity_kw=10.0
            )
    
    def test_invalid_efficiency(self):
        """Test that invalid efficiency raises ValueError."""
        with pytest.raises(ValueError, match="Panel efficiency"):
            PVCalculationInput(
                ghi=800.0,
                temperature=25.0,
                pv_capacity_kw=10.0,
                panel_efficiency=1.5  # Invalid
            )
    
    def test_positive_temperature_coefficient(self):
        """Test that positive temperature coefficient raises ValueError."""
        with pytest.raises(ValueError, match="Temperature coefficient should be negative"):
            PVCalculationInput(
                ghi=800.0,
                temperature=25.0,
                pv_capacity_kw=10.0,
                temperature_coefficient=0.004  # Should be negative
            )


class TestBatterySimulationInput:
    """Test BatterySimulationInput value object."""
    
    def test_valid_input(self):
        """Test creating valid battery simulation input."""
        battery_input = BatterySimulationInput(
            current_soc=0.5,
            power_demand=5.0,
            battery_capacity_kwh=20.0,
            charge_rate_kw=10.0,
            discharge_rate_kw=10.0,
            efficiency=0.95
        )
        
        assert battery_input.current_soc == 0.5
        assert battery_input.battery_capacity_kwh == 20.0
    
    def test_invalid_soc(self):
        """Test that invalid SoC raises ValueError."""
        with pytest.raises(ValueError, match="SoC must be between 0 and 1"):
            BatterySimulationInput(
                current_soc=1.2,  # Invalid
                power_demand=5.0,
                battery_capacity_kwh=20.0,
                charge_rate_kw=10.0,
                discharge_rate_kw=10.0
            )
    
    def test_invalid_soc_limits(self):
        """Test that invalid SoC limits raise ValueError."""
        with pytest.raises(ValueError, match="Invalid SoC limits"):
            BatterySimulationInput(
                current_soc=0.5,
                power_demand=5.0,
                battery_capacity_kwh=20.0,
                charge_rate_kw=10.0,
                discharge_rate_kw=10.0,
                min_soc=0.9,  # min > max
                max_soc=0.1
            )


class TestSimulationStepInput:
    """Test SimulationStepInput value object."""
    
    def test_valid_input(self):
        """Test creating valid simulation step input."""
        step_input = SimulationStepInput(
            load_demand=3.0,
            ghi=800.0,
            temperature=25.0,
            control_action=0.5
        )
        
        assert step_input.load_demand == 3.0
        assert step_input.control_action == 0.5
    
    def test_negative_load(self):
        """Test that negative load raises ValueError."""
        with pytest.raises(ValueError, match="Load demand cannot be negative"):
            SimulationStepInput(
                load_demand=-1.0,  # Invalid
                ghi=800.0,
                temperature=25.0,
                control_action=0.0
            )
    
    def test_invalid_control_action(self):
        """Test that invalid control action raises ValueError."""
        with pytest.raises(ValueError, match="Control action must be between -1 and 1"):
            SimulationStepInput(
                load_demand=3.0,
                ghi=800.0,
                temperature=25.0,
                control_action=1.5  # Invalid
            )
    
    def test_boundary_control_actions(self):
        """Test boundary values for control action."""
        # Test -1 (valid)
        step_input_min = SimulationStepInput(
            load_demand=3.0,
            ghi=800.0,
            temperature=25.0,
            control_action=-1.0
        )
        assert step_input_min.control_action == -1.0
        
        # Test +1 (valid)
        step_input_max = SimulationStepInput(
            load_demand=3.0,
            ghi=800.0,
            temperature=25.0,
            control_action=1.0
        )
        assert step_input_max.control_action == 1.0


# Run tests with: pytest backend/tests/unit/test_value_objects.py -v
