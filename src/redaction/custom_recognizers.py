"""
Custom Presidio recognizers for domain-specific PII.

This module adds support for detecting entities that are not covered by
Presidio's default recognizers, such as:

- Account Numbers
- Aadhaar Numbers
- Complaint IDs
- Credit Card Numbers

These recognizers are registered with Presidio's AnalyzerEngine.
"""

from presidio_analyzer import Pattern, PatternRecognizer


class AccountNumberRecognizer(PatternRecognizer):
    """
    Detects bank/customer account numbers.

    Examples:
        AC987654321
        ACC123456789
        ACC-10023456

    NOTE:
    Only prefixed formats are matched (ACC-/AC/ACCOUNT).
    A generic bare-digit pattern was intentionally removed because it
    collided with phone numbers and other numeric PII (e.g. a 10-digit
    account pattern would also match a 10-digit phone number), causing
    false positives.
    """

    PATTERNS = [
        Pattern(
            name="account_number_prefix",
            regex=r"\b(?:AC|ACC|ACCOUNT)[-_ ]?\d{6,16}\b",
            score=0.80,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="ACCOUNT_NUMBER",
            patterns=self.PATTERNS,
        )


class AadhaarRecognizer(PatternRecognizer):
    """
    Detects Indian Aadhaar numbers.

    Examples:
        1234 5678 9012

    NOTE:
    Uses lookaround assertions to ensure exactly 3 space-separated
    4-digit groups are matched, and not a subset of a longer digit
    sequence (e.g. a 4-group, space-separated credit card number like
    "4111 1111 1111 1111" would otherwise have its first or last three
    groups misidentified as an Aadhaar number).

    The plain 12-digit (no spaces) pattern was removed since it
    collided with other numeric PII of the same length.
    """

    PATTERNS = [
        Pattern(
            name="aadhaar_spaced",
            regex=r"(?<!\d{4}\s)\b\d{4}\s\d{4}\s\d{4}\b(?!\s\d{4})",
            score=0.95,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="AADHAAR_NUMBER",
            patterns=self.PATTERNS,
        )


class ComplaintIDRecognizer(PatternRecognizer):
    """
    Detects complaint/ticket IDs.

    Examples:
        CMP12345
        CMP-2025-45678
        CMP-2026-00001
        COMPLAINT123
        TICKET-98765
        CASE001245

    NOTE:
    The pattern now allows multiple hyphen/underscore-separated
    alphanumeric groups after the prefix, so multi-segment IDs like
    "CMP-2026-00001" are matched in full instead of stopping at the
    first hyphen.
    """

    PATTERNS = [
        Pattern(
            name="complaint_id",
            regex=r"\b(?:CMP|CASE|TICKET|COMPLAINT)[-_]?[A-Z0-9]+(?:[-_][A-Z0-9]+)*\b",
            score=0.90,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="COMPLAINT_ID",
            patterns=self.PATTERNS,
        )


class CreditCardRecognizer(PatternRecognizer):
    """
    Detects common credit/debit card numbers.

    Supports:
        4111111111111111
        4111-1111-1111-1111
        4111 1111 1111 1111

    NOTE:
    This recognizer only checks formatting.
    It does not perform Luhn validation.
    """

    PATTERNS = [
        Pattern(
            name="credit_card",
            regex=r"\b(?:\d{4}[- ]?){3}\d{4}\b",
            score=0.90,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="CREDIT_CARD",
            patterns=self.PATTERNS,
        )

class CredentialRecognizer(PatternRecognizer):
    """
    Detects login credentials (usernames, passwords, login IDs) written
    either in key-value style (password: X) or natural language style
    (password is X) within complaint text.

    Examples:
        password: mySecret123
        pwd = hunter2
        username is john_doe99
        my password is hunter2

    NOTE:
    Credentials have no consistent linguistic structure (unlike names,
    emails, or phone numbers), so generic NER cannot detect them. This
    recognizer matches on a credential-indicating keyword followed by
    either a colon/equals sign OR the words "is"/"are", then a token.
    It will still miss credentials with no such indicator word at all
    (e.g. a bare password typed with no label) -- a known, documented
    limitation given credentials have no reliable structural pattern.
    """

    PATTERNS = [
        Pattern(
            name="credential_keyvalue_or_natural",
            regex=r"(?i)\b(password|pwd|pass|username|user\s*name|login|user\s*id|userid)\s*(?:[:=]|\bis\b|\bare\b)\s*[^\s,\.]+",
            score=0.85,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="CREDENTIAL",
            patterns=self.PATTERNS,
        )

def get_custom_recognizers():
    return [
        AccountNumberRecognizer(),
        AadhaarRecognizer(),
        ComplaintIDRecognizer(),
        CreditCardRecognizer(),
        CredentialRecognizer(),
    ]