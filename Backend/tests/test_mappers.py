"""Tests for the Open Charge Map -> ChargingStation mapping.

Pure functions, so these need no HTTP mocking at all. The POI dictionaries here
follow the shape OCM v3 returns from /poi/.
"""

from datetime import timezone
from typing import Any

from app.services.mappers import (
    map_charger_type,
    map_connector_types,
    map_last_updated_at,
    map_max_power_kw,
    map_network,
    map_poi_to_station,
    map_pois_to_stations,
    map_status,
    map_total_connectors,
)

ORIGIN_LAT = 19.0760
ORIGIN_LON = 72.8777


def full_poi() -> dict[str, Any]:
    """A richly-populated POI: everything our model can carry is present."""
    return {
        "ID": 12345,
        "OperatorInfo": {"ID": 23, "Title": "Tata Power"},
        "UsageCost": "Rs 18/kWh",
        "NumberOfPoints": 6,
        "StatusType": {"ID": 50, "Title": "Operational", "IsOperational": True},
        "DateLastStatusUpdate": "2026-08-14T09:20:00Z",
        "OpeningTimes": "24 hours",
        "AddressInfo": {
            "Title": "Phoenix Marketcity",
            "AddressLine1": "LBS Marg",
            "AddressLine2": "Kurla West",
            "Town": "Mumbai",
            "StateOrProvince": "Maharashtra",
            "Postcode": "400070",
            "Latitude": 19.0866,
            "Longitude": 72.8891,
            "Distance": 999.0,  # deliberately wrong; must be ignored
        },
        "Connections": [
            {
                "ConnectionType": {"ID": 33, "Title": "CCS (Type 2)"},
                "CurrentTypeID": 30,
                "PowerKW": 120.0,
                "Quantity": 4,
            },
            {
                "ConnectionType": {"ID": 25, "Title": "Type 2 (Socket Only)"},
                "CurrentTypeID": 20,
                "PowerKW": 22.0,
                "Quantity": 2,
            },
        ],
    }


def sparse_poi() -> dict[str, Any]:
    """The realistic OCM case: a name, a location, and almost nothing else."""
    return {
        "ID": 999,
        "AddressInfo": {
            "Title": "Some Charger",
            "Latitude": 19.0866,
            "Longitude": 72.8891,
        },
    }


# --- 1. Full mapping ---------------------------------------------------------


def test_maps_a_fully_populated_poi() -> None:
    station = map_poi_to_station(full_poi(), ORIGIN_LAT, ORIGIN_LON)
    assert station is not None
    assert station.id == "ocm-12345"
    assert station.name == "Phoenix Marketcity"
    assert station.network == "Tata Power"
    assert station.address == "LBS Marg, Kurla West, Mumbai, Maharashtra, 400070"
    assert station.latitude == 19.0866
    assert station.longitude == 72.8891
    assert station.total_connectors == 6
    assert station.max_power_kw == 120.0
    assert station.connector_types == ["CCS2", "Type2"]
    assert station.charger_type == "BOTH"
    assert station.is_open_24_hours is True
    assert station.hours == "24 hours"
    assert station.last_updated_at is not None
    assert station.last_updated_at.tzinfo is not None


def test_camelcase_json_shape_is_preserved() -> None:
    station = map_poi_to_station(full_poi(), ORIGIN_LAT, ORIGIN_LON)
    assert station is not None
    payload = station.model_dump(by_alias=True)
    for key in ("distanceKm", "maxPowerKw", "connectorTypes", "isOpen24Hours", "lastUpdatedAt"):
        assert key in payload, f"missing camelCase key {key}"


# --- 2. Missing optional fields ----------------------------------------------


def test_sparse_poi_yields_nulls_not_placeholders() -> None:
    station = map_poi_to_station(sparse_poi(), ORIGIN_LAT, ORIGIN_LON)
    assert station is not None
    assert station.network is None
    assert station.address is None
    assert station.status is None
    assert station.available_connectors is None
    assert station.total_connectors is None
    assert station.max_power_kw is None
    assert station.charger_type is None
    assert station.price_per_kwh is None
    assert station.currency is None
    assert station.is_open_24_hours is None
    assert station.hours is None
    assert station.last_updated_at is None
    # Never null, so the frontend's unguarded .join() is safe.
    assert station.connector_types == []


def test_placeholder_operator_is_treated_as_missing() -> None:
    poi = sparse_poi()
    poi["OperatorInfo"] = {"ID": 1, "Title": "(Unknown Operator)"}
    station = map_poi_to_station(poi, ORIGIN_LAT, ORIGIN_LON)
    assert station is not None
    assert station.network is None


def test_never_invents_pricing() -> None:
    # UsageCost is present and free-text; it must not become a number.
    station = map_poi_to_station(full_poi(), ORIGIN_LAT, ORIGIN_LON)
    assert station is not None
    assert station.price_per_kwh is None
    assert station.currency is None


def test_never_invents_live_availability() -> None:
    station = map_poi_to_station(full_poi(), ORIGIN_LAT, ORIGIN_LON)
    assert station is not None
    # 0 would read as "none free" in the UI; OCM has no live counts.
    assert station.available_connectors is None


# --- 3. Connector mapping ----------------------------------------------------


def test_connector_labels_are_shortened_and_deduplicated() -> None:
    poi = sparse_poi()
    poi["Connections"] = [
        {"ConnectionType": {"Title": "Type 2 (Socket Only)"}},
        {"ConnectionType": {"Title": "Type 2 (Tethered Connector)"}},
        {"ConnectionType": {"Title": "CHAdeMO"}},
    ]
    assert map_connector_types(poi) == ["Type2", "CHAdeMO"]


def test_unrecognised_connector_title_passes_through_verbatim() -> None:
    poi = sparse_poi()
    poi["Connections"] = [{"ConnectionType": {"Title": "Bharat AC-001"}}]
    assert map_connector_types(poi) == ["Bharat AC-001"]


def test_unknown_connector_titles_are_dropped() -> None:
    poi = sparse_poi()
    poi["Connections"] = [
        {"ConnectionType": {"Title": "Unknown"}},
        {"ConnectionType": {"Title": ""}},
        {"ConnectionType": None},
        {},
        {"ConnectionType": {"Title": "CHAdeMO"}},
    ]
    assert map_connector_types(poi) == ["CHAdeMO"]


def test_total_connectors_prefers_number_of_points() -> None:
    poi = sparse_poi()
    poi["NumberOfPoints"] = 8
    poi["Connections"] = [{"Quantity": 2}]
    assert map_total_connectors(poi) == 8


def test_total_connectors_sums_quantity_when_all_present() -> None:
    poi = sparse_poi()
    poi["Connections"] = [{"Quantity": 2}, {"Quantity": 3}]
    assert map_total_connectors(poi) == 5


def test_total_connectors_is_none_when_any_quantity_is_missing() -> None:
    poi = sparse_poi()
    poi["Connections"] = [{"Quantity": 2}, {}]
    assert map_total_connectors(poi) is None


def test_total_connectors_is_none_without_connections() -> None:
    assert map_total_connectors(sparse_poi()) is None


def test_max_power_takes_the_highest_rating() -> None:
    poi = sparse_poi()
    poi["Connections"] = [{"PowerKW": 22.0}, {"PowerKW": 60.0}, {"PowerKW": None}]
    assert map_max_power_kw(poi) == 60.0


def test_max_power_is_none_when_no_rating_is_stated() -> None:
    poi = sparse_poi()
    poi["Connections"] = [{"PowerKW": None}, {"PowerKW": 0}]
    assert map_max_power_kw(poi) is None


# --- 4. Status mapping -------------------------------------------------------


def test_status_operational_does_not_become_available() -> None:
    # The crux: "Operational" means the site works, not that a plug is free.
    poi = sparse_poi()
    poi["StatusType"] = {"ID": 50, "Title": "Operational", "IsOperational": True}
    assert map_status(poi) is None


def test_status_automated_available() -> None:
    poi = sparse_poi()
    poi["StatusType"] = {"ID": 10, "IsOperational": True}
    assert map_status(poi) == "available"


def test_status_automated_in_use_is_busy() -> None:
    poi = sparse_poi()
    poi["StatusType"] = {"ID": 20, "IsOperational": True}
    assert map_status(poi) == "busy"


def test_status_not_operational_is_offline() -> None:
    poi = sparse_poi()
    poi["StatusType"] = {"ID": 100, "Title": "Not Operational", "IsOperational": False}
    assert map_status(poi) == "offline"


def test_status_missing_is_none() -> None:
    assert map_status(sparse_poi()) is None


def test_status_is_never_the_string_unknown() -> None:
    for status_type in (
        {"ID": 0, "Title": "Unknown"},
        {"ID": 50, "IsOperational": True},
        {"ID": 75, "Title": "Partly Operational (Mixed)", "IsOperational": True},
        None,
        "nonsense",
    ):
        poi = sparse_poi()
        poi["StatusType"] = status_type
        assert map_status(poi) != "unknown"


def test_planned_and_removed_stations_are_dropped() -> None:
    for status_id in (150, 200, 210):
        poi = sparse_poi()
        poi["StatusType"] = {"ID": status_id}
        assert map_poi_to_station(poi, ORIGIN_LAT, ORIGIN_LON) is None


# --- 5. Charger type ---------------------------------------------------------


def test_charger_type_ac_only() -> None:
    poi = sparse_poi()
    poi["Connections"] = [{"CurrentTypeID": 10}, {"CurrentTypeID": 20}]
    assert map_charger_type(poi) == "AC"


def test_charger_type_dc_only() -> None:
    poi = sparse_poi()
    poi["Connections"] = [{"CurrentTypeID": 30}]
    assert map_charger_type(poi) == "DC"


def test_charger_type_both() -> None:
    poi = sparse_poi()
    poi["Connections"] = [{"CurrentTypeID": 20}, {"CurrentTypeID": 30}]
    assert map_charger_type(poi) == "BOTH"


def test_charger_type_is_none_without_current_type() -> None:
    poi = sparse_poi()
    # High power alone must not be read as DC - 43 kW AC exists.
    poi["Connections"] = [{"PowerKW": 120.0}]
    assert map_charger_type(poi) is None


# --- 6. Timestamps -----------------------------------------------------------


def test_last_updated_at_parses_zulu_time_as_aware() -> None:
    poi = {"DateLastStatusUpdate": "2026-08-14T09:20:00Z"}
    parsed = map_last_updated_at(poi)
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timezone.utc.utcoffset(None)


def test_naive_timestamp_is_tagged_utc() -> None:
    parsed = map_last_updated_at({"DateLastStatusUpdate": "2026-08-14T09:20:00"})
    assert parsed is not None
    assert parsed.tzinfo is not None


def test_unparseable_timestamp_becomes_none() -> None:
    assert map_last_updated_at({"DateLastStatusUpdate": "not a date"}) is None
    assert map_last_updated_at({}) is None


# --- 7. Records that cannot be shown ----------------------------------------


def test_poi_without_a_name_is_dropped() -> None:
    poi = sparse_poi()
    poi["AddressInfo"]["Title"] = "   "
    assert map_poi_to_station(poi, ORIGIN_LAT, ORIGIN_LON) is None


def test_poi_without_coordinates_is_dropped() -> None:
    poi = sparse_poi()
    del poi["AddressInfo"]["Latitude"]
    assert map_poi_to_station(poi, ORIGIN_LAT, ORIGIN_LON) is None


def test_poi_with_out_of_range_coordinates_is_dropped() -> None:
    poi = sparse_poi()
    poi["AddressInfo"]["Latitude"] = 999.0
    assert map_poi_to_station(poi, ORIGIN_LAT, ORIGIN_LON) is None


def test_poi_without_an_id_is_dropped() -> None:
    poi = sparse_poi()
    del poi["ID"]
    assert map_poi_to_station(poi, ORIGIN_LAT, ORIGIN_LON) is None


def test_batch_mapping_skips_bad_records_without_failing() -> None:
    stations = map_pois_to_stations(
        [full_poi(), {}, {"ID": 5}, sparse_poi()], ORIGIN_LAT, ORIGIN_LON
    )
    assert len(stations) == 2


def test_empty_input_yields_empty_output() -> None:
    assert map_pois_to_stations([], ORIGIN_LAT, ORIGIN_LON) == []


# --- 8. ID-only records (what live OCM actually returns) ---------------------
# OCM's /poi/ endpoint sends "OperatorInfo": null, "StatusType": null and
# "ConnectionType": null, giving only the numeric IDs. These cover that path.


def live_shape_poi() -> dict[str, Any]:
    """A POI in the shape live OCM returns: reference objects null, IDs only."""
    return {
        "ID": 307102,
        "OperatorInfo": None,
        "StatusType": None,
        "OperatorID": 45,
        "StatusTypeID": 50,
        "NumberOfPoints": 1,
        "DateLastStatusUpdate": "2025-03-10T14:49:00Z",
        "AddressInfo": {
            "Title": "Andheri West",
            "AddressLine1": "Four Bunglows",
            "Town": "Mumbai",
            "StateOrProvince": "Maharashtra",
            "Postcode": "400057",
            "Latitude": 19.1166,
            "Longitude": 72.82927,
        },
        "Connections": [
            {
                "ConnectionTypeID": 33,
                "ConnectionType": None,
                "StatusTypeID": 50,
                "CurrentTypeID": 30,
                "CurrentType": None,
                "PowerKW": 120.0,
                "Quantity": 1,
            }
        ],
    }


def test_connector_types_resolve_from_id_when_object_is_null() -> None:
    assert map_connector_types(live_shape_poi()) == ["CCS2"]


def test_connector_type_id_zero_is_dropped() -> None:
    poi = sparse_poi()
    poi["Connections"] = [{"ConnectionTypeID": 0, "ConnectionType": None}]
    assert map_connector_types(poi) == []


def test_status_resolves_from_status_type_id() -> None:
    poi = sparse_poi()
    for status_id, expected in [(10, "available"), (20, "busy"), (100, "offline"), (50, None)]:
        poi["StatusTypeID"] = status_id
        poi["StatusType"] = None
        assert map_status(poi) == expected, f"StatusTypeID {status_id}"


def test_temporarily_unavailable_is_offline_despite_is_operational_true() -> None:
    # OCM's reference data marks StatusTypeID 30 as IsOperational=True, so an
    # IsOperational check alone would report a knowingly-down site as fine.
    poi = sparse_poi()
    poi["StatusTypeID"] = 30
    assert map_status(poi) == "offline"


def test_planned_and_removed_are_dropped_via_flat_id() -> None:
    for status_id in (150, 200, 210):
        poi = sparse_poi()
        poi["StatusTypeID"] = status_id
        assert map_poi_to_station(poi, ORIGIN_LAT, ORIGIN_LON) is None


def test_charger_type_resolves_from_current_type_id() -> None:
    assert map_charger_type(live_shape_poi()) == "DC"


def test_charger_type_falls_back_to_definitional_connector_type() -> None:
    poi = sparse_poi()
    poi["Connections"] = [{"ConnectionTypeID": 2}]  # CHAdeMO is DC by definition
    assert map_charger_type(poi) == "DC"

    poi["Connections"] = [{"ConnectionTypeID": 25}]  # Type 2 socket is AC
    assert map_charger_type(poi) == "AC"

    poi["Connections"] = [{"ConnectionTypeID": 25}, {"ConnectionTypeID": 33}]
    assert map_charger_type(poi) == "BOTH"


def test_ambiguous_connectors_support_no_charger_type_conclusion() -> None:
    for ambiguous_id in (27, 30):  # NACS, Tesla - both AC and DC in the wild
        poi = sparse_poi()
        poi["Connections"] = [{"ConnectionTypeID": ambiguous_id}]
        assert map_charger_type(poi) is None, f"ConnectionTypeID {ambiguous_id}"


def test_placeholder_operator_ids_yield_no_network() -> None:
    for operator_id in (1, 45):
        poi = sparse_poi()
        poi["OperatorID"] = operator_id
        poi["OperatorInfo"] = None
        station = map_poi_to_station(poi, ORIGIN_LAT, ORIGIN_LON)
        assert station is not None
        assert station.network is None


def test_live_shape_poi_maps_end_to_end() -> None:
    station = map_poi_to_station(live_shape_poi(), ORIGIN_LAT, ORIGIN_LON)
    assert station is not None
    assert station.id == "ocm-307102"
    assert station.name == "Andheri West"
    assert station.connector_types == ["CCS2"]
    assert station.charger_type == "DC"
    assert station.max_power_kw == 120.0
    assert station.total_connectors == 1
    assert station.network is None
    assert station.status is None
    assert station.available_connectors is None


def test_repeated_address_parts_are_not_duplicated() -> None:
    poi = sparse_poi()
    poi["AddressInfo"]["AddressLine1"] = "Equinox Business Park, Kurla West, Mumbai, Maharashtra"
    poi["AddressInfo"]["Town"] = "Mumbai"
    poi["AddressInfo"]["StateOrProvince"] = "Maharashtra"
    station = map_poi_to_station(poi, ORIGIN_LAT, ORIGIN_LON)
    assert station is not None
    assert station.address == "Equinox Business Park, Kurla West, Mumbai, Maharashtra"


# --- 9. Distance -------------------------------------------------------------


def test_distance_is_computed_from_our_origin_and_rounded() -> None:
    station = map_poi_to_station(full_poi(), ORIGIN_LAT, ORIGIN_LON)
    assert station is not None
    # OCM's own AddressInfo.Distance of 999.0 must be ignored.
    assert station.distance_km == 1.7


def test_distance_is_zero_at_the_origin() -> None:
    poi = sparse_poi()
    poi["AddressInfo"]["Latitude"] = ORIGIN_LAT
    poi["AddressInfo"]["Longitude"] = ORIGIN_LON
    station = map_poi_to_station(poi, ORIGIN_LAT, ORIGIN_LON)
    assert station is not None
    assert station.distance_km == 0.0
