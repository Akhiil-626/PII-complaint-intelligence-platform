"""Unit and integration tests for FastAPI backend endpoints."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    from api.main import state, _load_models_worker
    if "processor" not in state:
        _load_models_worker()
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


def test_submit_to_queue_flow(client: TestClient) -> None:
    # 1. Submit a distinctive complaint
    payload = {
        "text": "Distinctive automated test complaint: Unrecognized fee on account 987654321 for user test@example.com."
    }
    submit_res = client.post("/api/complaints", json=payload)
    assert submit_res.status_code == 200
    cid = submit_res.json()["complaint_id"]

    # 2. Check that it appears in the review queue
    queue_res = client.get("/api/review-queue")
    assert queue_res.status_code == 200
    queue_items = queue_res.json()
    queue_ids = [item["complaint_id"] for item in queue_items]
    assert cid in queue_ids
    # Check that newest submission is near the top
    assert queue_items[0]["complaint_id"] == cid

    # 3. Resolve the complaint
    resolve_res = client.post(f"/api/review-queue/{cid}/resolve")
    assert resolve_res.status_code == 200

    # 4. Confirm it is removed from the review queue
    updated_queue_res = client.get("/api/review-queue")
    assert updated_queue_res.status_code == 200
    updated_ids = [item["complaint_id"] for item in updated_queue_res.json()]
    assert cid not in updated_ids
