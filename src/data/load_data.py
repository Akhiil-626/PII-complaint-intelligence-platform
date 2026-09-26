"""Utilities for loading complaint datasets incrementally."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pandas as pd


def load_complaint_dataset(csv_path: str | Path, chunksize: int = 1000) -> Iterator[pd.DataFrame]:
    """Load a complaint CSV file in chunks for memory-efficient processing."""
    raise NotImplementedError


def sample_rows(csv_path: str | Path, n_rows: int = 1000, output_path: str | Path | None = None) -> pd.DataFrame:
    """Create a smaller sample of the dataset for local experimentation."""
    raise NotImplementedError
