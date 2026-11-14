#!/usr/bin/env python3
"""
CLI runner for RMS Synthetic Data Generator and Validator.
Usage:
    python run_generator.py --scale 0.1     # Fast starter dataset (~3,000 orders, 500 returns)
    python run_generator.py --scale 1.0     # Full challenge volume (30,000 orders, 5,000 returns, 8,000 lines)
    python run_generator.py --validate-only # Run validation on existing data
"""

import argparse
import sys
import os

from data_generator.generator import RMSDataGenerator
from data_generator.validator import validate_all


def main():
    parser = argparse.ArgumentParser(description="Returns Management System (RMS) Data Generator")
    parser.add_argument("--seed", type=int, default=20261022, help="Deterministic random seed (default: 20261022)")
    parser.add_argument("--scale", type=float, default=1.0, help="Scale factor (1.0 = 30k orders, 0.1 = 3k orders)")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory for CSVs")
    parser.add_argument("--validate-only", action="store_true", help="Only run validator on existing CSVs")

    args = parser.parse_args()

    if args.validate_only:
        validate_all(data_dir=args.output_dir)
        return

    print("=====================================================================")
    print("      RETURNS MANAGEMENT SYSTEM (RMS) - DATA GENERATOR               ")
    print("=====================================================================")
    gen = RMSDataGenerator(seed=args.seed, scale=args.scale, output_dir=args.output_dir)
    gen.generate_all()

    print("\n---------------------------------------------------------------------")
    print("                   RUNNING AUTOMATED VALIDATION                      ")
    print("---------------------------------------------------------------------")
    summary = validate_all(data_dir=args.output_dir)

    print("\n[✓] Finished successfully!")
    print(f"    - Seed: {args.seed}")
    print(f"    - Scale: {args.scale}")
    print(f"    - Status: {summary['status']}")


if __name__ == "__main__":
    main()
