"""
Central configuration for the Privacy-Preserving Complaint Intelligence Platform.

Currently contains only the configuration required for the PII
redaction module. Additional model names, paths, and settings
can be added as the project grows.
"""

from pathlib import Path

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

# Model directory
MODELS_DIR = BASE_DIR / "models"
SAVED_MODELS_DIR = MODELS_DIR / "saved"

# =============================================================================
# spaCy Configuration
# =============================================================================

# spaCy model used by Presidio
SPACY_MODEL = "en_core_web_lg"

# =============================================================================
# Redaction Settings
# =============================================================================

# Language used by Presidio Analyzer
DEFAULT_LANGUAGE = "en"

# Placeholder format for redacted entities
REDACTION_FORMAT = "[{entity}]"