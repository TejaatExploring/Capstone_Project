"""
Manual 48-Hour Simulation
==========================

Runs a detailed 48-hour simulation with realistic weather patterns
and inspects all system values at each timestep.
"""

import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from backend.services.physics.physics_engine import PhysicsEngine
from backend.services.weather.nasa_power_service import NASAPowerService
from backend.core.models import (
    SystemState,
    ComponentSpecs,
    SimulationStepInput
)


def generate_realistic_weather(hours: int) -> tuple:
    """Generate realistic GHI and temperature for specified hours."""
    ghi_values = []
    temp_values = []
    
    for hour in range(hours):
        hour_of_day = hour % 24
        
        # GHI pattern (W/m²): night=0, sunrise/sunset=low, noon=peak
        if hour_of_day < 6 or hour_of_day > 18:
            ghi = 0.0  # Night
        elif hour_of_day == 6:
            ghi = 50.0  # Dawn
        elif hour_of_day == 7:
            ghi = 150.0
        elif hour_of_day == 8:
            ghi = 300.0
        elif hour_of_day == 9:
            ghi = 500.0
        elif hour_of_day == 10:
            ghi = 700.0
        elif hour_of_day == 11:
            ghi = 850.0
        elif hour_of_day == 12:
            ghi = 900.0  # Solar noon
        elif hour_of_day == 13:
            ghi = 850.0
        elif hour_of_day == 14:
            ghi = 700.0
        elif hour_of_day == 15:
            ghi = 500.0
        elif hour_of_day == 16:
            ghi = 300.0
        elif hour_of_day == 17:
            ghi = 150.0
        elif hour_of_day == 18:
            ghi = 50.0  # Dusk
        else:
            ghi = 0.0
        
        # Temperature pattern (°C): cooler at night, warmer during day
        if hour_of_day < 6:
            temp = 12.0 + (hour_of_day * 0.5)  # 12-15°C predawn
        elif hour_of_day < 12:
            temp = 15.0 + ((hour_of_day - 6) * 2.5)  # 15-30°C morning
        elif hour_of_day < 18:
            temp = 30.0 - ((hour_of_day - 12) * 2.0)  # 30-18°C afternoon
        else:
            temp = 18.0 - ((hour_of_day - 18) * 1.0)  # 18-12°C evening
        
        ghi_values.append(ghi)
        temp_values.append(temp)
    
    return ghi_values, temp_values


def generate_load_profile(hours: int) -> list:
    """Generate realistic residential load profile (kW)."""
    load_values = []
    
    for hour in range(hours):
        hour_of_day = hour % 24
        
        # Residential load pattern
        if hour_of_day < 6:
            load = 2.0  # Night (base load)
        elif hour_of_day == 6:
            load = 3.0  # Morning wake up
        elif hour_of_day == 7:
            load = 5.0  # Breakfast
        elif hour_of_day == 8:
            load = 7.0  # Peak morning
        elif hour_of_day < 12:
            load = 4.0  # Mid-morning
        elif hour_of_day == 12:
            load = 6.0  # Lunch
        elif hour_of_day < 17:
            load = 4.0  # Afternoon
        elif hour_of_day == 17:
            load = 7.0  # Evening start
        elif hour_of_day == 18:
            load = 8.0  # Peak evening
        elif hour_of_day == 19:
            load = 8.0  # Dinner
        elif hour_of_day == 20:
            load = 6.0  # After dinner
        elif hour_of_day == 21:
            load = 5.0
        elif hour_of_day == 22:
            load = 4.0
        elif hour_of_day == 23:
            load = 3.0  # Pre-sleep
        
        load_values.append(load)
    
    return load_values


def print_section_header(title: str):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def print_hourly_summary(hour: int, state: SystemState, ghi: float, temp: float, load: float):
    """Print detailed summary for one hour."""
    print(f"\n{'-'*80}")
    print(f"Hour {hour:2d} | Day {hour//24 + 1}, Hour {hour%24:02d}:00")
    print(f"{'-'*80}")
    print(f"  Weather:")
    print(f"    GHI:         {ghi:6.1f} W/m²")
    print(f"    Temperature: {temp:6.1f} °C")
    print(f"\n  Power Flows:")
    print(f"    PV Output:   {state.pv_power:6.2f} kW")
    print(f"    Load Demand: {load:6.2f} kW")
    print(f"    Battery:     {state.battery_power:6.2f} kW  {'(charging)' if state.battery_power > 0 else '(discharging)' if state.battery_power < 0 else '(idle)'}")
    print(f"    Grid:        {state.grid_power:6.2f} kW  {'(importing)' if state.grid_power > 0 else '(exporting)' if state.grid_power < 0 else '(balanced)'}")
    print(f"\n  Battery State:")
    print(f"    SoC:         {state.soc:6.1%}")
    print(f"    Energy:      {state.soc * 20.0:6.2f} kWh / 20.0 kWh")
    print(f"    Cycles:      {state.battery_cycles:6.3f}")
    print(f"\n  Economics:")
    print(f"    Total Cost:     ${state.total_cost:7.2f}")
    print(f"    Total Revenue:  ${state.total_revenue:7.2f}")
    print(f"    Net Cost:       ${state.total_cost - state.total_revenue:7.2f}")
    print(f"\n  Metrics:")
    print(f"    Unmet Load:  {state.unmet_load:6.2f} kWh")
    print(f"    Excess PV:   {state.excess_pv:6.2f} kWh")


def print_daily_summary(day: int, states: list):
    """Print summary for one day (24 hours)."""
    start_idx = (day - 1) * 24
    end_idx = day * 24
    day_states = states[start_idx:end_idx]
    
    total_pv = sum(s.pv_power for s in day_states)
    total_load = sum(s.load_demand for s in day_states)
    total_battery_charge = sum(s.battery_power for s in day_states if s.battery_power > 0)
    total_battery_discharge = sum(-s.battery_power for s in day_states if s.battery_power < 0)
    total_grid_import = sum(s.grid_power for s in day_states if s.grid_power > 0)
    total_grid_export = sum(-s.grid_power for s in day_states if s.grid_power < 0)
    
    start_soc = states[start_idx - 1].soc if start_idx > 0 else 0.5
    end_soc = day_states[-1].soc
    
    daily_cost = day_states[-1].total_cost - (states[start_idx - 1].total_cost if start_idx > 0 else 0)
    daily_revenue = day_states[-1].total_revenue - (states[start_idx - 1].total_revenue if start_idx > 0 else 0)
    
    print_section_header(f"Day {day} Summary (24 hours)")
    print(f"\n  Energy Production & Consumption:")
    print(f"    Total PV Generation:    {total_pv:7.2f} kWh")
    print(f"    Total Load:             {total_load:7.2f} kWh")
    print(f"    Net Balance:            {total_pv - total_load:7.2f} kWh")
    print(f"\n  Battery Activity:")
    print(f"    Total Charged:          {total_battery_charge:7.2f} kWh")
    print(f"    Total Discharged:       {total_battery_discharge:7.2f} kWh")
    print(f"    Start SoC:              {start_soc:6.1%}")
    print(f"    End SoC:                {end_soc:6.1%}")
    print(f"    SoC Change:             {end_soc - start_soc:+6.1%}")
    print(f"    Cycles:                 {day_states[-1].battery_cycles - (states[start_idx - 1].battery_cycles if start_idx > 0 else 0):6.3f}")
    print(f"\n  Grid Interaction:")
    print(f"    Total Import:           {total_grid_import:7.2f} kWh")
    print(f"    Total Export:           {total_grid_export:7.2f} kWh")
    print(f"    Net Grid Usage:         {total_grid_import - total_grid_export:7.2f} kWh")
    print(f"\n  Economics:")
    print(f"    Daily Cost:             ${daily_cost:7.2f}")
    print(f"    Daily Revenue:          ${daily_revenue:7.2f}")
    print(f"    Net Daily Cost:         ${daily_cost - daily_revenue:7.2f}")
    print(f"\n  Self-Sufficiency:")
    print(f"    PV/Load Ratio:          {(total_pv / total_load * 100) if total_load > 0 else 0:6.1f}%")
    print(f"    Grid Independence:      {((1 - total_grid_import / total_load) * 100) if total_load > 0 else 0:6.1f}%")


def print_final_summary(states: list, hours: int):
    """Print overall simulation summary."""
    final_state = states[-1]
    
    total_pv = sum(s.pv_power for s in states)
    total_load = sum(s.load_demand for s in states)
    total_grid_import = sum(s.grid_power for s in states if s.grid_power > 0)
    total_grid_export = sum(-s.grid_power for s in states if s.grid_power < 0)
    
    print_section_header(f"Final Summary ({hours} hours)")
    print(f"\n  Simulation Period:")
    print(f"    Total Hours:            {hours}")
    print(f"    Total Days:             {hours / 24:.1f}")
    print(f"\n  Energy Totals:")
    print(f"    Total PV Generation:    {total_pv:7.2f} kWh")
    print(f"    Total Load:             {total_load:7.2f} kWh")
    print(f"    Total Grid Import:      {total_grid_import:7.2f} kWh")
    print(f"    Total Grid Export:      {total_grid_export:7.2f} kWh")
    print(f"    Unmet Load:             {final_state.unmet_load:7.2f} kWh")
    print(f"    Excess PV:              {final_state.excess_pv:7.2f} kWh")
    print(f"\n  Battery Performance:")
    print(f"    Initial SoC:            50.0%")
    print(f"    Final SoC:              {final_state.soc:6.1%}")
    print(f"    Total Cycles:           {final_state.battery_cycles:6.3f}")
    print(f"    Estimated Lifetime:     {3000 / final_state.battery_cycles if final_state.battery_cycles > 0 else 0:6.0f} periods")
    print(f"\n  Financial Summary:")
    print(f"    Total Cost:             ${final_state.total_cost:7.2f}")
    print(f"    Total Revenue:          ${final_state.total_revenue:7.2f}")
    print(f"    Net Cost:               ${final_state.total_cost - final_state.total_revenue:7.2f}")
    print(f"    Average Cost/Day:       ${(final_state.total_cost - final_state.total_revenue) / (hours / 24):7.2f}")
    print(f"\n  System Efficiency:")
    print(f"    PV Utilization:         {(total_pv / (total_load + final_state.excess_pv) * 100) if (total_load + final_state.excess_pv) > 0 else 0:6.1f}%")
    print(f"    Self-Sufficiency:       {((1 - total_grid_import / total_load) * 100) if total_load > 0 else 0:6.1f}%")
    print(f"    Grid Export Ratio:      {(total_grid_export / total_pv * 100) if total_pv > 0 else 0:6.1f}%")


def main():
    """Run 48-hour simulation with detailed inspection."""
    print_section_header("48-Hour Simulation Start")
    print("\n  System Configuration:")
    print("    PV Capacity:        10.0 kW")
    print("    Battery Capacity:   20.0 kWh")
    print("    Battery Power:      5.0 kW")
    print("    Panel Efficiency:   20%")
    print("    Inverter Efficiency: 96%")
    print("    Battery Efficiency: 95%")
    print("    Min SoC:            20%")
    print("    Max SoC:            90%")
    
    # Initialize components
    physics_engine = PhysicsEngine()
    
    specs = ComponentSpecs(
        pv_capacity_kw=10.0,
        battery_capacity_kwh=20.0,
        battery_power_kw=5.0,
        panel_efficiency=0.20,
        inverter_efficiency=0.96,
        battery_efficiency=0.95,
        temperature_coefficient=-0.004,
        min_soc=0.2,
        max_soc=0.9
    )
    
    state = SystemState(
        timestep=0,
        soc=0.5,  # Start at 50% SoC
        pv_power=0.0,
        load_demand=0.0,
        battery_power=0.0,
        grid_power=0.0,
        total_cost=0.0,
        total_revenue=0.0,
        battery_cycles=0.0,
        unmet_load=0.0,
        excess_pv=0.0
    )
    
    # Generate weather and load profiles
    hours = 48
    ghi_values, temp_values = generate_realistic_weather(hours)
    load_values = generate_load_profile(hours)
    
    print(f"\n  Simulation Duration: {hours} hours (2 days)")
    print(f"  Control Strategy: Neutral (control_action = 0.0)")
    
    # Store all states for summary
    states = []
    
    # Run simulation
    for hour in range(hours):
        ghi = ghi_values[hour]
        temp = temp_values[hour]
        load = load_values[hour]
        
        step_input = SimulationStepInput(
            ghi=ghi,
            temperature=temp,
            load_demand=load,
            control_action=0.0  # Neutral control
        )
        
        state = physics_engine.step(state, specs, step_input)
        states.append(state)
        
        # Print detailed hourly summary
        print_hourly_summary(hour, state, ghi, temp, load)
    
    # Print daily summaries
    print_daily_summary(1, states)
    print_daily_summary(2, states)
    
    # Print final summary
    print_final_summary(states, hours)
    
    print("\n" + "="*80)
    print(" Simulation Complete")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
