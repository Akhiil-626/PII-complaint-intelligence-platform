"""Evaluation script for the PII redaction pipeline.

This module loads a synthetic, manually-annotated evaluation dataset
(data/eval/synth_data.json), runs the project's Presidio-based redaction
pipeline (src.redaction.presidio_pipeline.PresidioRedactionPipeline) against
every complaint, and compares the detected entities to the ground-truth
entities.

For every entity type it computes True Positives (TP), False Positives (FP),
and False Negatives (FN), and derives Precision, Recall, and F1 Score from
first principles (no sklearn.metrics dependency). An aggregate ("Overall")
score across all entity types is also produced.

A prediction is only considered a match if BOTH the entity `type` and the
exact `text` span match the ground truth annotation for that complaint.

Usage
-----
    python -m src.redaction.evaluate_redaction
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple, TypedDict

from src.redaction.presidio_pipeline import PresidioRedactionPipeline

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATASET_PATH = Path("data/eval/synth_data.json")

ENTITY_TYPES: Tuple[str, ...] = (
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "ACCOUNT_NUMBER",
    "AADHAAR_NUMBER",
    "COMPLAINT_ID",
    "CREDIT_CARD",
    "CREDENTIAL",
)


# ---------------------------------------------------------------------------
# Typed data structures
# ---------------------------------------------------------------------------

class EntityDict(TypedDict):
    """A single PII entity: its type label and exact surface text."""

    type: str
    text: str


class ComplaintRecord(TypedDict):
    """A single evaluation record loaded from synth_data.json."""

    id: str
    complaint_text: str
    entities: List[EntityDict]


class EntityCounts(TypedDict):
    """Raw TP / FP / FN counts for one entity type (or overall)."""

    tp: int
    fp: int
    fn: int


class MetricScores(TypedDict):
    """Derived precision / recall / F1 for one entity type (or overall)."""

    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_dataset(dataset_path: Path = DATASET_PATH) -> List[ComplaintRecord]:
    """Load the synthetic evaluation dataset from disk.

    Args:
        dataset_path: Path to the JSON file containing the list of
            annotated complaint records.

    Returns:
        A list of complaint records, each containing the raw complaint
        text and its ground-truth entity annotations.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If the file does not contain a JSON array.
    """
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found at: {dataset_path.resolve()}"
        )

    with dataset_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a JSON array of complaint records in {dataset_path}, "
            f"got {type(data).__name__}."
        )

    return data


# ---------------------------------------------------------------------------
# Prediction extraction
# ---------------------------------------------------------------------------

def extract_predictions(
    pipeline: PresidioRedactionPipeline, text: str
) -> List[EntityDict]:
    """Run the redaction pipeline on a complaint and normalize its output.

    Converts Presidio's `RecognizerResult` objects (which reference entity
    spans via start/end offsets) into plain dictionaries containing the
    entity type and the literal detected text, extracted from the original
    complaint via `text[result.start:result.end]`.

    Args:
        pipeline: An initialized PresidioRedactionPipeline instance.
        text: The raw (un-redacted) complaint text to analyze.

    Returns:
        A list of predicted entities, each with `type` and `text` keys.
    """
    results = pipeline.detect(text)

    predictions: List[EntityDict] = []
    for result in results:
        detected_text = text[result.start:result.end]
        predictions.append({"type": result.entity_type, "text": detected_text})

    return predictions


# ---------------------------------------------------------------------------
# Sample-level evaluation
# ---------------------------------------------------------------------------

def evaluate_sample(
    ground_truth: List[EntityDict], predictions: List[EntityDict]
) -> Dict[str, EntityCounts]:
    """Compare predicted entities to ground truth for a single complaint.

    A prediction is counted as a True Positive only if there exists a
    ground-truth entity with the exact same `type` AND exact same `text`
    that has not already been matched. Unmatched predictions are False
    Positives; unmatched ground-truth entities are False Negatives.

    Matching is performed per-entity-type using multisets, so duplicate
    entity values are handled correctly (each ground-truth occurrence can
    only be matched once).

    Args:
        ground_truth: The list of true entities for this complaint.
        predictions: The list of entities detected by the pipeline.

    Returns:
        A mapping from entity type to a dict of {"tp": int, "fp": int,
        "fn": int} counts for this single complaint.
    """
    counts: Dict[str, EntityCounts] = {
        etype: {"tp": 0, "fp": 0, "fn": 0} for etype in ENTITY_TYPES
    }

    # Build a mutable pool of remaining ground-truth (type, text) pairs,
    # grouped by type, so each true entity can only satisfy one prediction.
    remaining_truth: Dict[str, List[str]] = defaultdict(list)
    for entity in ground_truth:
        remaining_truth[entity["type"]].append(entity["text"])

    for prediction in predictions:
        etype = prediction["type"]
        ptext = prediction["text"]

        if etype not in counts:
            # Entity type outside our tracked schema; ignore for scoring.
            continue

        pool = remaining_truth.get(etype, [])
        if ptext in pool:
            pool.remove(ptext)
            counts[etype]["tp"] += 1
        else:
            counts[etype]["fp"] += 1

    # Anything left unmatched in remaining_truth was never predicted.
    for etype, leftover in remaining_truth.items():
        if etype not in counts:
            continue
        counts[etype]["fn"] += len(leftover)

    return counts


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def _safe_divide(numerator: float, denominator: float) -> float:
    """Divide two numbers, returning 0.0 instead of raising on division by zero.

    Args:
        numerator: The dividend.
        denominator: The divisor.

    Returns:
        numerator / denominator, or 0.0 if denominator is 0.
    """
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_metrics(tp: int, fp: int, fn: int) -> MetricScores:
    """Compute precision, recall, and F1 score from raw TP/FP/FN counts.

    Formulas:
        Precision = TP / (TP + FP)
        Recall    = TP / (TP + FN)
        F1        = 2 * Precision * Recall / (Precision + Recall)

    All divisions are guarded against division-by-zero, returning 0.0
    in degenerate cases (e.g., no predictions and no ground truth).

    Args:
        tp: True positive count.
        fp: False positive count.
        fn: False negative count.

    Returns:
        A dict with precision, recall, f1, and the original tp/fp/fn counts.
    """
    precision = _safe_divide(tp, tp + fp)
    recall = _safe_divide(tp, tp + fn)
    f1 = _safe_divide(2 * precision * recall, precision + recall)

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def aggregate_counts(
    per_sample_counts: List[Dict[str, EntityCounts]]
) -> Dict[str, EntityCounts]:
    """Sum per-complaint TP/FP/FN counts into per-entity-type totals.

    Args:
        per_sample_counts: A list of per-complaint count dicts, as produced
            by `evaluate_sample`, one per evaluated complaint.

    Returns:
        A mapping from entity type to aggregated {"tp", "fp", "fn"} counts
        across the entire dataset.
    """
    totals: Dict[str, EntityCounts] = {
        etype: {"tp": 0, "fp": 0, "fn": 0} for etype in ENTITY_TYPES
    }

    for sample_counts in per_sample_counts:
        for etype, counts in sample_counts.items():
            totals[etype]["tp"] += counts["tp"]
            totals[etype]["fp"] += counts["fp"]
            totals[etype]["fn"] += counts["fn"]

    return totals


def compute_all_metrics(
    totals: Dict[str, EntityCounts]
) -> Tuple[MetricScores, Dict[str, MetricScores]]:
    """Compute overall and per-entity-type metrics from aggregated counts.

    Args:
        totals: Aggregated TP/FP/FN counts per entity type, as produced by
            `aggregate_counts`.

    Returns:
        A tuple of:
            - overall: MetricScores computed across all entity types combined.
            - per_entity: mapping from entity type to its own MetricScores.
    """
    overall_tp = sum(counts["tp"] for counts in totals.values())
    overall_fp = sum(counts["fp"] for counts in totals.values())
    overall_fn = sum(counts["fn"] for counts in totals.values())

    overall = compute_metrics(overall_tp, overall_fp, overall_fn)

    per_entity: Dict[str, MetricScores] = {}
    for etype in ENTITY_TYPES:
        counts = totals[etype]
        per_entity[etype] = compute_metrics(counts["tp"], counts["fp"], counts["fn"])

    return overall, per_entity


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _format_pct(value: float) -> str:
    """Format a 0-1 float score as a percentage string with 2 decimal places.

    Args:
        value: A score in the range [0, 1].

    Returns:
        A string like "98.25%".
    """
    return f"{value * 100:.2f}%"


def print_report(
    overall: MetricScores,
    per_entity: Dict[str, MetricScores],
    num_complaints: int,
    total_expected: int,
    total_detected: int,
    total_correct: int,
) -> None:
    """Print a clean, human-readable evaluation report to the console.

    Args:
        overall: Aggregate metrics across all entity types.
        per_entity: Per-entity-type metrics, keyed by entity type name.
        num_complaints: Number of complaints evaluated.
        total_expected: Total number of ground-truth entities across the
            dataset.
        total_detected: Total number of entities predicted by the pipeline
            across the dataset.
        total_correct: Total number of correct (type + text exact match)
            detections across the dataset.
    """
    divider = "=" * 56
    subdivider = "-" * 56

    print(divider)
    print("PII REDACTION EVALUATION")
    print(divider)

    print("Overall")
    print(f"Precision : {_format_pct(overall['precision'])}")
    print(f"Recall    : {_format_pct(overall['recall'])}")
    print(f"F1 Score  : {_format_pct(overall['f1'])}")

    for etype in ENTITY_TYPES:
        scores = per_entity[etype]
        print(subdivider)
        print(etype)
        print(f"Precision : {_format_pct(scores['precision'])}")
        print(f"Recall    : {_format_pct(scores['recall'])}")
        print(f"F1 Score  : {_format_pct(scores['f1'])}")

    print(subdivider)
    print(f"Complaints evaluated     : {num_complaints}")
    print(f"Total expected entities  : {total_expected}")
    print(f"Total detected entities  : {total_detected}")
    print(f"Total correct detections : {total_correct}")
    print(divider)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full redaction evaluation pipeline end to end.

    Loads the evaluation dataset, runs the Presidio-based redaction
    pipeline over every complaint, computes per-entity and overall
    precision/recall/F1, and prints a console report.
    """
    records = load_dataset(DATASET_PATH)
    pipeline = PresidioRedactionPipeline()

    per_sample_counts: List[Dict[str, EntityCounts]] = []

    total_expected = 0
    total_detected = 0
    total_correct = 0

    for record in records:
        text = record["complaint_text"]
        ground_truth = record["entities"]

        predictions = extract_predictions(pipeline, text)
        sample_counts = evaluate_sample(ground_truth, predictions)
        per_sample_counts.append(sample_counts)

        total_expected += len(ground_truth)
        total_detected += len(predictions)
        total_correct += sum(counts["tp"] for counts in sample_counts.values())

    totals = aggregate_counts(per_sample_counts)
    overall, per_entity = compute_all_metrics(totals)

    print_report(
        overall=overall,
        per_entity=per_entity,
        num_complaints=len(records),
        total_expected=total_expected,
        total_detected=total_detected,
        total_correct=total_correct,
    )


if __name__ == "__main__":
    main()