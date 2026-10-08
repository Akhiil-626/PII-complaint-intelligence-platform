"""Utilities for loading and sampling complaint datasets incrementally."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional, Union
import pandas as pd


def load_complaint_dataset(
    csv_path: Union[str, Path],
    chunksize: int = 1000,
) -> Iterator[pd.DataFrame]:
    """Load a complaint CSV file in chunks for memory-efficient processing.
    
    Args:
        csv_path: Path to the CSV file.
        chunksize: Number of rows per chunk.
        
    Yields:
        DataFrame chunks.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Complaint dataset not found at: {path.resolve()}")

    return pd.read_csv(path, chunksize=chunksize)


def sample_rows(
    csv_path: Union[str, Path],
    n_rows: int = 1000,
    output_path: Optional[Union[str, Path]] = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """Create a smaller stratified or random sample of the dataset for local experimentation.
    
    Args:
        csv_path: Path to the source CSV file.
        n_rows: Number of rows to sample.
        output_path: Optional destination file path to save the sample.
        random_state: Random seed for reproducibility.
        
    Returns:
        Sampled DataFrame.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found at: {path.resolve()}")

    df = pd.read_csv(path)
    sample_size = min(len(df), n_rows)

    strat_col = "Product" if "Product" in df.columns else None
    if strat_col and df[strat_col].nunique() > 1:
        # Sample proportionally across products
        sampled = (
            df.groupby(strat_col, group_keys=False)
            .apply(lambda x: x.sample(max(1, int(len(x) * (sample_size / len(df)))), random_state=random_state))
        )
        # Pad or trim to exactly sample_size if needed
        if len(sampled) < sample_size:
            remaining = df[~df.index.isin(sampled.index)]
            additional = remaining.sample(min(len(remaining), sample_size - len(sampled)), random_state=random_state)
            sampled = pd.concat([sampled, additional], ignore_index=True)
        elif len(sampled) > sample_size:
            sampled = sampled.sample(sample_size, random_state=random_state)
    else:
        sampled = df.sample(sample_size, random_state=random_state)

    sampled = sampled.reset_index(drop=True)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        sampled.to_csv(out_p, index=False)

    return sampled
