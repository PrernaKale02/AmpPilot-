"""Nearby EV charging stations, backed by Open Charge Map.

The route orchestrates and validates; it does not know what OCM's JSON looks
like. Fetching lives in `app.services.open_charge_map`, normalisation in
`app.services.mappers`, and the distance maths in `app.core.geo`.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Query

from app.schemas.charging import NearbyStationsResponse, Origin
from app.services.mappers import map_pois_to_stations
from app.services.open_charge_map import fetch_nearby_pois

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["charging"])


@router.get(
    "/charging-stations",
    response_model=NearbyStationsResponse,
    summary="List EV charging stations near a coordinate",
)
async def get_nearby_charging_stations(
    latitude: Annotated[
        float,
        Query(ge=-90, le=90, description="Search origin latitude, WGS84 decimal degrees."),
    ],
    longitude: Annotated[
        float,
        Query(ge=-180, le=180, description="Search origin longitude, WGS84 decimal degrees."),
    ],
    radius_km: Annotated[
        float,
        Query(gt=0, le=50, description="Search radius in kilometres."),
    ] = 10.0,
) -> NearbyStationsResponse:
    """Returns stations within `radius_km` of the given point, nearest first.

    An empty result is a 200 with an empty `stations` array, not a 404: the
    query succeeded, and the app already renders a designed empty state for it.

    Upstream failures surface as 502/504/503 via the handlers in `app.main`.
    """
    logger.info(
        "Starting nearest charging station search: latitude=%s longitude=%s radius_km=%s",
        latitude,
        longitude,
        radius_km,
    )
    pois = await fetch_nearby_pois(latitude, longitude, radius_km)
    stations = map_pois_to_stations(pois, latitude, longitude)

    # OCM applies its own radius server-side, but it is the provider's filter
    # against its own distance calculation. Re-filtering on our own haversine
    # figure keeps the response consistent with the distances we publish.
    within_radius = [station for station in stations if station.distance_km <= radius_km]
    within_radius.sort(key=lambda station: station.distance_km)

    return NearbyStationsResponse(
        stations=within_radius,
        origin=Origin(latitude=latitude, longitude=longitude),
        radius_km=radius_km,
    )
