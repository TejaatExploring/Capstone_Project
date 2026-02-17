# Energy Balance Bug Fix

## Critical Bug Discovered

During manual validation of the 48-hour simulation, a critical energy conservation violation was discovered in the `PhysicsEngine.step()` function.

### Bug Symptoms

**Scenario:** Load=2kW, PV=0kW, Battery discharges 1kW  
**Expected:** Grid should import 1kW (Load - PV - BatteryDischarge = 2 - 0 - 1 = 1)  
**Bug Produced:** Grid imported 3kW (violating energy conservation)

### Root Cause

The grid calculation had **three fundamental errors**:

1. **Wrong Sign Convention:**
   ```python
   # BUGGY CODE:
   grid_power = load_demand - pv_power - battery_result.actual_power_flow
   # When battery discharges (actual_power_flow = -1):
   # grid = 2 - 0 - (-1) = 3  ❌ WRONG!
   ```

2. **Double-Counting:**
   ```python
   # BUGGY CODE:
   total_grid_power = grid_power + battery_result.grid_power
   # Added battery.grid_power on top of already-calculated grid_power
   ```

3. **Incorrect Energy Tracking:**
   - `unmet_load` was calculated even with unlimited grid capacity
   - `excess_pv` calculation was confusing and incorrect

## The Fix

### 1. Corrected Grid Calculation

**Physics:** Grid must balance the energy equation:
```
Load = PV + Battery_discharge + Grid_import
Grid = Load - PV + Battery_power
```

**Code Fix:**
```python
# FIXED CODE:
# Battery sign convention (now explicitly documented):
# - actual_power_flow > 0: Battery CHARGING (consuming power)
# - actual_power_flow < 0: Battery DISCHARGING (providing power)

grid_power = (
    step_input.load_demand 
    - pv_power 
    + battery_result.actual_power_flow  # Charging adds to demand
)

# When battery discharges (actual_power_flow = -1):
# grid = 2 - 0 + (-1) = 1  ✅ CORRECT!
```

### 2. Removed Double-Counting

Removed the line that added `battery_result.grid_power` since battery limitations are already accounted for in `battery_result.actual_power_flow`.

### 3. Fixed Energy Tracking

```python
# Unmet load = 0 (unlimited grid assumption)
unmet_load = 0.0

# Excess PV = amount exported to grid
excess_pv = abs(grid_power) if grid_power < 0 else 0.0
```

### 4. Added Energy Conservation Validation

```python
# Energy balance check
battery_discharge = abs(battery_result.actual_power_flow) if battery_result.actual_power_flow < 0 else 0.0
battery_charge = battery_result.actual_power_flow if battery_result.actual_power_flow > 0 else 0.0
grid_import = grid_power if grid_power > 0 else 0.0
grid_export = abs(grid_power) if grid_power < 0 else 0.0

energy_in = pv_power + battery_discharge + grid_import
energy_out = step_input.load_demand + battery_charge + grid_export
energy_balance_error = abs(energy_in - energy_out)

if energy_balance_error > 1e-3:  # Tolerance: 1 Watt
    logger.warning(f"Energy balance violation: {energy_balance_error:.6f} kW")
```

## Validation

### New Test Case Added

`test_energy_balance_grid_calculation()` - Tests two scenarios:
1. **Battery discharges to help meet load**
   - Verifies Grid = Load - PV - Battery_discharge
   - Confirms energy conservation: Energy_IN = Energy_OUT
   
2. **Battery charges from excess PV**
   - Verifies Grid = Load - PV + Battery_charge
   - Confirms energy balance maintained

### Test Results

```
============================= 35 tests passing =============================
tests/unit/test_physics_engine.py::TestEdgeCases::test_energy_balance_grid_calculation PASSED [100%]
```

All 35 tests pass (34 original + 1 new test).

### 48-Hour Simulation Verification

**Before Fix (Hour 0):**
```
Power Flows:
  PV Output:     0.00 kW
  Load Demand:   2.00 kW
  Battery:      -1.00 kW  (discharging)
  Grid:          3.00 kW  (importing)  ❌ WRONG!

Energy balance: 0 + 1 + 3 = 4 ≠ 2 (VIOLATES PHYSICS)
```

**After Fix (Hour 0):**
```
Power Flows:
  PV Output:     0.00 kW
  Load Demand:   2.00 kW
  Battery:      -1.00 kW  (discharging)
  Grid:          1.00 kW  (importing)  ✅ CORRECT!

Energy balance: 0 + 1 + 1 = 2 ✓ (CONSERVES ENERGY)
```

## Impact

### Files Modified

1. **backend/services/physics/physics_engine.py**
   - Lines 316-326: Fixed grid calculation
   - Lines 330-340: Fixed cost calculation references
   - Lines 360-395: Fixed energy tracking and added conservation check
   - Lines 405-410: Fixed SystemState creation

2. **tests/unit/test_physics_engine.py**
   - Added `test_energy_balance_grid_calculation()` with comprehensive energy balance tests

### Coverage Maintained

- **Before:** 86% coverage (34/34 tests passing)
- **After:** 86% coverage (35/35 tests passing)

## Conclusion

This fix ensures the physics engine now correctly implements the fundamental law of energy conservation:

```
Energy IN = Energy OUT

PV + Battery_discharge + Grid_import = Load + Battery_charge + Grid_export
```

All simulations now produce physically correct results that respect energy balance constraints.

---

**Fixed on:** 2026-02-17  
**Severity:** CRITICAL (Energy conservation violation)  
**Status:** ✅ RESOLVED
