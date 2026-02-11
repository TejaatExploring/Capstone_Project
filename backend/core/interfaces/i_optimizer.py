"""
Optimizer Interface
===================

Defines the contract for system sizing optimization.
Optimizes PV and battery capacity subject to constraints.

Implementation: Phase 3 (Brain 1b - Genetic Algorithm)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from ..models.component_specs import ComponentSpecs
from ..models.simulation_config import OptimizationConfig


class IOptimizer(ABC):
    """
    Abstract interface for system component optimization.
    
    Strategy: Multi-objective optimization with constraints.
    Brain 1b: Genetic Algorithm using DEAP
    """
    
    @abstractmethod
    def optimize(
        self,
        load_profile: List[float],
        weather_data: Dict[str, List[float]],
        config: OptimizationConfig
    ) -> Tuple[ComponentSpecs, Dict[str, float]]:
        """
        Optimize system component sizing.
        
        Args:
            load_profile: Hourly load demand profile (kW)
            weather_data: Weather data (GHI, temperature)
            config: Optimization configuration (constraints, objectives)
            
        Returns:
            Tuple of (optimal_specs, optimization_metrics)
            - optimal_specs: Optimized component specifications
            - optimization_metrics: Generation history, convergence, etc.
        """
        pass
    
    @abstractmethod
    def evaluate_fitness(
        self,
        specs: ComponentSpecs,
        load_profile: List[float],
        weather_data: Dict[str, List[float]]
    ) -> float:
        """
        Evaluate fitness of a given system configuration.
        
        Args:
            specs: Component specifications to evaluate
            load_profile: Load demand profile
            weather_data: Weather data
            
        Returns:
            Fitness score (higher is better)
        """
        pass
    
    @abstractmethod
    def get_convergence_history(self) -> Dict[str, List[float]]:
        """
        Get optimization convergence history.
        
        Returns:
            Dictionary with generation-wise best/avg/worst fitness
        """
        pass
