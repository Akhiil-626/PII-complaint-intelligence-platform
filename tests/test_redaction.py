"""Unit tests for the Presidio PII redaction pipeline and custom recognizers."""

import pytest
from src.redaction.presidio_pipeline import PresidioRedactionPipeline


@pytest.fixture(scope="module")
def redactor() -> PresidioRedactionPipeline:
    return PresidioRedactionPipeline()


def test_redact_person_and_email(redactor: PresidioRedactionPipeline) -> None:
    text = "Hello, my name is Alice Walker. Please contact me at alice.w@example.com."
    result = redactor.redact_with_metadata(text)

    assert "Alice Walker" not in result["redacted_text"]
    assert "alice.w@example.com" not in result["redacted_text"]
    assert "[PERSON]" in result["redacted_text"]
    assert "[EMAIL_ADDRESS]" in result["redacted_text"]

    entity_types = {e["entity_type"] for e in result["entities"]}
    assert "PERSON" in entity_types
    assert "EMAIL_ADDRESS" in entity_types


def test_redact_phone_and_account(redactor: PresidioRedactionPipeline) -> None:
    text = "Call me at +91 9876543210 regarding account ACC-9876543210."
    result = redactor.redact_with_metadata(text)

    assert "9876543210" not in result["redacted_text"]
    assert "[ACCOUNT_NUMBER]" in result["redacted_text"]
    assert "[PHONE_NUMBER]" in result["redacted_text"]


def test_redact_aadhaar_and_credit_card(redactor: PresidioRedactionPipeline) -> None:
    text = "My Aadhaar is 1234 5678 9012 and my card number is 4111 2222 3333 4444."
    result = redactor.redact_with_metadata(text)

    assert "1234 5678 9012" not in result["redacted_text"]
    assert "4111 2222 3333 4444" not in result["redacted_text"]
    assert "[AADHAAR_NUMBER]" in result["redacted_text"]
    assert "[CREDIT_CARD]" in result["redacted_text"]


def test_redact_complaint_id_and_credentials(redactor: PresidioRedactionPipeline) -> None:
    text = "My ticket is CMP-2026-99999. My username is alice_w99 and password is SuperSecret123."
    result = redactor.redact_with_metadata(text)

    assert "CMP-2026-99999" not in result["redacted_text"]
    assert "SuperSecret123" not in result["redacted_text"]
    assert "[COMPLAINT_ID]" in result["redacted_text"]
    assert "[CREDENTIAL]" in result["redacted_text"]


def test_redact_empty_and_clean_text(redactor: PresidioRedactionPipeline) -> None:
    empty_result = redactor.redact_with_metadata("")
    assert empty_result["redacted_text"] == ""
    assert len(empty_result["entities"]) == 0

    clean_text = "The interest rate increased unexpectedly without prior notification."
    clean_result = redactor.redact_with_metadata(clean_text)
    assert clean_result["redacted_text"] == clean_text
    assert len(clean_result["entities"]) == 0