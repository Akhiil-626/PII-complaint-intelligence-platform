"""
Classical baseline classifier for complaint domain/category classification.

This module trains a TF-IDF + Linear SVM classifier on the CFPB complaint
dataset (data/processed/complaints_small.csv), using a consolidated version
of the "Product" column as the classification target. CFPB revised its
category taxonomy over the years, producing near-duplicate labels (e.g.
"Credit reporting" vs "Credit reporting, credit repair services, or other
personal consumer reports"). These are merged here into a single clean
category schema before training, since treating them as distinct classes
artificially fragments semantically identical complaints and hurts model
performance.

Usage
-----
    python -m src.classification.baseline_tfidf_svm
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, accuracy_score, f1_score

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_PATH = Path("data/processed/complaints_small.csv")

NARRATIVE_COL = "Consumer complaint narrative"
LABEL_COL = "Product"
CLEAN_LABEL_COL = "Product_clean"

TEST_SIZE = 0.2
RANDOM_STATE = 42
MAX_FEATURES = 5000

# Consolidation map: raw CFPB "Product" label -> unified category.
# Anything not listed here is kept as-is.
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

# Categories to drop entirely due to insufficient sample size for reliable
# training/evaluation (fewer than MIN_CATEGORY_COUNT total rows).
MIN_CATEGORY_COUNT = 20


# ---------------------------------------------------------------------------
# Data loading + category consolidation
# ---------------------------------------------------------------------------

def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load, clean, and consolidate categories in the complaint dataset.

    Args:
        path: Path to the cleaned/sampled CFPB CSV file.

    Returns:
        A DataFrame with a new `Product_clean` column containing the
        consolidated category labels, with rare categories dropped.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {path.resolve()}")

    df = pd.read_csv(path)
    df = df.dropna(subset=[NARRATIVE_COL, LABEL_COL])

    df[CLEAN_LABEL_COL] = df[LABEL_COL].map(lambda x: CATEGORY_MAP.get(x, x))

    counts = df[CLEAN_LABEL_COL].value_counts()
    rare_categories = counts[counts < MIN_CATEGORY_COUNT].index.tolist()
    if rare_categories:
        print(f"Dropping rare categories (< {MIN_CATEGORY_COUNT} rows): {rare_categories}\n")
        df = df[~df[CLEAN_LABEL_COL].isin(rare_categories)]

    return df


# ---------------------------------------------------------------------------
# Train / test split
# ---------------------------------------------------------------------------

def split_data(
    df: pd.DataFrame,
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Split the dataset into stratified train/test sets.

    Args:
        df: The cleaned, consolidated complaint DataFrame.

    Returns:
        A tuple of (X_train, X_test, y_train, y_test).
    """
    X = df[NARRATIVE_COL]
    y = df[CLEAN_LABEL_COL]

    return train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------

def train_model(
    X_train: pd.Series, y_train: pd.Series
) -> Tuple[TfidfVectorizer, LinearSVC]:
    """Fit a TF-IDF vectorizer and a Linear SVM classifier.

    Args:
        X_train: Training complaint narratives.
        y_train: Training labels (consolidated Product categories).

    Returns:
        A tuple of (fitted vectorizer, fitted classifier).
    """
    vectorizer = TfidfVectorizer(
        max_features=MAX_FEATURES, stop_words="english", ngram_range=(1, 2)
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)

    clf = LinearSVC(class_weight="balanced")
    clf.fit(X_train_tfidf, y_train)

    return vectorizer, clf


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_model(
    vectorizer: TfidfVectorizer,
    clf: LinearSVC,
    X_test: pd.Series,
    y_test: pd.Series,
) -> None:
    """Evaluate the trained model and print a classification report.

    Args:
        vectorizer: The fitted TF-IDF vectorizer.
        clf: The fitted Linear SVM classifier.
        X_test: Test complaint narratives.
        y_test: True test labels.
    """
    X_test_tfidf = vectorizer.transform(X_test)
    y_pred = clf.predict(X_test_tfidf)

    accuracy = accuracy_score(y_test, y_pred)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    print("=" * 56)
    print("TF-IDF + LINEAR SVM BASELINE (consolidated categories)")
    print("=" * 56)
    print(f"Accuracy      : {accuracy * 100:.2f}%")
    print(f"Weighted F1   : {weighted_f1 * 100:.2f}%")
    print("-" * 56)
    print("Per-class report:\n")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("=" * 56)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    """Load data, consolidate categories, train baseline, print results."""
    df = load_data(DATA_PATH)
    print(f"Loaded {len(df)} rows, {df[CLEAN_LABEL_COL].nunique()} consolidated categories.\n")
    print(df[CLEAN_LABEL_COL].value_counts())
    print()

    X_train, X_test, y_train, y_test = split_data(df)
    vectorizer, clf = train_model(X_train, y_train)
    evaluate_model(vectorizer, clf, X_test, y_test)


if __name__ == "__main__":
    main()