"""
Load Generator Service
=======================

Main service implementing synthetic load generation using Markov + KMeans.

Architecture: Implements ILoadGenerator interface
Strategy: Cluster-based Markov Chain generation
"""

import numpy as np
import pickle
from pathlib import Path
from typing import Dict, Optional
import logging

from backend.core.interfaces import ILoadGenerator
from backend.core.models import LoadProfile, ClusteringResult, MarkovTransitionMatrix
from .data_loader import SmartMeterDataLoader
from .clustering import LoadClusterer
from .markov_model import MarkovLoadModel

logger = logging.getLogger(__name__)


class LoadGenerator(ILoadGenerator):
    """
    Synthetic load profile generator using Markov Chain + KMeans clustering.
    
    Architecture:
        Implements: ILoadGenerator (Clean Architecture compliance)
        Dependencies: SmartMeterDataLoader, LoadClusterer, MarkovLoadModel
        
    Algorithm:
        1. Training Phase:
            a. Load historical smart meter data
            b. Extract daily 24-hour profiles
            c. Cluster profiles using KMeans (auto-optimize K)
            d. Build Markov transition matrix from cluster sequence
            e. Persist models to disk
            
        2. Generation Phase:
            a. Generate cluster sequence using Markov chain
            b. For each cluster: sample from centroid + Gaussian noise
            c. Concatenate hourly values
            d. Apply bounds and smoothing
            e. Return LoadProfile
            
    Performance:
        - Training: < 10 seconds for 1 year data
        - Generation: < 1 second for 720 hours
        
    Complexity:
        - Training: O(n_days * K * iterations)
        - Generation: O(n_days_to_generate * 24)
    """
    
    def __init__(
        self,
        k_min: int = 2,
        k_max: int = 10,
        smoothing_alpha: float = 0.01,
        noise_std_ratio: float = 0.1,
        random_state: int = 42
    ):
        """
        Initialize Load Generator.
        
        Args:
            k_min: Minimum clusters to try
            k_max: Maximum clusters to try
            smoothing_alpha: Markov smoothing parameter
            noise_std_ratio: Std of Gaussian noise as ratio of centroid mean
            random_state: Random seed for reproducibility
        """
        self.k_min = k_min
        self.k_max = k_max
        self.smoothing_alpha = smoothing_alpha
        self.noise_std_ratio = noise_std_ratio
        self.random_state = random_state
        
        # Components (initialized during training)
        self.data_loader = SmartMeterDataLoader()
        self.clusterer: Optional[LoadClusterer] = None
        self.markov_model: Optional[MarkovLoadModel] = None
        
        # Training artifacts
        self.clustering_result: Optional[ClusteringResult] = None
        self.transition_matrix: Optional[MarkovTransitionMatrix] = None
        self.training_stats: dict = {}
        
        logger.info("LoadGenerator initialized")
    
    def train(self, data_path: str, n_clusters: int = None) -> Dict[str, float]:
        """
        Train the load generation model on historical data.
        
        Args:
            data_path: Path to smart meter CSV file
            n_clusters: Fixed number of clusters (None = auto-optimize)
            
        Returns:
            Training metrics dictionary
        """
        logger.info(f"Starting training on {data_path}")
        
        # Step 1: Load and preprocess data
        logger.info("Step 1/4: Loading data...")
        df_hourly = self.data_loader.load_and_preprocess(data_path)
        data_stats = self.data_loader.get_summary_statistics(df_hourly)
        logger.info(f"Loaded {data_stats['duration_hours']} hours ({data_stats['duration_days']:.1f} days)")
        
        # Step 2: Cluster daily profiles
        logger.info("Step 2/4: Clustering daily profiles...")
        self.clusterer = LoadClusterer(
            k_min=self.k_min,
            k_max=self.k_max,
            random_state=self.random_state
        )
        
        daily_profiles = self.clusterer.extract_daily_profiles(df_hourly)
        self.clustering_result = self.clusterer.fit(daily_profiles, n_clusters)
        cluster_stats = self.clusterer.get_cluster_summary()
        logger.info(
            f"Clustered into K={self.clustering_result.n_clusters} groups "
            f"(silhouette={self.clustering_result.silhouette_score:.4f})"
        )
        
        # Step 3: Build Markov transition model
        logger.info("Step 3/4: Building Markov transition model...")
        self.markov_model = MarkovLoadModel(
            n_clusters=self.clustering_result.n_clusters,
            smoothing_alpha=self.smoothing_alpha
        )
        
        self.transition_matrix = self.markov_model.fit(self.clustering_result.labels)
        markov_stats = self.markov_model.get_transition_summary()
        logger.info("Markov model trained")
        
        # Step 4: Compile training statistics
        self.training_stats = {
            **data_stats,
            **cluster_stats,
            **markov_stats,
            'noise_std_ratio': self.noise_std_ratio,
        }
        
        logger.info("Training complete")
        return self.training_stats
    
    def generate_profile(
        self,
        duration_hours: int = 720,
        seed: int = None
    ) -> np.ndarray:
        """
        Generate synthetic load profile.
        
        Args:
            duration_hours: Number of hours to generate (default: 720 = 30 days)
            seed: Random seed (None = use class random_state)
            
        Returns:
            Array of load values (kW) for each hour
            
        Raises:
            ValueError: If model not trained
        """
        if self.clustering_result is None or self.transition_matrix is None:
            raise ValueError("Model not trained. Call train() or load_model() first.")
        
        logger.info(f"Generating {duration_hours} hours of load profile")
        
        # Setup RNG
        if seed is None:
            seed = self.random_state
        rng = np.random.default_rng(seed)
        
        # Calculate number of days needed
        n_days = int(np.ceil(duration_hours / 24))
        
        # Step 1: Generate cluster sequence using Markov chain
        cluster_sequence = self.markov_model.generate_sequence(
            n_days=n_days,
            initial_state=None,  # Sample from uniform
            rng=rng
        )
        
        # Step 2: Generate hourly loads from cluster centroids + noise
        hourly_loads = []
        
        for day_idx, cluster_id in enumerate(cluster_sequence):
            # Get cluster centroid
            centroid = self.clustering_result.cluster_centers[cluster_id]
            
            # Add Gaussian noise for realism
            centroid_mean = np.mean(centroid)
            noise_std = centroid_mean * self.noise_std_ratio
            noise = rng.normal(0, noise_std, size=24)
            
            daily_loads = centroid + noise
            
            # Ensure non-negative
            daily_loads = np.maximum(daily_loads, 0.0)
            
            hourly_loads.extend(daily_loads)
        
        # Step 3: Truncate to exact duration
        hourly_loads = np.array(hourly_loads[:duration_hours])
        
        # Step 4: Apply smoothing at day boundaries to avoid discontinuities
        hourly_loads = self._smooth_profile(hourly_loads)
        
        logger.info(f"Generated profile: mean={np.mean(hourly_loads):.2f} kW, "
                   f"max={np.max(hourly_loads):.2f} kW")
        
        return hourly_loads
    
    def _smooth_profile(self, loads: np.ndarray, window_size: int = 3) -> np.ndarray:
        """
        Apply light smoothing to reduce sharp transitions.
        
        Args:
            loads: Hourly load array
            window_size: Moving average window size
            
        Returns:
            Smoothed load array
        """
        if len(loads) < window_size:
            return loads
        
        # Simple moving average
        smoothed = np.convolve(loads, np.ones(window_size)/window_size, mode='same')
        
        # Preserve edges
        smoothed[:window_size//2] = loads[:window_size//2]
        smoothed[-(window_size//2):] = loads[-(window_size//2):]
        
        return smoothed
    
    def save_model(self, path: str) -> None:
        """
        Persist trained model to disk.
        
        Args:
            path: Directory path to save model files
        """
        if self.clustering_result is None or self.transition_matrix is None:
            raise ValueError("Model not trained. Call train() first.")
        
        path_dir = Path(path)
        path_dir.mkdir(parents=True, exist_ok=True)
        
        # Save clusterer
        clusterer_path = path_dir / "kmeans_model.pkl"
        with open(clusterer_path, 'wb') as f:
            pickle.dump({
                'kmeans': self.clusterer.kmeans,
                'scaler': self.clusterer.scaler,
                'clustering_result': self.clustering_result,
            }, f)
        logger.info(f"Saved KMeans model to {clusterer_path}")
        
        # Save Markov model
        markov_path = path_dir / "markov_matrix.pkl"
        with open(markov_path, 'wb') as f:
            pickle.dump({
                'transition_matrix': self.transition_matrix,
                'n_clusters': self.markov_model.n_clusters,
                'smoothing_alpha': self.markov_model.smoothing_alpha,
            }, f)
        logger.info(f"Saved Markov model to {markov_path}")
        
        # Save training stats
        stats_path = path_dir / "training_stats.pkl"
        with open(stats_path, 'wb') as f:
            pickle.dump(self.training_stats, f)
        logger.info(f"Saved training stats to {stats_path}")
    
    def load_model(self, path: str) -> None:
        """
        Load pre-trained model from disk.
        
        Args:
            path: Directory path containing model files
        """
        path_dir = Path(path)
        
        if not path_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {path}")
        
        # Load clusterer
        clusterer_path = path_dir / "kmeans_model.pkl"
        with open(clusterer_path, 'rb') as f:
            cluster_data = pickle.load(f)
        
        self.clusterer = LoadClusterer(
            k_min=self.k_min,
            k_max=self.k_max,
            random_state=self.random_state
        )
        self.clusterer.kmeans = cluster_data['kmeans']
        self.clusterer.scaler = cluster_data['scaler']
        self.clustering_result = cluster_data['clustering_result']
        logger.info(f"Loaded KMeans model from {clusterer_path}")
        
        # Load Markov model
        markov_path = path_dir / "markov_matrix.pkl"
        with open(markov_path, 'rb') as f:
            markov_data = pickle.load(f)
        
        self.markov_model = MarkovLoadModel(
            n_clusters=markov_data['n_clusters'],
            smoothing_alpha=markov_data['smoothing_alpha']
        )
        self.transition_matrix = markov_data['transition_matrix']
        self.markov_model.transition_matrix = self.transition_matrix
        logger.info(f"Loaded Markov model from {markov_path}")
        
        # Load training stats
        stats_path = path_dir / "training_stats.pkl"
        if stats_path.exists():
            with open(stats_path, 'rb') as f:
                self.training_stats = pickle.load(f)
            logger.info(f"Loaded training stats from {stats_path}")
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Get statistical properties of the model.
        
        Returns:
            Dictionary with training statistics
        """
        if not self.training_stats:
            raise ValueError("Model not trained. Call train() first.")
        
        return self.training_stats.copy()
