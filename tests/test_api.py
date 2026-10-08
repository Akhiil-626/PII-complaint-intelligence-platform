"""Unit and integration tests for FastAPI backend endpoints."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "privacy_mode" in data


def test_dashboard_data_endpoint(client: TestClient) -> None:
    response = client.get("/dashboard-data")
    assert response.status_code == 200
    data = response.json()
    assert "total_complaints" in data
    assert "total_categories" in data
    assert "total_pii_redacted" in data
    assert "k_anonymity" in data
    assert isinstance(data["category_distribution"], list)


def test_create_complaint_endpoint(client: TestClient) -> None:
    payload = {
        "text": "My name is John Doe and my credit card 4111 2222 3333 4444 was charged incorrectly. Email john@example.com."
    }
    response = client.post("/complaints", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "complaint_id" in data
    assert "redacted_text" in data
    assert "John Doe" not in data["redacted_text"]
    assert "4111 2222 3333 4444" not in data["redacted_text"]
    assert data["entities_count"] >= 2
    assert "sentiment" in data


def test_create_complaint_empty_validation(client: TestClient) -> None:
    payload = {"text": "   "}
    response = client.post("/complaints", json=payload)
    assert response.status_code == 400


def test_review_queue_and_resolve(client: TestClient) -> None:
    # 1. Fetch queue
    queue_res = client.get("/complaints/review-queue")
    assert queue_res.status_code == 200
    assert isinstance(queue_res.json(), list)

    # 2. Test resolve 404 for invalid ID
    resolve_res = client.post("/complaints/NON_EXISTENT_ID/resolve")
    assert resolve_res.status_code == 404
