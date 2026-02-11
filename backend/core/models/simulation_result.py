"""
Simulation Result Model
========================

Encapsulates complete simulation results with performance metrics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import numpy as np


@dataclass
class SimulationResult:
    """
    Complete results from an energy system simulation.
    
    Attributes:
        states: Time series of system states
        metrics: Performance metrics
        metadata: Additional simulation metadata
    """
    states: List['SystemState'] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_metrics(self) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics from states.
        
        Returns:
            Dictionary of performance metrics
        """
        if not self.states:
            return {}
        
        # Extract time series
        pv_power = np.array([s.pv_power for s in self.states])
        load_demand = np.array([s.load_demand for s in self.states])
        battery_power = np.array([s.battery_power for s in self.states])
        grid_power = np.array([s.grid_power for s in self.states])
        soc = np.array([s.soc for s in self.states])
        
        # Calculate metrics
        total_pv_generation = np.sum(pv_power)
        total_load = np.sum(load_demand)
        total_grid_import = np.sum(np.maximum(grid_power, 0))
        total_grid_export = np.sum(np.minimum(grid_power, 0))
        
        self.metrics = {
            "total_pv_generation_kwh": total_pv_generation,
            "total_load_kwh": total_load,
            "total_grid_import_kwh": total_grid_import,
            "total_grid_export_kwh": abs(total_grid_export),
            "self_consumption_ratio": (total_pv_generation - abs(total_grid_export)) / total_pv_generation if total_pv_generation > 0 else 0,
            "self_sufficiency_ratio": (total_load - total_grid_import) / total_load if total_load > 0 else 0,
            "total_cost_usd": self.states[-1].total_cost if self.states else 0,
            "total_revenue_usd": self.states[-1].total_revenue if self.states else 0,
            "net_cost_usd": (self.states[-1].total_cost - self.states[-1].total_revenue) if self.states else 0,
            "battery_cycles": self.states[-1].battery_cycles if self.states else 0,
            "unmet_load_kwh": self.states[-1].unmet_load if self.states else 0,
            "excess_pv_kwh": self.states[-1].excess_pv if self.states else 0,
            "avg_soc": np.mean(soc),
            "min_soc": np.min(soc),
            "max_soc": np.max(soc),
        }
        
        return self.metrics
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "metrics": self.metrics,
            "metadata": self.metadata,
            "num_timesteps": len(self.states)
        }
