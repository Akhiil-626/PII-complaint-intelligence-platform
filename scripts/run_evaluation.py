"""Run evaluation experiments and print a unified performance comparison table."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from src.classification.predict import predict
from src.redaction.evaluate_redaction import evaluate_sample, extract_predictions, load_dataset
from src.redaction.presidio_pipeline import PresidioRedactionPipeline
from src.utils.config import CATEGORY_MAP, COMPLAINTS_DATA_PATH, SYNTH_EVAL_PATH


def evaluate_pii_redaction() -> dict:
    """Run evaluation on ground-truth synthetic dataset."""
    pipeline = PresidioRedactionPipeline()
    records = load_dataset(SYNTH_EVAL_PATH)

    tp_total = 0
    fp_total = 0
    fn_total = 0

    for rec in records:
        preds = extract_predictions(pipeline, rec["complaint_text"])
        res = evaluate_sample(rec["entities"], preds)
        for counts in res.values():
            tp_total += counts["tp"]
            fp_total += counts["fp"]
            fn_total += counts["fn"]

    prec = tp_total / (tp_total + fp_total) if (tp_total + fp_total) else 0.0
    rec = tp_total / (tp_total + fn_total) if (tp_total + fn_total) else 0.0
    f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) else 0.0

    return {
        "precision": round(prec * 100, 2),
        "recall": round(rec * 100, 2),
        "f1": round(f1 * 100, 2),
    }


def evaluate_classifiers(sample_size: int = 400) -> pd.DataFrame:
    """Run evaluation on a test split of complaints."""
    df = pd.read_csv(COMPLAINTS_DATA_PATH).dropna(subset=["Consumer complaint narrative", "Product"])
    df["Product_clean"] = df["Product"].map(lambda x: CATEGORY_MAP.get(x, x))

    if len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)

    X = df["Consumer complaint narrative"].tolist()
    y = df["Product_clean"].tolist()

    models = ["tfidf_svm", "sentence_bert", "distilbert"]
    rows = []

    for m in models:
        try:
            preds = predict(X, model_type=m)
            acc = accuracy_score(y, preds)
            f1 = f1_score(y, preds, average="weighted", zero_division=0)
            rows.append({
                "Model": m,
                "Accuracy": f"{acc * 100:.2f}%",
                "Weighted F1": f"{f1 * 100:.2f}%",
                "Evaluated Samples": len(X),
            })
        except Exception as e:
            rows.append({
                "Model": m,
                "Accuracy": "Error",
                "Weighted F1": str(e),
                "Evaluated Samples": len(X),
            })

    return pd.DataFrame(rows)


def main() -> None:
    """Execute the evaluation workflow for all supported models."""
    print("=" * 60)
    print("RUNNING PLATFORM BENCHMARK & EVALUATION")
    print("=" * 60)

    print("\n1. Evaluating PII Redaction Pipeline...")
    pii_metrics = evaluate_pii_redaction()
    print(f"  Precision : {pii_metrics['precision']}%")
    print(f"  Recall    : {pii_metrics['recall']}%")
    print(f"  F1 Score  : {pii_metrics['f1']}%")

    print("\n2. Evaluating Multi-Model Classifiers...")
    clf_df = evaluate_classifiers(sample_size=300)
    print("\n" + clf_df.to_string(index=False))
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
