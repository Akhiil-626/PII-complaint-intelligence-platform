"""Data cleaning and lightweight preprocessing helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def drop_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with missing or junk values in required columns."""
    raise NotImplementedError


def balance_categories(df: pd.DataFrame, column: str = "category") -> pd.DataFrame:
    """Balance the dataset across categories for training experiments."""
    raise NotImplementedError
