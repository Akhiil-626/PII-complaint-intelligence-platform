"""Integration tests for the orchestrated end-to-end complaint pipeline."""

import pytest
from src.pipeline.full_pipeline import ComplaintPipeline, run_full_pipeline


@pytest.fixture(scope="module")
def pipeline() -> ComplaintPipeline:
    return ComplaintPipeline.get_instance()


def test_process_single_complaint(pipeline: ComplaintPipeline) -> None:
    raw_text = (
        "Hello, my name is John Doe. My credit card 4111 2222 3333 4444 was fraudulently charged $250. "
        "Please resolve this immediately or email me at john.doe@example.com."
    )
    res = pipeline.process_single(raw_text)

    # Validate output structure
    assert "complaint_id" in res
    assert res["complaint_id"].startswith("CMP-")
    assert "redacted_text" in res
    assert "entities_redacted" in res
    assert "model_comparison" in res
    assert "agreement" in res
    assert "final_classification" in res
    assert "sentiment" in res

    # Validate PII is not leaked in redacted text
    assert "John Doe" not in res["redacted_text"]
    assert "4111 2222 3333 4444" not in res["redacted_text"]
    assert "john.doe@example.com" not in res["redacted_text"]

    # Validate models executed
    assert "tfidf_svm" in res["model_comparison"]
    assert "sentence_bert_logreg" in res["model_comparison"]

    # Validate classification
    assert res["final_classification"]["domain"] in [
        "Credit/Prepaid card", "Bank account/service"
    ]


def test_run_full_pipeline_batch() -> None:
    texts = [
        "A collection agency is harassing my family over a debt I do not owe.",
        "Incorrect credit report information is lowering my credit score unfairly.",
    ]
    results = run_full_pipeline(texts)

    assert len(results) == 2
    for r in results:
        assert "complaint_id" in r
        assert "redacted_text" in r
        assert "final_classification" in r
