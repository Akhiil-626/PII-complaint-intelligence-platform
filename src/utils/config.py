"""
Central configuration for the Privacy-Preserving Complaint Intelligence Platform.

Contains unified paths, model identifiers, taxonomies, thresholds, and entity schemas.
"""

from pathlib import Path
from typing import Dict, Tuple

# =============================================================================
# Project Paths
# =============================================================================

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EVAL_DATA_DIR = DATA_DIR / "eval"

COMPLAINTS_DATA_PATH = PROCESSED_DATA_DIR / "complaints_small.csv"
SYNTH_EVAL_PATH = EVAL_DATA_DIR / "synth_data.json"
PIPELINE_RESULTS_PATH = PROCESSED_DATA_DIR / "pipeline_results.csv"
LIVE_SUBMISSIONS_PATH = PROCESSED_DATA_DIR / "live_submissions.csv"
CAUSAL_PAIRS_PATH = PROCESSED_DATA_DIR / "causal_pairs.json"

# Model directory
MODELS_DIR = BASE_DIR / "models"
SAVED_MODELS_DIR = MODELS_DIR / "saved"
LIVE_MODEL_DIR = SAVED_MODELS_DIR / "live_classifiers"
DISTILBERT_DIR = SAVED_MODELS_DIR / "domain_classifier_distilbert"
HIERARCHICAL_MODEL_DIR = SAVED_MODELS_DIR / "hierarchical"
CAUSAL_GRAPH_PATH = SAVED_MODELS_DIR / "causal_graph.gexf"

# =============================================================================
# Model Names & Presets
# =============================================================================

SPACY_MODEL = "en_core_web_lg"
DEFAULT_LANGUAGE = "en"
REDACTION_FORMAT = "[{entity}]"

SBERT_MODEL_NAME = "all-MiniLM-L6-v2"
DISTILBERT_BASE_MODEL = "distilbert-base-uncased"
OLLAMA_MODEL = "llama3.1:8b"

# =============================================================================
# Tracked Entities Schema
# =============================================================================

ENTITY_TYPES: Tuple[str, ...] = (
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "ACCOUNT_NUMBER",
    "AADHAAR_NUMBER",
    "COMPLAINT_ID",
    "CREDIT_CARD",
    "CREDENTIAL",
)

# =============================================================================
# Category Consolidation Mapping (CFPB Taxonomy Alignment)
# =============================================================================

CATEGORY_MAP: Dict[str, str] = {
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

DISTILBERT_LABELS = sorted([
    "Bank account/service",
    "Credit reporting",
    "Credit/Prepaid card",
    "Debt collection",
    "Money transfer",
    "Mortgage",
    "Personal/Payday loan",
    "Student loan",
    "Vehicle loan or lease",
])

# =============================================================================
# Operational Thresholds
# =============================================================================

LOW_CONFIDENCE_THRESHOLD = 0.40
K_ANONYMITY_THRESHOLD = 5
SPIKE_THRESHOLD = 0.30
SIMILARITY_THRESHOLD = 0.65
DISTILBERT_MAX_LENGTH = 256

RECOMMENDATION_RULES: Dict[str, str] = {
    "Debt collection": "Consider reviewing collection call scripts and staff training.",
    "Credit reporting": "Review recent changes to reporting/verification procedures.",
    "Credit/Prepaid card": "Check for recent card-related system outages or fee changes.",
    "Bank account/service": "Investigate recent changes to account terms or mobile banking stability.",
    "Mortgage": "Review recent servicing transfers or rate-adjustment communications.",
    "Student loan": "Check for recent servicer changes or repayment-plan communication issues.",
    "Personal/Payday loan": "Review recent changes to loan terms or collection practices.",
    "Money transfer": "Check for recent outages or delays in transfer processing systems.",
    "Vehicle loan or lease": "Review recent changes to payment processing or collection practices.",
}

DEFAULT_RECOMMENDATION = (
    "Volume increase detected -- recommend a manual review of recent process or system changes."
)