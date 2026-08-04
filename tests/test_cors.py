"""CORS middleware configuration tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "origin",
    ["http://localhost:5173", "https://sidefit12-frontend.vercel.app"],
)
def test_preflight_allows_configured_frontend(client: TestClient, origin: str) -> None:
    response = client.options(
        "/api/v1/home",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


def test_preflight_rejects_unconfigured_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/home",
        headers={
            "Origin": "https://untrusted.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
