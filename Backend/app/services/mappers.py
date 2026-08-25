"""Open Charge Map POI -> AmpPilot `ChargingStation`.

Pure functions: dict in, model out. No I/O, no network, no config. That is what
makes the mapping testable against captured fixtures without mocking HTTP.

The governing rule is that **nothing is invented**. OCM is crowd-sourced, so a
typical record has a title, coordinates and a connector list, and is silent on
almost everything else. Silence maps to `None`, never to a placeholder:

* no operator on record          -> ``network = None`` (not "Unknown operator")
* no connector count             -> ``total_connectors = None`` (not 0)
* no live availability           -> ``available_connectors = None`` (not 0)
* no power rating                -> ``max_power_kw = None`` (not 0)
* no tariff                      -> ``price_per_kwh = None`` and ``currency = None``

Two things were established by inspecting live OCM responses rather than
assumed, and they shape this module:

**Reference objects are never inlined.** ``/poi/`` returns ``"OperatorInfo":
null``, ``"StatusType": null`` and ``"ConnectionType": null`` and gives only the
numeric ``OperatorID`` / ``StatusTypeID`` / ``ConnectionTypeID``. This is true
with ``verbose=true`` as well - that flag only adds the null keys back, at
double the payload size. So every lookup below resolves an ID against a static
table taken from OCM's own ``/v3/referencedata/``, while still preferring an
expanded object on the chance a future response carries one.

**Status is mostly not availability.** OCM's ``Operational`` means the site
exists and works, not that a plug is free. It therefore maps to ``None``, not
``"available"`` - claiming a connector is free because a station is in service
would be exactly the inference this module refuses to make.
"""

from datetime import datetime, timezone
from typing import Any

from app.core.geo import haversine_km
from app.schemas.charging import ChargerType, ChargingStation, StationStatus

# --- OCM reference tables ----------------------------------------------------
# Taken verbatim from https://api.openchargemap.io/v3/referencedata/.
# Static enums, not data: resolving an ID to its published label is a lookup,
# not an invention.

#: StatusTypeID -> our availability state. IDs absent from this map yield None.
#: Note 30 "Temporarily Unavailable" carries IsOperational=True in OCM's own
#: reference data, so it has to be listed explicitly - an IsOperational check
#: alone would report a knowingly-down site as fine.
_STATUS_BY_ID: dict[int, StationStatus | None] = {
    0: None,  # Unknown
    10: "available",  # Currently Available (Automated Status)
    20: "busy",  # Currently In Use (Automated Status)
    30: "offline",  # Temporarily Unavailable
    50: None,  # Operational - the site works; says nothing about a free plug
    75: None,  # Partly Operational (Mixed)
    100: "offline",  # Not Operational
}

#: Sites that are not somewhere a driver can charge today. Dropped entirely
#: rather than surfaced as offline: a station planned for next year is not a
#: broken station, and a decommissioned one is not a station at all.
_EXCLUDED_STATUS_IDS = frozenset({150, 200, 210})

#: CurrentTypeID -> current family.
_CURRENT_TYPE_AC = frozenset({10, 20})  # AC (Single-Phase), AC (Three-Phase)
_CURRENT_TYPE_DC = frozenset({30})  # DC

#: ConnectionTypeID -> short display label.
_CONNECTION_TYPE_BY_ID: dict[int, str] = {
    1: "Type1",
    2: "CHAdeMO",
    3: "BS1363",
    4: "Commando",
    5: "LP Inductive",
    6: "SP Inductive",
    7: "Avcon",
    8: "Tesla Roadster",
    9: "NEMA 5-20R",
    10: "NEMA 14-30",
    11: "NEMA 14-50",
    13: "Europlug",
    14: "NEMA 6-20",
    15: "NEMA 6-15",
    16: "CEE 3-Pin",
    17: "CEE 5-Pin",
    18: "CEE+ 7-Pin",
    21: "XLR 4-Pin",
    22: "NEMA 5-15R",
    23: "CEE 7/5",
    24: "Wireless",
    25: "Type2",
    26: "Type3C",
    27: "NACS",
    28: "Schuko",
    29: "TypeI",
    30: "Tesla",
    31: "Tesla Battery Swap",
    32: "CCS1",
    33: "CCS2",
    34: "IEC 60309 3-Pin",
    35: "IEC 60309 5-Pin",
    36: "Type3A",
    1036: "Type2",
    1037: "TypeJ",
    1038: "GB/T AC",
    1039: "GB/T AC",
    1040: "GB/T DC",
    1041: "3-Phase 5-Pin",
    1042: "NEMA TT-30R",
    1043: "TypeM",
    1044: "ChaoJi",
}

#: Same labels keyed by OCM's title, for the rare record that carries an
#: expanded ConnectionType but no usable ID. Exact-match only; an unrecognised
#: title passes through verbatim rather than being guessed at.
_CONNECTION_TYPE_BY_TITLE: dict[str, str] = {
    "Type 1 (J1772)": "Type1",
    "Type 2 (Socket Only)": "Type2",
    "Type 2 (Tethered Connector)": "Type2",
    "CCS (Type 1)": "CCS1",
    "CCS (Type 2)": "CCS2",
    "CHAdeMO": "CHAdeMO",
    "NACS / Tesla Supercharger": "NACS",
    "Tesla (Model S/X)": "Tesla",
    "GB-T DC - GB/T 20234.3": "GB/T DC",
}

#: Connectors that are DC by definition. CCS, CHAdeMO, GB/T DC and ChaoJi carry
#: no AC variant, so this is a definitional lookup rather than a guess.
_DC_CONNECTION_TYPE_IDS = frozenset({2, 32, 33, 1040, 1044})

#: Connectors that are AC by definition: J1772, Mennekes, domestic and
#: industrial sockets. NACS (27) and Tesla (30) are deliberately absent - they
#: carry both AC and DC in different deployments, so they support no conclusion.
_AC_CONNECTION_TYPE_IDS = frozenset(
    {1, 3, 4, 9, 10, 11, 13, 14, 15, 16, 17, 18, 22, 23, 25, 26, 28, 29, 34, 35, 36,
     1036, 1037, 1038, 1039, 1041, 1042, 1043}
)

#: OCM operator entries that name no actual operator.
_PLACEHOLDER_OPERATOR_IDS = frozenset({1, 45})  # (Unknown Operator), (Business Owner at Location)
_PLACEHOLDER_OPERATOR_TITLES = frozenset(
    {"(unknown operator)", "(business owner at location)", "unknown", "unknown operator"}
)

#: Connector titles that carry no information.
_UNKNOWN_CONNECTOR_TITLES = frozenset({"unknown", "other", ""})

#: Opening-hours text that unambiguously means "always open". Anything else is
#: left as None rather than guessed at.
_ALWAYS_OPEN_PHRASES = frozenset(
    {
        "24 hours",
        "24 hours a day",
        "24/7",
        "24x7",
        "24 hrs",
        "24hrs",
        "open 24 hours",
        "24 hours daily",
        "always open",
    }
)


def _clean_str(value: Any) -> str | None:
    """Returns a stripped non-empty string, or None for anything else."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _int_or_none(value: Any) -> int | None:
    """Returns an int, or None. Rejects bools, which are ints in Python."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _positive_number(value: Any) -> float | None:
    """Returns a positive float, or None. Rejects bools, zero and negatives."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if value > 0 else None


def _non_negative_int(value: Any) -> int | None:
    """Returns a non-negative int, or None. Rejects bools and negatives."""
    parsed = _int_or_none(value)
    return parsed if parsed is not None and parsed >= 0 else None


def _connections(poi: dict[str, Any]) -> list[dict[str, Any]]:
    """The POI's connection entries, defensively filtered to dicts."""
    raw = poi.get("Connections")
    if not isinstance(raw, list):
        return []
    return [connection for connection in raw if isinstance(connection, dict)]


def _expanded(container: dict[str, Any], key: str) -> dict[str, Any] | None:
    """Returns `container[key]` when it is an expanded object, else None."""
    value = container.get(key)
    return value if isinstance(value, dict) else None


def map_network(poi: dict[str, Any]) -> str | None:
    """Operator name, or None when OCM names no actual operator.

    OCM's ``/poi/`` endpoint returns only ``OperatorID``; resolving an
    arbitrary ID to a brand name needs the 982-entry operator reference list,
    which this phase does not fetch. So a name is produced only when an
    expanded ``OperatorInfo`` happens to be present. Everything else is None
    rather than a fabricated label.
    """
    operator = _expanded(poi, "OperatorInfo")
    if operator is not None:
        title = _clean_str(operator.get("Title"))
        if title is not None and title.lower() not in _PLACEHOLDER_OPERATOR_TITLES:
            return title
        return None

    # Only an ID is available. Known placeholders are definitively "no
    # operator"; any other ID is simply unresolvable here.
    return None


def map_address(poi: dict[str, Any]) -> str | None:
    """A single-line address assembled from whichever parts OCM has.

    `AddressInfo.Title` is deliberately excluded - it is the station name, and
    repeating it in the address just makes the detail screen read twice.
    """
    info = _expanded(poi, "AddressInfo")
    if info is None:
        return None

    parts = [
        _clean_str(info.get(key))
        for key in ("AddressLine1", "AddressLine2", "Town", "StateOrProvince", "Postcode")
    ]
    present = [part for part in parts if part]
    if not present:
        return None

    # OCM authors often paste the whole address into AddressLine1, so drop any
    # part already contained in an earlier one rather than repeating it.
    deduped: list[str] = []
    for part in present:
        if not any(part.lower() in kept.lower() for kept in deduped):
            deduped.append(part)
    return ", ".join(deduped)


def _connector_label(connection: dict[str, Any]) -> str | None:
    """Display label for one connection, from its object or its type ID."""
    connection_type = _expanded(connection, "ConnectionType")
    if connection_type is not None:
        title = _clean_str(connection_type.get("Title"))
        if title is not None and title.lower() not in _UNKNOWN_CONNECTOR_TITLES:
            type_id = _int_or_none(connection_type.get("ID"))
            if type_id:
                return _CONNECTION_TYPE_BY_ID.get(type_id, title)
            return _CONNECTION_TYPE_BY_TITLE.get(title, title)

    type_id = _int_or_none(connection.get("ConnectionTypeID"))
    if type_id is None:
        return None
    return _CONNECTION_TYPE_BY_ID.get(type_id)


def map_connector_types(poi: dict[str, Any]) -> list[str]:
    """Distinct connector labels, in the order OCM lists them.

    An empty list means OCM lists no identifiable connector types. That is a
    real answer, not a missing one, so this never returns None - which also
    keeps the frontend's unguarded `.join()` safe.
    """
    labels: list[str] = []
    for connection in _connections(poi):
        label = _connector_label(connection)
        if label is not None and label not in labels:
            labels.append(label)
    return labels


def map_total_connectors(poi: dict[str, Any]) -> int | None:
    """Number of charge points, or None when OCM does not actually say.

    Prefers OCM's own `NumberOfPoints`. Falls back to summing per-connection
    `Quantity`, but only when *every* connection declares one - a partial sum
    would silently under-report, which is worse than admitting we do not know.
    """
    number_of_points = _non_negative_int(poi.get("NumberOfPoints"))
    if number_of_points:
        return number_of_points

    connections = _connections(poi)
    if not connections:
        return None

    quantities = [_non_negative_int(connection.get("Quantity")) for connection in connections]
    if any(quantity is None for quantity in quantities):
        return None

    total = sum(quantity for quantity in quantities if quantity is not None)
    return total or None


def map_max_power_kw(poi: dict[str, Any]) -> float | None:
    """Highest connector power rating in kW, or None if none is stated."""
    ratings = [_positive_number(connection.get("PowerKW")) for connection in _connections(poi)]
    present = [rating for rating in ratings if rating is not None]
    return max(present) if present else None


def map_charger_type(poi: dict[str, Any]) -> ChargerType | None:
    """AC / DC / BOTH, or None when the data supports no conclusion.

    Prefers the explicit ``CurrentTypeID``. Where that is absent, falls back to
    connector type, but only for connectors that are one or the other by
    definition - CCS and CHAdeMO are always DC, J1772 and Mennekes always AC.
    NACS and Tesla connectors are excluded from that fallback because they
    appear in both AC and DC installations.

    Power rating is deliberately never used as a proxy: 43 kW AC exists, so a
    high kW figure does not imply DC.
    """
    has_ac = False
    has_dc = False

    for connection in _connections(poi):
        current_type = _expanded(connection, "CurrentType")
        current_type_id = _int_or_none(
            current_type.get("ID") if current_type else connection.get("CurrentTypeID")
        )

        if current_type_id in _CURRENT_TYPE_AC:
            has_ac = True
            continue
        if current_type_id in _CURRENT_TYPE_DC:
            has_dc = True
            continue

        connection_type = _expanded(connection, "ConnectionType")
        type_id = _int_or_none(
            connection_type.get("ID") if connection_type else connection.get("ConnectionTypeID")
        )
        if type_id in _DC_CONNECTION_TYPE_IDS:
            has_dc = True
        elif type_id in _AC_CONNECTION_TYPE_IDS:
            has_ac = True

    if has_ac and has_dc:
        return "BOTH"
    if has_ac:
        return "AC"
    if has_dc:
        return "DC"
    return None


def map_status(poi: dict[str, Any]) -> StationStatus | None:
    """Availability, but only where OCM genuinely reports it.

    * automated "Currently Available"  -> ``"available"``
    * automated "Currently In Use"     -> ``"busy"``
    * "Temporarily Unavailable" / "Not Operational" -> ``"offline"``
    * plain "Operational", "Unknown", "Partly Operational", or absent -> ``None``

    "Operational" says the site works, not that a connector is free, so it
    cannot become ``"available"`` without inventing availability.
    """
    status_type = _expanded(poi, "StatusType")
    status_id = _int_or_none(
        status_type.get("ID") if status_type else poi.get("StatusTypeID")
    )

    if status_id is not None and status_id in _STATUS_BY_ID:
        return _STATUS_BY_ID[status_id]

    # Unrecognised ID: fall back to the operational flag if an object gave us
    # one, otherwise admit we do not know.
    if status_type is not None and status_type.get("IsOperational") is False:
        return "offline"
    return None


def map_hours(poi: dict[str, Any]) -> tuple[bool | None, str | None]:
    """Returns ``(is_open_24_hours, hours)`` from OCM's free-text opening times.

    The text is passed through verbatim. ``is_open_24_hours`` is True only when
    the text unambiguously says so; otherwise it stays None, because text we
    cannot parse is not evidence that a site closes.
    """
    hours = _clean_str(poi.get("OpeningTimes"))
    if hours is None:
        return None, None

    normalised = hours.lower().strip().strip(".")
    is_24h = True if normalised in _ALWAYS_OPEN_PHRASES else None
    return is_24h, hours


def map_last_updated_at(poi: dict[str, Any]) -> datetime | None:
    """Parses `DateLastStatusUpdate` into a timezone-aware datetime.

    OCM publishes these in UTC; a value that arrives without an offset is
    tagged UTC rather than dropped. Anything unparseable becomes None - a
    freshness claim shown to the user must never be fabricated.
    """
    raw = _clean_str(poi.get("DateLastStatusUpdate"))
    if raw is None:
        return None

    # `fromisoformat` only learned to accept a trailing "Z" in Python 3.11.
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None

    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def map_poi_to_station(
    poi: dict[str, Any],
    origin_latitude: float,
    origin_longitude: float,
) -> ChargingStation | None:
    """Maps one OCM POI to a `ChargingStation`, or None if it is unusable.

    Returns None when the record lacks an id, a name or coordinates - without
    those there is nothing to show - or when its status marks it as planned or
    removed rather than a station a driver could visit today.

    :param poi: One decoded OCM POI object.
    :param origin_latitude: Search origin latitude, for the distance figure.
    :param origin_longitude: Search origin longitude, for the distance figure.
    """
    poi_id = _int_or_none(poi.get("ID"))
    if poi_id is None:
        return None

    status_type = _expanded(poi, "StatusType")
    status_id = _int_or_none(
        status_type.get("ID") if status_type else poi.get("StatusTypeID")
    )
    if status_id in _EXCLUDED_STATUS_IDS:
        return None

    info = _expanded(poi, "AddressInfo")
    if info is None:
        return None

    name = _clean_str(info.get("Title"))
    if name is None:
        return None

    latitude = info.get("Latitude")
    longitude = info.get("Longitude")
    if not isinstance(latitude, (int, float)) or isinstance(latitude, bool):
        return None
    if not isinstance(longitude, (int, float)) or isinstance(longitude, bool):
        return None
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        return None

    # Distance is always computed here from the caller's origin. OCM ships an
    # `AddressInfo.Distance`, but it reflects whatever origin and unit OCM was
    # queried with, so it is not trusted.
    distance_km = haversine_km(origin_latitude, origin_longitude, latitude, longitude)

    is_open_24_hours, hours = map_hours(poi)

    return ChargingStation(
        id=f"ocm-{poi_id}",
        name=name,
        latitude=float(latitude),
        longitude=float(longitude),
        # Rounded because the app renders this value unformatted.
        distance_km=round(distance_km, 1),
        network=map_network(poi),
        address=map_address(poi),
        status=map_status(poi),
        # OCM carries no live per-connector availability, so this is always
        # None. A 0 would read in the UI as "none free", which is a claim the
        # data does not support.
        available_connectors=None,
        total_connectors=map_total_connectors(poi),
        max_power_kw=map_max_power_kw(poi),
        connector_types=map_connector_types(poi),
        charger_type=map_charger_type(poi),
        # OCM's `UsageCost` is free text ("Free", "Rs 18/kWh", "0.30 GBP/kWh"),
        # not a machine-readable tariff. Parsing it into a float would invent
        # precision that is not there, so pricing stays unset - and currency
        # with it, since a currency without a price asserts nothing.
        price_per_kwh=None,
        currency=None,
        is_open_24_hours=is_open_24_hours,
        hours=hours,
        last_updated_at=map_last_updated_at(poi),
    )


def map_pois_to_stations(
    pois: list[dict[str, Any]],
    origin_latitude: float,
    origin_longitude: float,
) -> list[ChargingStation]:
    """Maps a batch of OCM POIs, silently dropping unusable records.

    One malformed entry must not fail the whole request - OCM is crowd-sourced
    and partial records are normal.
    """
    stations = []
    for poi in pois:
        station = map_poi_to_station(poi, origin_latitude, origin_longitude)
        if station is not None:
            stations.append(station)
    return stations
