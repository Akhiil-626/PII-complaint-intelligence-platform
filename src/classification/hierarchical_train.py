"""
Script to train and save the hierarchical classifier model.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split

from src.classification.hierarchical_classifier import (
    load_data,
    consolidate_issues_per_domain,
    DATA_PATH,
    NARRATIVE_COL,
    CLEAN_LABEL_COL,
    CLEAN_ISSUE_COL,
    MIN_ISSUE_COUNT,
    MAX_FEATURES,
    TEST_SIZE,
    RANDOM_STATE
)

def slugify(text: str) -> str:
    """Convert string to slug for safe filenames.
    
    Args:
        text: The text to slugify.
        
    Returns:
        The slugified text.
    """
    text = text.lower()
    text = re.sub(r'[\s/]+', '_', text)
    return text

def train_domain_classifier(df: pd.DataFrame) -> dict:
    """Train the top-level domain classifier.
    
    Args:
        df: The pandas DataFrame with complaint data.
        
    Returns:
        A dictionary with the fitted vectorizer and classifier.
    """
    X = df[NARRATIVE_COL]
    y = df[CLEAN_LABEL_COL]

    # Exactly same configuration as baseline_tfidf_svm.py for consistency
    vectorizer = TfidfVectorizer(
        max_features=5000, stop_words="english", ngram_range=(1, 2)
    )
    X_tfidf = vectorizer.fit_transform(X)

    clf = LinearSVC(class_weight="balanced")
    clf.fit(X_tfidf, y)
    
    return {"vectorizer": vectorizer, "classifier": clf}

def main() -> None:
    """Main execution of the hierarchical training script."""
    print("Loading data...")
    df = load_data(DATA_PATH)
    df = consolidate_issues_per_domain(df)

    out_dir = Path("models/saved/hierarchical")
    out_dir.mkdir(parents=True, exist_ok=True)
    subclass_dir = out_dir / "subclassifiers"
    subclass_dir.mkdir(parents=True, exist_ok=True)

    print("Training domain classifier...")
    domain_model = train_domain_classifier(df)
    joblib.dump(domain_model, out_dir / "domain_classifier.joblib")

    saved_domains = []
    skipped_domains = []
    metadata: Dict[str, Any] = {
        "trained_domains": {},
        "skipped_domains": [],
        "domain_issues": {}
    }

    print("Training sub-classifiers...")
    # Iterate over domains to build subclassifiers
    for domain in sorted(df[CLEAN_LABEL_COL].unique()):
        domain_df = df[df[CLEAN_LABEL_COL] == domain]
        
        issue_counts = domain_df[CLEAN_ISSUE_COL].value_counts()
        valid_issues = issue_counts[issue_counts >= MIN_ISSUE_COUNT].index.tolist()
        
        filtered = domain_df[domain_df[CLEAN_ISSUE_COL].isin(valid_issues)]
        
        if filtered[CLEAN_ISSUE_COL].nunique() < 2 or len(filtered) < 30:
            skipped_domains.append((domain, "Not enough valid data/classes"))
            metadata["skipped_domains"].append(domain)
            continue
            
        X = filtered[NARRATIVE_COL]
        y = filtered[CLEAN_ISSUE_COL]
        
        vectorizer = TfidfVectorizer(
            max_features=MAX_FEATURES, stop_words="english", ngram_range=(1, 2)
        )
        X_tfidf = vectorizer.fit_transform(X)
        
        clf = LinearSVC(class_weight="balanced")
        clf.fit(X_tfidf, y)

        slug = slugify(domain)
        # Save subclassifier
        model_dict = {"vectorizer": vectorizer, "classifier": clf}
        joblib.dump(model_dict, subclass_dir / f"{slug}.joblib")
        
        saved_domains.append(domain)
        metadata["trained_domains"][domain] = slug
        metadata["domain_issues"][domain] = sorted(valid_issues)
        
    # Save metadata
    with open(out_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)
    print(f"Total domains processed: {len(df[CLEAN_LABEL_COL].unique())}")
    print(f"Domain classifier saved to: {out_dir / 'domain_classifier.joblib'}")
    print("\nSaved Sub-classifiers:")
    for d in saved_domains:
        counts = len(metadata["domain_issues"][d])
        print(f"  - {d} ({counts} sub-issues)")
        
    print("\nSkipped Domains:")
    for d, reason in skipped_domains:
        print(f"  - {d}: {reason}")
    print("=" * 60)

if __name__ == "__main__":
    main()
