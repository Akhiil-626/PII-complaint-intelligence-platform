"""Tests for the classification module scaffolding."""

from src.classification.predict import predict


def test_predict_placeholder() -> None:
    """The prediction call is not implemented yet."""
    try:
        predict(["sample text"])
    except NotImplementedError:
        pass
