"""
Fine-tuned DistilBERT classifier for complaint domain/category classification.

This module fine-tunes a pretrained DistilBERT model (from HuggingFace) on
the same consolidated CFPB complaint categories used by the TF-IDF+SVM and
Sentence-BERT baselines, completing a three-way comparison between
classical ML, embedding-based, and transformer fine-tuning approaches.

Usage
-----
    python -m src.classification.distilbert_finetune
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_PATH = Path("data/processed/complaints_small.csv")

NARRATIVE_COL = "Consumer complaint narrative"
LABEL_COL = "Product"
CLEAN_LABEL_COL = "Product_clean"

TEST_SIZE = 0.2
RANDOM_STATE = 42
MODEL_NAME = "distilbert-base-uncased"
MAX_LENGTH = 128
NUM_EPOCHS = 2
MIN_CATEGORY_COUNT = 20
OUTPUT_DIR = "./models/saved/domain_classifier_distilbert"

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
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(eval_pred) -> dict:
    """Compute accuracy and weighted F1 for HuggingFace's Trainer callback.

    Args:
        eval_pred: A tuple of (logits, labels) provided by the Trainer.

    Returns:
        A dict with "accuracy" and "f1" keys.
    """
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1": f1_score(labels, preds, average="weighted"),
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    """Load data, fine-tune DistilBERT, and print evaluation results."""
    df = load_data(DATA_PATH)
    print(f"Loaded {len(df)} rows, {df[CLEAN_LABEL_COL].nunique()} consolidated categories.\n")

    le = LabelEncoder()
    df["label"] = le.fit_transform(df[CLEAN_LABEL_COL])
    num_labels = len(le.classes_)
    print("Categories:", list(le.classes_))

    train_df, test_df = train_test_split(
        df, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=df["label"]
    )

    train_ds = Dataset.from_pandas(
        train_df[[NARRATIVE_COL, "label"]].rename(columns={NARRATIVE_COL: "text"}),
        preserve_index=False,
    )
    test_ds = Dataset.from_pandas(
        test_df[[NARRATIVE_COL, "label"]].rename(columns={NARRATIVE_COL: "text"}),
        preserve_index=False,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize(batch):
        return tokenizer(
            batch["text"], padding="max_length", truncation=True, max_length=MAX_LENGTH
        )

    train_ds = train_ds.map(tokenize, batched=True)
    test_ds = test_ds.map(tokenize, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=num_labels
    )

    training_args = TrainingArguments(
        output_dir="./results",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=NUM_EPOCHS,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=test_ds,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    print("=" * 56)
    print("DISTILBERT FINE-TUNED CLASSIFIER")
    print("=" * 56)
    eval_results = trainer.evaluate()
    print(f"Accuracy      : {eval_results['eval_accuracy'] * 100:.2f}%")
    print(f"Weighted F1   : {eval_results['eval_f1'] * 100:.2f}%")
    print("=" * 56)

    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\nModel saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
