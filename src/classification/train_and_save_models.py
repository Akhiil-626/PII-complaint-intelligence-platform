"""
Trains the TF-IDF+SVM and Sentence-BERT+LogisticRegression classifiers
once and saves them to disk for reuse in live prediction (see
src.classification.live_predict).

DistilBERT is NOT retrained here -- it is expected to already be saved at
models/saved/domain_classifier_distilbert by running
src.classification.distilbert_finetune separately (fine-tuning is too
slow to duplicate in this script). If that directory is missing, this
script prints a warning and proceeds with only the other two models.

Usage
-----
    python -m src.classification.train_and_save_models
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_PATH = Path("data/processed/complaints_small.csv")
MODEL_DIR = Path("models/saved/live_classifiers")

NARRATIVE_COL = "Consumer complaint narrative"
LABEL_COL = "Product"
CLEAN_LABEL_COL = "Product_clean"

MAX_FEATURES = 5000
MIN_CATEGORY_COUNT = 20
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"

DISTILBERT_DIR = Path("models/saved/domain_classifier_distilbert")

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
# Data loading
# ---------------------------------------------------------------------------

def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load and consolidate categories in the complaint dataset.

    Args:
        path: Path to the cleaned/sampled CFPB CSV file.

    Returns:
        A DataFrame with a Product_clean column, rare categories dropped.
    """
    df = pd.read_csv(path)
    df = df.dropna(subset=[NARRATIVE_COL, LABEL_COL])
    df[CLEAN_LABEL_COL] = df[LABEL_COL].map(lambda x: CATEGORY_MAP.get(x, x))

    counts = df[CLEAN_LABEL_COL].value_counts()
    rare = counts[counts < MIN_CATEGORY_COUNT].index.tolist()
    if rare:
        df = df[~df[CLEAN_LABEL_COL].isin(rare)]
    return df


# ---------------------------------------------------------------------------
# Training + saving
# ---------------------------------------------------------------------------

def train_and_save_tfidf_svm(df: pd.DataFrame, output_dir: Path) -> None:
    """Train TF-IDF+SVM on the full dataset and save vectorizer + classifier.

    Args:
        df: The consolidated complaint DataFrame.
        output_dir: Directory to save the model files into.
    """
    print("Training TF-IDF + SVM...")
    vectorizer = TfidfVectorizer(max_features=MAX_FEATURES, stop_words="english")
    X = vectorizer.fit_transform(df[NARRATIVE_COL])
    y = df[CLEAN_LABEL_COL]

    clf = LinearSVC(class_weight="balanced")
    clf.fit(X, y)

    joblib.dump(vectorizer, output_dir / "tfidf_vectorizer.joblib")
    joblib.dump(clf, output_dir / "tfidf_svm_classifier.joblib")
    print(f"  Saved to {output_dir}/tfidf_vectorizer.joblib and tfidf_svm_classifier.joblib")


def train_and_save_sbert_logreg(df: pd.DataFrame, output_dir: Path) -> None:
    """Train Sentence-BERT+LogisticRegression on the full dataset and save it.

    Args:
        df: The consolidated complaint DataFrame.
        output_dir: Directory to save the model files into.
    """
    print("Training Sentence-BERT + Logistic Regression...")
    print("  Loading Sentence-BERT model (may download on first run)...")
    embedder = SentenceTransformer(SBERT_MODEL_NAME)

    print("  Generating embeddings for full training set...")
    X_emb = embedder.encode(df[NARRATIVE_COL].tolist(), show_progress_bar=True, batch_size=32)
    y = df[CLEAN_LABEL_COL]

    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X_emb, y)

    joblib.dump(clf, output_dir / "sbert_logreg_classifier.joblib")
    print(f"  Saved to {output_dir}/sbert_logreg_classifier.joblib")
    print(f"  (Sentence-BERT embedder itself is loaded fresh at inference time "
          f"via SentenceTransformer('{SBERT_MODEL_NAME}') -- no need to save it.)")


def check_distilbert_saved(distilbert_dir: Path = DISTILBERT_DIR) -> bool:
    """Check whether a fine-tuned DistilBERT model is already saved.

    Args:
        distilbert_dir: Expected path to the saved DistilBERT model.

    Returns:
        True if the directory exists and appears to contain model files.
    """
    if not distilbert_dir.exists():
        return False
    return any(distilbert_dir.iterdir())


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    """Load data, train TF-IDF+SVM and Sentence-BERT+LogReg, save all models."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data(DATA_PATH)
    print(f"Loaded {len(df)} rows, {df[CLEAN_LABEL_COL].nunique()} categories.\n")

    train_and_save_tfidf_svm(df, MODEL_DIR)
    print()
    train_and_save_sbert_logreg(df, MODEL_DIR)
    print()

    if check_distilbert_saved():
        print(f"DistilBERT model found at {DISTILBERT_DIR} -- ready for live use.")
    else:
        print(f"WARNING: No fine-tuned DistilBERT model found at {DISTILBERT_DIR}.")
        print("Run 'python -m src.classification.distilbert_finetune' first if "
              "you want DistilBERT included in live predictions. Continuing "
              "with only TF-IDF+SVM and Sentence-BERT+LogReg for now.")

    print("\nDone. Saved category labels used:", sorted(df[CLEAN_LABEL_COL].unique()))


if __name__ == "__main__":
    main()
