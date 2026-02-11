"""
PV Calculation Input Value Object
===================================

Immutable value object representing inputs for PV power calculation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PVCalculationInput:
    """
    Immutable value object for PV power calculation parameters.
    
    Eliminates primitive obsession by grouping related parameters
    into a cohesive domain object.
    
    Attributes:
        ghi: Global Horizontal Irradiance (W/m²)
        temperature: Ambient temperature (°C)
        pv_capacity_kw: Installed PV capacity (kW)
        panel_efficiency: Panel efficiency (0-1)
        temperature_coefficient: Temperature power coefficient (per °C)
        inverter_efficiency: Inverter efficiency (0-1)
    """
    ghi: float
    temperature: float
    pv_capacity_kw: float
    panel_efficiency: float = 0.20
    temperature_coefficient: float = -0.004
    inverter_efficiency: float = 0.98
    
    def __post_init__(self):
        """Validate PV calculation inputs."""
        if self.ghi < 0:
            raise ValueError(f"GHI cannot be negative, got {self.ghi}")
        if self.pv_capacity_kw < 0:
            raise ValueError(f"PV capacity cannot be negative, got {self.pv_capacity_kw}")
        if not 0 < self.panel_efficiency <= 1:
            raise ValueError(f"Panel efficiency must be between 0 and 1, got {self.panel_efficiency}")
        if not 0 < self.inverter_efficiency <= 1:
            raise ValueError(f"Inverter efficiency must be between 0 and 1, got {self.inverter_efficiency}")
        if self.temperature_coefficient > 0:
            raise ValueError(f"Temperature coefficient should be negative, got {self.temperature_coefficient}")


@dataclass(frozen=True)
class BatterySimulationInput:
    """
    Immutable value object for battery simulation parameters.
    
    Eliminates primitive obsession for battery simulation inputs.
    
    Attributes:
        current_soc: Current state of charge (0-1)
        power_demand: Net power demand (kW)
                     - Positive: charge battery
                     - Negative: discharge battery
        battery_capacity_kwh: Battery capacity (kWh)
        charge_rate_kw: Maximum charge rate (kW)
        discharge_rate_kw: Maximum discharge rate (kW)
        efficiency: Round-trip efficiency (0-1)
        delta_t: Time step (hours)
        min_soc: Minimum allowed SoC (0-1)
        max_soc: Maximum allowed SoC (0-1)
    """
    current_soc: float
    power_demand: float
    battery_capacity_kwh: float
    charge_rate_kw: float
    discharge_rate_kw: float
    efficiency: float = 0.95
    delta_t: float = 1.0
    min_soc: float = 0.1
    max_soc: float = 0.9
    
    def __post_init__(self):
        """Validate battery simulation inputs."""
        if not 0 <= self.current_soc <= 1:
            raise ValueError(f"SoC must be between 0 and 1, got {self.current_soc}")
        if self.battery_capacity_kwh < 0:
            raise ValueError("Battery capacity cannot be negative")
        if self.charge_rate_kw < 0:
            raise ValueError("Charge rate cannot be negative")
        if self.discharge_rate_kw < 0:
            raise ValueError("Discharge rate cannot be negative")
        if not 0 < self.efficiency <= 1:
            raise ValueError(f"Efficiency must be between 0 and 1, got {self.efficiency}")
        if self.delta_t <= 0:
            raise ValueError("Time step must be positive")
        if not 0 <= self.min_soc < self.max_soc <= 1:
            raise ValueError("Invalid SoC limits")


@dataclass(frozen=True)
class SimulationStepInput:
    """
    Immutable value object for simulation step parameters.
    
    Eliminates primitive obsession for step method inputs.
    
    Attributes:
        load_demand: Load demand for this timestep (kW)
        ghi: Global Horizontal Irradiance (W/m²)
        temperature: Ambient temperature (°C)
        control_action: Control signal from controller (-1 to 1)
                       - Positive: Increase battery charge
                       - Negative: Increase battery discharge
                       - Zero: Let system decide
    """
    load_demand: float
    ghi: float
    temperature: float
    control_action: float
    
    def __post_init__(self):
        """Validate simulation step inputs."""
        if self.load_demand < 0:
            raise ValueError("Load demand cannot be negative")
        if self.ghi < 0:
            raise ValueError("GHI cannot be negative")
        if not -1 <= self.control_action <= 1:
            raise ValueError(f"Control action must be between -1 and 1, got {self.control_action}")
