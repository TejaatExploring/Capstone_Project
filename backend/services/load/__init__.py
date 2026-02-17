"""
Load Generation Service Module
================================

Synthetic load profile generation using Markov Chain + KMeans clustering.

Main Components:
    - LoadGenerator: Main service implementing ILoadGenerator
    - SmartMeterDataLoader: Data preprocessing
    - LoadClusterer: KMeans clustering with auto K optimization
    - MarkovLoadModel: Markov chain for cluster transitions
    - Baselines: Flat and Historical Replay baselines

Usage:
    Training:
        python -m backend.services.load.training
        
    Inference:
        python -m backend.services.load.inference --hours 720
        
    Programmatic:
        from backend.services.load import LoadGenerator
        
        generator = LoadGenerator()
        generator.train("backend/Dataset/smart_meter_data.csv")
        profile = generator.generate_profile(duration_hours=720)
"""

from .load_generator import LoadGenerator
from .data_loader import SmartMeterDataLoader
from .clustering import LoadClusterer
from .markov_model import MarkovLoadModel
from .baselines import FlatBaseline, HistoricalReplayBaseline, compare_profiles

__all__ = [
    "LoadGenerator",
    "SmartMeterDataLoader",
    "LoadClusterer",
    "MarkovLoadModel",
    "FlatBaseline",
    "HistoricalReplayBaseline",
    "compare_profiles",
]
