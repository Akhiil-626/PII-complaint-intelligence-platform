"""
K-anonymity mitigation for the complaint dataset.

Building on the audit in src.privacy.k_anonymity_audit (which measures
re-identification risk from residual quasi-identifiers after PII
redaction), this module applies standard anonymization techniques --
generalization and field suppression -- to reduce that risk, and reports
a direct before/after comparison.

Two mitigation strategies are compared against the original
(un-mitigated) quasi-identifier set:

1. "quarter_binning": generalizes the received-date quasi-identifier from
   month-level to quarter-level precision, reducing date granularity.
2. "drop_subproduct": removes the most granular quasi-identifier
   (Sub-product) entirely, since fine-grained sub-product values are
   often the biggest single driver of small equivalence classes.

Usage
-----
    python -m src.privacy.k_anonymity_mitigation
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd

from src.privacy.k_anonymity_audit import (
    DATA_PATH,
    K_THRESHOLD,
    compute_k_anonymity,
    load_and_prepare,
    summarize_risk,
)

# ---------------------------------------------------------------------------
# Mitigation strategy definitions
# ---------------------------------------------------------------------------

BASELINE_QIS: List[str] = ["Product_clean", "Sub-product", "Issue", "received_month"]

STRATEGIES: Dict[str, List[str]] = {
    "baseline (no mitigation)": BASELINE_QIS,
    "quarter_binning": ["Product_clean", "Sub-product", "Issue", "received_quarter"],
    "drop_subproduct": ["Product_clean", "Issue", "received_month"],
    "quarter_binning + drop_subproduct": ["Product_clean", "Issue", "received_quarter"],
}


# ---------------------------------------------------------------------------
# Generalization
# ---------------------------------------------------------------------------

def add_generalized_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add generalized (coarser) versions of quasi-identifier fields.

    Args:
        df: The prepared complaint DataFrame, expected to already have a
            `received_month` column (from `load_and_prepare`).

    Returns:
        The input DataFrame with an added `received_quarter` column,
        derived by generalizing `received_month` to quarter precision.
    """
    df = df.copy()

    # received_month is a string like "2019-09"; convert back to a period
    # to derive the quarter safely.
    month_periods = pd.PeriodIndex(df["received_month"], freq="M")
    df["received_quarter"] = month_periods.asfreq("Q").astype(str)

    return df


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def run_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Run the k-anonymity audit under each mitigation strategy and compare.

    Args:
        df: The prepared complaint DataFrame with generalized fields already
            added (see `add_generalized_fields`).

    Returns:
        A DataFrame with one row per strategy, containing its resulting
        privacy risk summary statistics, for side-by-side comparison.
    """
    rows = []

    for strategy_name, quasi_identifiers in STRATEGIES.items():
        df_scored = compute_k_anonymity(df, quasi_identifiers=quasi_identifiers)
        summary = summarize_risk(df_scored, k_threshold=K_THRESHOLD)

        rows.append(
            {
                "strategy": strategy_name,
                "quasi_identifiers": ", ".join(quasi_identifiers),
                "pct_unique_k1": summary["pct_unique"],
                "pct_at_risk": summary["pct_at_risk"],
                "mean_k": summary["mean_k"],
                "median_k": summary["median_k"],
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(comparison: pd.DataFrame) -> None:
    """Print a console report comparing mitigation strategies.

    Args:
        comparison: The comparison DataFrame produced by `run_comparison`.
    """
    divider = "=" * 90

    print(divider)
    print("K-ANONYMITY MITIGATION COMPARISON")
    print(divider)

    for _, row in comparison.iterrows():
        print(f"\nStrategy: {row['strategy']}")
        print(f"  Quasi-identifiers : {row['quasi_identifiers']}")
        print(f"  Uniquely identifiable (k=1) : {row['pct_unique_k1']}%")
        print(f"  At-risk (k < {K_THRESHOLD})            : {row['pct_at_risk']}%")
        print(f"  Mean k-value                : {row['mean_k']}")
        print(f"  Median k-value              : {row['median_k']}")

    print("\n" + divider)

    baseline_risk = comparison.iloc[0]["pct_at_risk"]
    best_row = comparison.iloc[1:].loc[comparison.iloc[1:]["pct_at_risk"].idxmin()]
    improvement = round(baseline_risk - best_row["pct_at_risk"], 2)

    print(
        f"Best mitigation: '{best_row['strategy']}' reduced at-risk records "
        f"from {baseline_risk}% to {best_row['pct_at_risk']}% "
        f"(an improvement of {improvement} percentage points)."
    )
    print(divider)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full mitigation comparison end to end and print the report."""
    df = load_and_prepare(DATA_PATH)
    df = add_generalized_fields(df)

    comparison = run_comparison(df)
    print_report(comparison)


if __name__ == "__main__":
    main()