"""
Core Interfaces Module
======================

Contains all abstract base classes (ABCs) that define contracts for the IEMS system.
These interfaces enforce dependency inversion and enable clean architecture.

Design Pattern: Strategy Pattern, Dependency Inversion Principle
"""

from .i_weather_service import IWeatherService
from .i_physics_engine import IPhysicsEngine
from .i_load_generator import ILoadGenerator
from .i_optimizer import IOptimizer
from .i_controller import IController
from .i_baseline import IBaseline

__all__ = [
    "IWeatherService",
    "IPhysicsEngine",
    "ILoadGenerator",
    "IOptimizer",
    "IController",
    "IBaseline",
]
