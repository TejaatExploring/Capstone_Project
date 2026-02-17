"""
Load Clustering Module
=======================

KMeans clustering for daily load profiles with automatic K optimization.

Responsibilities:
    - Cluster daily 24-hour load profiles
    - Optimize number of clusters using silhouette score
    - Store and retrieve cluster centroids
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from typing import Optional, Tuple
import logging

from backend.core.models import DailyLoadProfile, ClusteringResult

logger = logging.getLogger(__name__)


class LoadClusterer:
    """
    Clusters daily load profiles using KMeans algorithm.
    
    Purpose:
        Discover typical daily consumption patterns (e.g., weekday, weekend, high-load)
        
    Algorithm:
        1. Extract daily 24-hour profiles
        2. Optional: Standardize features
        3. Try K = k_min to k_max
        4. Select K with best silhouette score
        5. Store cluster centroids
        
    Complexity:
        Training: O(n_days * K * 24 * iterations)
        Inference: O(K * 24)
        
    Assumptions:
        - Daily profiles are somewhat stable
        - Clusters represent load behavior archetypes
    """
    
    def __init__(
        self,
        k_min: int = 2,
        k_max: int = 10,
        random_state: int = 42,
        standardize: bool = True
    ):
        """
        Initialize the clusterer.
        
        Args:
            k_min: Minimum number of clusters to try
            k_max: Maximum number of clusters to try
            random_state: Random seed for reproducibility
            standardize: Whether to standardize features before clustering
        """
        self.k_min = k_min
        self.k_max = k_max
        self.random_state = random_state
        self.standardize = standardize
        
        self.scaler: Optional[StandardScaler] = None
        self.kmeans: Optional[KMeans] = None
        self.clustering_result: Optional[ClusteringResult] = None
        
        logger.info(f"LoadClusterer initialized (K range: {k_min}-{k_max})")
    
    def fit(
        self,
        daily_profiles: np.ndarray,
        n_clusters: Optional[int] = None
    ) -> ClusteringResult:
        """
        Fit KMeans clustering on daily load profiles.
        
        Args:
            daily_profiles: Array of shape (n_days, 24) with daily load profiles
            n_clusters: Fixed number of clusters (None = auto-optimize)
            
        Returns:
            ClusteringResult containing cluster information
            
        Raises:
            ValueError: If input data is invalid
        """
        logger.info(f"Fitting clusterer on {len(daily_profiles)} daily profiles")
        
        # Validate input
        if daily_profiles.ndim != 2 or daily_profiles.shape[1] != 24:
            raise ValueError(
                f"Expected shape (n_days, 24), got {daily_profiles.shape}"
            )
        
        if len(daily_profiles) < self.k_max:
            logger.warning(
                f"Not enough days ({len(daily_profiles)}) for k_max={self.k_max}, "
                f"reducing to {len(daily_profiles) // 2}"
            )
            self.k_max = max(2, len(daily_profiles) // 2)
        
        # Standardize features if requested
        X = daily_profiles.copy()
        if self.standardize:
            self.scaler = StandardScaler()
            X = self.scaler.fit_transform(X)
            logger.debug("Features standardized")
        
        # Determine optimal K
        if n_clusters is None:
            optimal_k, best_score = self._find_optimal_k(X)
            logger.info(f"Optimal K={optimal_k} (silhouette={best_score:.4f})")
        else:
            optimal_k = n_clusters
            logger.info(f"Using fixed K={optimal_k}")
        
        # Fit final model with optimal K
        self.kmeans = KMeans(
            n_clusters=optimal_k,
            random_state=self.random_state,
            n_init=10
        )
        labels = self.kmeans.fit_predict(X)
        
        # Get cluster centers in original scale
        if self.standardize:
            centers_original = self.scaler.inverse_transform(self.kmeans.cluster_centers_)
        else:
            centers_original = self.kmeans.cluster_centers_
        
        # Compute silhouette score on original data
        if len(np.unique(labels)) > 1:
            sil_score = silhouette_score(daily_profiles, labels)
        else:
            sil_score = -1.0
            logger.warning("Only one cluster, silhouette score undefined")
        
        # Create result object
        self.clustering_result = ClusteringResult(
            n_clusters=optimal_k,
            cluster_centers=centers_original,
            labels=labels,
            silhouette_score=sil_score,
            inertia=self.kmeans.inertia_
        )
        
        logger.info(f"Clustering complete: K={optimal_k}, silhouette={sil_score:.4f}")
        return self.clustering_result
    
    def _find_optimal_k(self, X: np.ndarray) -> Tuple[int, float]:
        """
        Find optimal number of clusters using silhouette score.
        
        Args:
            X: Standardized feature matrix
            
        Returns:
            Tuple of (optimal_k, best_silhouette_score)
        """
        logger.debug(f"Searching for optimal K in range [{self.k_min}, {self.k_max}]")
        
        best_k = self.k_min
        best_score = -1.0
        scores = {}
        
        for k in range(self.k_min, self.k_max + 1):
            # Fit KMeans
            kmeans_temp = KMeans(
                n_clusters=k,
                random_state=self.random_state,
                n_init=10
            )
            labels = kmeans_temp.fit_predict(X)
            
            # Compute silhouette score
            if len(np.unique(labels)) > 1:
                score = silhouette_score(X, labels)
                scores[k] = score
                
                logger.debug(f"K={k}: silhouette={score:.4f}")
                
                if score > best_score:
                    best_score = score
                    best_k = k
        
        return best_k, best_score
    
    def predict(self, daily_profile: np.ndarray) -> int:
        """
        Predict cluster label for a single daily profile.
        
        Args:
            daily_profile: Array of shape (24,) with hourly loads
            
        Returns:
            Cluster label (0 to n_clusters-1)
            
        Raises:
            ValueError: If model not trained
        """
        if self.kmeans is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        if daily_profile.shape != (24,):
            raise ValueError(f"Expected shape (24,), got {daily_profile.shape}")
        
        # Reshape for sklearn
        X = daily_profile.reshape(1, -1)
        
        # Standardize if needed
        if self.standardize and self.scaler is not None:
            X = self.scaler.transform(X)
        
        label = self.kmeans.predict(X)[0]
        return int(label)
    
    def get_cluster_summary(self) -> dict:
        """
        Get summary information about the clustering result.
        
        Returns:
            Dictionary with cluster statistics
            
        Raises:
            ValueError: If model not trained
        """
        if self.clustering_result is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        result = self.clustering_result
        distribution = result.get_cluster_distribution()
        
        summary = {
            'n_clusters': result.n_clusters,
            'silhouette_score': result.silhouette_score,
            'inertia': result.inertia,
            'cluster_sizes': dict(zip(range(result.n_clusters), distribution)),
        }
        
        # Add mean load for each cluster
        for i in range(result.n_clusters):
            cluster_mean = float(np.mean(result.cluster_centers[i]))
            cluster_peak = float(np.max(result.cluster_centers[i]))
            summary[f'cluster_{i}_mean_kw'] = cluster_mean
            summary[f'cluster_{i}_peak_kw'] = cluster_peak
        
        return summary
    
    def extract_daily_profiles(
        self,
        hourly_data: pd.DataFrame
    ) -> np.ndarray:
        """
        Extract daily 24-hour profiles from hourly time series.
        
        Args:
            hourly_data: DataFrame with 'load_kw' column and DatetimeIndex
            
        Returns:
            Array of shape (n_complete_days, 24)
        """
        if 'load_kw' not in hourly_data.columns:
            raise ValueError("DataFrame must have 'load_kw' column")
        
        # Ensure hourly frequency and continuous index
        hourly_data = hourly_data.asfreq('H', fill_value=0.0)
        
        # Get complete days only
        n_complete_days = len(hourly_data) // 24
        n_hours_to_use = n_complete_days * 24
        
        if n_complete_days == 0:
            raise ValueError("Need at least 24 hours of data")
        
        # Truncate to complete days
        data_truncated = hourly_data['load_kw'].values[:n_hours_to_use]
        
        # Reshape into (n_days, 24)
        daily_profiles = data_truncated.reshape(n_complete_days, 24)
        
        logger.debug(f"Extracted {n_complete_days} daily profiles")
        return daily_profiles
