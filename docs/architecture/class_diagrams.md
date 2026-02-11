# Class Diagrams - IEMS

## Core Interfaces Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                         <<interface>>                            │
│                       IWeatherService                            │
├─────────────────────────────────────────────────────────────────┤
│ + fetch_hourly_data(lat, lon, start, end, params): Dict         │
│ + validate_location(lat, lon): bool                             │
└─────────────────────────────────────────────────────────────────┘
                              △
                              │ implements
                              │
                  ┌───────────┴───────────┐
                  │   NASAPowerService    │
                  └───────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         <<interface>>                            │
│                       IPhysicsEngine                             │
├─────────────────────────────────────────────────────────────────┤
│ + calculate_pv_power(ghi, temp, capacity): float                │
│ + simulate_battery(soc, demand, capacity): Tuple                │
│ + step(state, specs, load, ghi, temp, action): SystemState      │
└─────────────────────────────────────────────────────────────────┘
                              △
                              │ implements
                              │
                  ┌───────────┴───────────┐
                  │   PhysicsEngine       │
                  └───────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         <<interface>>                            │
│                       ILoadGenerator                             │
├─────────────────────────────────────────────────────────────────┤
│ + train(data_path, n_clusters): Dict                            │
│ + generate_profile(duration, seed): ndarray                     │
│ + save_model(path): None                                        │
│ + load_model(path): None                                        │
└─────────────────────────────────────────────────────────────────┘
                              △
                              │ implements
                              │
                  ┌───────────┴───────────┐
                  │ MarkovKMeansGenerator │
                  └───────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         <<interface>>                            │
│                         IOptimizer                               │
├─────────────────────────────────────────────────────────────────┤
│ + optimize(load, weather, config): Tuple[Specs, Dict]           │
│ + evaluate_fitness(specs, load, weather): float                 │
│ + get_convergence_history(): Dict                               │
└─────────────────────────────────────────────────────────────────┘
                              △
                              │ implements
                              │
                  ┌───────────┴───────────┐
                  │  GeneticOptimizer     │
                  └───────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         <<interface>>                            │
│                         IController                              │
├─────────────────────────────────────────────────────────────────┤
│ + select_action(state, deterministic): float                    │
│ + train(episodes, loads, weather): Dict                         │
│ + save_policy(path): None                                       │
│ + load_policy(path): None                                       │
└─────────────────────────────────────────────────────────────────┘
                              △
                              │ implements
                              │
                  ┌───────────┴───────────┐
                  │    DQNController      │
                  └───────────────────────┘
```

## Domain Models

### Core Entities

```
┌──────────────────────────┐
│   SimulationConfig       │
├──────────────────────────┤
│ - latitude: float        │
│ - longitude: float       │
│ - start_date: datetime   │
│ - end_date: datetime     │
│ - timestep_hours: float  │
│ - random_seed: int       │
└──────────────────────────┘

┌──────────────────────────┐
│   OptimizationConfig     │
├──────────────────────────┤
│ - budget_constraint      │
│ - roof_area_constraint   │
│ - population_size        │
│ - num_generations        │
│ - objectives: Dict       │
└──────────────────────────┘

┌──────────────────────────┐
│     ComponentSpecs       │
├──────────────────────────┤
│ - pv_capacity_kw         │
│ - battery_capacity_kwh   │
│ - battery_power_kw       │
│ - panel_efficiency       │
│ - battery_efficiency     │
│ + calculate_cost()       │
│ + calculate_roof_area()  │
└──────────────────────────┘

┌──────────────────────────┐
│      SystemState         │
├──────────────────────────┤
│ - timestep: int          │
│ - soc: float             │
│ - pv_power: float        │
│ - load_demand: float     │
│ - battery_power: float   │
│ - grid_power: float      │
│ - total_cost: float      │
│ + copy(): SystemState    │
└──────────────────────────┘

┌──────────────────────────┐
│    SimulationResult      │
├──────────────────────────┤
│ - states: List[State]    │
│ - metrics: Dict          │
│ - metadata: Dict         │
│ + calculate_metrics()    │
│ + to_dict(): Dict        │
└──────────────────────────┘
```

### Value Objects (Immutable)

```
┌─────────────────────────────┐
│    <<value object>>         │
│       WeatherData           │
├─────────────────────────────┤
│ - latitude: float           │
│ - longitude: float          │
│ - start_date: datetime      │
│ - end_date: datetime        │
│ - ghi_values: tuple[float]  │
│ - temperature_values: tuple │
│ - timestamps: tuple         │
├─────────────────────────────┤
│ + num_hours: int            │
│ + get_hour_data(idx): tuple │
└─────────────────────────────┘

┌─────────────────────────────┐
│    <<value object>>         │
│  BatterySimulationResult    │
├─────────────────────────────┤
│ - new_soc: float            │
│ - actual_power_flow: float  │
│ - grid_power: float         │
│ - energy_stored: float      │
│ - energy_discharged: float  │
│ - efficiency_loss: float    │
├─────────────────────────────┤
│ + is_charging: bool         │
│ + is_discharging: bool      │
│ + is_idle: bool             │
│ + is_importing: bool        │
│ + is_exporting: bool        │
└─────────────────────────────┘

┌─────────────────────────────┐
│    <<value object>>         │
│    PVCalculationInput       │
├─────────────────────────────┤
│ - ghi: float                │
│ - temperature: float        │
│ - pv_capacity_kw: float     │
│ - panel_efficiency: float   │
│ - temperature_coeff: float  │
│ - inverter_efficiency: float│
└─────────────────────────────┘

┌─────────────────────────────┐
│    <<value object>>         │
│  BatterySimulationInput     │
├─────────────────────────────┤
│ - current_soc: float        │
│ - power_demand: float       │
│ - battery_capacity_kwh      │
│ - charge_rate_kw: float     │
│ - discharge_rate_kw: float  │
│ - efficiency: float         │
│ - delta_t: float            │
│ - min_soc/max_soc: float    │
└─────────────────────────────┘

┌─────────────────────────────┐
│    <<value object>>         │
│   SimulationStepInput       │
├─────────────────────────────┤
│ - load_demand: float        │
│ - ghi: float                │
│ - temperature: float        │
│ - control_action: float     │
└─────────────────────────────┘
```

## Dependency Injection Container

```
┌─────────────────────────────────────────────────────────────┐
│                        Container                             │
├─────────────────────────────────────────────────────────────┤
│ + config: Settings                                           │
│ + weather_service: IWeatherService                           │
│ + physics_engine: IPhysicsEngine                             │
│ + load_generator: ILoadGenerator                             │
│ + optimizer: IOptimizer                                      │
│ + controller: IController                                    │
│ + flat_baseline: IBaseline                                   │
│ + brute_force_baseline: IBaseline                            │
│ + rule_based_baseline: IBaseline                             │
└─────────────────────────────────────────────────────────────┘
              │
              │ provides dependencies to
              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Application Services                      │
│        (Weather, Physics, Brain 1a, Brain 1b, Brain 2)      │
└─────────────────────────────────────────────────────────────┘
```

## Relationship Diagram

```
┌──────────────┐     uses      ┌─────────────┐
│ IController  │──────────────→│  IPhysics   │
│  (Brain 2)   │               │   Engine    │
└──────────────┘               └─────────────┘
      │                               ↑
      │ uses                          │ uses
      ↓                               │
┌──────────────┐               ┌─────┴───────┐
│  IOptimizer  │──────────────→│  IWeather   │
│  (Brain 1b)  │     uses      │   Service   │
└──────────────┘               └─────────────┘
      ↑
      │ uses
      │
┌─────┴────────┐
│  ILoad       │
│  Generator   │
│  (Brain 1a)  │
└──────────────┘
```

## Notes

- All interfaces use **composition over inheritance**
- Dependencies flow **inward** (from infrastructure to domain)
- Domain layer has **no external dependencies**
- Service implementations are **injected at runtime**
