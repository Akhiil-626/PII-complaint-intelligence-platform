"""
Sentence-BERT embedding + Logistic Regression classifier.

This module trains a classifier on the same consolidated CFPB complaint
categories as the TF-IDF+SVM baseline, but uses pretrained Sentence-BERT
sentence embeddings instead of TF-IDF vectors. This captures semantic
meaning (e.g. paraphrases, synonyms) rather than relying purely on
surface-level word overlap, and is compared directly against the
TF-IDF+SVM baseline to evaluate whether semantic embeddings improve
performance on this dataset size.

Usage
-----
    python -m src.classification.sentence_bert_classifier
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
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
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
MIN_CATEGORY_COUNT = 20

# Same consolidation map as the TF-IDF+SVM baseline, kept identical here
# so both models are evaluated on exactly the same label schema.
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
# Embedding generation
# ---------------------------------------------------------------------------

def generate_embeddings(
    texts: pd.Series, model: SentenceTransformer
) -> np.ndarray:
    """Encode a series of complaint narratives into Sentence-BERT embeddings.

    Args:
        texts: Complaint narrative strings.
        model: A loaded SentenceTransformer model.

    Returns:
        A 2D numpy array of shape (n_samples, embedding_dim).
    """
    return model.encode(
        texts.tolist(), show_progress_bar=True, batch_size=32
    )


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
        A tuple of (X_train_text, X_test_text, y_train, y_test), where the
        X values are still raw text (embedding happens after the split so
        train/test embeddings are generated identically but independently).
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
    X_train_emb: np.ndarray, y_train: pd.Series
) -> LogisticRegression:
    """Fit a Logistic Regression classifier on Sentence-BERT embeddings.

    Args:
        X_train_emb: Training embeddings.
        y_train: Training labels (consolidated Product categories).

    Returns:
        The fitted LogisticRegression classifier.
    """
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X_train_emb, y_train)
    return clf


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_model(
    clf: LogisticRegression, X_test_emb: np.ndarray, y_test: pd.Series
) -> None:
    """Evaluate the trained model and print a classification report.

    Args:
        clf: The fitted LogisticRegression classifier.
        X_test_emb: Test embeddings.
        y_test: True test labels.
    """
    y_pred = clf.predict(X_test_emb)

    accuracy = accuracy_score(y_test, y_pred)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    print("=" * 56)
    print("SENTENCE-BERT + LOGISTIC REGRESSION")
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
    """Load data, generate embeddings, train, and evaluate the classifier."""
    df = load_data(DATA_PATH)
    print(f"Loaded {len(df)} rows, {df[CLEAN_LABEL_COL].nunique()} consolidated categories.\n")

    X_train_text, X_test_text, y_train, y_test = split_data(df)

    print("Loading Sentence-BERT model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("Generating training embeddings...")
    X_train_emb = generate_embeddings(X_train_text, model)

    print("Generating test embeddings...")
    X_test_emb = generate_embeddings(X_test_text, model)

    clf = train_model(X_train_emb, y_train)
    evaluate_model(clf, X_test_emb, y_test)


if __name__ == "__main__":
    main()