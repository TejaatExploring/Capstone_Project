"""
Application Settings
====================

Centralized configuration management using Pydantic BaseSettings.
Supports environment variables and .env files.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application-wide settings.
    
    Configuration precedence:
    1. Environment variables
    2. .env file
    3. Default values
    """
    
    # Application
    APP_NAME: str = "Intelligent Energy Management Simulator"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # NASA POWER API
    NASA_API_BASE_URL: str = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    NASA_API_TIMEOUT: int = 30
    NASA_API_RETRIES: int = 3
    
    # Database (future use)
    DATABASE_URL: Optional[str] = None
    
    # Paths
    DATASET_PATH: str = "./backend/Dataset"
    TRAINED_MODELS_PATH: str = "./backend/trained_models"
    
    # Training defaults
    DEFAULT_RANDOM_SEED: int = 42
    DEFAULT_TRAIN_TEST_SPLIT: float = 0.8
    
    # Optimization defaults
    GA_POPULATION_SIZE: int = 100
    GA_NUM_GENERATIONS: int = 50
    GA_CROSSOVER_PROB: float = 0.7
    GA_MUTATION_PROB: float = 0.2
    
    # DQN defaults
    DQN_LEARNING_RATE: float = 0.001
    DQN_GAMMA: float = 0.99
    DQN_EPSILON_START: float = 1.0
    DQN_EPSILON_END: float = 0.01
    DQN_EPSILON_DECAY: float = 0.995
    DQN_BATCH_SIZE: int = 64
    DQN_MEMORY_SIZE: int = 10000
    DQN_TARGET_UPDATE_FREQ: int = 10
    
    # Cost parameters
    PV_COST_PER_KW: float = 1000.0
    BATTERY_COST_PER_KWH: float = 500.0
    ELECTRICITY_COST_PER_KWH: float = 0.15
    GRID_SELL_PRICE_PER_KWH: float = 0.08
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    return Settings()
