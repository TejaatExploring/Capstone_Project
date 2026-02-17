"""
Load Generation Inference Script
=================================

Generate synthetic load profiles using pre-trained model.

Usage:
    python -m backend.services.load.inference --hours 720 --seed 42

Output:
    - Generated load profile (NumPy array or CSV)
    - Statistics and visualization (optional)
"""

import logging
import argparse
import numpy as np
from pathlib import Path

from .load_generator import LoadGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main inference pipeline."""
    parser = argparse.ArgumentParser(description="Generate synthetic load profile")
    parser.add_argument(
        '--hours',
        type=int,
        default=720,
        help='Number of hours to generate (default: 720 = 30 days)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default='backend/trained_models/load_generator',
        help='Directory containing trained models'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (CSV format)'
    )
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("SYNTHETIC LOAD GENERATION - INFERENCE")
    logger.info("="*80)
    logger.info(f"Model Directory: {args.model_dir}")
    logger.info(f"Duration: {args.hours} hours ({args.hours/24:.1f} days)")
    logger.info(f"Random Seed: {args.seed}")
    logger.info("")
    
    # Load trained model
    logger.info("Loading trained model...")
    generator = LoadGenerator()
    
    try:
        generator.load_model(args.model_dir)
        logger.info("Model loaded successfully")
    except FileNotFoundError:
        logger.error(f"Model not found at {args.model_dir}")
        logger.error("Please train the model first using: python -m backend.services.load.training")
        return
    logger.info("")
    
    # Generate profile
    logger.info(f"Generating {args.hours} hours of synthetic load...")
    profile = generator.generate_profile(
        duration_hours=args.hours,
        seed=args.seed
    )
    logger.info("Generation complete")
    logger.info("")
    
    # Statistics
    logger.info("Profile Statistics:")
    logger.info(f"  Duration: {len(profile)} hours ({len(profile)/24:.1f} days)")
    logger.info(f"  Mean Load: {np.mean(profile):.3f} kW")
    logger.info(f"  Std Dev: {np.std(profile):.3f} kW")
    logger.info(f"  Min Load: {np.min(profile):.3f} kW")
    logger.info(f"  Max Load: {np.max(profile):.3f} kW")
    logger.info(f"  Total Energy: {np.sum(profile):.3f} kWh")
    logger.info("")
    
    # Save output if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        np.savetxt(output_path, profile, delimiter=',', header='load_kw', comments='')
        logger.info(f"Profile saved to {output_path}")
    else:
        logger.info("No output file specified (use --output to save)")
    
    logger.info("="*80)
    logger.info("INFERENCE COMPLETE")
    logger.info("="*80)
    
    return profile


if __name__ == "__main__":
    main()
