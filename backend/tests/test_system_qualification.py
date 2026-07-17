import asyncio
import time
from typing import Any

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import create_app
from app.presentation.api.routes.health import check_database


def test_every_api_operation_has_unique_id_and_protected_contracts_declare_bearer() -> None:
    schema: dict[str, Any] = create_app().openapi()
    operations = [
        operation
        for path in schema["paths"].values()
        for method, operation in path.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]
    operation_ids = [operation["operationId"] for operation in operations]
    assert len(operation_ids) == len(set(operation_ids))
    assert len(operations) >= 25
    assert schema["paths"]["/api/v1/admin/overview"]["get"]["security"]
    assert schema["paths"]["/api/v1/notifications/evaluate-location"]["post"]["security"]


def test_security_headers_and_request_id_are_present_without_cache_leakage() -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            "/api/v1/health/live", headers={"X-Request-ID": "qualification-request"}
        )
    assert response.headers["X-Request-ID"] == "qualification-request"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Content-Security-Policy"].startswith("default-src 'none'")


def test_readiness_fails_closed_when_database_dependency_is_unavailable() -> None:
    class BrokenSession:
        async def execute(self, statement: object) -> None:
            raise OperationalError("SELECT 1", {}, Exception("database offline"))

    async def scenario() -> None:
        with pytest.raises(HTTPException) as error:
            await check_database(BrokenSession())  # type: ignore[arg-type]
        assert error.value.status_code == 503
        assert error.value.detail == "database unavailable"

    asyncio.run(scenario())


def test_liveness_handles_concurrent_smoke_load_with_bounded_latency() -> None:
    async def scenario() -> None:
        application = create_app()
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            started = time.perf_counter()
            responses = await asyncio.gather(
                *(client.get("/api/v1/health/live") for _ in range(200))
            )
            elapsed = time.perf_counter() - started
        assert all(response.status_code == 200 for response in responses)
        assert elapsed < 5.0

    asyncio.run(scenario())


def test_openapi_and_profile_contract_do_not_expose_sensitive_fields() -> None:
    schema_text = str(create_app().openapi())
    user_properties = create_app().openapi()["components"]["schemas"]["UserResponse"][
        "properties"
    ]
    assert "password_hash" not in schema_text
    assert "mfa_secret" not in schema_text
    assert "mfa_secret" not in user_properties
