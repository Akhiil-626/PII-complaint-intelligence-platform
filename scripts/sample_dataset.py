"""Standalone script for creating a small sample dataset from raw complaint data."""

from __future__ import annotations

import argparse
from pathlib import Path
from src.data.load_data import sample_rows
from src.utils.config import COMPLAINTS_DATA_PATH


def main() -> None:
    """Generate a small local sample of complaint data."""
    parser = argparse.ArgumentParser(description="Sample complaint records from dataset.")
    parser.add_argument("--input", default=str(COMPLAINTS_DATA_PATH), help="Source CSV file path")
    parser.add_argument("--output", default="data/processed/complaints_sample.csv", help="Target CSV file path")
    parser.add_argument("--rows", type=int, default=500, help="Number of rows to sample")

    args = parser.parse_args()

    print(f"Sampling {args.rows} rows from {args.input}...")
    sample_df = sample_rows(args.input, n_rows=args.rows, output_path=args.output)
    print(f"Successfully saved {len(sample_df)} sampled rows to: {args.output}")


if __name__ == "__main__":
    main()
