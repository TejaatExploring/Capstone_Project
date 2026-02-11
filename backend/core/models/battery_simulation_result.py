"""
Battery Simulation Result Value Object
========================================

Immutable value object representing the result of battery simulation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BatterySimulationResult:
    """
    Immutable value object for battery simulation results.
    
    Eliminates tuple return types by providing a well-defined,
    self-documenting domain object.
    
    Attributes:
        new_soc: Updated state of charge (0-1)
        actual_power_flow: Actual power to/from battery (kW)
                          - Positive: charging
                          - Negative: discharging
        grid_power: Power to/from grid (kW)
                   - Positive: import from grid
                   - Negative: export to grid
        energy_stored: Energy added to battery (kWh)
        energy_discharged: Energy removed from battery (kWh)
        efficiency_loss: Energy lost to inefficiency (kWh)
    """
    new_soc: float
    actual_power_flow: float
    grid_power: float
    energy_stored: float
    energy_discharged: float
    efficiency_loss: float
    
    def __post_init__(self):
        """Validate battery simulation results."""
        if not 0 <= self.new_soc <= 1:
            raise ValueError(f"SoC must be between 0 and 1, got {self.new_soc}")
        if self.energy_stored < 0:
            raise ValueError("energy_stored cannot be negative")
        if self.energy_discharged < 0:
            raise ValueError("energy_discharged cannot be negative")
        if self.efficiency_loss < 0:
            raise ValueError("efficiency_loss cannot be negative")
    
    @property
    def is_charging(self) -> bool:
        """Check if battery is charging."""
        return self.actual_power_flow > 0
    
    @property
    def is_discharging(self) -> bool:
        """Check if battery is discharging."""
        return self.actual_power_flow < 0
    
    @property
    def is_idle(self) -> bool:
        """Check if battery is idle."""
        return self.actual_power_flow == 0
    
    @property
    def is_importing(self) -> bool:
        """Check if importing from grid."""
        return self.grid_power > 0
    
    @property
    def is_exporting(self) -> bool:
        """Check if exporting to grid."""
        return self.grid_power < 0
