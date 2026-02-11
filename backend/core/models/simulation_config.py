"""
Simulation Configuration Models
================================

Defines configuration objects for simulation and optimization.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class SimulationConfig:
    """
    Configuration for energy system simulation.
    
    Attributes:
        latitude: Location latitude (-90 to 90)
        longitude: Location longitude (-180 to 180)
        start_date: Simulation start date
        end_date: Simulation end date
        timestep_hours: Simulation timestep (default: 1 hour)
        random_seed: Random seed for reproducibility
    """
    latitude: float
    longitude: float
    start_date: datetime
    end_date: datetime
    timestep_hours: float = 1.0
    random_seed: Optional[int] = None
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        if self.timestep_hours <= 0:
            raise ValueError("timestep_hours must be positive")


@dataclass
class OptimizationConfig:
    """
    Configuration for genetic algorithm optimization.
    
    Attributes:
        budget_constraint: Maximum budget (USD)
        roof_area_constraint: Maximum roof area (m²)
        population_size: GA population size
        num_generations: Number of GA generations
        crossover_prob: Crossover probability
        mutation_prob: Mutation probability
        pv_cost_per_kw: PV cost (USD/kW)
        battery_cost_per_kwh: Battery cost (USD/kWh)
        electricity_cost_per_kwh: Grid electricity cost (USD/kWh)
        grid_sell_price_per_kwh: Grid sell price (USD/kWh)
        objectives: Optimization objectives
    """
    budget_constraint: float
    roof_area_constraint: float
    population_size: int = 100
    num_generations: int = 50
    crossover_prob: float = 0.7
    mutation_prob: float = 0.2
    pv_cost_per_kw: float = 1000.0
    battery_cost_per_kwh: float = 500.0
    electricity_cost_per_kwh: float = 0.15
    grid_sell_price_per_kwh: float = 0.08
    objectives: Dict[str, Any] = field(default_factory=lambda: {
        "minimize_cost": True,
        "maximize_self_consumption": True,
        "minimize_grid_import": True
    })
    
    def __post_init__(self):
        """Validate optimization parameters."""
        if self.budget_constraint <= 0:
            raise ValueError("budget_constraint must be positive")
        if self.roof_area_constraint <= 0:
            raise ValueError("roof_area_constraint must be positive")
        if self.population_size < 10:
            raise ValueError("population_size must be at least 10")
        if self.num_generations < 1:
            raise ValueError("num_generations must be at least 1")
        if not 0 <= self.crossover_prob <= 1:
            raise ValueError("crossover_prob must be between 0 and 1")
        if not 0 <= self.mutation_prob <= 1:
            raise ValueError("mutation_prob must be between 0 and 1")
