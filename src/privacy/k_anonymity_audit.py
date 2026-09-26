"""
K-anonymity privacy audit for the complaint dataset.

Even after direct PII (names, emails, phone numbers, account numbers) is
redacted from complaint narratives, structured "quasi-identifier" fields
often remain — category, sub-category, issue type, and date. If a specific
combination of these is rare or unique within the dataset, a record can
still be individually re-identified by an attacker with minimal outside
knowledge, even without any PII in the text itself.

This module computes each record's k-anonymity value: the number of other
records in the dataset that share its exact quasi-identifier combination.
A record with k=1 is uniquely identifiable from non-PII fields alone. This
is a standard, well-established privacy metric (distinct from, and
complementary to, entity-level redaction precision/recall) and is used
here to audit record-level re-identification risk.

Usage
-----
    python -m src.privacy.k_anonymity_audit
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_PATH = Path("data/processed/complaints_small.csv")

NARRATIVE_COL = "Consumer complaint narrative"
LABEL_COL = "Product"
DATE_COL = "Date received"

# Quasi-identifier fields used for the k-anonymity computation. These are
# non-PII structured fields that remain in the dataset after redaction but
# can still narrow a record down to a small, potentially unique group.
QUASI_IDENTIFIERS = ["Product_clean", "Sub-product", "Issue", "received_month"]

# A record is flagged "at risk" if its k-anonymity value falls below this
# threshold (i.e. it shares its quasi-identifier combination with fewer
# than K_THRESHOLD other records).
K_THRESHOLD = 5

# Same category consolidation used by the classification modules, kept
# identical here so quasi-identifier groupings reflect the same clean
# category schema used elsewhere in the project.
CATEGORY_MAP = {
    "Credit reporting, credit repair services, or other personal consumer reports": "Credit reporting",
    "Credit reporting": "Credit reporting",

    "Credit card or prepaid card": "Credit/Prepaid card",
    "Credit card": "Credit/Prepaid card",
    "Prepaid card": "Credit/Prepaid card",

    "Money transfer, virtual currency, or money service": "Money transfer",
    "Money transfers": "Money transfer",

    "Payday loan, title loan, or personal loan": "Personal/Payday loan",
    "Payday loan": "Personal/Payday loan",
    "Consumer Loan": "Personal/Payday loan",

    "Bank account or service": "Bank account/service",
    "Checking or savings account": "Bank account/service",
}


# ---------------------------------------------------------------------------
# Data loading + preparation
# ---------------------------------------------------------------------------

def load_and_prepare(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the complaint dataset and derive quasi-identifier fields.

    Args:
        path: Path to the cleaned/sampled CFPB CSV file.

    Returns:
        A DataFrame with a consolidated `Product_clean` category column and
        a `received_month` column (year-month) derived from the raw date,
        used as generalized quasi-identifiers for the k-anonymity audit.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {path.resolve()}")

    df = pd.read_csv(path)
    df = df.dropna(subset=[NARRATIVE_COL, LABEL_COL])

    df["Product_clean"] = df[LABEL_COL].map(lambda x: CATEGORY_MAP.get(x, x))

    if DATE_COL in df.columns:
        df["received_month"] = pd.to_datetime(
            df[DATE_COL], errors="coerce"
        ).dt.to_period("M").astype(str)
    else:
        df["received_month"] = "unknown"

    # Missing quasi-identifier fields are filled with a placeholder so they
    # still participate in grouping (a missing sub-product is itself a
    # shared trait among records that lack one, not something to drop).
    for col in ["Sub-product", "Issue"]:
        if col in df.columns:
            df[col] = df[col].fillna("(missing)")
        else:
            df[col] = "(missing)"

    return df


# ---------------------------------------------------------------------------
# K-anonymity computation
# ---------------------------------------------------------------------------

def compute_k_anonymity(
    df: pd.DataFrame, quasi_identifiers: List[str] = QUASI_IDENTIFIERS
) -> pd.DataFrame:
    """Compute the k-anonymity value for every record in the dataset.

    Groups records by their exact combination of quasi-identifier values
    and assigns each record a `k_value` equal to the size of its group
    (i.e. how many records, including itself, share that combination).

    Args:
        df: The prepared complaint DataFrame, including all columns listed
            in `quasi_identifiers`.
        quasi_identifiers: The list of column names treated as
            quasi-identifiers for this audit.

    Returns:
        The input DataFrame with an added `k_value` column.
    """
    group_sizes = df.groupby(quasi_identifiers, dropna=False)[quasi_identifiers[0]].transform("size")
    df = df.copy()
    df["k_value"] = group_sizes
    return df


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def summarize_risk(df: pd.DataFrame, k_threshold: int = K_THRESHOLD) -> dict:
    """Summarize dataset-wide k-anonymity risk statistics.

    Args:
        df: A DataFrame that already has a `k_value` column (see
            `compute_k_anonymity`).
        k_threshold: The k-value below which a record is considered "at
            risk" of re-identification.

    Returns:
        A dict of summary statistics: total records, unique (k=1) records,
        at-risk records (k < threshold), min/mean/median k, and the
        percentage of records at risk.
    """
    total = len(df)
    unique_records = int((df["k_value"] == 1).sum())
    at_risk = int((df["k_value"] < k_threshold).sum())

    return {
        "total_records": total,
        "unique_records_k1": unique_records,
        "at_risk_records": at_risk,
        "pct_at_risk": round((at_risk / total) * 100, 2) if total else 0.0,
        "pct_unique": round((unique_records / total) * 100, 2) if total else 0.0,
        "min_k": int(df["k_value"].min()) if total else 0,
        "mean_k": round(df["k_value"].mean(), 2) if total else 0.0,
        "median_k": round(df["k_value"].median(), 2) if total else 0.0,
    }


def print_report(summary: dict, k_threshold: int = K_THRESHOLD) -> None:
    """Print a console report of the k-anonymity audit results.

    Args:
        summary: The summary dict produced by `summarize_risk`.
        k_threshold: The k-value threshold used to flag at-risk records,
            included here for display purposes.
    """
    divider = "=" * 56

    print(divider)
    print("K-ANONYMITY PRIVACY AUDIT")
    print(divider)
    print(f"Quasi-identifiers used : {', '.join(QUASI_IDENTIFIERS)}")
    print(f"At-risk threshold (k)  : < {k_threshold}")
    print("-" * 56)
    print(f"Total records evaluated     : {summary['total_records']:,}")
    print(f"Uniquely identifiable (k=1) : {summary['unique_records_k1']:,} "
          f"({summary['pct_unique']}%)")
    print(f"At-risk records (k < {k_threshold})   : {summary['at_risk_records']:,} "
          f"({summary['pct_at_risk']}%)")
    print("-" * 56)
    print(f"Minimum k-value  : {summary['min_k']}")
    print(f"Mean k-value     : {summary['mean_k']}")
    print(f"Median k-value   : {summary['median_k']}")
    print(divider)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full k-anonymity audit end to end and print the report."""
    df = load_and_prepare(DATA_PATH)
    df = compute_k_anonymity(df)
    summary = summarize_risk(df)
    print_report(summary)


if __name__ == "__main__":
    main()