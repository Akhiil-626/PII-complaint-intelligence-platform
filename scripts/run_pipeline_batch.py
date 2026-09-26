"""
Batch pipeline runner: applies PII redaction and hierarchical
classification to every complaint in the dataset, saving combined
results for downstream use (e.g. a dashboard).

For each complaint, this script:
1. Redacts PII from the raw narrative (via PresidioRedactionPipeline)
2. Predicts domain and sub-issue on the REDACTED text (via
   HierarchicalClassifier) -- classification runs on redacted text to
   keep the pipeline privacy-first end to end, consistent with the
   project's core design principle
3. Records per-entity-type redaction counts for that complaint

Results are saved to data/processed/pipeline_results.csv, with one row
per complaint and one column per tracked entity type (count of that
entity type redacted in that complaint), plus classification outputs
and the original date/true-label fields for reference.

Usage
-----
    python -m scripts.run_pipeline_batch
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.redaction.presidio_pipeline import PresidioRedactionPipeline
from src.classification.hierarchical_predict import HierarchicalClassifier

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_PATH = Path("data/processed/complaints_small.csv")
OUTPUT_PATH = Path("data/processed/pipeline_results.csv")

NARRATIVE_COL = "Consumer complaint narrative"

ENTITY_TYPES = (
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "ACCOUNT_NUMBER",
    "AADHAAR_NUMBER",
    "COMPLAINT_ID",
    "CREDIT_CARD",
    "CREDENTIAL",
)

# Print a progress update every N rows, since the full dataset can take a
# while to process (redaction + classification per row).
PROGRESS_INTERVAL = 100


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(path: Path = INPUT_PATH) -> pd.DataFrame:
    """Load the complaint dataset for batch processing.

    Args:
        path: Path to the cleaned/sampled CFPB CSV file.

    Returns:
        A DataFrame with rows missing the narrative column dropped.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {path.resolve()}")

    df = pd.read_csv(path)
    df = df.dropna(subset=[NARRATIVE_COL])
    return df


# ---------------------------------------------------------------------------
# Per-row processing
# ---------------------------------------------------------------------------

def count_entities_by_type(entities: List[Dict]) -> Dict[str, int]:
    """Count redacted entities per tracked entity type for one complaint.

    Args:
        entities: The "entities" list from
            PresidioRedactionPipeline.redact_with_metadata's output.

    Returns:
        A dict mapping each entity type in ENTITY_TYPES to its count in
        this complaint (0 if none found). Entity types outside the
        tracked schema are ignored.
    """
    counts = {etype: 0 for etype in ENTITY_TYPES}
    for entity in entities:
        etype = entity.get("entity_type")
        if etype in counts:
            counts[etype] += 1
    return counts


def process_row(
    row: pd.Series,
    redactor: PresidioRedactionPipeline,
    classifier: HierarchicalClassifier,
) -> Dict:
    """Run redaction and hierarchical classification on a single complaint.

    Args:
        row: A row from the complaint DataFrame.
        redactor: An initialized PresidioRedactionPipeline instance.
        classifier: An initialized HierarchicalClassifier instance.

    Returns:
        A flat dict combining original metadata, redaction entity counts,
        and classification predictions -- one row's worth of pipeline
        output.
    """
    narrative = row[NARRATIVE_COL]

    redaction_result = redactor.redact_with_metadata(narrative)
    redacted_text = redaction_result["redacted_text"]
    entity_counts = count_entities_by_type(redaction_result["entities"])

    prediction = classifier.predict(redacted_text)

    result = {
        "date": row.get("Date received"),
        "true_product": row.get("Product"),
        "true_issue": row.get("Issue"),
        "redacted_text": redacted_text,
        "predicted_category": prediction["domain"],
        "predicted_sub_issue": prediction["sub_issue"],
        "domain_confidence": prediction["domain_confidence"],
        "sub_issue_confidence": prediction["sub_issue_confidence"],
    }
    result.update(entity_counts)

    return result


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full batch pipeline over the dataset and save combined results."""
    df = load_data(INPUT_PATH)
    total = len(df)
    print(f"Loaded {total} complaints. Starting batch pipeline...\n")

    redactor = PresidioRedactionPipeline()
    classifier = HierarchicalClassifier()

    results = []
    for idx, (_, row) in enumerate(df.iterrows()):
        result = process_row(row, redactor, classifier)
        results.append(result)

        if (idx + 1) % PROGRESS_INTERVAL == 0 or (idx + 1) == total:
            print(f"Processed {idx + 1}/{total} complaints...")

    results_df = pd.DataFrame(results)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_PATH, index=False)

    print(f"\nDone. Results saved to: {OUTPUT_PATH}")
    print(f"Total rows: {len(results_df)}")
    print(f"Columns: {list(results_df.columns)}")


if __name__ == "__main__":
    main()
