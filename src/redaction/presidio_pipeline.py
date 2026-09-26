"""
Wrapper around Presidio Analyzer and Anonymizer components.

This module provides a unified interface for:
- Detecting PII using Presidio
- Registering custom recognizers
- Redacting detected entities
- Returning metadata for downstream NLP modules
"""

from __future__ import annotations

from typing import Any

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import (
    CreditCardRecognizer,
    EmailRecognizer,
    PhoneRecognizer,
    SpacyRecognizer,
    UrlRecognizer,
    UsSsnRecognizer,
    IpRecognizer,
    NhsRecognizer,
)
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from src.redaction.custom_recognizers import get_custom_recognizers
from src.utils.config import (
    SPACY_MODEL,
    DEFAULT_LANGUAGE,
    REDACTION_FORMAT,
)


class PresidioRedactionPipeline:
    """
    Wrapper around Presidio's AnalyzerEngine and AnonymizerEngine.

    Supported entities:
        - PERSON
        - EMAIL_ADDRESS
        - PHONE_NUMBER
        - ACCOUNT_NUMBER
        - CREDIT_CARD
        - AADHAAR_NUMBER
        - COMPLAINT_ID
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

        # Configure spaCy NLP engine
        provider = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [
                    {
                        "lang_code": DEFAULT_LANGUAGE,
                        "model_name": SPACY_MODEL,
                    }
                ],
            }
        )

        nlp_engine = provider.create_engine()

        # Build the recognizer registry by directly instantiating each
        # predefined recognizer we need. This completely bypasses Presidio's
        # YAML-based loader (load_predefined_recognizers) which, in this
        # installed version (2.2.360), incorrectly passes `supported_language`
        # as a keyword argument to CreditCardRecognizer.__init__(), causing a
        # TypeError. Direct instantiation avoids that broken code path.
        registry = RecognizerRegistry()

        _builtin_recognizers = [
            CreditCardRecognizer(),
            EmailRecognizer(supported_language=DEFAULT_LANGUAGE),
            PhoneRecognizer(supported_language=DEFAULT_LANGUAGE),
            SpacyRecognizer(supported_language=DEFAULT_LANGUAGE),
            UrlRecognizer(supported_language=DEFAULT_LANGUAGE),
            UsSsnRecognizer(supported_language=DEFAULT_LANGUAGE),
            IpRecognizer(supported_language=DEFAULT_LANGUAGE),
            NhsRecognizer(supported_language=DEFAULT_LANGUAGE),
        ]
        for r in _builtin_recognizers:
            registry.add_recognizer(r)

        # Register custom recognizers on the same registry
        for recognizer in get_custom_recognizers():
            registry.add_recognizer(recognizer)

        # Initialize Presidio Analyzer with the manually built registry
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry,
            supported_languages=[DEFAULT_LANGUAGE],
        )

        # Initialize Presidio Anonymizer
        self.anonymizer = AnonymizerEngine()

    def detect(self, text: str):
        """
        Detect PII entities in text.

        Parameters
        ----------
        text : str
            Input complaint text.

        Returns
        -------
        list
            List of Presidio RecognizerResult objects.
        """

        return self.analyzer.analyze(
            text=text,
            language=DEFAULT_LANGUAGE,
        )

    def redact(self, text: str) -> str:
        """
        Redact PII from text.

        Parameters
        ----------
        text : str

        Returns
        -------
        str
            Redacted text.
        """

        results = self.detect(text)

        operators = {
            result.entity_type: OperatorConfig(
                "replace",
                {
                    "new_value": REDACTION_FORMAT.format(
                        entity=result.entity_type
                    )
                },
            )
            for result in results
        }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators,
        )

        return anonymized.text

    def redact_with_metadata(self, text: str) -> dict[str, Any]:
        """
        Redact text and return metadata.

        Returns
        -------
        dict
            {
                "original_text": str,
                "redacted_text": str,
                "entities": list
            }
        """

        results = self.detect(text)

        operators = {
            result.entity_type: OperatorConfig(
                "replace",
                {
                    "new_value": REDACTION_FORMAT.format(
                        entity=result.entity_type
                    )
                },
            )
            for result in results
        }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators,
        )

        entities = [
            {
                "entity_type": result.entity_type,
                "text": text[result.start : result.end],
                "start": result.start,
                "end": result.end,
                "score": round(result.score, 3),
            }
            for result in results
        ]

        return {
            "original_text": text,
            "redacted_text": anonymized.text,
            "entities": entities,
        }


if __name__ == "__main__":
    pipeline = PresidioRedactionPipeline()

    sample_text = """
    Hello,

I'm Rahul Sharma.

Email: rahul@gmail.com

Phone: 9876543210

Account Number: ACC987654321

Complaint ID: CMP-2025-12345

Aadhaar: 1234 5678 9012
    """

    result = pipeline.redact_with_metadata(sample_text)

    print("\nOriginal Text:\n")
    print(result["original_text"])

    print("\n" + "=" * 60)

    print("\nRedacted Text:\n")
    print(result["redacted_text"])

    print("\n" + "=" * 60)

    print("\nDetected Entities:\n")

    for entity in result["entities"]:
        print(entity)