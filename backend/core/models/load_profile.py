"""
Load Profile Domain Models
===========================

Value objects representing load consumption profiles.
These are immutable, validated domain entities.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass(frozen=True)
class DailyLoadProfile:
    """
    Represents a 24-hour load profile for a single day.
    
    Purpose: Encapsulate daily consumption patterns for clustering
    Invariants:
        - Must have exactly 24 hourly values
        - All values must be non-negative
        - Values represent kW demand
    """
    hourly_loads: np.ndarray = field(repr=False)  # Shape: (24,)
    date: Optional[str] = None
    cluster_id: Optional[int] = None
    
    def __post_init__(self):
        """Validate invariants."""
        if self.hourly_loads.shape != (24,):
            raise ValueError(f"DailyLoadProfile must have 24 hours, got {len(self.hourly_loads)}")
        if np.any(self.hourly_loads < 0):
            raise ValueError("Load values cannot be negative")
    
    @property
    def mean_load(self) -> float:
        """Average load for the day (kW)."""
        return float(np.mean(self.hourly_loads))
    
    @property
    def peak_load(self) -> float:
        """Maximum load for the day (kW)."""
        return float(np.max(self.hourly_loads))
    
    @property
    def total_energy(self) -> float:
        """Total energy consumed in the day (kWh)."""
        return float(np.sum(self.hourly_loads))
    
    @property
    def load_factor(self) -> float:
        """Load factor: mean_load / peak_load."""
        peak = self.peak_load
        return self.mean_load / peak if peak > 0 else 0.0


@dataclass(frozen=True)
class LoadProfile:
    """
    Represents a multi-hour load profile (e.g., 720 hours = 30 days).
    
    Purpose: Encapsulate generated or historical load sequences
    Invariants:
        - All values must be non-negative
        - Values represent kW demand at hourly intervals
    """
    hourly_loads: np.ndarray = field(repr=False)  # Shape: (n_hours,)
    start_timestamp: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate invariants."""
        if self.hourly_loads.ndim != 1:
            raise ValueError("LoadProfile must be 1-dimensional array")
        if np.any(self.hourly_loads < 0):
            raise ValueError("Load values cannot be negative")
        if len(self.hourly_loads) == 0:
            raise ValueError("LoadProfile cannot be empty")
    
    @property
    def duration_hours(self) -> int:
        """Number of hours in the profile."""
        return len(self.hourly_loads)
    
    @property
    def mean_load(self) -> float:
        """Average load (kW)."""
        return float(np.mean(self.hourly_loads))
    
    @property
    def peak_load(self) -> float:
        """Maximum load (kW)."""
        return float(np.max(self.hourly_loads))
    
    @property
    def min_load(self) -> float:
        """Minimum load (kW)."""
        return float(np.min(self.hourly_loads))
    
    @property
    def std_load(self) -> float:
        """Standard deviation of load (kW)."""
        return float(np.std(self.hourly_loads))
    
    @property
    def total_energy(self) -> float:
        """Total energy consumed (kWh)."""
        return float(np.sum(self.hourly_loads))
    
    def to_daily_profiles(self) -> List[DailyLoadProfile]:
        """
        Split the load profile into daily 24-hour profiles.
        
        Returns:
            List of DailyLoadProfile objects
            
        Note:
            If duration is not a multiple of 24, the last incomplete day is discarded.
        """
        n_complete_days = self.duration_hours // 24
        daily_profiles = []
        
        for day_idx in range(n_complete_days):
            start_hour = day_idx * 24
            end_hour = start_hour + 24
            daily_loads = self.hourly_loads[start_hour:end_hour]
            
            daily_profiles.append(DailyLoadProfile(
                hourly_loads=daily_loads,
                cluster_id=None
            ))
        
        return daily_profiles
    
    def get_statistics(self) -> dict:
        """
        Get comprehensive statistics about the load profile.
        
        Returns:
            Dictionary with statistical metrics
        """
        return {
            "duration_hours": self.duration_hours,
            "mean_kw": self.mean_load,
            "std_kw": self.std_load,
            "min_kw": self.min_load,
            "max_kw": self.peak_load,
            "total_kwh": self.total_energy,
            "percentile_25": float(np.percentile(self.hourly_loads, 25)),
            "percentile_50": float(np.percentile(self.hourly_loads, 50)),
            "percentile_75": float(np.percentile(self.hourly_loads, 75)),
            "percentile_95": float(np.percentile(self.hourly_loads, 95)),
        }


@dataclass(frozen=True)
class ClusteringResult:
    """
    Stores the result of KMeans clustering on daily load profiles.
    
    Purpose: Encapsulate clustering model state
    """
    n_clusters: int
    cluster_centers: np.ndarray  # Shape: (n_clusters, 24)
    labels: np.ndarray  # Shape: (n_days,)
    silhouette_score: float
    inertia: float
    
    def __post_init__(self):
        """Validate invariants."""
        if self.n_clusters <= 0:
            raise ValueError("Number of clusters must be positive")
        if self.cluster_centers.shape[0] != self.n_clusters:
            raise ValueError(f"Expected {self.n_clusters} cluster centers")
        if self.cluster_centers.shape[1] != 24:
            raise ValueError("Cluster centers must have 24 hourly values")
        if not -1 <= self.silhouette_score <= 1:
            raise ValueError("Silhouette score must be in [-1, 1]")
    
    def get_cluster_distribution(self) -> np.ndarray:
        """
        Get the probability distribution over clusters.
        
        Returns:
            Array of shape (n_clusters,) with probabilities summing to 1
        """
        counts = np.bincount(self.labels, minlength=self.n_clusters)
        return counts / counts.sum()


@dataclass(frozen=True)
class MarkovTransitionMatrix:
    """
    Stores the Markov transition probability matrix for cluster transitions.
    
    Purpose: Model the temporal dynamics of cluster transitions day-to-day
    Invariants:
        - Must be square matrix (n_clusters x n_clusters)
        - Each row must sum to 1 (probability distribution)
        - All values must be in [0, 1]
    """
    matrix: np.ndarray  # Shape: (n_clusters, n_clusters)
    n_clusters: int
    smoothing_alpha: float = 0.01
    
    def __post_init__(self):
        """Validate invariants."""
        if self.matrix.shape != (self.n_clusters, self.n_clusters):
            raise ValueError(
                f"Transition matrix must be {self.n_clusters}x{self.n_clusters}, "
                f"got {self.matrix.shape}"
            )
        
        # Check if all values in [0, 1]
        if np.any(self.matrix < 0) or np.any(self.matrix > 1):
            raise ValueError("Transition probabilities must be in [0, 1]")
        
        # Check if rows sum to 1 (with tolerance for floating point)
        row_sums = np.sum(self.matrix, axis=1)
        if not np.allclose(row_sums, 1.0, atol=1e-6):
            raise ValueError(f"Transition matrix rows must sum to 1, got {row_sums}")
    
    def sample_next_state(self, current_state: int, rng: np.random.Generator) -> int:
        """
        Sample the next cluster state given current state.
        
        Args:
            current_state: Current cluster ID (0 to n_clusters-1)
            rng: Random number generator for reproducibility
            
        Returns:
            Next cluster ID sampled from transition probabilities
        """
        if not 0 <= current_state < self.n_clusters:
            raise ValueError(f"Invalid state {current_state}, must be in [0, {self.n_clusters})")
        
        probabilities = self.matrix[current_state, :]
        next_state = rng.choice(self.n_clusters, p=probabilities)
        return int(next_state)
