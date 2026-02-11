# Dataset Directory

This directory contains CSV files with historical load data for Brain 1a (Load Generator).

## Expected Format

Each CSV file should contain hourly load data with the following structure:

```csv
timestamp,load_kw
2024-01-01 00:00:00,2.5
2024-01-01 01:00:00,2.1
2024-01-01 02:00:00,1.9
...
```

## Data Requirements

- **Column 1**: `timestamp` - ISO format datetime (YYYY-MM-DD HH:MM:SS)
- **Column 2**: `load_kw` - Load demand in kilowatts (positive float)

## Minimum Data Size

- At least 30 days of hourly data (720 rows)
- Recommended: 1 year of data (8760 rows) for better pattern learning

## File Naming Convention

- `load_profile_<location>_<year>.csv`
- Example: `load_profile_residential_2024.csv`

## To Be Populated in Phase 2

Place your CSV files here before starting Phase 2 (Brain 1a implementation).
