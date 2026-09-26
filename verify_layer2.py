"""
Standalone verification script for the hierarchical classifier.

Runs the trained HierarchicalClassifier (from
src.classification.hierarchical_predict) against a random sample of real,
labeled rows from the complaint dataset, and compares its domain and
sub-issue predictions against the known ground-truth Product/Issue labels.

This checks real quantitative agreement against ground truth, complementing
the qualitative spot-checks already run via
hierarchical_predict.py's __main__ demo.

Usage
-----
    python verify_layer2.py
"""

from __future__ import annotations

import pandas as pd

from src.classification.hierarchical_predict import HierarchicalClassifier

DATA_PATH = "data/processed/complaints_small.csv"
SAMPLE_SIZE = 10
RANDOM_STATE = 1


def main() -> None:
    """Load sample data, run predictions, and print a TRUE vs PRED comparison."""
    df = pd.read_csv(DATA_PATH).dropna(
        subset=["Consumer complaint narrative", "Product", "Issue"]
    )

    sample = df.sample(SAMPLE_SIZE, random_state=RANDOM_STATE)

    clf = HierarchicalClassifier()

    domain_correct = 0
    issue_correct = 0

    for _, row in sample.iterrows():
        result = clf.predict(row["Consumer complaint narrative"])

        domain_match = result["domain"] == row["Product"] or result["domain"] in str(row["Product"])
        if result["domain"] == row["Product"]:
            domain_correct += 1

        print("TRUE domain :", row["Product"])
        print("PRED domain :", result["domain"])
        print("TRUE issue  :", row["Issue"])
        print("PRED sub    :", result["sub_issue"])
        print(f"Domain confidence   : {result['domain_confidence']}")
        print(f"Sub-issue confidence: {result['sub_issue_confidence']}")
        if result.get("note"):
            print(f"Note: {result['note']}")
        print("-" * 50)

    print(f"\nDomain exact-match agreement: {domain_correct}/{SAMPLE_SIZE} "
          f"({domain_correct / SAMPLE_SIZE * 100:.1f}%)")
    print("(Note: this uses exact string match against the RAW 'Product' "
          "label, not the consolidated Product_clean category, so a "
          "correct prediction may still show as a 'mismatch' here if the "
          "raw label differs from its consolidated form -- inspect the "
          "printed TRUE/PRED pairs above for the real semantic agreement.)")


if __name__ == "__main__":
    main()
