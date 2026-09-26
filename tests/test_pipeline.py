"""Tests for the orchestrated pipeline scaffolding."""

from src.pipeline.full_pipeline import run_full_pipeline


def test_pipeline_placeholder() -> None:
    """The pipeline entrypoint is not implemented yet."""
    try:
        run_full_pipeline(["sample complaint"])
    except NotImplementedError:
        pass
