"""
Pytest Configuration
====================

Shared fixtures and configuration for all tests.
"""

import pytest
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture
def sample_simulation_config():
    """Fixture providing sample simulation configuration."""
    from datetime import datetime
    from backend.core.models import SimulationConfig
    
    return SimulationConfig(
        latitude=40.7128,
        longitude=-74.0060,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        timestep_hours=1.0,
        random_seed=42
    )


@pytest.fixture
def sample_component_specs():
    """Fixture providing sample component specifications."""
    from backend.core.models import ComponentSpecs
    
    return ComponentSpecs(
        pv_capacity_kw=10.0,
        battery_capacity_kwh=20.0,
        battery_power_kw=5.0,
        panel_efficiency=0.20,
        battery_efficiency=0.95,
        initial_soc=0.5
    )


@pytest.fixture
def sample_system_state():
    """Fixture providing sample system state."""
    from backend.core.models import SystemState
    
    return SystemState(
        timestep=0,
        soc=0.5,
        pv_power=5.0,
        load_demand=3.0,
        battery_power=0.0,
        grid_power=0.0
    )
