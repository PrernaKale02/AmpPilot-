"""End-to-end tests for GET /api/charging-stations.

The OCM client is replaced at the route's import site, so these exercise the
real router, schema serialisation and exception handlers without any network.
"""

from contextlib import contextmanager
from typing import Any

from fastapi.testclient import TestClient

from app.api.routes import charging
from app.core.exceptions import UpstreamError, UpstreamNotConfigured, UpstreamTimeout
from app.main import app

ENDPOINT = "/api/charging-stations"
QUERY = {"latitude": 19.0760, "longitude": 72.8777, "radius_km": 15}

client = TestClient(app)


@contextmanager
def ocm_returning(pois: list[dict[str, Any]]):
    """Swaps the route's fetch function for one returning `pois`."""
    original = charging.fetch_nearby_pois

    async def fake(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return pois

    charging.fetch_nearby_pois = fake
    try:
        yield
    finally:
        charging.fetch_nearby_pois = original


@contextmanager
def ocm_raising(exc: Exception):
    """Swaps the route's fetch function for one that raises `exc`."""
    original = charging.fetch_nearby_pois

    async def fake(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        raise exc

    charging.fetch_nearby_pois = fake
    try:
        yield
    finally:
        charging.fetch_nearby_pois = original


def poi(poi_id: int, latitude: float, longitude: float, title: str) -> dict[str, Any]:
    return {
        "ID": poi_id,
        "AddressInfo": {"Title": title, "Latitude": latitude, "Longitude": longitude},
    }


# --- Success paths -----------------------------------------------------------


def test_empty_upstream_result_is_a_200_with_an_empty_envelope() -> None:
    with ocm_returning([]):
        response = client.get(ENDPOINT, params=QUERY)

    assert response.status_code == 200
    assert response.json() == {
        "stations": [],
        "origin": {"latitude": 19.0760, "longitude": 72.8777},
        "radiusKm": 15.0,
    }


def test_search_start_is_logged(caplog) -> None:
    with ocm_returning([]), caplog.at_level("INFO"):
        client.get(ENDPOINT, params=QUERY)

    assert "Starting nearest charging station search" in caplog.text
    assert "latitude=19.076" in caplog.text
    assert "longitude=72.8777" in caplog.text
    assert "radius_km=15" in caplog.text


def test_stations_are_sorted_nearest_first() -> None:
    pois = [
        poi(3, 19.2183, 72.9781, "Thane"),  # ~19 km, outside a 15 km radius
        poi(2, 19.1197, 72.9051, "Powai"),  # ~5.6 km
        poi(1, 19.0866, 72.8891, "Kurla"),  # ~1.7 km
    ]
    with ocm_returning(pois):
        response = client.get(ENDPOINT, params=QUERY)

    body = response.json()
    assert response.status_code == 200
    assert [station["name"] for station in body["stations"]] == ["Kurla", "Powai"]
    assert [station["distanceKm"] for station in body["stations"]] == [1.7, 5.6]


def test_stations_outside_the_radius_are_excluded() -> None:
    with ocm_returning([poi(3, 19.2183, 72.9781, "Thane")]):
        response = client.get(ENDPOINT, params={**QUERY, "radius_km": 15})
        assert response.json()["stations"] == []

    with ocm_returning([poi(3, 19.2183, 72.9781, "Thane")]):
        response = client.get(ENDPOINT, params={**QUERY, "radius_km": 25})
        assert len(response.json()["stations"]) == 1


def test_response_is_camelcase_and_never_reports_unknown_status() -> None:
    with ocm_returning([poi(1, 19.0866, 72.8891, "Kurla")]):
        body = client.get(ENDPOINT, params=QUERY).json()

    station = body["stations"][0]
    for key in ("distanceKm", "maxPowerKw", "connectorTypes", "isOpen24Hours", "lastUpdatedAt"):
        assert key in station
    assert station["status"] is None
    assert station["status"] != "unknown"


def test_origin_and_radius_are_echoed() -> None:
    with ocm_returning([]):
        body = client.get(
            ENDPOINT, params={"latitude": 1.5, "longitude": -2.5, "radius_km": 7}
        ).json()

    assert body["origin"] == {"latitude": 1.5, "longitude": -2.5}
    assert body["radiusKm"] == 7.0


# --- Upstream failures -------------------------------------------------------


def test_upstream_failure_returns_502() -> None:
    with ocm_raising(UpstreamError("provider exploded")):
        response = client.get(ENDPOINT, params=QUERY)

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "UPSTREAM_ERROR"


def test_upstream_timeout_returns_504() -> None:
    with ocm_raising(UpstreamTimeout("too slow")):
        response = client.get(ENDPOINT, params=QUERY)

    assert response.status_code == 504
    assert response.json()["detail"]["code"] == "UPSTREAM_TIMEOUT"


def test_missing_api_key_returns_503() -> None:
    with ocm_raising(UpstreamNotConfigured("OPEN_CHARGE_MAP_API_KEY is not set.")):
        response = client.get(ENDPOINT, params=QUERY)

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "PROVIDER_NOT_CONFIGURED"


def test_error_bodies_leak_no_internal_detail() -> None:
    with ocm_raising(UpstreamError("secret-key-abc123 rejected by https://provider/x?key=abc")):
        body = client.get(ENDPOINT, params=QUERY).text

    assert "secret-key-abc123" not in body
    assert "provider/x" not in body


# --- Validation is unchanged from Phase 1 ------------------------------------


def test_invalid_parameters_still_return_422() -> None:
    for params in (
        {"latitude": 100, "longitude": 72.8777},
        {"latitude": 19.076, "longitude": 200},
        {"latitude": 19.076, "longitude": 72.8777, "radius_km": 0},
        {"latitude": 19.076, "longitude": 72.8777, "radius_km": 51},
        {"longitude": 72.8777},
    ):
        response = client.get(ENDPOINT, params=params)
        assert response.status_code == 422, f"{params} gave {response.status_code}"


def test_health_needs_no_provider_key() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
