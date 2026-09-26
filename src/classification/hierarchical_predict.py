"""
Script to load and make predictions using the trained hierarchical classifier.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Dict, Any, Optional

import joblib
import numpy as np


def softmax(x: np.ndarray) -> np.ndarray:
    """Compute softmax values for each set of scores in x.
    
    Args:
        x: Array-like containing scores.
        
    Returns:
        Softmax normalized probability array.
    """
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


class HierarchicalClassifier:
    """Hierarchical (domain -> sub-issue) classifier loader and predictor."""
    
    def __init__(self, model_dir: str = "models/saved/hierarchical"):
        """Load the hierarchial models from disk.
        
        Args:
            model_dir: Path to the directory where models are saved.
            
        Raises:
            FileNotFoundError: If the models directory does not exist or missing files.
        """
        self.model_dir = Path(model_dir)
        if not self.model_dir.exists():
            raise FileNotFoundError(
                f"Model directory not found: {self.model_dir}. "
                "Please run hierarchical_train.py first."
            )
            
        domain_model_path = self.model_dir / "domain_classifier.joblib"
        if not domain_model_path.exists():
            raise FileNotFoundError(f"Domain model not found: {domain_model_path}.")
            
        domain_model = joblib.load(domain_model_path)
        self.domain_vectorizer = domain_model["vectorizer"]
        self.domain_classifier = domain_model["classifier"]
        
        with open(self.model_dir / "metadata.json", "r") as f:
            self.metadata = json.load(f)
            
        self.subclassifiers = {}
        subclass_dir = self.model_dir / "subclassifiers"
        for domain, slug in self.metadata["trained_domains"].items():
            path = subclass_dir / f"{slug}.joblib"
            self.subclassifiers[domain] = joblib.load(path)

    def _get_confidence(self, clf: Any, X: Any) -> float:
        """Calculate proxy confidence score for LinearSVC predictions.
        
        Since LinearSVC lacks predict_proba by default, this uses the 
        decision_function distance to the separating hyperplane. 
        Applying softmax over the distances provides a pseudo-probability distribution
        as proxy confidence score.
        
        Args:
            clf: The trained classifier.
            X: Vectorized input features.
            
        Returns:
            Confidence metric (float in 0-1).
        """
        scores = clf.decision_function(X)[0]
        
        if hasattr(scores, '__iter__') and len(scores) > 1:
            # Multi-class scenario
            probs = softmax(scores)
            return float(np.max(probs))
        else:
            # Binary classification case fallback where decision_function is 1D
            score = float(scores) if not hasattr(scores, '__iter__') else float(scores[0])
            prob = 1 / (1 + math.exp(-score))
            return float(max(prob, 1 - prob))

    def predict(self, text: str) -> Dict[str, Any]:
        """Predict the domain and sub-issue for a given complaint text.
        
        Args:
            text: The complaint narrative.
            
        Returns:
            A dictionary containing domain, sub_issue, confidences, and notes.
        """
        X_tfidf = self.domain_vectorizer.transform([text])
        domain = str(self.domain_classifier.predict(X_tfidf)[0])
        domain_conf = self._get_confidence(self.domain_classifier, X_tfidf)
        
        result = {
            "domain": domain,
            "sub_issue": None,
            "domain_confidence": round(domain_conf, 4),
            "sub_issue_confidence": None,
            "note": None
        }
        
        if domain in self.subclassifiers:
            sub_model = self.subclassifiers[domain]
            sub_X = sub_model["vectorizer"].transform([text])
            sub_issue = str(sub_model["classifier"].predict(sub_X)[0])
            sub_conf = self._get_confidence(sub_model["classifier"], sub_X)
            result["sub_issue"] = sub_issue
            result["sub_issue_confidence"] = round(sub_conf, 4)
        else:
            result["note"] = (
                f"No sub-classifier available for domain '{domain}' "
                "(likely skipped during training due to insufficient data)."
            )
            
        return result


def main() -> None:
    """Demonstration of predicting hierarchical classes."""
    try:
        classifier = HierarchicalClassifier()
    except FileNotFoundError as e:
        print(f"Error loading classifier: {e}")
        return
    
    examples = [
        "I was checking my credit score and saw a hard inquiry from a company I don't recognize.",
        "A debt collector keeps calling my workplace even after I told them I am not allowed to receive personal calls there.",
        "I tried to transfer money to my friend via the app, but the money left my bank account and never arrived at his."
    ]
    
    for i, text in enumerate(examples, 1):
        print(f"\n--- Example {i} ---")
        print(f"Text: '{text}'")
        res = classifier.predict(text)
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
