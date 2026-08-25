"""Open Charge Map API v3 client.

Owns exactly one thing: getting a list of raw POI dictionaries out of
https://api.openchargemap.io/v3/poi/ and turning any failure into a domain
exception. It does no parsing and knows nothing about `ChargingStation` - that
is `app.services.mappers`.

One request per call, never a retry loop: OCM is a free community service and
this endpoint is called on every screen load.
"""

import logging
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import UpstreamError, UpstreamTimeout

logger = logging.getLogger(__name__)

OCM_POI_URL = "https://api.openchargemap.io/v3/poi/"

# OCM asks API consumers to identify themselves.
USER_AGENT = "AmpPilot/0.1 (EV charging companion app)"


async def fetch_nearby_pois(
    latitude: float,
    longitude: float,
    radius_km: float,
    *,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    """Fetches raw OCM POI records near a coordinate.

    :param latitude: Search origin latitude, WGS84 decimal degrees.
    :param longitude: Search origin longitude, WGS84 decimal degrees.
    :param radius_km: Search radius in kilometres, passed to OCM as `distance`.
    :param settings: Injectable settings; defaults to the process settings.
    :param client: Injectable HTTP client, so tests can supply a
        `httpx.MockTransport` instead of reaching the network.
    :returns: The decoded JSON array, unmodified. Empty list if OCM found none.
    :raises UpstreamNotConfigured: no API key configured.
    :raises UpstreamTimeout: OCM did not answer in time.
    :raises UpstreamError: transport failure, error status, or unusable body.
    """
    settings = settings or get_settings()
    api_key = settings.require_open_charge_map_api_key()

    params = {
        "output": "json",
        "latitude": latitude,
        "longitude": longitude,
        "distance": radius_km,
        "distanceunit": "KM",
        "maxresults": settings.open_charge_map_max_results,
        "compact": "true",
        "verbose": "false",
    }

    # The key goes in the header, not the `key=` query parameter OCM also
    # accepts. httpx puts the full request URL into its exception messages and
    # into `response.url`, so a query-string key would leak into any log line
    # or traceback that touched the request. A header cannot.
    headers = {
        "X-API-Key": api_key,
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    timeout = settings.open_charge_map_timeout_seconds

    try:
        if client is None:
            async with httpx.AsyncClient(timeout=timeout) as owned_client:
                response = await owned_client.get(OCM_POI_URL, params=params, headers=headers)
        else:
            response = await client.get(
                OCM_POI_URL, params=params, headers=headers, timeout=timeout
            )
    except httpx.TimeoutException as exc:
        logger.warning("Open Charge Map request timed out after %ss", timeout)
        raise UpstreamTimeout("Open Charge Map did not respond in time.") from exc
    except httpx.HTTPError as exc:
        # Log the exception *type* only. The message can embed the request URL.
        logger.error("Open Charge Map request failed: %s", type(exc).__name__)
        raise UpstreamError("Could not reach Open Charge Map.") from exc

    if response.status_code != httpx.codes.OK:
        # Never log response.url - it would carry the query string.
        logger.error("Open Charge Map returned HTTP %s", response.status_code)
        raise UpstreamError(f"Open Charge Map returned HTTP {response.status_code}.")

    try:
        payload = response.json()
    except ValueError as exc:
        logger.error("Open Charge Map returned a non-JSON body")
        raise UpstreamError("Open Charge Map returned an unreadable response.") from exc

    if not isinstance(payload, list):
        logger.error("Open Charge Map returned %s, expected a list", type(payload).__name__)
        raise UpstreamError("Open Charge Map returned an unexpected response shape.")

    # Tolerate stray non-object entries rather than failing the whole request.
    return [poi for poi in payload if isinstance(poi, dict)]
