"""
Hierarchical (domain -> sub-issue) classifier for complaint routing.

Extends the flat domain classification (Product_clean, 9 categories) with
a second stage: for each domain, a dedicated sub-classifier predicts the
specific `Issue` within that domain. This enables fine-grained routing
(e.g. "Debt collection -> Attempts to collect debt not owed") rather than
just department-level classification.

Like the `Product` field, CFPB's `Issue` field contains near-duplicate
labels from taxonomy revisions over time (e.g. "Incorrect information on
your report" vs "Incorrect information on credit report", or "Dealing
with your lender or servicer" vs "Dealing with my lender or servicer").
These are consolidated via fuzzy text similarity before training, for the
same reason the `Product` field was consolidated: training on
near-duplicate labels artificially fragments semantically identical
complaints and hurts every downstream metric.

Usage
-----
    python -m src.classification.hierarchical_classifier
"""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_PATH = Path("data/processed/complaints_small.csv")

NARRATIVE_COL = "Consumer complaint narrative"
LABEL_COL = "Product"
ISSUE_COL = "Issue"
CLEAN_LABEL_COL = "Product_clean"
CLEAN_ISSUE_COL = "Issue_clean"

TEST_SIZE = 0.2
RANDOM_STATE = 42
MAX_FEATURES = 3000

# Minimum rows a domain needs (after category consolidation) to be
# considered for hierarchical sub-classification at all.
MIN_DOMAIN_COUNT = 20

# Minimum rows a specific sub-issue needs, within its domain, to be kept
# as its own class rather than dropped as too rare to train/evaluate.
MIN_ISSUE_COUNT = 15

# Similarity threshold (0-1) above which two issue labels are considered
# near-duplicates and merged. Uses simple sequence-matching ratio on
# lowercased text, which is enough to catch wording-only differences like
# "your report" vs "credit report" without needing an embedding model.
ISSUE_SIMILARITY_THRESHOLD = 0.6

# Same Product consolidation map used by the flat classifiers, kept
# identical here so the domain stage matches exactly.
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
# Data loading + domain consolidation
# ---------------------------------------------------------------------------

def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the dataset and consolidate the top-level domain (Product) field.

    Args:
        path: Path to the cleaned/sampled CFPB CSV file.

    Returns:
        A DataFrame with a `Product_clean` column, rows with rare domains
        dropped.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {path.resolve()}")

    df = pd.read_csv(path)
    df = df.dropna(subset=[NARRATIVE_COL, LABEL_COL, ISSUE_COL])

    df[CLEAN_LABEL_COL] = df[LABEL_COL].map(lambda x: CATEGORY_MAP.get(x, x))

    counts = df[CLEAN_LABEL_COL].value_counts()
    rare_domains = counts[counts < MIN_DOMAIN_COUNT].index.tolist()
    if rare_domains:
        print(f"Dropping rare domains (< {MIN_DOMAIN_COUNT} rows): {rare_domains}\n")
        df = df[~df[CLEAN_LABEL_COL].isin(rare_domains)]

    return df


# ---------------------------------------------------------------------------
# Issue label consolidation (fuzzy near-duplicate merging)
# ---------------------------------------------------------------------------

def _similarity(a: str, b: str) -> float:
    """Compute a simple text similarity ratio between two strings.

    Args:
        a: First string.
        b: Second string.

    Returns:
        A similarity ratio in [0, 1], where 1.0 means identical.
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def build_issue_consolidation_map(
    issue_labels: List[str], threshold: float = ISSUE_SIMILARITY_THRESHOLD
) -> Dict[str, str]:
    """Group near-duplicate issue labels and map each to a canonical form.

    Compares every pair of distinct issue labels using text similarity; any
    pair above `threshold` is merged into the same group. Within each
    group, the shortest label is chosen as the canonical representative
    (shorter CFPB labels are typically the more recent, cleaner wording).

    Args:
        issue_labels: The list of distinct raw issue label strings to
            consolidate.
        threshold: Similarity ratio above which two labels are merged.

    Returns:
        A dict mapping every raw issue label to its canonical (merged)
        label.
    """
    unassigned = list(issue_labels)
    groups: List[List[str]] = []

    while unassigned:
        seed = unassigned.pop(0)
        group = [seed]

        remaining = []
        for label in unassigned:
            if _similarity(seed, label) >= threshold:
                group.append(label)
            else:
                remaining.append(label)
        unassigned = remaining

        groups.append(group)

    mapping: Dict[str, str] = {}
    for group in groups:
        canonical = min(group, key=len)
        for label in group:
            mapping[label] = canonical

    return mapping


def consolidate_issues_per_domain(df: pd.DataFrame) -> pd.DataFrame:
    """Consolidate near-duplicate issue labels, separately within each domain.

    Consolidation is done per-domain (not globally) since the same issue
    wording can be a near-duplicate within one domain's context but an
    unrelated coincidence across domains.

    Args:
        df: The domain-consolidated complaint DataFrame.

    Returns:
        The input DataFrame with an added `Issue_clean` column.
    """
    df = df.copy()
    df[CLEAN_ISSUE_COL] = df[ISSUE_COL]

    for domain in df[CLEAN_LABEL_COL].unique():
        mask = df[CLEAN_LABEL_COL] == domain
        distinct_issues = df.loc[mask, ISSUE_COL].unique().tolist()

        issue_map = build_issue_consolidation_map(distinct_issues)
        df.loc[mask, CLEAN_ISSUE_COL] = df.loc[mask, ISSUE_COL].map(issue_map)

    return df


# ---------------------------------------------------------------------------
# Sub-classifier training (one per domain)
# ---------------------------------------------------------------------------

def train_and_evaluate_subclassifier(
    domain: str, domain_df: pd.DataFrame
) -> Tuple[str, dict] | None:
    """Train and evaluate a sub-issue classifier for a single domain.

    Rows whose Issue_clean value is too rare within this domain (below
    MIN_ISSUE_COUNT) are dropped before training, since they cannot be
    reliably learned or evaluated. Domains left with fewer than 2 distinct
    sub-issue classes after filtering are skipped entirely.

    Args:
        domain: The domain (Product_clean) name being processed.
        domain_df: The subset of the full dataset belonging to this domain.

    Returns:
        A tuple of (domain, metrics_dict), or None if this domain was
        skipped (too few classes/rows to train a meaningful classifier).
    """
    issue_counts = domain_df[CLEAN_ISSUE_COL].value_counts()
    valid_issues = issue_counts[issue_counts >= MIN_ISSUE_COUNT].index.tolist()

    filtered = domain_df[domain_df[CLEAN_ISSUE_COL].isin(valid_issues)]

    if filtered[CLEAN_ISSUE_COL].nunique() < 2 or len(filtered) < 30:
        print(f"[SKIPPED] '{domain}': not enough data/classes after filtering "
              f"(<2 sub-issue classes with >= {MIN_ISSUE_COUNT} rows, or <30 total rows).")
        return None

    X = filtered[NARRATIVE_COL]
    y = filtered[CLEAN_ISSUE_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    vectorizer = TfidfVectorizer(
        max_features=MAX_FEATURES, stop_words="english", ngram_range=(1, 2)
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    clf = LinearSVC(class_weight="balanced")
    clf.fit(X_train_tfidf, y_train)

    y_pred = clf.predict(X_test_tfidf)

    accuracy = accuracy_score(y_test, y_pred)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    print(f"\n--- Domain: {domain} ---")
    print(f"Sub-issue classes: {filtered[CLEAN_ISSUE_COL].nunique()} "
          f"(from {domain_df[CLEAN_ISSUE_COL].nunique()} original, "
          f"{len(filtered)} rows after filtering)")
    print(f"Accuracy    : {accuracy * 100:.2f}%")
    print(f"Weighted F1 : {weighted_f1 * 100:.2f}%")
    print(classification_report(y_test, y_pred, zero_division=0))

    return domain, {
        "accuracy": accuracy,
        "weighted_f1": weighted_f1,
        "num_classes": filtered[CLEAN_ISSUE_COL].nunique(),
        "num_rows": len(filtered),
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    """Load data, consolidate labels, train per-domain sub-classifiers, report."""
    df = load_data(DATA_PATH)
    df = consolidate_issues_per_domain(df)

    print("=" * 60)
    print("HIERARCHICAL CLASSIFICATION: DOMAIN -> SUB-ISSUE")
    print("=" * 60)

    results = {}
    for domain in sorted(df[CLEAN_LABEL_COL].unique()):
        domain_df = df[df[CLEAN_LABEL_COL] == domain]
        result = train_and_evaluate_subclassifier(domain, domain_df)
        if result is not None:
            domain_name, metrics = result
            results[domain_name] = metrics

    print("\n" + "=" * 60)
    print("SUMMARY ACROSS ALL DOMAINS")
    print("=" * 60)
    for domain, metrics in results.items():
        print(f"{domain:35s} | Acc: {metrics['accuracy']*100:5.2f}% | "
              f"F1: {metrics['weighted_f1']*100:5.2f}% | "
              f"Classes: {metrics['num_classes']} | Rows: {metrics['num_rows']}")

    if results:
        avg_acc = sum(m["accuracy"] for m in results.values()) / len(results)
        avg_f1 = sum(m["weighted_f1"] for m in results.values()) / len(results)
        print("-" * 60)
        print(f"Average sub-classifier accuracy : {avg_acc * 100:.2f}%")
        print(f"Average sub-classifier F1        : {avg_f1 * 100:.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()