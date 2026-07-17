"""Contract tests for platform probes."""

from fastapi.testclient import TestClient

from app.main import create_app
from app.presentation.api.routes.health import check_database


def test_liveness_contract() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_identifies_service() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "ParkShield AI API"


def test_readiness_contract_with_available_database() -> None:
    application = create_app()
    application.dependency_overrides[check_database] = lambda: None
    with TestClient(application) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
