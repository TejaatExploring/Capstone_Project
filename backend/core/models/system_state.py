"""
System State Model
==================

Represents the dynamic state of the energy system at any point in time.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemState:
    """
    Snapshot of energy system state at a specific timestep.
    
    Attributes:
        timestep: Current simulation timestep
        soc: Battery state of charge (0-1)
        pv_power: PV generation (kW)
        load_demand: Load demand (kW)
        battery_power: Battery power flow (kW, positive=charging)
        grid_power: Grid power flow (kW, positive=import)
        total_cost: Cumulative cost (USD)
        total_revenue: Cumulative revenue from grid export (USD)
        battery_cycles: Cumulative battery cycles
        unmet_load: Unmet load energy (kWh)
        excess_pv: Curtailed PV energy (kWh)
    """
    timestep: int
    soc: float
    pv_power: float
    load_demand: float
    battery_power: float
    grid_power: float
    total_cost: float = 0.0
    total_revenue: float = 0.0
    battery_cycles: float = 0.0
    unmet_load: float = 0.0
    excess_pv: float = 0.0
    
    def __post_init__(self):
        """Validate state values."""
        if not 0 <= self.soc <= 1:
            raise ValueError(f"SoC must be between 0 and 1, got {self.soc}")
        if self.pv_power < 0:
            raise ValueError(f"PV power cannot be negative, got {self.pv_power}")
        if self.load_demand < 0:
            raise ValueError(f"Load demand cannot be negative, got {self.load_demand}")
    
    def copy(self) -> 'SystemState':
        """Create a deep copy of the state."""
        return SystemState(
            timestep=self.timestep,
            soc=self.soc,
            pv_power=self.pv_power,
            load_demand=self.load_demand,
            battery_power=self.battery_power,
            grid_power=self.grid_power,
            total_cost=self.total_cost,
            total_revenue=self.total_revenue,
            battery_cycles=self.battery_cycles,
            unmet_load=self.unmet_load,
            excess_pv=self.excess_pv
        )
