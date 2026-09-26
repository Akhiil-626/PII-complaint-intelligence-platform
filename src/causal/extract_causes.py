"""
Root-cause causal extraction using a local LLM (via Ollama).

For a sample of complaints drawn from each category in the dataset, this
module first redacts PII (reusing the existing PresidioRedactionPipeline),
then prompts a locally-running LLM (llama3.1:8b via Ollama) to extract an
immediate cause and, where inferable, a root cause behind the complaint.

Running this extraction locally (rather than via a cloud LLM API) keeps
the project's privacy-first design consistent end-to-end: complaint text,
even after redaction, never leaves the local machine at any pipeline
stage.

Results are cached to data/processed/causal_pairs.json so the (slower,
local) LLM does not need to be re-run on every script execution.

Usage
-----
    python -m src.causal.extract_causes
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import ollama
import pandas as pd

from src.redaction.presidio_pipeline import PresidioRedactionPipeline

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_PATH = Path("data/processed/complaints_small.csv")
OUTPUT_PATH = Path("data/processed/causal_pairs.json")

NARRATIVE_COL = "Consumer complaint narrative"
LABEL_COL = "Product"

OLLAMA_MODEL = "llama3.1:8b"

# Number of complaints sampled per category. Kept small since local LLM
# inference is slower than a cloud API and this is a proof-of-concept
# extraction layer, not a full-dataset batch job.
SAMPLES_PER_CATEGORY = 5
RANDOM_STATE = 42

PROMPT_TEMPLATE = """You are analyzing a customer complaint to identify why it happened.

Given the complaint below, identify:
1. The immediate cause: what directly triggered this complaint (a short phrase, 3-8 words)
2. The root cause: the underlying reason behind it, if you can reasonably infer one (a short phrase, 3-8 words). If no root cause can be inferred, use null.

Respond with ONLY a valid JSON object in this exact format, no other text:
{{"immediate_cause": "...", "root_cause": "..." or null}}

Complaint:
{complaint_text}
"""


# ---------------------------------------------------------------------------
# Data loading + sampling
# ---------------------------------------------------------------------------

def load_sample(
    path: Path = DATA_PATH,
    samples_per_category: int = SAMPLES_PER_CATEGORY,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Load the complaint dataset and sample a fixed number of rows per category.

    Args:
        path: Path to the cleaned/sampled CFPB CSV file.
        samples_per_category: Number of rows to sample from each distinct
            value in LABEL_COL.
        random_state: Random seed for reproducible sampling.

    Returns:
        A DataFrame containing the sampled rows across all categories.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {path.resolve()}")

    df = pd.read_csv(path)
    df = df.dropna(subset=[NARRATIVE_COL, LABEL_COL])

    sampled = (
        df.groupby(LABEL_COL, group_keys=False)[df.columns]
        .apply(
            lambda x: x.sample(min(len(x), samples_per_category), random_state=random_state),
            include_groups=False,
        )
    )
    return sampled.reset_index(drop=True)


# ---------------------------------------------------------------------------
# LLM extraction
# ---------------------------------------------------------------------------

def extract_json_from_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """Extract a JSON object from a raw LLM text response.

    Local LLMs sometimes wrap JSON in markdown code fences or add stray
    text around it. This searches for the first '{...}' block and parses
    it, tolerating minor formatting noise.

    Args:
        raw_text: The raw string returned by the LLM.

    Returns:
        The parsed dict, or None if no valid JSON object could be extracted.
    """
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def query_llm_for_causes(complaint_text: str, model: str = OLLAMA_MODEL) -> Dict[str, Any]:
    """Query the local Ollama model for immediate and root cause extraction.

    Args:
        complaint_text: The (already redacted) complaint text to analyze.
        model: The Ollama model name to use.

    Returns:
        A dict with "immediate_cause" and "root_cause" keys. If the LLM
        response could not be parsed as valid JSON, both fields are set to
        None and a "parse_error" flag is included.
    """
    prompt = PROMPT_TEMPLATE.format(complaint_text=complaint_text)

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_content = response["message"]["content"]
    parsed = extract_json_from_response(raw_content)

    if parsed is None:
        return {
            "immediate_cause": None,
            "root_cause": None,
            "parse_error": True,
            "raw_response": raw_content,
        }

    return {
        "immediate_cause": parsed.get("immediate_cause"),
        "root_cause": parsed.get("root_cause"),
        "parse_error": False,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_extraction(df: pd.DataFrame, redactor: PresidioRedactionPipeline) -> List[Dict[str, Any]]:
    """Run redaction + causal extraction over every row in the sample.

    Args:
        df: The sampled complaint DataFrame (see `load_sample`).
        redactor: An initialized PresidioRedactionPipeline instance.

    Returns:
        A list of result dicts, one per complaint, each containing the
        category, redacted text, and extracted cause information.
    """
    results = []

    total = len(df)
    for idx, row in df.reset_index(drop=True).iterrows():
        print(f"Processing {idx + 1}/{total} ({row[LABEL_COL]})...")

        redacted_text = redactor.redact(row[NARRATIVE_COL])
        causes = query_llm_for_causes(redacted_text)

        results.append(
            {
                "category": row[LABEL_COL],
                "redacted_text": redacted_text,
                "immediate_cause": causes["immediate_cause"],
                "root_cause": causes["root_cause"],
                "parse_error": causes["parse_error"],
            }
        )

    return results


def save_results(results: List[Dict[str, Any]], path: Path = OUTPUT_PATH) -> None:
    """Save extraction results to a JSON file.

    Args:
        results: The list of result dicts from `run_extraction`.
        path: Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def main() -> None:
    """Load a sample, run causal extraction via local LLM, and save results."""
    df = load_sample()
    print(f"Sampled {len(df)} complaints across {df[LABEL_COL].nunique()} categories.\n")

    redactor = PresidioRedactionPipeline()
    results = run_extraction(df, redactor)

    save_results(results)

    parse_errors = sum(1 for r in results if r["parse_error"])
    print(f"\nDone. {len(results)} complaints processed, {parse_errors} parse errors.")
    print(f"Results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
