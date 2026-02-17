"""
Load Generation Training Script
================================

Trains the Markov + KMeans load generation model on smart meter data.

Usage:
    python -m backend.services.load.training

Output:
    - Trained models saved to backend/trained_models/
    - Training metrics logged
    - Evaluation report generated
"""

import logging
from pathlib import Path
import time

from .load_generator import LoadGenerator
from .baselines import FlatBaseline, HistoricalReplayBaseline, generate_evaluation_report
from .data_loader import SmartMeterDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main training pipeline."""
    logger.info("="*80)
    logger.info("BRAIN 1A: SYNTHETIC LOAD GENERATOR TRAINING")
    logger.info("="*80)
    logger.info("")
    
    # Configuration
    data_path = "backend/Dataset/smart_meter_data.csv"
    model_dir = "backend/trained_models/load_generator"
    
    logger.info(f"Data Source: {data_path}")
    logger.info(f"Model Output: {model_dir}")
    logger.info("")
    
    # Step 1: Train Main Model (Markov + KMeans)
    logger.info("Training Main Model (Markov + KMeans)...")
    logger.info("-" * 80)
    
    start_time = time.time()
    
    generator = LoadGenerator(
        k_min=2,
        k_max=10,
        smoothing_alpha=0.01,
        noise_std_ratio=0.1,
        random_state=42
    )
    
    training_metrics = generator.train(data_path)
    
    train_time = time.time() - start_time
    logger.info(f"Training completed in {train_time:.2f} seconds")
    logger.info("")
    
    # Log key metrics
    logger.info("Training Metrics:")
    logger.info(f"  Duration: {training_metrics['duration_days']:.1f} days")
    logger.info(f"  Mean Load: {training_metrics['mean_kw']:.3f} kW")
    logger.info(f"  Peak Load: {training_metrics['max_kw']:.3f} kW")
    logger.info(f"  Clusters (K): {training_metrics['n_clusters']}")
    logger.info(f"  Silhouette Score: {training_metrics['silhouette_score']:.4f}")
    logger.info("")
    
    # Save model
    logger.info(f"Saving model to {model_dir}...")
    generator.save_model(model_dir)
    logger.info("Model saved successfully")
    logger.info("")
    
    # Step 2: Train Baselines
    logger.info("Training Baseline Models...")
    logger.info("-" * 80)
    
    # Flat baseline
    flat_baseline = FlatBaseline()
    flat_baseline.train(data_path)
    flat_baseline.save_model(model_dir)
    logger.info("FlatBaseline trained and saved")
    
    # Historical replay baseline
    replay_baseline = HistoricalReplayBaseline()
    replay_baseline.train(data_path)
    replay_baseline.save_model(model_dir)
    logger.info("HistoricalReplayBaseline trained and saved")
    logger.info("")
    
    # Step 3: Generate Evaluation Profiles
    logger.info("Generating Evaluation Profiles...")
    logger.info("-" * 80)
    
    # Load real data for comparison
    data_loader = SmartMeterDataLoader()
    df_real = data_loader.load_and_preprocess(data_path)
    real_profile = df_real['load_kw'].values[:720]  # First 720 hours
    
    logger.info(f"Real profile: {len(real_profile)} hours")
    
    # Generate synthetic profiles
    start_gen = time.time()
    markov_profile = generator.generate_profile(duration_hours=720, seed=42)
    gen_time = time.time() - start_gen
    logger.info(f"Markov+KMeans profile generated in {gen_time:.4f} seconds")
    
    flat_profile = flat_baseline.generate_profile(duration_hours=720)
    logger.info("Flat baseline profile generated")
    
    replay_profile = replay_baseline.generate_profile(duration_hours=720, seed=42)
    logger.info("Historical replay profile generated")
    logger.info("")
    
    # Step 4: Statistical Comparison
    logger.info("Statistical Comparison...")
    logger.info("-" * 80)
    
    synthetic_profiles = {
        'Markov+KMeans': markov_profile,
        'Flat Baseline': flat_profile,
        'Historical Replay': replay_profile
    }
    
    report = generate_evaluation_report(real_profile, synthetic_profiles)
    print(report)
    
    # Save report
    report_path = Path(model_dir) / "evaluation_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Evaluation report saved to {report_path}")
    logger.info("")
    
    # Step 5: Performance Summary
    logger.info("="*80)
    logger.info("TRAINING SUMMARY")
    logger.info("="*80)
    logger.info(f"Training Time: {train_time:.2f} seconds ({'✓ PASS' if train_time < 10 else '✗ FAIL'} < 10s)")
    logger.info(f"Generation Time: {gen_time:.4f} seconds ({'✓ PASS' if gen_time < 1 else '✗ FAIL'} < 1s)")
    logger.info(f"Model Saved: {model_dir}")
    logger.info(f"Evaluation Report: {report_path}")
    logger.info("="*80)


if __name__ == "__main__":
    main()
