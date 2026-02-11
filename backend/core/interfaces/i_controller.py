"""
Controller Interface
====================

Defines the contract for real-time energy dispatch control.
Makes decisions on battery charge/discharge and grid interaction.

Implementation: Phase 4 (Brain 2 - DQN)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np
from ..models.system_state import SystemState


class IController(ABC):
    """
    Abstract interface for energy dispatch controllers.
    
    Strategy: Learn optimal control policy through reinforcement learning.
    Brain 2: Deep Q-Network (DQN)
    """
    
    @abstractmethod
    def select_action(
        self,
        state: SystemState,
        deterministic: bool = False
    ) -> float:
        """
        Select control action based on current system state.
        
        Args:
            state: Current system state
            deterministic: If True, use greedy action (no exploration)
            
        Returns:
            Control action (-1 to 1)
            - Positive: Charge battery from grid/PV
            - Negative: Discharge battery to load
        """
        pass
    
    @abstractmethod
    def train(
        self,
        num_episodes: int,
        load_profiles: list,
        weather_data: list,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Train the controller using reinforcement learning.
        
        Args:
            num_episodes: Number of training episodes
            load_profiles: List of training load profiles
            weather_data: List of corresponding weather data
            verbose: Whether to print training progress
            
        Returns:
            Training metrics (rewards, losses, etc.)
        """
        pass
    
    @abstractmethod
    def save_policy(self, path: str) -> None:
        """
        Save trained policy to disk.
        
        Args:
            path: File path to save policy
        """
        pass
    
    @abstractmethod
    def load_policy(self, path: str) -> None:
        """
        Load pre-trained policy from disk.
        
        Args:
            path: File path to load policy from
        """
        pass
    
    @abstractmethod
    def get_training_metrics(self) -> Dict[str, Any]:
        """
        Get training performance metrics.
        
        Returns:
            Dictionary with episode rewards, losses, epsilon values, etc.
        """
        pass
