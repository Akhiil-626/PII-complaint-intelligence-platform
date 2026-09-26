"""Simple logging setup for the project."""

from __future__ import annotations

import logging


def setup_logger(name: str = "complaint_intelligence") -> logging.Logger:
    """Create and return a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
    return logger
