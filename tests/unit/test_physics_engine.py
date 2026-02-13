"""
Unit Tests for PhysicsEngine
==============================

Comprehensive tests for deterministic physics simulation.
"""

import pytest
import numpy as np

from backend.services.physics.physics_engine import PhysicsEngine
from backend.core.models import (
    SystemState,
    ComponentSpecs,
    PVCalculationInput,
    BatterySimulationInput,
    BatterySimulationResult,
    SimulationStepInput
)
from backend.core.exceptions import PhysicsEngineError


@pytest.fixture
def physics_engine():
    """Create PhysicsEngine instance."""
    return PhysicsEngine()


@pytest.fixture
def standard_specs():
    """Create standard component specifications."""
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


class TestPVPowerCalculation:
    """Test PV power calculation."""
    
    def test_standard_conditions(self, physics_engine):
        """Test PV power under standard test conditions (STC)."""
        input_data = PVCalculationInput(
            ghi=1000.0,  # STC irradiance
            temperature=25.0,  # STC ambient (cell will be 45°C)
            pv_capacity_kw=10.0,
            panel_efficiency=0.20,
            temperature_coefficient=-0.004,
            inverter_efficiency=0.96
        )
        
        power = physics_engine.calculate_pv_power(input_data)
        
        # At STC, output should be close to rated capacity
        # Cell temp = 25 + 20 = 45°C → temp_factor = 1 + (-0.004)(45-25) = 0.92
        # power = 10 * (1000/1000) * 0.92 * 0.96 = 8.832 kW
        expected_power = 10.0 * 1.0 * 0.92 * 0.96
        assert pytest.approx(power, rel=0.01) == expected_power
    
    def test_zero_irradiance(self, physics_engine):
        """Test PV power at night (zero irradiance)."""
        input_data = PVCalculationInput(
            ghi=0.0,
            temperature=15.0,
            pv_capacity_kw=10.0,
            panel_efficiency=0.20,
            temperature_coefficient=-0.004,
            inverter_efficiency=0.96
        )
        
        power = physics_engine.calculate_pv_power(input_data)
        assert power == 0.0
    
    def test_low_irradiance(self, physics_engine):
        """Test PV power under cloudy conditions."""
        input_data = PVCalculationInput(
            ghi=200.0,  # 20% of STC
            temperature=20.0,
            pv_capacity_kw=10.0,
            panel_efficiency=0.20,
            temperature_coefficient=-0.004,
            inverter_efficiency=0.96
        )
        
        power = physics_engine.calculate_pv_power(input_data)
        
        # power = 10 * (200/1000) * temp_factor * 0.96
        # Cell temp = 20 + 20 = 40°C → temp_factor = 1 + (-0.004)(40-25) = 0.94
        expected_power = 10.0 * 0.2 * 0.94 * 0.96
        assert pytest.approx(power, rel=0.01) == expected_power
    
    def test_high_temperature(self, physics_engine):
        """Test PV power on a hot day."""
        input_data = PVCalculationInput(
            ghi=1000.0,
            temperature=40.0,  # Hot ambient → cell = 60°C
            pv_capacity_kw=10.0,
            panel_efficiency=0.20,
            temperature_coefficient=-0.004,
            inverter_efficiency=0.96
        )
        
        power = physics_engine.calculate_pv_power(input_data)
        
        # Cell temp = 40 + 20 = 60°C → temp_factor = 1 + (-0.004)(60-25) = 0.86
        expected_power = 10.0 * 1.0 * 0.86 * 0.96
        assert pytest.approx(power, rel=0.01) == expected_power
    
    def test_cold_temperature(self, physics_engine):
        """Test PV power on a cold day (higher efficiency)."""
        input_data = PVCalculationInput(
            ghi=1000.0,
            temperature=-10.0,  # Cold ambient → cell = 10°C
            pv_capacity_kw=10.0,
            panel_efficiency=0.20,
            temperature_coefficient=-0.004,
            inverter_efficiency=0.96
        )
        
        power = physics_engine.calculate_pv_power(input_data)
        
        # Cell temp = -10 + 20 = 10°C → temp_factor = 1 + (-0.004)(10-25) = 1.06
        expected_power = 10.0 * 1.0 * 1.06 * 0.96
        assert pytest.approx(power, rel=0.01) == expected_power
    
    def test_negative_irradiance(self, physics_engine):
        """Test handling of invalid negative irradiance."""
        # Negative GHI should raise ValueError during validation
        with pytest.raises(ValueError, match="GHI cannot be negative"):
            input_data = PVCalculationInput(
                ghi=-100.0,
                temperature=25.0,
                pv_capacity_kw=10.0,
                panel_efficiency=0.20,
                temperature_coefficient=-0.004,
                inverter_efficiency=0.96
            )


class TestBatterySimulation:
    """Test battery simulation."""
    
    def test_charging(self, physics_engine):
        """Test battery charging."""
        input_data = BatterySimulationInput(
            current_soc=0.5,
            power_demand=5.0,  # 5 kW charging
            battery_capacity_kwh=20.0,
            charge_rate_kw=5.0,
            discharge_rate_kw=5.0,
            efficiency=0.95,
            delta_t=1.0,  # 1 hour
            min_soc=0.2,
            max_soc=0.9
        )
        
        result = physics_engine.simulate_battery(input_data)
        
        # Energy stored = 5 kW * 1 hr * 0.95 = 4.75 kWh
        # New SoC = (0.5 * 20 + 4.75) / 20 = 0.7375
        expected_soc = (10.0 + 4.75) / 20.0
        assert pytest.approx(result.new_soc, rel=0.01) == expected_soc
        assert result.actual_power_flow == pytest.approx(5.0, rel=0.01)
        assert result.energy_stored == pytest.approx(4.75, rel=0.01)
        assert result.is_charging  # Property, not method
    
    def test_discharging(self, physics_engine):
        """Test battery discharging."""
        input_data = BatterySimulationInput(
            current_soc=0.7,
            power_demand=-4.0,  # 4 kW discharge
            battery_capacity_kwh=20.0,
            charge_rate_kw=5.0,
            discharge_rate_kw=5.0,
            efficiency=0.95,
            delta_t=1.0,
            min_soc=0.2,
            max_soc=0.9
        )
        
        result = physics_engine.simulate_battery(input_data)
        
        # Energy needed from battery = 4 kW * 1 hr / 0.95 = 4.21 kWh
        # New SoC = (0.7 * 20 - 4.21) / 20 = 0.4895
        energy_from_battery = 4.0 / 0.95
        expected_soc = (14.0 - energy_from_battery) / 20.0
        assert pytest.approx(result.new_soc, rel=0.01) == expected_soc
        assert result.actual_power_flow < 0  # Negative for discharge
        assert result.energy_discharged > 0
        assert result.is_discharging  # Property, not method
    
    def test_charging_to_max_soc(self, physics_engine):
        """Test charging when approaching max SoC."""
        input_data = BatterySimulationInput(
            current_soc=0.85,
            power_demand=5.0,  # Try to charge 5 kW
            battery_capacity_kwh=20.0,
            charge_rate_kw=5.0,
            discharge_rate_kw=5.0,
            efficiency=0.95,
            delta_t=1.0,
            min_soc=0.2,
            max_soc=0.9
        )
        
        result = physics_engine.simulate_battery(input_data)
        
        # Max SoC is 0.9, already at 0.85
        # Available capacity = (0.9 - 0.85) * 20 = 1.0 kWh
        # Can only charge 1.0 kWh
        assert result.new_soc == pytest.approx(0.9, rel=0.01)
        assert result.actual_power_flow < 5.0  # Limited by available capacity
        assert result.grid_power > 0  # Excess power goes to grid
    
    def test_discharging_to_min_soc(self, physics_engine):
        """Test discharging when approaching min SoC."""
        input_data = BatterySimulationInput(
            current_soc=0.25,
            power_demand=-5.0,  # Try to discharge 5 kW
            battery_capacity_kwh=20.0,
            charge_rate_kw=5.0,
            discharge_rate_kw=5.0,
            efficiency=0.95,
            delta_t=1.0,
            min_soc=0.2,
            max_soc=0.9
        )
        
        result = physics_engine.simulate_battery(input_data)
        
        # Min SoC is 0.2, currently at 0.25
        # Available energy = (0.25 - 0.2) * 20 = 1.0 kWh
        # Can only discharge ~0.95 kW (accounting for efficiency)
        assert result.new_soc == pytest.approx(0.2, rel=0.01)
        assert abs(result.actual_power_flow) < 5.0  # Limited by available energy
        assert result.grid_power > 0  # Need to import from grid
    
    def test_idle(self, physics_engine):
        """Test battery in idle state (no charging or discharging)."""
        input_data = BatterySimulationInput(
            current_soc=0.6,
            power_demand=0.0,
            battery_capacity_kwh=20.0,
            charge_rate_kw=5.0,
            discharge_rate_kw=5.0,
            efficiency=0.95,
            delta_t=1.0,
            min_soc=0.2,
            max_soc=0.9
        )
        
        result = physics_engine.simulate_battery(input_data)
        
        assert result.new_soc == 0.6  # No change
        assert result.actual_power_flow == 0.0
        assert result.grid_power == 0.0
        assert result.is_idle  # Property, not method
    
    def test_efficiency_loss(self, physics_engine):
        """Test efficiency loss calculation."""
        input_data = BatterySimulationInput(
            current_soc=0.5,
            power_demand=5.0,
            battery_capacity_kwh=20.0,
            charge_rate_kw=5.0,
            discharge_rate_kw=5.0,
            efficiency=0.95,
            delta_t=1.0,
            min_soc=0.2,
            max_soc=0.9
        )
        
        result = physics_engine.simulate_battery(input_data)
        
        # Input energy = 5 kWh, stored = 4.75 kWh, loss = 0.25 kWh
        expected_loss = 5.0 * 1.0 - 4.75
        assert pytest.approx(result.efficiency_loss, rel=0.01) == expected_loss


class TestSimulationStep:
    """Test complete simulation step."""
    
    def test_sunny_day_excess_pv(self, physics_engine, initial_state, standard_specs):
        """Test step with excess PV power (charge battery)."""
        step_input = SimulationStepInput(
            ghi=800.0,
            temperature=25.0,
            load_demand=2.0,  # Low load
            control_action=1.0  # Full charging
        )
        
        new_state = physics_engine.step(initial_state, standard_specs, step_input)
        
        # PV should generate significant power
        assert new_state.pv_power > 5.0
        
        # Net power = PV - Load > 0 → battery should charge
        assert new_state.soc > initial_state.soc
        
        # Grid should export if PV > Load + Battery charge
        assert new_state.timestep == 1
    
    def test_night_high_load(self, physics_engine, initial_state, standard_specs):
        """Test step at night with high load (discharge battery + grid import)."""
        step_input = SimulationStepInput(
            ghi=0.0,  # Night
            temperature=15.0,
            load_demand=8.0,  # High load
            control_action=-1.0  # Full discharge
        )
        
        new_state = physics_engine.step(initial_state, standard_specs, step_input)
        
        # No PV power at night
        assert new_state.pv_power == 0.0
        
        # Battery should discharge
        assert new_state.soc < initial_state.soc
        
        # Grid should import (battery alone can't meet 8 kW load with 5 kW discharge rate)
        assert new_state.grid_power > 0
        
        # Cost should increase
        assert new_state.total_cost > 0
    
    def test_cost_accounting(self, physics_engine, initial_state, standard_specs):
        """Test cost tracking."""
        step_input = SimulationStepInput(
            ghi=0.0,
            temperature=20.0,
            load_demand=5.0,
            control_action=0.0
        )
        
        new_state = physics_engine.step(initial_state, standard_specs, step_input)
        
        # Should have imported from grid → cost > 0
        assert new_state.total_cost > 0
        assert new_state.total_revenue == 0
    
    def test_battery_degradation_tracking(self, physics_engine, initial_state, standard_specs):
        """Test battery cycle tracking."""
        # Discharge battery significantly
        step_input = SimulationStepInput(
            ghi=0.0,
            temperature=20.0,
            load_demand=10.0,
            control_action=-1.0
        )
        
        new_state = physics_engine.step(initial_state, standard_specs, step_input)
        
        # Battery cycles should increase
        assert new_state.battery_cycles > 0
    
    def test_state_accumulation(self, physics_engine, initial_state, standard_specs):
        """Test that costs and cycles accumulate over multiple steps."""
        step_input = SimulationStepInput(
            ghi=0.0,
            temperature=20.0,
            load_demand=5.0,
            control_action=0.0
        )
        
        # Step 1
        state1 = physics_engine.step(initial_state, standard_specs, step_input)
        cost1 = state1.total_cost
        
        # Step 2
        state2 = physics_engine.step(state1, standard_specs, step_input)
        cost2 = state2.total_cost
        
        # Costs should accumulate
        assert cost2 > cost1
        assert state2.timestep == 2


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_extreme_temperature(self, physics_engine):
        """Test PV calculation at extreme temperature."""
        input_data = PVCalculationInput(
            ghi=1000.0,
            temperature=60.0,  # Very hot
            pv_capacity_kw=10.0,
            panel_efficiency=0.20,
            temperature_coefficient=-0.004,
            inverter_efficiency=0.96
        )
        
        power = physics_engine.calculate_pv_power(input_data)
        
        # Should still produce power, just reduced
        assert power > 0
        assert power < 10.0  # Less than rated capacity
    
    def test_very_small_timestep(self, physics_engine):
        """Test battery simulation with small timestep."""
        input_data = BatterySimulationInput(
            current_soc=0.5,
            power_demand=5.0,
            battery_capacity_kwh=20.0,
            charge_rate_kw=5.0,
            discharge_rate_kw=5.0,
            efficiency=0.95,
            delta_t=0.1,  # 6 minutes
            min_soc=0.2,
            max_soc=0.9
        )
        
        result = physics_engine.simulate_battery(input_data)
        
        # Should still work correctly with small timestep
        assert 0.2 <= result.new_soc <= 0.9
        assert result.energy_stored < 1.0  # Small energy change
