"""
Integration Tests for Load Generation Pipeline
===============================================

End-to-end tests for the complete load generation workflow.

Coverage:
    - Full training pipeline
    - Full generation pipeline
    - Model persistence
    - Baseline comparisons
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path

from backend.services.load import LoadGenerator, FlatBaseline, HistoricalReplayBaseline
from backend.services.load.baselines import generate_evaluation_report, compare_profiles
from backend.services.load.data_loader import SmartMeterDataLoader


class TestLoadGenerationPipeline:
    """Integration tests for complete load generation pipeline."""
    
    def test_full_training_pipeline(self):
        """
        Test complete training workflow:
        1. Load data
        2. Cluster profiles
        3. Build Markov model
        4. Save models
        5. Generate profiles
        """
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        # Train generator
        generator = LoadGenerator(k_min=2, k_max=5, random_state=42)
        metrics = generator.train(data_path)
        
        # Verify training metrics
        assert 'duration_days' in metrics
        assert 'n_clusters' in metrics
        assert 'silhouette_score' in metrics
        assert metrics['n_clusters'] >= 2
        assert metrics['n_clusters'] <= 5
        assert -1 <= metrics['silhouette_score'] <= 1
        
        # Generate profile
        profile = generator.generate_profile(duration_hours=720, seed=42)
        
        # Verify generated profile
        assert len(profile) == 720
        assert profile.min() >= 0
        assert profile.max() > 0
        assert np.std(profile) > 0  # Not flat
    
    def test_model_persistence_workflow(self):
        """
        Test model save/load workflow:
        1. Train model
        2. Save to disk
        3. Load from disk
        4. Generate identical profiles
        """
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Train and save
            generator1 = LoadGenerator(k_min=2, k_max=3, random_state=42)
            generator1.train(data_path)
            generator1.save_model(tmpdir)
            
            # Generate profile from trained model
            profile1 = generator1.generate_profile(duration_hours=100, seed=123)
            
            # Load and generate
            generator2 = LoadGenerator()
            generator2.load_model(tmpdir)
            profile2 = generator2.generate_profile(duration_hours=100, seed=123)
            
            # Should be identical
            np.testing.assert_array_equal(profile1, profile2)
    
    def test_baseline_comparison_workflow(self):
        """
        Test baseline comparison workflow:
        1. Train all models (Markov, Flat, Replay)
        2. Generate profiles
        3. Compare statistics
        """
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        # Train main model
        generator = LoadGenerator(k_min=2, k_max=3, random_state=42)
        generator.train(data_path)
        
        # Train baselines
        flat = FlatBaseline()
        flat.train(data_path)
        
        replay = HistoricalReplayBaseline()
        replay.train(data_path)
        
        # Generate profiles
        markov_profile = generator.generate_profile(duration_hours=720, seed=42)
        flat_profile = flat.generate_profile(duration_hours=720)
        replay_profile = replay.generate_profile(duration_hours=720, seed=42)
        
        # All should be valid
        assert len(markov_profile) == 720
        assert len(flat_profile) == 720
        assert len(replay_profile) == 720
        
        # Markov should be more variable than flat
        assert np.std(markov_profile) > np.std(flat_profile)
        
        # Replay should have realistic variability
        assert np.std(replay_profile) > 0
    
    def test_evaluation_report_generation(self):
        """
        Test evaluation report generation:
        1. Load real data
        2. Generate synthetic profiles
        3. Create comparison report
        """
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        # Load real data
        loader = SmartMeterDataLoader()
        df_real = loader.load_and_preprocess(data_path)
        real_profile = df_real['load_kw'].values[:720]
        
        # Train and generate
        generator = LoadGenerator(k_min=2, k_max=3, random_state=42)
        generator.train(data_path)
        markov_profile = generator.generate_profile(duration_hours=720, seed=42)
        
        flat = FlatBaseline()
        flat.train(data_path)
        flat_profile = flat.generate_profile(duration_hours=720)
        
        # Generate report
        synthetic_profiles = {
            'Markov+KMeans': markov_profile,
            'Flat': flat_profile
        }
        
        report = generate_evaluation_report(real_profile, synthetic_profiles)
        
        # Verify report contains key information
        assert 'Real Data Summary' in report
        assert 'Mean Load' in report
        assert 'Markov+KMeans' in report
        assert 'Flat' in report
        assert 'KS Test' in report
    
    def test_reproducibility_with_seed(self):
        """
        Test reproducibility across multiple runs with same seed.
        """
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        generator1 = LoadGenerator(k_min=2, k_max=3, random_state=42)
        generator1.train(data_path)
        
        generator2 = LoadGenerator(k_min=2, k_max=3, random_state=42)
        generator2.train(data_path)
        
        # Generate with same seed
        profile1 = generator1.generate_profile(duration_hours=720, seed=999)
        profile2 = generator2.generate_profile(duration_hours=720, seed=999)
        
        # Should be identical
        np.testing.assert_array_equal(profile1, profile2)
    
    def test_no_negative_loads(self):
        """
        Test that generated profiles never have negative loads.
        """
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        generator = LoadGenerator(k_min=2, k_max=3, random_state=42)
        generator.train(data_path)
        
        # Generate multiple profiles with different seeds
        for seed in [1, 42, 123, 999]:
            profile = generator.generate_profile(duration_hours=720, seed=seed)
            assert np.all(profile >= 0), f"Found negative loads with seed {seed}"
    
    def test_performance_requirements(self):
        """
        Test performance requirements:
        - Training < 10 seconds
        - Generation (720 hours) < 1 second
        """
        import time
        
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        # Test training time
        generator = LoadGenerator(k_min=2, k_max=3, random_state=42)
        
        start_train = time.time()
        generator.train(data_path)
        train_time = time.time() - start_train
        
        assert train_time < 10.0, f"Training took {train_time:.2f}s (> 10s limit)"
        
        # Test generation time
        start_gen = time.time()
        profile = generator.generate_profile(duration_hours=720, seed=42)
        gen_time = time.time() - start_gen
        
        assert gen_time < 1.0, f"Generation took {gen_time:.4f}s (> 1s limit)"
    
    def test_statistical_similarity_to_real_data(self):
        """
        Test that generated profiles are statistically similar to real data.
        """
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        # Load real data
        loader = SmartMeterDataLoader()
        df_real = loader.load_and_preprocess(data_path)
        real_profile = df_real['load_kw'].values[:720]
        
         # Train and generate
        generator = LoadGenerator(k_min=2, k_max=5, random_state=42)
        generator.train(data_path)
        synthetic_profile = generator.generate_profile(duration_hours=720, seed=42)
        
        # Compare statistics
        metrics = compare_profiles(real_profile, synthetic_profile)
        
        # Mean should be within 20% of real mean
        assert metrics['mean_error_pct'] < 20.0
        
        # Should have positive KS p-value (distributions not too different)
        assert metrics['ks_pvalue'] > 0.0
    
    def test_multiple_duration_generation(self):
        """
        Test generating profiles of various durations.
        """
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        generator = LoadGenerator(k_min=2, k_max=3, random_state=42)
        generator.train(data_path)
        
        # Test various durations
        durations = [24, 168, 720, 1000]
        
        for duration in durations:
            profile = generator.generate_profile(duration_hours=duration, seed=42)
            assert len(profile) == duration
            assert profile.min() >= 0
            assert profile.max() > 0


class TestDataLoaderIntegration:
    """Integration tests for data loading and preprocessing."""
    
    def test_load_real_dataset(self):
        """Test loading actual smart meter dataset."""
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        loader = SmartMeterDataLoader()
        df = loader.load_and_preprocess(data_path, min_hours=24)
        
        # Verify structure
        assert 'load_kw' in df.columns
        assert len(df) >= 24
        assert df.index.name is None or 'timestamp' in str(df.index.name).lower()
        
        # Verify data quality
        assert not df['load_kw'].isna().any()
        assert (df['load_kw'] >= 0).all()
    
    def test_summary_statistics_real_data(self):
        """Test summary statistics on real dataset."""
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        loader = SmartMeterDataLoader()
        df = loader.load_and_preprocess(data_path)
        
        stats = loader.get_summary_statistics(df)
        
        assert stats['duration_hours'] > 0
        assert stats['mean_kw'] > 0
        assert stats['max_kw'] >= stats['mean_kw']
        assert stats['total_kwh'] > 0


class TestClusteringIntegration:
    """Integration tests for clustering on real data."""
    
    def test_cluster_real_data(self):
        """Test clustering on real smart meter data."""
        data_path = "backend/Dataset/smart_meter_data.csv"
        
        # Load data
        from backend.services.load.data_loader import SmartMeterDataLoader
        from backend.services.load.clustering import LoadClusterer
        
        loader = SmartMeterDataLoader()
        df = loader.load_and_preprocess(data_path)
        
        # Cluster
        clusterer = LoadClusterer(k_min=2, k_max=5, random_state=42)
        daily_profiles = clusterer.extract_daily_profiles(df)
        result = clusterer.fit(daily_profiles)
        
        # Verify results
        assert 2 <= result.n_clusters <= 5
        assert -1 <= result.silhouette_score <= 1
        assert len(result.labels) == len(daily_profiles)
        assert result.cluster_centers.shape == (result.n_clusters, 24)
