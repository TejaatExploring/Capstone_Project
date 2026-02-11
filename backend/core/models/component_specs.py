"""
Component Specifications Model
===============================

Defines specifications for energy system components (PV, Battery, etc.).
"""

from dataclasses import dataclass


@dataclass
class ComponentSpecs:
    """
    Specifications for energy system components.
    
    Attributes:
        pv_capacity_kw: PV array capacity (kW)
        battery_capacity_kwh: Battery energy capacity (kWh)
        battery_power_kw: Battery power rating (kW)
        panel_efficiency: PV panel efficiency (0-1)
        battery_efficiency: Battery round-trip efficiency (0-1)
        inverter_efficiency: Inverter efficiency (0-1)
        temperature_coefficient: PV temperature coefficient (per °C)
        min_soc: Minimum allowed state of charge (0-1)
        max_soc: Maximum allowed state of charge (0-1)
        initial_soc: Initial state of charge (0-1)
    """
    pv_capacity_kw: float
    battery_capacity_kwh: float
    battery_power_kw: float
    panel_efficiency: float = 0.20
    battery_efficiency: float = 0.95
    inverter_efficiency: float = 0.98
    temperature_coefficient: float = -0.004
    min_soc: float = 0.1
    max_soc: float = 0.9
    initial_soc: float = 0.5
    
    def __post_init__(self):
        """Validate component specifications."""
        if self.pv_capacity_kw < 0:
            raise ValueError("PV capacity cannot be negative")
        if self.battery_capacity_kwh < 0:
            raise ValueError("Battery capacity cannot be negative")
        if self.battery_power_kw < 0:
            raise ValueError("Battery power rating cannot be negative")
        if not 0 < self.panel_efficiency <= 1:
            raise ValueError("Panel efficiency must be between 0 and 1")
        if not 0 < self.battery_efficiency <= 1:
            raise ValueError("Battery efficiency must be between 0 and 1")
        if not 0 < self.inverter_efficiency <= 1:
            raise ValueError("Inverter efficiency must be between 0 and 1")
        if not 0 <= self.min_soc < self.max_soc <= 1:
            raise ValueError("Invalid SoC limits")
        if not self.min_soc <= self.initial_soc <= self.max_soc:
            raise ValueError("Initial SoC outside allowed range")
    
    def calculate_cost(
        self,
        pv_cost_per_kw: float,
        battery_cost_per_kwh: float
    ) -> float:
        """
        Calculate total component cost.
        
        Args:
            pv_cost_per_kw: PV cost (USD/kW)
            battery_cost_per_kwh: Battery cost (USD/kWh)
            
        Returns:
            Total cost (USD)
        """
        pv_cost = self.pv_capacity_kw * pv_cost_per_kw
        battery_cost = self.battery_capacity_kwh * battery_cost_per_kwh
        return pv_cost + battery_cost
    
    def calculate_roof_area(self, panel_area_per_kw: float = 5.0) -> float:
        """
        Calculate required roof area.
        
        Args:
            panel_area_per_kw: Roof area per kW (m²/kW)
            
        Returns:
            Required roof area (m²)
        """
        return self.pv_capacity_kw * panel_area_per_kw
