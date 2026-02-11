"""
Physics Engine Interface
=========================

Defines the contract for deterministic energy system simulation.
Handles PV generation, battery dynamics, and grid interaction.

Implementation: Phase 1
"""

from abc import ABC, abstractmethod
from ..models.system_state import SystemState
from ..models.component_specs import ComponentSpecs
from ..models.calculation_inputs import (
    PVCalculationInput,
    BatterySimulationInput,
    SimulationStepInput
)
from ..models.battery_simulation_result import BatterySimulationResult


class IPhysicsEngine(ABC):
    """
    Abstract interface for physics-based energy system simulation.
    
    Responsibilities:
    - Calculate PV power generation
    - Simulate battery charge/discharge dynamics
    - Compute grid import/export
    - Track system state transitions
    
    Design: Uses value objects to eliminate primitive obsession and tuple returns.
    """
    
    @abstractmethod
    def calculate_pv_power(self, input_data: PVCalculationInput) -> float:
        """
        Calculate PV power output based on weather conditions.
        
        Args:
            input_data: PVCalculationInput value object containing all parameters
            
        Returns:
            PV power output (kW)
        """
        pass
    
    @abstractmethod
    def simulate_battery(self, input_data: BatterySimulationInput) -> BatterySimulationResult:
        """
        Simulate battery behavior for one time step.
        
        Args:
            input_data: BatterySimulationInput value object containing all parameters
            
        Returns:
            BatterySimulationResult value object containing:
            - new_soc: Updated state of charge (0-1)
            - actual_power_flow: Actual power to/from battery (kW)
            - grid_power: Power to/from grid (kW, positive=import)
            - energy_stored: Energy added to battery (kWh)
            - energy_discharged: Energy removed from battery (kWh)
            - efficiency_loss: Energy lost to inefficiency (kWh)
        """
        pass
    
    @abstractmethod
    def step(
        self,
        state: SystemState,
        specs: ComponentSpecs,
        step_input: SimulationStepInput
    ) -> SystemState:
        """
        Execute one simulation time step.
        
        Args:
            state: Current system state
            specs: Component specifications
            step_input: SimulationStepInput value object containing:
                - load_demand: Load demand for this timestep (kW)
                - ghi: Global Horizontal Irradiance (W/m²)
                - temperature: Ambient temperature (°C)
                - control_action: Control signal from controller (-1 to 1)
            
        Returns:
            Updated system state
        """
        pass
