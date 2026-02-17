"""
Baseline Load Generators
=========================

Simple baseline models for comparison with ML-based generation.

Baselines:
    1. Flat Baseline - Constant average load
    2. Historical Replay - Random sampling of real days
    3. Statistical comparisons
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from scipy import stats
import logging

from backend.core.interfaces import ILoadGenerator

logger = logging.getLogger(__name__)


class FlatBaseline(ILoadGenerator):
    """
    Flat load profile baseline (constant average).
    
    Purpose: Simplest baseline - constant load based on historical average
    Use Case: Null model for comparison
    """
    
    def __init__(self):
        """Initialize flat baseline."""
        self.mean_load: float = 0.0
        self.trained = False
        logger.info("FlatBaseline initialized")
    
    def train(self, data_path: str, n_clusters: int = None) -> Dict[str, float]:
        """Train by computing average load."""
        from .data_loader import SmartMeterDataLoader
        
        loader = SmartMeterDataLoader()
        df = loader.load_and_preprocess(data_path)
        
        self.mean_load = float(df['load_kw'].mean())
        self.trained = True
        
        logger.info(f"FlatBaseline trained: mean_load={self.mean_load:.2f} kW")
        
        return {
            'mean_load_kw': self.mean_load,
            'model_type': 'flat_baseline'
        }
    
    def generate_profile(
        self,
        duration_hours: int = 720,
        seed: int = None
    ) -> np.ndarray:
        """Generate flat profile (constant load)."""
        if not self.trained:
            raise ValueError("Model not trained")
        
        profile = np.full(duration_hours, self.mean_load)
        logger.debug(f"Generated flat profile: {duration_hours} hours @ {self.mean_load:.2f} kW")
        return profile
    
    def save_model(self, path: str) -> None:
        """Save mean load value."""
        import pickle
        from pathlib import Path
        
        path_file = Path(path) / "flat_baseline.pkl"
        path_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path_file, 'wb') as f:
            pickle.dump({'mean_load': self.mean_load}, f)
        logger.info(f"Saved FlatBaseline to {path_file}")
    
    def load_model(self, path: str) -> None:
        """Load mean load value."""
        import pickle
        from pathlib import Path
        
        path_file = Path(path) / "flat_baseline.pkl"
        
        with open(path_file, 'rb') as f:
            data = pickle.load(f)
        
        self.mean_load = data['mean_load']
        self.trained = True
        logger.info(f"Loaded FlatBaseline from {path_file}")
    
    def get_statistics(self) -> Dict[str, float]:
        """Get baseline statistics."""
        if not self.trained:
            raise ValueError("Model not trained")
        return {'mean_load_kw': self.mean_load}


class HistoricalReplayBaseline(ILoadGenerator):
    """
    Historical replay baseline - randomly sample real historical days.
    
    Purpose: Re-use actual historical data by random sampling
    Advantage: Preserves real load patterns
    Disadvantage: Limited diversity (only replays existing days)
    """
    
    def __init__(self):
        """Initialize historical replay baseline."""
        self.daily_profiles: np.ndarray = np.array([])  # Shape: (n_days, 24)
        self.trained = False
        logger.info("HistoricalReplayBaseline initialized")
    
    def train(self, data_path: str, n_clusters: int = None) -> Dict[str, float]:
        """Load historical daily profiles."""
        from .data_loader import SmartMeterDataLoader
        from .clustering import LoadClusterer
        
        loader = SmartMeterDataLoader()
        df = loader.load_and_preprocess(data_path)
        
        clusterer = LoadClusterer()
        self.daily_profiles = clusterer.extract_daily_profiles(df)
        self.trained = True
        
        logger.info(f"HistoricalReplayBaseline trained: {len(self.daily_profiles)} days")
        
        return {
            'n_days': len(self.daily_profiles),
            'mean_load_kw': float(np.mean(self.daily_profiles)),
            'model_type': 'historical_replay'
        }
    
    def generate_profile(
        self,
        duration_hours: int = 720,
        seed: int = None
    ) -> np.ndarray:
        """Generate profile by randomly sampling historical days."""
        if not self.trained:
            raise ValueError("Model not trained")
        
        rng = np.random.default_rng(seed)
        
        n_days = int(np.ceil(duration_hours / 24))
        
        # Randomly sample days with replacement
        sampled_indices = rng.integers(0, len(self.daily_profiles), size=n_days)
        sampled_days = self.daily_profiles[sampled_indices]
        
        # Flatten to hourly profile
        hourly_profile = sampled_days.flatten()[:duration_hours]
        
        logger.debug(f"Generated historical replay profile: {duration_hours} hours")
        return hourly_profile
    
    def save_model(self, path: str) -> None:
        """Save historical daily profiles."""
        import pickle
        from pathlib import Path
        
        path_file = Path(path) / "historical_replay.pkl"
        path_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path_file, 'wb') as f:
            pickle.dump({'daily_profiles': self.daily_profiles}, f)
        logger.info(f"Saved HistoricalReplayBaseline to {path_file}")
    
    def load_model(self, path: str) -> None:
        """Load historical daily profiles."""
        import pickle
        from pathlib import Path
        
        path_file = Path(path) / "historical_replay.pkl"
        
        with open(path_file, 'rb') as f:
            data = pickle.load(f)
        
        self.daily_profiles = data['daily_profiles']
        self.trained = True
        logger.info(f"Loaded HistoricalReplayBaseline from {path_file}")
    
    def get_statistics(self) -> Dict[str, float]:
        """Get baseline statistics."""
        if not self.trained:
            raise ValueError("Model not trained")
        return {
            'n_days': len(self.daily_profiles),
            'mean_load_kw': float(np.mean(self.daily_profiles))
        }


def compare_profiles(
    real_profile: np.ndarray,
    synthetic_profile: np.ndarray,
    profile_name: str = "Synthetic"
) -> Dict[str, float]:
    """
    Compare synthetic profile against real data statistically.
    
    Args:
        real_profile: Real historical load profile
        synthetic_profile: Generated synthetic profile
        profile_name: Name for logging
        
    Returns:
        Dictionary with comparison metrics
    """
    logger.info(f"Comparing {profile_name} profile against real data")
    
    # Basic statistics
    metrics = {
        'real_mean': float(np.mean(real_profile)),
        'synthetic_mean': float(np.mean(synthetic_profile)),
        'real_std': float(np.std(real_profile)),
        'synthetic_std': float(np.std(synthetic_profile)),
        'real_min': float(np.min(real_profile)),
        'synthetic_min': float(np.min(synthetic_profile)),
        'real_max': float(np.max(real_profile)),
        'synthetic_max': float(np.max(synthetic_profile)),
    }
    
    # Derived metrics
    metrics['mean_error'] = abs(metrics['synthetic_mean'] - metrics['real_mean'])
    metrics['mean_error_pct'] = (metrics['mean_error'] / metrics['real_mean']) * 100
    metrics['std_error'] = abs(metrics['synthetic_std'] - metrics['real_std'])
    metrics['std_error_pct'] = (metrics['std_error'] / metrics['real_std']) * 100
    
    # RMSE (if lengths match)
    if len(real_profile) == len(synthetic_profile):
        rmse = np.sqrt(np.mean((real_profile - synthetic_profile) ** 2))
        metrics['rmse'] = float(rmse)
        metrics['rmse_normalized'] = float(rmse / metrics['real_mean'])
    
    # Kolmogorov-Smirnov test (distribution similarity)
    ks_statistic, ks_pvalue = stats.ks_2samp(real_profile, synthetic_profile)
    metrics['ks_statistic'] = float(ks_statistic)
    metrics['ks_pvalue'] = float(ks_pvalue)
    metrics['ks_similar'] = ks_pvalue > 0.05  # p > 0.05 means distributions are similar
    
    # Percentiles
    for percentile in [25, 50, 75, 95]:
        metrics[f'real_p{percentile}'] = float(np.percentile(real_profile, percentile))
        metrics[f'synthetic_p{percentile}'] = float(np.percentile(synthetic_profile, percentile))
    
    logger.info(f"{profile_name} vs Real: mean_error={metrics['mean_error_pct']:.2f}%, "
               f"KS p-value={metrics['ks_pvalue']:.4f}")
    
    return metrics


def generate_evaluation_report(
    real_profile: np.ndarray,
    synthetic_profiles: Dict[str, np.ndarray]
) -> str:
    """
    Generate comprehensive evaluation report comparing multiple profiles.
    
    Args:
        real_profile: Real historical data
        synthetic_profiles: Dict mapping model names to generated profiles
        
    Returns:
        Formatted report string
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("LOAD PROFILE EVALUATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Real data summary
    report_lines.append("Real Data Summary:")
    report_lines.append(f"  Duration: {len(real_profile)} hours ({len(real_profile)/24:.1f} days)")
    report_lines.append(f"  Mean Load: {np.mean(real_profile):.3f} kW")
    report_lines.append(f"  Std Dev: {np.std(real_profile):.3f} kW")
    report_lines.append(f"  Min: {np.min(real_profile):.3f} kW")
    report_lines.append(f"  Max: {np.max(real_profile):.3f} kW")
    report_lines.append("")
    
    # Compare each synthetic profile
    all_metrics = {}
    for model_name, synthetic_profile in synthetic_profiles.items():
        metrics = compare_profiles(real_profile, synthetic_profile, model_name)
        all_metrics[model_name] = metrics
        
        report_lines.append(f"{model_name}:")
        report_lines.append(f"  Mean Error: {metrics['mean_error']:.3f} kW ({metrics['mean_error_pct']:.2f}%)")
        report_lines.append(f"  Std Error: {metrics['std_error']:.3f} kW ({metrics['std_error_pct']:.2f}%)")
        
        if 'rmse' in metrics:
            report_lines.append(f"  RMSE: {metrics['rmse']:.3f} kW (normalized: {metrics['rmse_normalized']:.3f})")
        
        report_lines.append(f"  KS Test: statistic={metrics['ks_statistic']:.4f}, "
                          f"p-value={metrics['ks_pvalue']:.4f} "
                          f"({'SIMILAR' if metrics['ks_similar'] else 'DIFFERENT'})")
        report_lines.append("")
    
    # Ranking
    report_lines.append("Ranking by Mean Error (lower is better):")
    ranked = sorted(all_metrics.items(), key=lambda x: x[1]['mean_error'])
    for rank, (name, metrics) in enumerate(ranked, 1):
        report_lines.append(f"  {rank}. {name}: {metrics['mean_error_pct']:.2f}% error")
    
    report_lines.append("")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)
