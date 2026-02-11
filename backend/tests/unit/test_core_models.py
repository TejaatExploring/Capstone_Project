"""
Test: Domain Models
===================

Unit tests for core domain models to validate Phase 0 architecture.
"""

import pytest
from datetime import datetime
from backend.core.models import (
    SimulationConfig,
    OptimizationConfig,
    ComponentSpecs,
    SystemState,
    SimulationResult
)
from backend.core.exceptions import IEMSException


class TestSimulationConfig:
    """Test SimulationConfig model."""
    
    def test_valid_config(self):
        """Test creating a valid simulation configuration."""
        config = SimulationConfig(
            latitude=40.7128,
            longitude=-74.0060,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            timestep_hours=1.0,
            random_seed=42
        )
        assert config.latitude == 40.7128
        assert config.longitude == -74.0060
        assert config.timestep_hours == 1.0
    
    def test_invalid_latitude(self):
        """Test that invalid latitude raises ValueError."""
        with pytest.raises(ValueError, match="Latitude must be between"):
            SimulationConfig(
                latitude=100,  # Invalid
                longitude=-74.0060,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31)
            )
    
    def test_invalid_date_range(self):
        """Test that invalid date range raises ValueError."""
        with pytest.raises(ValueError, match="start_date must be before end_date"):
            SimulationConfig(
                latitude=40.7128,
                longitude=-74.0060,
                start_date=datetime(2024, 1, 31),
                end_date=datetime(2024, 1, 1)  # End before start
            )


class TestComponentSpecs:
    """Test ComponentSpecs model."""
    
    def test_valid_specs(self):
        """Test creating valid component specifications."""
        specs = ComponentSpecs(
            pv_capacity_kw=10.0,
            battery_capacity_kwh=20.0,
            battery_power_kw=5.0,
            panel_efficiency=0.20,
            battery_efficiency=0.95
        )
        assert specs.pv_capacity_kw == 10.0
        assert specs.battery_capacity_kwh == 20.0
    
    def test_calculate_cost(self):
        """Test cost calculation."""
        specs = ComponentSpecs(
            pv_capacity_kw=10.0,
            battery_capacity_kwh=20.0,
            battery_power_kw=5.0
        )
        cost = specs.calculate_cost(
            pv_cost_per_kw=1000.0,
            battery_cost_per_kwh=500.0
        )
        expected_cost = (10.0 * 1000.0) + (20.0 * 500.0)
        assert cost == expected_cost
    
    def test_calculate_roof_area(self):
        """Test roof area calculation."""
        specs = ComponentSpecs(
            pv_capacity_kw=10.0,
            battery_capacity_kwh=20.0,
            battery_power_kw=5.0
        )
        area = specs.calculate_roof_area(panel_area_per_kw=5.0)
        assert area == 50.0  # 10 kW * 5 m²/kW


class TestSystemState:
    """Test SystemState model."""
    
    def test_valid_state(self):
        """Test creating a valid system state."""
        state = SystemState(
            timestep=0,
            soc=0.5,
            pv_power=5.0,
            load_demand=3.0,
            battery_power=0.0,
            grid_power=0.0
        )
        assert state.soc == 0.5
        assert state.pv_power == 5.0
    
    def test_invalid_soc(self):
        """Test that invalid SoC raises ValueError."""
        with pytest.raises(ValueError, match="SoC must be between 0 and 1"):
            SystemState(
                timestep=0,
                soc=1.5,  # Invalid
                pv_power=5.0,
                load_demand=3.0,
                battery_power=0.0,
                grid_power=0.0
            )
    
    def test_state_copy(self):
        """Test state deep copy."""
        state = SystemState(
            timestep=0,
            soc=0.5,
            pv_power=5.0,
            load_demand=3.0,
            battery_power=0.0,
            grid_power=0.0
        )
        copied = state.copy()
        assert copied.soc == state.soc
        assert copied.pv_power == state.pv_power
        assert copied is not state  # Different objects


class TestSimulationResult:
    """Test SimulationResult model."""
    
    def test_empty_result(self):
        """Test creating an empty result."""
        result = SimulationResult()
        assert len(result.states) == 0
        assert len(result.metrics) == 0
    
    def test_calculate_metrics(self):
        """Test calculating metrics from states."""
        # Create sample states
        states = [
            SystemState(
                timestep=i,
                soc=0.5,
                pv_power=5.0,
                load_demand=3.0,
                battery_power=0.0,
                grid_power=-2.0,  # Export
                total_cost=0.0,
                total_revenue=0.0
            )
            for i in range(10)
        ]
        
        result = SimulationResult(states=states)
        metrics = result.calculate_metrics()
        
        assert "total_pv_generation_kwh" in metrics
        assert "total_load_kwh" in metrics
        assert "self_consumption_ratio" in metrics
        assert metrics["total_pv_generation_kwh"] == 50.0  # 5 kW * 10 hours
        assert metrics["total_load_kwh"] == 30.0  # 3 kW * 10 hours


class TestOptimizationConfig:
    """Test OptimizationConfig model."""
    
    def test_valid_config(self):
        """Test creating a valid optimization configuration."""
        config = OptimizationConfig(
            budget_constraint=50000.0,
            roof_area_constraint=100.0,
            population_size=100,
            num_generations=50
        )
        assert config.budget_constraint == 50000.0
        assert config.population_size == 100
    
    def test_invalid_budget(self):
        """Test that invalid budget raises ValueError."""
        with pytest.raises(ValueError, match="budget_constraint must be positive"):
            OptimizationConfig(
                budget_constraint=-1000.0,  # Invalid
                roof_area_constraint=100.0
            )


# Run tests with: pytest backend/tests/unit/test_core_models.py -v
