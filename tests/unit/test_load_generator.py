"""
Unit Tests for Load Generator Module
======================================

Tests for synthetic load generation components.

Coverage:
    - Domain models (LoadProfile, DailyLoadProfile, etc.)
    - Data loader
    - Clustering
    - Markov model
    - Main generator
    - Baselines
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile

from backend.core.models import (
    LoadProfile,
    DailyLoadProfile,
    ClusteringResult,
    MarkovTransitionMatrix
)
from backend.services.load import (
    LoadGenerator,
    SmartMeterDataLoader,
    LoadClusterer,
    MarkovLoadModel,
    FlatBaseline,
    HistoricalReplayBaseline,
    compare_profiles
)


# ============================================================================
# Test Domain Models
# ============================================================================

class TestDailyLoadProfile:
    """Test DailyLoadProfile value object."""
    
    def test_valid_daily_profile(self):
        """Test creation of valid daily profile."""
        loads = np.random.rand(24) * 5  # 0-5 kW
        profile = DailyLoadProfile(hourly_loads=loads)
        
        assert profile.hourly_loads.shape == (24,)
        assert profile.mean_load >= 0
        assert profile.peak_load >= 0
        assert profile.total_energy >= 0
    
    def test_invalid_length(self):
        """Test rejection of non-24-hour profile."""
        loads = np.random.rand(20)
        
        with pytest.raises(ValueError, match="must have 24 hours"):
            DailyLoadProfile(hourly_loads=loads)
    
    def test_negative_values(self):
        """Test rejection of negative loads."""
        loads = np.array([1, 2, -1, 3] + [1]*20)
        
        with pytest.raises(ValueError, match="cannot be negative"):
            DailyLoadProfile(hourly_loads=loads)
    
    def test_load_factor(self):
        """Test load factor calculation."""
        loads = np.array([2.0] * 24)  # Constant load
        profile = DailyLoadProfile(hourly_loads=loads)
        
        assert profile.load_factor == 1.0  # Perfect load factor


class TestLoadProfile:
    """Test LoadProfile value object."""
    
    def test_valid_load_profile(self):
        """Test creation of valid load profile."""
        loads = np.random.rand(72) * 5  # 3 days
        profile = LoadProfile(hourly_loads=loads)
        
        assert profile.duration_hours == 72
        assert profile.mean_load >= 0
        assert profile.peak_load >= profile.mean_load
    
    def test_empty_profile(self):
        """Test rejection of empty profile."""
        with pytest.raises(ValueError, match="cannot be empty"):
            LoadProfile(hourly_loads=np.array([]))
    
    def test_to_daily_profiles(self):
        """Test splitting into daily profiles."""
        loads = np.random.rand(72) * 5  # 3 complete days
        profile = LoadProfile(hourly_loads=loads)
        
        daily_profiles = profile.to_daily_profiles()
        
        assert len(daily_profiles) == 3
        for daily in daily_profiles:
            assert isinstance(daily, DailyLoadProfile)
            assert daily.hourly_loads.shape == (24,)
    
    def test_incomplete_day_handling(self):
        """Test handling of incomplete last day."""
        loads = np.random.rand(50) * 5  # 2 days + 2 hours
        profile = LoadProfile(hourly_loads=loads)
        
        daily_profiles = profile.to_daily_profiles()
        
        assert len(daily_profiles) == 2  # Only complete days
    
    def test_statistics(self):
        """Test get_statistics method."""
        loads = np.array([1, 2, 3, 4, 5] * 10)  # 50 hours
        profile = LoadProfile(hourly_loads=loads)
        
        stats = profile.get_statistics()
        
        assert 'mean_kw' in stats
        assert 'std_kw' in stats
        assert 'max_kw' in stats
        assert 'total_kwh' in stats
        assert stats['max_kw'] == 5.0


class TestClusteringResult:
    """Test ClusteringResult value object."""
    
    def test_valid_clustering_result(self):
        """Test creation of valid clustering result."""
        centers = np.random.rand(3, 24)
        labels = np.array([0, 1, 2, 0, 1])
        
        result = ClusteringResult(
            n_clusters=3,
            cluster_centers=centers,
            labels=labels,
            silhouette_score=0.5,
            inertia=100.0
        )
        
        assert result.n_clusters == 3
        assert result.cluster_centers.shape == (3, 24)
    
    def test_invalid_silhouette_score(self):
        """Test rejection of invalid silhouette score."""
        centers = np.random.rand(3, 24)
        labels = np.array([0, 1, 2])
        
        with pytest.raises(ValueError, match="Silhouette score must be in"):
            ClusteringResult(
                n_clusters=3,
                cluster_centers=centers,
                labels=labels,
                silhouette_score=1.5,  # Invalid
                inertia=100.0
            )
    
    def test_cluster_distribution(self):
        """Test cluster distribution calculation."""
        centers = np.random.rand(3, 24)
        labels = np.array([0, 0, 1, 1, 2])  # 2, 2, 1 instances
        
        result = ClusteringResult(
            n_clusters=3,
            cluster_centers=centers,
            labels=labels,
            silhouette_score=0.5,
            inertia=100.0
        )
        
        dist = result.get_cluster_distribution()
        
        assert dist.shape == (3,)
        assert np.isclose(dist.sum(), 1.0)
        assert np.isclose(dist[0], 0.4)  # 2/5
        assert np.isclose(dist[2], 0.2)  # 1/5


class TestMarkovTransitionMatrix:
    """Test MarkovTransitionMatrix value object."""
    
    def test_valid_transition_matrix(self):
        """Test creation of valid transition matrix."""
        matrix = np.array([
            [0.7, 0.2, 0.1],
            [0.3, 0.5, 0.2],
            [0.1, 0.3, 0.6]
        ])
        
        markov = MarkovTransitionMatrix(
            matrix=matrix,
            n_clusters=3
        )
        
        assert markov.n_clusters == 3
        assert markov.matrix.shape == (3, 3)
    
    def test_invalid_row_sums(self):
        """Test rejection of matrix with rows not summing to 1."""
        matrix = np.array([
            [0.7, 0.2, 0.2],  # Sums to 1.1
            [0.3, 0.5, 0.2],
            [0.1, 0.3, 0.6]
        ])
        
        with pytest.raises(ValueError, match="rows must sum to 1"):
            MarkovTransitionMatrix(matrix=matrix, n_clusters=3)
    
    def test_sample_next_state(self):
        """Test sampling next state."""
        matrix = np.array([
            [1.0, 0.0],  # Always stays in state 0
            [0.0, 1.0]   # Always stays in state 1
        ])
        
        markov = MarkovTransitionMatrix(matrix=matrix, n_clusters=2)
        rng = np.random.default_rng(42)
        
        # Should always return same state
        assert markov.sample_next_state(0, rng) == 0
        assert markov.sample_next_state(1, rng) == 1


# ============================================================================
# Test Data Loader
# ============================================================================

class TestSmartMeterDataLoader:
    """Test SmartMeterDataLoader."""
    
    @pytest.fixture
    def sample_csv(self):
        """Create temporary CSV file with sample data."""
        data = {
            'x_Timestamp': pd.date_range('2021-01-01', periods=100, freq='15T'),
            't_kWh': np.random.rand(100) * 2,
            'z_Avg Voltage (Volt)': [230] * 100,
            'meter': ['A'] * 100
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            yield f.name
        
        Path(f.name).unlink()
    
    def test_load_and_preprocess(self, sample_csv):
        """Test loading and preprocessing CSV."""
        loader = SmartMeterDataLoader()
        df = loader.load_and_preprocess(sample_csv, min_hours=1)
        
        assert 'load_kw' in df.columns
        assert len(df) >= 1
        assert df['load_kw'].min() >= 0
    
    def test_file_not_found(self):
        """Test error handling for missing file."""
        loader = SmartMeterDataLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load_and_preprocess("nonexistent.csv")
    
    def test_summary_statistics(self, sample_csv):
        """Test summary statistics extraction."""
        loader = SmartMeterDataLoader()
        df = loader.load_and_preprocess(sample_csv, min_hours=1)
        
        stats = loader.get_summary_statistics(df)
        
        assert 'duration_hours' in stats
        assert 'mean_kw' in stats
        assert 'max_kw' in stats


# ============================================================================
# Test Clustering
# ============================================================================

class TestLoadClusterer:
    """Test LoadClusterer."""
    
    @pytest.fixture
    def sample_daily_profiles(self):
        """Create sample daily profiles."""
        # Create 10 days of data with 2 distinct patterns
        pattern1 = np.array([0.5]*8 + [2.0]*12 + [0.5]*4)  # Day pattern
        pattern2 = np.array([0.3]*24)  # Night pattern
        
        profiles = []
        for i in range(10):
            if i % 2 == 0:
                profiles.append(pattern1 + np.random.randn(24) * 0.1)
            else:
                profiles.append(pattern2 + np.random.randn(24) * 0.1)
        
        return np.array(profiles)
    
    def test_fit_clustering(self, sample_daily_profiles):
        """Test fitting KMeans clustering."""
        clusterer = LoadClusterer(k_min=2, k_max=3)
        result = clusterer.fit(sample_daily_profiles)
        
        assert isinstance(result, ClusteringResult)
        assert result.n_clusters >= 2
        assert result.n_clusters <= 3
        assert len(result.labels) == len(sample_daily_profiles)
    
    def test_predict_cluster(self, sample_daily_profiles):
        """Test predicting cluster for new profile."""
        clusterer = LoadClusterer(k_min=2, k_max=3)
        clusterer.fit(sample_daily_profiles)
        
        new_profile = sample_daily_profiles[0]
        label = clusterer.predict(new_profile)
        
        assert isinstance(label, int)
        assert 0 <= label < clusterer.clustering_result.n_clusters
    
    def test_extract_daily_profiles(self):
        """Test extracting daily profiles from time series."""
        # Create 3 days of hourly data
        hourly_data = np.random.rand(72) * 5
        df = pd.DataFrame(
            {'load_kw': hourly_data},
            index=pd.date_range('2021-01-01', periods=72, freq='H')
        )
        
        clusterer = LoadClusterer()
        daily_profiles = clusterer.extract_daily_profiles(df)
        
        assert daily_profiles.shape == (3, 24)


# ============================================================================
# Test Markov Model
# ============================================================================

class TestMarkovLoadModel:
    """Test MarkovLoadModel."""
    
    def test_fit_markov_model(self):
        """Test fitting Markov model."""
        # Sequence with clear transitions
        sequence = np.array([0, 1, 0, 1, 0, 1, 2, 2, 2])
        
        model = MarkovLoadModel(n_clusters=3)
        result = model.fit(sequence)
        
        assert isinstance(result, MarkovTransitionMatrix)
        assert result.n_clusters == 3
    
    def test_generate_sequence(self):
        """Test generating cluster sequence."""
        sequence = np.array([0, 1, 0, 1, 0, 1])
        
        model = MarkovLoadModel(n_clusters=2)
        model.fit(sequence)
        
        generated = model.generate_sequence(n_days=10, seed=42)
        
        assert len(generated) == 10
        assert all(0 <= x < 2 for x in generated)
    
    def test_stationary_distribution(self):
        """Test computing stationary distribution."""
        sequence = np.array([0, 1, 0, 1, 0, 1] * 10)
        
        model = MarkovLoadModel(n_clusters=2)
        model.fit(sequence)
        
        stationary = model.get_stationary_distribution()
        
        assert stationary.shape == (2,)
        assert np.isclose(stationary.sum(), 1.0)


# ============================================================================
# Test Main Generator
# ============================================================================

class TestLoadGenerator:
    """Test LoadGenerator."""
    
    @pytest.fixture
    def trained_generator(self):
        """Create and train a generator on real data."""
        generator = LoadGenerator(k_min=2, k_max=3, random_state=42)
        # Train on actual dataset
        generator.train("backend/Dataset/smart_meter_data.csv")
        return generator
    
    def test_generate_profile_720_hours(self, trained_generator):
        """Test generating 720-hour profile."""
        profile = trained_generator.generate_profile(duration_hours=720, seed=42)
        
        assert isinstance(profile, np.ndarray)
        assert len(profile) == 720
        assert profile.min() >= 0
    
    def test_generate_reproducibility(self, trained_generator):
        """Test reproducibility with same seed."""
        profile1 = trained_generator.generate_profile(duration_hours=100, seed=42)
        profile2 = trained_generator.generate_profile(duration_hours=100, seed=42)
        
        np.testing.assert_array_equal(profile1, profile2)
    
    def test_save_and_load_model(self, trained_generator):
        """Test model persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save
            trained_generator.save_model(tmpdir)
            
            # Load
            new_generator = LoadGenerator()
            new_generator.load_model(tmpdir)
            
            # Generate should work
            profile = new_generator.generate_profile(duration_hours=24, seed=42)
            assert len(profile) == 24


# ============================================================================
# Test Baselines
# ============================================================================

class TestFlatBaseline:
    """Test FlatBaseline."""
    
    def test_train_flat_baseline(self):
        """Test training flat baseline."""
        baseline = FlatBaseline()
        metrics = baseline.train("backend/Dataset/smart_meter_data.csv")
        
        assert 'mean_load_kw' in metrics
        assert baseline.mean_load > 0
    
    def test_generate_flat_profile(self):
        """Test generating flat profile."""
        baseline = FlatBaseline()
        baseline.train("backend/Dataset/smart_meter_data.csv")
        
        profile = baseline.generate_profile(duration_hours=100)
        
        assert len(profile) == 100
        assert np.all(profile == baseline.mean_load)


class TestHistoricalReplayBaseline:
    """Test HistoricalReplayBaseline."""
    
    def test_train_replay_baseline(self):
        """Test training historical replay baseline."""
        baseline = HistoricalReplayBaseline()
        metrics = baseline.train("backend/Dataset/smart_meter_data.csv")
        
        assert 'n_days' in metrics
        assert baseline.daily_profiles.shape[1] == 24
    
    def test_generate_replay_profile(self):
        """Test generating replay profile."""
        baseline = HistoricalReplayBaseline()
        baseline.train("backend/Dataset/smart_meter_data.csv")
        
        profile = baseline.generate_profile(duration_hours=72, seed=42)
        
        assert len(profile) == 72
        assert profile.min() >= 0


# ============================================================================
# Test Comparison Utilities
# ============================================================================

class TestCompareProfiles:
    """Test profile comparison utilities."""
    
    def test_compare_profiles(self):
        """Test statistical comparison of profiles."""
        real = np.random.rand(100) * 5
        synthetic = real + np.random.randn(100) * 0.1
        
        metrics = compare_profiles(real, synthetic)
        
        assert 'real_mean' in metrics
        assert 'synthetic_mean' in metrics
        assert 'mean_error_pct' in metrics
        assert 'ks_statistic' in metrics
        assert 'ks_pvalue' in metrics
