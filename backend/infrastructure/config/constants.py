"""
System Constants
================

Physical constants and system-wide default values.
"""

# Physical constants
SOLAR_CONSTANT = 1361  # W/m² - Solar constant at top of atmosphere
STANDARD_TEST_CONDITION_IRRADIANCE = 1000  # W/m² - STC irradiance
STANDARD_TEST_CONDITION_TEMPERATURE = 25  # °C - STC temperature

# Component defaults
DEFAULT_PANEL_EFFICIENCY = 0.20  # 20%
DEFAULT_BATTERY_EFFICIENCY = 0.95  # 95% round-trip
DEFAULT_INVERTER_EFFICIENCY = 0.98  # 98%
DEFAULT_TEMPERATURE_COEFFICIENT = -0.004  # per °C
DEFAULT_MIN_SOC = 0.1  # 10%
DEFAULT_MAX_SOC = 0.9  # 90%
DEFAULT_INITIAL_SOC = 0.5  # 50%

# Simulation defaults
DEFAULT_TIMESTEP_HOURS = 1.0  # 1 hour
DEFAULT_SIMULATION_DURATION_HOURS = 720  # 30 days

# Physical limits
MAX_PV_CAPACITY_KW = 1000  # Maximum PV capacity
MAX_BATTERY_CAPACITY_KWH = 10000  # Maximum battery capacity
MIN_PV_CAPACITY_KW = 0  # Minimum PV capacity
MIN_BATTERY_CAPACITY_KWH = 0  # Minimum battery capacity

# Optimization bounds
PV_CAPACITY_RANGE = (0, 100)  # kW
BATTERY_CAPACITY_RANGE = (0, 200)  # kWh
BATTERY_POWER_RANGE = (0, 50)  # kW

# NASA POWER API parameters
NASA_PARAMETERS = ["GHI", "T2M"]  # Global Horizontal Irradiance, Temperature at 2m
NASA_COMMUNITY = "RE"  # Renewable Energy community
NASA_FORMAT = "JSON"

# Machine learning
KMEANS_MIN_CLUSTERS = 2
KMEANS_MAX_CLUSTERS = 20
SILHOUETTE_THRESHOLD = 0.5

# DQN reward function weights
LAMBDA_BATTERY_DEGRADATION = 0.1
LAMBDA_GRID_IMPORT = 0.2
LAMBDA_PEAK_PENALTY = 0.3

# Validation thresholds
MIN_IMPROVEMENT_THRESHOLD = 0.05  # 5% minimum improvement over baseline
STATISTICAL_SIGNIFICANCE_ALPHA = 0.05  # p-value threshold
