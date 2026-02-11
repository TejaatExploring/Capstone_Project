"""
Phase 0 Validation Script
==========================

This script verifies that the Phase 0 architecture is correctly set up.
It tests:
1. All imports work correctly
2. Domain models can be instantiated
3. Configuration system works
4. Dependency injection container is functional
5. Logging is configured

Run: python validate_phase_0.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_imports():
    """Test that all core modules can be imported."""
    print("=" * 70)
    print("TEST 1: Module Imports")
    print("=" * 70)
    
    try:
        # Core interfaces
        from backend.core.interfaces import (
            IWeatherService, IPhysicsEngine, ILoadGenerator,
            IOptimizer, IController, IBaseline
        )
        print("✅ Core interfaces imported successfully")
        
        # Core models
        from backend.core.models import (
            SimulationConfig, OptimizationConfig, ComponentSpecs,
            SystemState, SimulationResult
        )
        print("✅ Core models imported successfully")
        
        # Infrastructure
        from backend.infrastructure.config import get_settings
        from backend.infrastructure.di import get_container
        from backend.infrastructure.logging import get_logger
        print("✅ Infrastructure modules imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_models():
    """Test that domain models can be instantiated and validated."""
    print("\n" + "=" * 70)
    print("TEST 2: Domain Models")
    print("=" * 70)
    
    try:
        from backend.core.models import (
            SimulationConfig, ComponentSpecs, SystemState
        )
        
        # Test SimulationConfig
        config = SimulationConfig(
            latitude=40.7128,
            longitude=-74.0060,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            timestep_hours=1.0,
            random_seed=42
        )
        print(f"✅ SimulationConfig created: {config.latitude}°N, {config.longitude}°E")
        
        # Test ComponentSpecs
        specs = ComponentSpecs(
            pv_capacity_kw=10.0,
            battery_capacity_kwh=20.0,
            battery_power_kw=5.0
        )
        cost = specs.calculate_cost(1000.0, 500.0)
        print(f"✅ ComponentSpecs created: {specs.pv_capacity_kw} kW PV, Cost: ${cost:,.2f}")
        
        # Test SystemState
        state = SystemState(
            timestep=0,
            soc=0.5,
            pv_power=5.0,
            load_demand=3.0,
            battery_power=0.0,
            grid_power=0.0
        )
        print(f"✅ SystemState created: SoC={state.soc}, PV={state.pv_power} kW")
        
        # Test validation
        try:
            invalid_state = SystemState(
                timestep=0,
                soc=1.5,  # Invalid
                pv_power=5.0,
                load_demand=3.0,
                battery_power=0.0,
                grid_power=0.0
            )
            print("❌ Validation failed: Invalid SoC should raise error")
            return False
        except ValueError:
            print("✅ Validation works: Invalid SoC rejected")
        
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test that configuration system works."""
    print("\n" + "=" * 70)
    print("TEST 3: Configuration System")
    print("=" * 70)
    
    try:
        from backend.infrastructure.config import get_settings
        from backend.infrastructure.config.constants import (
            DEFAULT_PANEL_EFFICIENCY, DEFAULT_BATTERY_EFFICIENCY
        )
        
        settings = get_settings()
        print(f"✅ Settings loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
        print(f"✅ NASA API URL: {settings.NASA_API_BASE_URL}")
        print(f"✅ Constants: Panel Efficiency={DEFAULT_PANEL_EFFICIENCY}, "
              f"Battery Efficiency={DEFAULT_BATTERY_EFFICIENCY}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_dependency_injection():
    """Test that DI container is functional."""
    print("\n" + "=" * 70)
    print("TEST 4: Dependency Injection")
    print("=" * 70)
    
    try:
        from backend.infrastructure.di import get_container
        
        container = get_container()
        print("✅ DI container created")
        
        # Test that container has expected providers
        assert hasattr(container, 'config')
        assert hasattr(container, 'weather_service')
        assert hasattr(container, 'physics_engine')
        print("✅ Container has all expected providers")
        
        return True
    except Exception as e:
        print(f"❌ DI test failed: {e}")
        return False


def test_logging():
    """Test that logging system works."""
    print("\n" + "=" * 70)
    print("TEST 5: Logging System")
    print("=" * 70)
    
    try:
        from backend.infrastructure.logging import get_logger
        
        logger = get_logger(__name__)
        logger.info("Test log message")
        print("✅ Logger created and functional")
        
        return True
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False


def test_exceptions():
    """Test that custom exceptions are defined."""
    print("\n" + "=" * 70)
    print("TEST 6: Custom Exceptions")
    print("=" * 70)
    
    try:
        from backend.core.exceptions import (
            IEMSException, WeatherServiceError, PhysicsEngineError,
            LoadGeneratorError, OptimizerError, ControllerError,
            ConfigurationError, ValidationError
        )
        
        # Test raising and catching
        try:
            raise ValidationError("Test validation error")
        except IEMSException as e:
            print(f"✅ Exception hierarchy works: {type(e).__name__}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Exception test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PHASE 0 VALIDATION SUITE" + " " * 29 + "║")
    print("║" + " " * 10 + "Intelligent Energy Management Simulator" + " " * 19 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    tests = [
        ("Module Imports", test_imports),
        ("Domain Models", test_models),
        ("Configuration System", test_configuration),
        ("Dependency Injection", test_dependency_injection),
        ("Logging System", test_logging),
        ("Custom Exceptions", test_exceptions),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED - PHASE 0 ARCHITECTURE IS VALID!")
        print("=" * 70)
        print("\n✅ Ready to proceed to Phase 1: Physics Engine Implementation")
        return 0
    else:
        print("❌ SOME TESTS FAILED - PLEASE FIX ISSUES BEFORE PROCEEDING")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
