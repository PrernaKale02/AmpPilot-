"""Tests for the Open Charge Map client.

Every request is served by `httpx.MockTransport`, which ships with httpx - no
extra mocking dependency, and no test ever touches the live OCM API.
"""

import asyncio
import json

import httpx

from app.core.config import Settings
from app.core.exceptions import UpstreamError, UpstreamNotConfigured, UpstreamTimeout
from app.services.open_charge_map import OCM_POI_URL, fetch_nearby_pois

LAT = 19.0760
LON = 72.8777


def settings_with_key(key: str | None = "test-key-not-real") -> Settings:
    """Settings with an explicit key, so tests never read the real `.env`."""
    return Settings(
        open_charge_map_api_key=key,
        open_charge_map_timeout_seconds=1.0,
        open_charge_map_max_results=50,
    )


def client_returning(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def expect_raises(exc_type, coro_factory) -> Exception:
    """Runs an awaitable and asserts it raises `exc_type`. Returns the error."""
    try:
        asyncio.run(coro_factory())
    except exc_type as exc:
        return exc
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(f"expected {exc_type.__name__}, got {type(exc).__name__}: {exc}")
    raise AssertionError(f"expected {exc_type.__name__}, nothing was raised")


# --- Success -----------------------------------------------------------------


def test_returns_the_decoded_poi_list() -> None:
    payload = [{"ID": 1}, {"ID": 2}]

    async def run() -> list:
        async with client_returning(lambda _: httpx.Response(200, json=payload)) as client:
            return await fetch_nearby_pois(
                LAT, LON, 15, settings=settings_with_key(), client=client
            )

    assert asyncio.run(run()) == payload


def test_empty_result_is_an_empty_list_not_an_error() -> None:
    async def run() -> list:
        async with client_returning(lambda _: httpx.Response(200, json=[])) as client:
            return await fetch_nearby_pois(
                LAT, LON, 15, settings=settings_with_key(), client=client
            )

    assert asyncio.run(run()) == []


def test_non_object_entries_are_filtered_out() -> None:
    async def run() -> list:
        payload = [{"ID": 1}, "junk", None, 42]
        async with client_returning(lambda _: httpx.Response(200, json=payload)) as client:
            return await fetch_nearby_pois(
                LAT, LON, 15, settings=settings_with_key(), client=client
            )

    assert asyncio.run(run()) == [{"ID": 1}]


# --- Request construction ----------------------------------------------------


def test_api_key_is_sent_as_a_header_and_never_in_the_query_string() -> None:
    """Security regression test: a key in the URL leaks into logs and tracebacks."""
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, json=[])

    async def run() -> None:
        async with client_returning(handler) as client:
            await fetch_nearby_pois(
                LAT, LON, 15, settings=settings_with_key("super-secret"), client=client
            )

    asyncio.run(run())
    request = captured["request"]

    assert request.headers["X-API-Key"] == "super-secret"
    assert "super-secret" not in str(request.url)
    assert "key" not in dict(request.url.params)


def test_request_uses_the_documented_ocm_parameters() -> None:
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, json=[])

    async def run() -> None:
        async with client_returning(handler) as client:
            await fetch_nearby_pois(
                LAT, LON, 15, settings=settings_with_key(), client=client
            )

    asyncio.run(run())
    request = captured["request"]
    params = dict(request.url.params)

    assert str(request.url).startswith(OCM_POI_URL)
    assert params["output"] == "json"
    assert float(params["latitude"]) == LAT
    assert float(params["longitude"]) == LON
    assert float(params["distance"]) == 15
    assert params["distanceunit"] == "KM"
    assert params["maxresults"] == "50"
    assert params["compact"] == "true"
    assert params["verbose"] == "false"
    assert "AmpPilot" in request.headers["User-Agent"]


def test_only_one_request_is_made() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=[])

    async def run() -> None:
        async with client_returning(handler) as client:
            await fetch_nearby_pois(LAT, LON, 15, settings=settings_with_key(), client=client)

    asyncio.run(run())
    assert calls["n"] == 1


# --- Missing configuration ---------------------------------------------------


def test_missing_api_key_raises_not_configured() -> None:
    async def run() -> None:
        await fetch_nearby_pois(LAT, LON, 15, settings=settings_with_key(""))

    expect_raises(UpstreamNotConfigured, run)


def test_whitespace_api_key_raises_not_configured() -> None:
    async def run() -> None:
        await fetch_nearby_pois(LAT, LON, 15, settings=settings_with_key("   "))

    expect_raises(UpstreamNotConfigured, run)


def test_missing_key_error_does_not_reach_the_network() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=[])

    async def run() -> None:
        async with client_returning(handler) as client:
            await fetch_nearby_pois(
                LAT, LON, 15, settings=settings_with_key(""), client=client
            )

    expect_raises(UpstreamNotConfigured, run)
    assert calls["n"] == 0


# --- Upstream failures -------------------------------------------------------


def test_timeout_raises_upstream_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    async def run() -> None:
        async with client_returning(handler) as client:
            await fetch_nearby_pois(LAT, LON, 15, settings=settings_with_key(), client=client)

    expect_raises(UpstreamTimeout, run)


def test_transport_error_raises_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route to host", request=request)

    async def run() -> None:
        async with client_returning(handler) as client:
            await fetch_nearby_pois(LAT, LON, 15, settings=settings_with_key(), client=client)

    expect_raises(UpstreamError, run)


def test_server_error_status_raises_upstream_error() -> None:
    async def run() -> None:
        async with client_returning(lambda _: httpx.Response(500, text="boom")) as client:
            await fetch_nearby_pois(LAT, LON, 15, settings=settings_with_key(), client=client)

    expect_raises(UpstreamError, run)


def test_forbidden_status_raises_upstream_error() -> None:
    async def run() -> None:
        async with client_returning(lambda _: httpx.Response(403, text="bad key")) as client:
            await fetch_nearby_pois(LAT, LON, 15, settings=settings_with_key(), client=client)

    expect_raises(UpstreamError, run)


def test_upstream_error_message_never_contains_the_api_key() -> None:
    async def run() -> None:
        async with client_returning(lambda _: httpx.Response(500, text="boom")) as client:
            await fetch_nearby_pois(
                LAT, LON, 15, settings=settings_with_key("super-secret"), client=client
            )

    error = expect_raises(UpstreamError, run)
    assert "super-secret" not in str(error)


# --- Malformed bodies --------------------------------------------------------


def test_non_json_body_raises_upstream_error() -> None:
    async def run() -> None:
        async with client_returning(lambda _: httpx.Response(200, text="<html>nope")) as client:
            await fetch_nearby_pois(LAT, LON, 15, settings=settings_with_key(), client=client)

    expect_raises(UpstreamError, run)


def test_json_object_instead_of_array_raises_upstream_error() -> None:
    async def run() -> None:
        body = json.dumps({"error": "quota exceeded"})
        response = httpx.Response(200, text=body, headers={"content-type": "application/json"})
        async with client_returning(lambda _: response) as client:
            await fetch_nearby_pois(LAT, LON, 15, settings=settings_with_key(), client=client)

    expect_raises(UpstreamError, run)
