"""
Baseline Interface
==================

Defines the contract for baseline/benchmark strategies.
Used for comparative validation of AI-based solutions.

Implementation: All phases (flat, brute-force, rule-based)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np


class IBaseline(ABC):
    """
    Abstract interface for baseline strategies.
    
    Purpose: Establish performance benchmarks for AI methods.
    Types:
    - Flat profiles (Phase 2)
    - Brute-force optimization (Phase 3)
    - Rule-based control (Phase 4)
    """
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute baseline strategy.
        
        Args:
            **kwargs: Strategy-specific parameters
            
        Returns:
            Strategy-specific output
        """
        pass
    
    @abstractmethod
    def compare_with_ai(
        self,
        ai_results: Dict[str, Any],
        baseline_results: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Compare baseline performance against AI method.
        
        Args:
            ai_results: Results from AI-based method
            baseline_results: Results from baseline method
            
        Returns:
            Comparison metrics (improvement %, statistical tests, etc.)
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        Get human-readable description of baseline strategy.
        
        Returns:
            Description string
        """
        pass
