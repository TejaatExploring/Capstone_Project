"""
Load Generator Interface
=========================

Defines the contract for synthetic load profile generation.
Uses machine learning to generate realistic load patterns.

Implementation: Phase 2 (Brain 1a - Markov + KMeans)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
import numpy as np


class ILoadGenerator(ABC):
    """
    Abstract interface for load profile generation services.
    
    Strategy: Use historical data + ML to generate realistic load patterns.
    Brain 1a: Markov Chain + KMeans clustering
    """
    
    @abstractmethod
    def train(self, data_path: str, n_clusters: int = None) -> Dict[str, float]:
        """
        Train the load generation model on historical data.
        
        Args:
            data_path: Path to CSV file with historical load data
            n_clusters: Number of clusters for KMeans (None = auto-optimize)
            
        Returns:
            Training metrics (e.g., silhouette_score, n_clusters_used)
        """
        pass
    
    @abstractmethod
    def generate_profile(
        self,
        duration_hours: int = 720,
        seed: int = None
    ) -> np.ndarray:
        """
        Generate a synthetic load profile.
        
        Args:
            duration_hours: Length of profile to generate (default: 720 = 30 days)
            seed: Random seed for reproducibility
            
        Returns:
            Array of load values (kW) for each hour
        """
        pass
    
    @abstractmethod
    def save_model(self, path: str) -> None:
        """
        Persist the trained model to disk.
        
        Args:
            path: File path to save model (.pkl)
        """
        pass
    
    @abstractmethod
    def load_model(self, path: str) -> None:
        """
        Load a pre-trained model from disk.
        
        Args:
            path: File path to load model from (.pkl)
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, float]:
        """
        Get statistical properties of generated profiles.
        
        Returns:
            Dictionary with mean, std, min, max, etc.
        """
        pass
