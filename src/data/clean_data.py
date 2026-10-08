"""Data cleaning and preprocessing utilities for complaint datasets."""

from __future__ import annotations

from typing import List, Optional
import pandas as pd

from src.utils.config import CATEGORY_MAP


def drop_invalid_rows(
    df: pd.DataFrame,
    required_cols: Optional[List[str]] = None,
    min_length: int = 15,
) -> pd.DataFrame:
    """Drop rows with missing or junk values in required columns.
    
    Args:
        df: Input DataFrame.
        required_cols: Columns that must not be null. Defaults to common complaint columns.
        min_length: Minimum character length for narrative text.
        
    Returns:
        Cleaned DataFrame.
    """
    df = df.copy()
    cols = required_cols or ["Consumer complaint narrative", "Product"]
    existing_cols = [c for c in cols if c in df.columns]

    df = df.dropna(subset=existing_cols)

    # Narrative length filter
    narrative_col = "Consumer complaint narrative"
    if narrative_col in df.columns:
        df = df[df[narrative_col].astype(str).str.strip().str.len() >= min_length]

    # Map Product to Product_clean if Product is present
    if "Product" in df.columns and "Product_clean" not in df.columns:
        df["Product_clean"] = df["Product"].map(lambda x: CATEGORY_MAP.get(x, x))

    return df.reset_index(drop=True)


def balance_categories(
    df: pd.DataFrame,
    column: str = "Product_clean",
    max_samples_per_category: Optional[int] = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """Balance or down-sample the dataset across categories for training experiments.
    
    Args:
        df: Input DataFrame.
        column: Column to balance across.
        max_samples_per_category: Maximum rows per class. If None, uses smallest class count.
        random_state: Random seed for reproducibility.
        
    Returns:
        Balanced DataFrame.
    """
    if column not in df.columns:
        if "Product" in df.columns:
            column = "Product"
        else:
            return df

    counts = df[column].value_counts()
    min_count = counts.min()
    target_count = max_samples_per_category if max_samples_per_category else min_count

    balanced_dfs = []
    for cat in counts.index:
        cat_df = df[df[column] == cat]
        sample_size = min(len(cat_df), target_count)
        sampled = cat_df.sample(sample_size, random_state=random_state)
        balanced_dfs.append(sampled)

    balanced_df = pd.concat(balanced_dfs, ignore_index=True)
    return balanced_df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
