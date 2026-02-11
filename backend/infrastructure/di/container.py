"""
Dependency Injection Container
===============================

Centralized dependency injection using dependency-injector.
Implements Inversion of Control (IoC) principle.

Design Pattern: Dependency Injection Container
"""

from dependency_injector import containers, providers
from ..config.settings import Settings


class Container(containers.DeclarativeContainer):
    """
    IoC container for dependency injection.
    
    Usage:
        container = Container()
        container.wire(modules=[...])
        
        # In your code:
        from dependency_injector.wiring import Provide, inject
        
        @inject
        def my_function(
            weather_service: IWeatherService = Provide[Container.weather_service]
        ):
            ...
    """
    
    # Configuration
    config = providers.Singleton(Settings)
    
    # Services (to be registered in respective phases)
    # Phase 1
    weather_service = providers.Singleton(
        lambda: None  # Will be replaced with actual implementation
    )
    
    physics_engine = providers.Singleton(
        lambda: None
    )
    
    # Phase 2
    load_generator = providers.Singleton(
        lambda: None
    )
    
    # Phase 3
    optimizer = providers.Singleton(
        lambda: None
    )
    
    # Phase 4
    controller = providers.Singleton(
        lambda: None
    )
    
    # Baselines
    flat_baseline = providers.Singleton(
        lambda: None
    )
    
    brute_force_baseline = providers.Singleton(
        lambda: None
    )
    
    rule_based_baseline = providers.Singleton(
        lambda: None
    )


def get_container() -> Container:
    """
    Get or create the global container instance.
    
    Returns:
        Container instance
    """
    if not hasattr(get_container, "_instance"):
        get_container._instance = Container()
    return get_container._instance
