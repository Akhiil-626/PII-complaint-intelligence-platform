"""Helpers for generating synthetic PII evaluation examples."""

from __future__ import annotations

from typing import List, Dict


def generate_synthetic_examples(count: int = 20) -> List[Dict[str, object]]:
    """Create synthetic complaint texts with inserted PII placeholders."""
    raise NotImplementedError


def expand_eval_dataset(source_path: str, output_path: str) -> None:
    """Expand a ground-truth evaluation set with synthetic examples."""
    raise NotImplementedError
