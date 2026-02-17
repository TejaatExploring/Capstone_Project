"""
Smart Meter Data Loader
========================

Loads and preprocesses smart meter CSV data for load generation.

Responsibilities:
    - Load CSV file
    - Validate schema
    - Handle missing values
    - Resample to hourly intervals
    - Clean and normalize data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SmartMeterDataLoader:
    """
    Loads and preprocesses smart meter data from CSV.
    
    Purpose:
        Clean and prepare raw smart meter data for ML training
        
    Input Format:
        CSV with columns: x_Timestamp, t_kWh, z_Avg Voltage (Volt), 
                         z_Avg Current (Amp), y_Freq (Hz), meter
                         
    Output Format:
        DataFrame with DateTime index and hourly 'load_kw' column
        
    Assumptions:
        - Data may have sub-hourly intervals (3-min, 15-min, etc.)
        - Missing values may exist
        - Multiple meters may be present (aggregate them)
        - t_kWh represents energy consumed in the interval
    """
    
    def __init__(self):
        """Initialize the data loader."""
        logger.info("SmartMeterDataLoader initialized")
    
    def load_and_preprocess(
        self,
        csv_path: str,
        resample_freq: str = '1H',
        min_hours: int = 168  # Minimum 1 week of data
    ) -> pd.DataFrame:
        """
        Load CSV data and preprocess to hourly load profile.
        
        Args:
            csv_path: Path to smart meter CSV file
            resample_freq: Resampling frequency (default: '1H' = hourly)
            min_hours: Minimum required hours of data
            
        Returns:
            DataFrame with DatetimeIndex and 'load_kw' column
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If data is invalid or insufficient
        """
        logger.info(f"Loading data from {csv_path}")
        
        # Step 1: Load CSV
        df = self._load_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from CSV")
        
        # Step 2: Parse timestamps
        df = self._parse_timestamps(df)
        
        # Step 3: Extract load column (t_kWh)
        df = self._extract_load_column(df)
        
        # Step 4: Handle missing values
        df = self._handle_missing_values(df)
        
        # Step 5: Aggregate multiple meters if present
        df = self._aggregate_meters(df)
        
        # Step 6: Resample to hourly intervals
        df = self._resample_to_hourly(df, resample_freq)
        
        # Step 7: Convert energy (kWh) to power (kW)
        df = self._energy_to_power(df, resample_freq)
        
        # Step 8: Validate final data
        self._validate_data(df, min_hours)
        
        logger.info(f"Preprocessing complete: {len(df)} hourly samples")
        return df
    
    def _load_csv(self, csv_path: str) -> pd.DataFrame:
        """Load CSV file with error handling."""
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            return df
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {e}")
    
    def _parse_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse timestamp column and set as index."""
        timestamp_col = None
        
        # Find timestamp column (flexible naming)
        for col in df.columns:
            if 'timestamp' in col.lower() or 'time' in col.lower() or 'date' in col.lower():
                timestamp_col = col
                break
        
        if timestamp_col is None:
            raise ValueError("No timestamp column found in CSV")
        
        logger.debug(f"Using timestamp column: {timestamp_col}")
        
        try:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            df = df.set_index(timestamp_col)
            df = df.sort_index()
            return df
        except Exception as e:
            raise ValueError(f"Failed to parse timestamps: {e}")
    
    def _extract_load_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract energy consumption column."""
        load_col = None
        
        # Find energy/load column (flexible naming)
        for col in df.columns:
            col_lower = col.lower()
            if 'kwh' in col_lower or 'load' in col_lower or 'energy' in col_lower:
                load_col = col
                break
        
        if load_col is None:
            raise ValueError("No load/energy column found in CSV")
        
        logger.debug(f"Using load column: {load_col}")
        
        # Keep only the load column
        df_load = df[[load_col]].copy()
        df_load.columns = ['load_kwh']
        
        return df_load
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values with interpolation."""
        missing_count = df['load_kwh'].isna().sum()
        
        if missing_count > 0:
            logger.warning(f"Found {missing_count} missing values, interpolating...")
            
            # Linear interpolation for missing values
            df['load_kwh'] = df['load_kwh'].interpolate(method='linear')
            
            # Forward fill for any remaining NaNs at boundaries
            df['load_kwh'] = df['load_kwh'].fillna(method='ffill').fillna(method='bfill')
            
            # If still NaN, fill with 0
            df['load_kwh'] = df['load_kwh'].fillna(0.0)
        
        return df
    
    def _aggregate_meters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate multiple meters if present."""
        # If there are duplicate timestamps (multiple meters), sum them
        if df.index.duplicated().any():
            logger.info("Multiple meters detected, aggregating...")
            df = df.groupby(df.index).sum()
        
        return df
    
    def _resample_to_hourly(self, df: pd.DataFrame, freq: str) -> pd.DataFrame:
        """Resample data to specified frequency (e.g., hourly)."""
        logger.debug(f"Resampling to {freq}")
        
        # Resample and sum energy values
        df_resampled = df.resample(freq).sum()
        
        # Ensure continuous hourly index (fill gaps with 0)
        if len(df_resampled) > 0:
            full_index = pd.date_range(
                start=df_resampled.index.min(),
                end=df_resampled.index.max(),
                freq=freq
            )
            df_resampled = df_resampled.reindex(full_index, fill_value=0.0)
        
        return df_resampled
    
    def _energy_to_power(self, df: pd.DataFrame, freq: str) -> pd.DataFrame:
        """
        Convert energy (kWh) to average power (kW).
        
        For hourly data: power_kw = energy_kwh / 1 hour = energy_kwh
        For sub-hourly: need to scale appropriately
        """
        # For hourly data, energy = power (both in kW scale)
        # For other frequencies, may need adjustment
        df['load_kw'] = df['load_kwh'].copy()
        
        # Remove the load_kwh column
        df = df[['load_kw']]
        
        # Clip negative values (measurement errors)
        df['load_kw'] = df['load_kw'].clip(lower=0.0)
        
        return df
    
    def _validate_data(self, df: pd.DataFrame, min_hours: int):
        """Validate the final preprocessed data."""
        if len(df) < min_hours:
            raise ValueError(
                f"Insufficient data: {len(df)} hours < minimum {min_hours} hours"
            )
        
        if df['load_kw'].isna().any():
            raise ValueError("Data still contains NaN values after preprocessing")
        
        if (df['load_kw'] < 0).any():
            raise ValueError("Data contains negative load values")
        
        # Check for unrealistic values (very large spikes)
        mean_load = df['load_kw'].mean()
        max_load = df['load_kw'].max()
        
        if max_load > mean_load * 100:
            logger.warning(
                f"Detected very large load spike: max={max_load:.2f} kW, "
                f"mean={mean_load:.2f} kW"
            )
        
        logger.info(f"Data validation passed: {len(df)} hours, "
                   f"mean={mean_load:.2f} kW, max={max_load:.2f} kW")
    
    def get_summary_statistics(self, df: pd.DataFrame) -> dict:
        """
        Get summary statistics of the loaded data.
        
        Args:
            df: Preprocessed DataFrame
            
        Returns:
            Dictionary with statistical metrics
        """
        load = df['load_kw']
        
        return {
            'duration_hours': len(df),
            'duration_days': len(df) / 24,
            'mean_kw': float(load.mean()),
            'std_kw': float(load.std()),
            'min_kw': float(load.min()),
            'max_kw': float(load.max()),
            'total_kwh': float(load.sum()),
            'percentile_25': float(load.quantile(0.25)),
            'percentile_50': float(load.quantile(0.50)),
            'percentile_75': float(load.quantile(0.75)),
            'percentile_95': float(load.quantile(0.95)),
            'zero_load_hours': int((load == 0).sum()),
        }
