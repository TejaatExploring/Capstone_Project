"""
Deterministic Physics Engine
==============================

Production-grade physics simulation for solar-battery-grid systems.
Implements deterministic calculations for PV generation, battery dynamics,
and grid interaction.

Mathematical Models:
-------------------
1. PV Power: P_out = P_rated × (GHI / 1000) × [1 - γ(T_cell - 25)]
2. Battery: SoC dynamics with charge/discharge limits
3. Grid: Import/export based on power balance

No AI/ML components - pure physics simulation.
"""

from typing import Optional
import numpy as np

from ...core.interfaces import IPhysicsEngine
from ...core.models import (
    SystemState,
    ComponentSpecs,
    PVCalculationInput,
    BatterySimulationInput,
    BatterySimulationResult,
    SimulationStepInput
)
from ...core.exceptions import PhysicsEngineError
from ...infrastructure.config.constants import (
    STANDARD_TEST_CONDITION_IRRADIANCE,
    STANDARD_TEST_CONDITION_TEMPERATURE
)
from ...infrastructure.logging import get_logger

logger = get_logger(__name__)


class PhysicsEngine(IPhysicsEngine):
    """
    Deterministic physics simulation engine.
    
    Implements:
    - PV power generation based on irradiance and temperature
    - Battery charge/discharge dynamics with efficiency
    - Grid import/export logic
    - System state transitions
    
    Design:
    - Stateless (pure functions)
    - Uses value objects for inputs/outputs
    - Comprehensive validation
    - No side effects
    """
    
    def __init__(self):
        """Initialize physics engine."""
        logger.info("PhysicsEngine initialized")
    
    def calculate_pv_power(self, input_data: PVCalculationInput) -> float:
        """
        Calculate PV power output based on weather conditions.
        
        Formula:
            P_out = P_rated × (GHI / 1000) × η_inverter × [1 - γ(T_cell - 25)]
        
        Where:
            - P_rated: PV capacity (kW)
            - GHI: Global Horizontal Irradiance (W/m²)
            - γ: Temperature coefficient (typically -0.004/°C)
            - T_cell: Cell temperature (°C)
            - T_cell ≈ T_ambient + 20 (simple approximation)
        
        Args:
            input_data: PVCalculationInput value object
            
        Returns:
            PV power output (kW), guaranteed non-negative
        """
        try:
            # Handle edge case: zero irradiance
            if input_data.ghi <= 0:
                return 0.0
            
            # Calculate cell temperature (simple approximation)
            # In reality: T_cell = T_ambient + (NOCT - 20) * (GHI / 800)
            # We use simplified: T_cell = T_ambient + 20
            cell_temperature = input_data.temperature + 20.0
            
            # Temperature derating factor
            # Reference: 25°C (Standard Test Conditions)
            temp_diff = cell_temperature - STANDARD_TEST_CONDITION_TEMPERATURE
            temp_factor = 1.0 + (input_data.temperature_coefficient * temp_diff)
            
            # Ensure temp_factor doesn't go negative (extreme cold)
            temp_factor = max(temp_factor, 0.0)
            
            # Irradiance factor (normalized to 1000 W/m² STC)
            irradiance_factor = input_data.ghi / STANDARD_TEST_CONDITION_IRRADIANCE
            
            # Calculate power output
            power_output = (
                input_data.pv_capacity_kw
                * irradiance_factor
                * temp_factor
                * input_data.inverter_efficiency
            )
            
            # Ensure non-negative
            power_output = max(power_output, 0.0)
            
            return power_output
            
        except Exception as e:
            raise PhysicsEngineError(f"PV power calculation failed: {e}")
    
    def simulate_battery(
        self,
        input_data: BatterySimulationInput
    ) -> BatterySimulationResult:
        """
        Simulate battery behavior for one time step.
        
        Physics:
        -------
        - Charge: Energy flows INTO battery (reduces from grid/PV)
        - Discharge: Energy flows OUT of battery (supplies load)
        - Efficiency loss applies in both directions
        - SoC bounds: [min_soc, max_soc]
        - Power limits: charge_rate_kw, discharge_rate_kw
        
        Args:
            input_data: BatterySimulationInput value object
            
        Returns:
            BatterySimulationResult with new SoC, power flows, and energy accounting
        """
        try:
            current_soc = input_data.current_soc
            power_demand = input_data.power_demand  # +ve = charge, -ve = discharge
            capacity = input_data.battery_capacity_kwh
            efficiency = input_data.efficiency
            delta_t = input_data.delta_t
            
            # Initialize result variables
            actual_power_flow = 0.0
            grid_power = 0.0
            energy_stored = 0.0
            energy_discharged = 0.0
            efficiency_loss = 0.0
            
            # Charging scenario
            if power_demand > 0:
                # Limit by charge rate
                charge_power = min(power_demand, input_data.charge_rate_kw)
                
                # Calculate energy that would be stored (accounting for efficiency)
                energy_to_store = charge_power * delta_t * efficiency
                
                # Check SoC limits
                current_energy = current_soc * capacity
                max_energy = input_data.max_soc * capacity
                available_capacity = max_energy - current_energy
                
                if available_capacity <= 0:
                    # Battery full
                    new_soc = input_data.max_soc
                    actual_power_flow = 0.0
                    grid_power = power_demand  # All power goes to grid (or is wasted)
                else:
                    # Can charge
                    actual_energy_stored = min(energy_to_store, available_capacity)
                    actual_power_flow = actual_energy_stored / (delta_t * efficiency)
                    
                    new_soc = (current_energy + actual_energy_stored) / capacity
                    new_soc = min(new_soc, input_data.max_soc)
                    
                    energy_stored = actual_energy_stored
                    efficiency_loss = (actual_power_flow * delta_t) - actual_energy_stored
                    grid_power = power_demand - actual_power_flow
            
            # Discharging scenario
            elif power_demand < 0:
                # Limit by discharge rate
                discharge_power = min(abs(power_demand), input_data.discharge_rate_kw)
                
                # Calculate energy that needs to be taken from battery
                energy_needed = discharge_power * delta_t
                
                # Check SoC limits
                current_energy = current_soc * capacity
                min_energy = input_data.min_soc * capacity
                available_energy = current_energy - min_energy
                
                if available_energy <= 0:
                    # Battery empty
                    new_soc = input_data.min_soc
                    actual_power_flow = 0.0
                    grid_power = abs(power_demand)  # Import from grid
                else:
                    # Can discharge
                    actual_energy_removed = min(energy_needed / efficiency, available_energy)
                    actual_output_power = actual_energy_removed * efficiency / delta_t
                    actual_power_flow = -actual_output_power
                    
                    new_soc = (current_energy - actual_energy_removed) / capacity
                    new_soc = max(new_soc, input_data.min_soc)
                    
                    energy_discharged = actual_energy_removed
                    efficiency_loss = actual_energy_removed - (actual_output_power * delta_t)
                    
                    # If couldn't meet full demand, import from grid
                    shortfall = abs(power_demand) - actual_output_power
                    grid_power = max(shortfall, 0.0)
            
            # Idle scenario
            else:
                new_soc = current_soc
                actual_power_flow = 0.0
                grid_power = 0.0
            
            # Create result value object
            result = BatterySimulationResult(
                new_soc=new_soc,
                actual_power_flow=actual_power_flow,
                grid_power=grid_power,
                energy_stored=energy_stored,
                energy_discharged=energy_discharged,
                efficiency_loss=efficiency_loss
            )
            
            return result
            
        except Exception as e:
            raise PhysicsEngineError(f"Battery simulation failed: {e}")
    
    def step(
        self,
        state: SystemState,
        specs: ComponentSpecs,
        step_input: SimulationStepInput
    ) -> SystemState:
        """
        Execute one simulation time step.
        
        Logic Flow:
        -----------
        1. Calculate PV power from weather
        2. Determine net power (PV - Load)
        3. Apply control action to battery
        4. Calculate grid import/export
        5. Update system state
        
        Args:
            state: Current system state
            specs: Component specifications
            step_input: Simulation step inputs (load, weather, control)
            
        Returns:
            Updated system state
        """
        try:
            # Step 1: Calculate PV power
            pv_input = PVCalculationInput(
                ghi=step_input.ghi,
                temperature=step_input.temperature,
                pv_capacity_kw=specs.pv_capacity_kw,
                panel_efficiency=specs.panel_efficiency,
                temperature_coefficient=specs.temperature_coefficient,
                inverter_efficiency=specs.inverter_efficiency
            )
            pv_power = self.calculate_pv_power(pv_input)
            
            # Step 2: Calculate net power (PV - Load)
            net_power = pv_power - step_input.load_demand
            
            # Step 3: Determine battery action based on control signal and net power
            # Control action: -1 (force discharge) to +1 (force charge)
            # If net_power > 0: excess PV available
            # If net_power < 0: power shortage
            
            # Battery power demand calculation
            if net_power > 0:
                # Excess power available - can charge
                # Control action modulates charging
                # control_action = +1.0 → charge fully with excess
                # control_action = 0.0 → charge at 50% of excess
                # control_action = -1.0 → don't charge (may even force discharge)
                if step_input.control_action >= 0:
                    battery_power_demand = net_power * (0.5 + 0.5 * step_input.control_action)
                else:
                    # Negative control action: force discharge even with excess PV
                    battery_power_demand = abs(net_power) * step_input.control_action
            elif net_power < 0:
                # Power shortage - need to discharge or import from grid
                # control_action = -1.0 → discharge fully to meet shortfall
                # control_action = 0.0 → discharge at 50% of shortfall (rest from grid)
                # control_action = +1.0 → don't discharge, import all from grid
                battery_power_demand = net_power * (1.0 - step_input.control_action) / 2.0
            else:
                # Perfect balance
                battery_power_demand = 0.0
            
            # Step 4: Simulate battery
            battery_input = BatterySimulationInput(
                current_soc=state.soc,
                power_demand=battery_power_demand,
                battery_capacity_kwh=specs.battery_capacity_kwh,
                charge_rate_kw=specs.battery_power_kw,
                discharge_rate_kw=specs.battery_power_kw,
                efficiency=specs.battery_efficiency,
                delta_t=1.0,  # 1 hour timestep
                min_soc=specs.min_soc,
                max_soc=specs.max_soc
            )
            battery_result = self.simulate_battery(battery_input)
            
            # Step 5: Calculate grid power using strict energy balance
            # ========================================================
            # SIGN CONVENTION:
            # - battery_result.actual_power_flow > 0: Battery CHARGING (consuming power)
            # - battery_result.actual_power_flow < 0: Battery DISCHARGING (providing power)
            #
            # ENERGY BALANCE EQUATION:
            # Load_demand = PV_power + Battery_discharge + Grid_import
            #
            # Rearranging:
            # Grid = Load - PV + Battery_power (since charging adds to demand)
            #
            # Grid > 0: Importing from grid
            # Grid < 0: Exporting to grid
            
            grid_power = (
                step_input.load_demand 
                - pv_power 
                + battery_result.actual_power_flow  # Charging is positive, adds to demand
            )
            
            # Note: battery_result.grid_power is NOT used here - it's already accounted for
            # in battery_result.actual_power_flow (battery limits what it can provide)
            
            # Step 6: Calculate costs
            # Simple cost model (will be enhanced in Brain 2)
            electricity_cost = 0.15  # USD/kWh
            sell_price = 0.08  # USD/kWh
            
            if grid_power > 0:
                # Importing
                step_cost = grid_power * electricity_cost
                step_revenue = 0.0
            else:
                # Exporting
                step_cost = 0.0
                step_revenue = abs(grid_power) * sell_price
            
            # Step 7: Track battery degradation (cycles)
            # One full cycle = discharge from 100% to 0%
            energy_throughput = battery_result.energy_discharged
            cycle_increment = energy_throughput / specs.battery_capacity_kwh
            
            # Step 8: Track unmet load and excess PV
            # =======================================
            # ASSUMPTION: Grid has unlimited capacity
            # Therefore, unmet_load = 0 (grid can always meet demand)
            # 
            # Excess PV: Amount of PV generation exported to grid (couldn't use locally)
            unmet_load = 0.0  # Unlimited grid assumption
            excess_pv = abs(grid_power) if grid_power < 0 else 0.0
            
            # Step 9: Energy conservation validation (optional debug check)
            # =============================================================
            # Total Energy IN:  PV + Battery_discharge + Grid_import
            # Total Energy OUT: Load + Battery_charge + Grid_export
            # These should balance (within numerical tolerance)
            
            battery_discharge = abs(battery_result.actual_power_flow) if battery_result.actual_power_flow < 0 else 0.0
            battery_charge = battery_result.actual_power_flow if battery_result.actual_power_flow > 0 else 0.0
            grid_import = grid_power if grid_power > 0 else 0.0
            grid_export = abs(grid_power) if grid_power < 0 else 0.0
            
            energy_in = pv_power + battery_discharge + grid_import
            energy_out = step_input.load_demand + battery_charge + grid_export
            energy_balance_error = abs(energy_in - energy_out)
            
            if energy_balance_error > 1e-3:  # Tolerance: 1 Watt
                logger.warning(
                    f"Energy balance violation at timestep {state.timestep + 1}: "
                    f"IN={energy_in:.6f} kW, OUT={energy_out:.6f} kW, "
                    f"ERROR={energy_balance_error:.6f} kW"
                )
            
            # Step 10: Create new system state
            new_state = SystemState(
                timestep=state.timestep + 1,
                soc=battery_result.new_soc,
                pv_power=pv_power,
                load_demand=step_input.load_demand,
                battery_power=battery_result.actual_power_flow,
                grid_power=grid_power,  # Corrected: no longer double-counting
                total_cost=state.total_cost + step_cost,
                total_revenue=state.total_revenue + step_revenue,
                battery_cycles=state.battery_cycles + cycle_increment,
                unmet_load=state.unmet_load + unmet_load,  # Always 0 for unlimited grid
                excess_pv=state.excess_pv + excess_pv
            )
            
            return new_state
            
        except Exception as e:
            raise PhysicsEngineError(f"Simulation step failed: {e}")
