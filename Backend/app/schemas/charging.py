"""The backend/frontend contract for EV charging stations.

Python attributes stay snake_case; the JSON on the wire is camelCase, produced
by a single `alias_generator` on the shared base model rather than an alias per
field. FastAPI serialises response models by alias, so route code can keep
constructing these with snake_case keyword arguments.

**Nullability is the contract here.** Open Charge Map is a crowd-sourced
dataset: most stations carry a name, coordinates and connector list, and little
else. Every field the provider cannot reliably supply is optional and is sent
as `null` rather than filled with a placeholder, a zero, or a guess. A `null`
means "we do not know", which is information; a fabricated `0` would read as
"none available", which is a different and false claim.

``status`` deliberately has no ``"unknown"`` member. Availability is either
known from the provider or it is `null` — an "Unknown" state is not something
the API is able to express, so it cannot leak to the UI by accident.
"""

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

#: Real availability states only. `None` covers "not known", so there is
#: deliberately no "unknown" member for the mapper to fall back onto.
StationStatus = Literal["available", "busy", "offline"]

#: Kind of charging offered at the site.
ChargerType = Literal["AC", "DC", "BOTH"]


class CamelModel(BaseModel):
    """Base model emitting camelCase JSON while accepting snake_case in Python."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class Origin(CamelModel):
    """The coordinate a station search was run from."""

    latitude: float = Field(ge=-90, le=90, description="WGS84 decimal degrees.")
    longitude: float = Field(ge=-180, le=180, description="WGS84 decimal degrees.")


class ChargingStation(CamelModel):
    """A single EV charging site, in the shape the frontend already renders.

    Required fields are only those without which the station cannot be shown at
    all: an identifier, a name, and a location.
    """

    id: str = Field(min_length=1, description="Stable station identifier, e.g. 'ocm-12345'.")
    name: str = Field(min_length=1, description="Display name of the station.")
    latitude: float = Field(ge=-90, le=90, description="WGS84 decimal degrees.")
    longitude: float = Field(ge=-180, le=180, description="WGS84 decimal degrees.")
    distance_km: float = Field(
        ge=0,
        description="Great-circle distance from the search origin, km, rounded to 1 decimal.",
    )

    network: str | None = Field(
        default=None,
        description="Operator running the station. Null when the provider has no operator on record.",
    )
    address: str | None = Field(
        default=None,
        description="Single-line address assembled from the provider's address parts.",
    )
    status: StationStatus | None = Field(
        default=None,
        description=(
            "Current availability. Null whenever the provider does not genuinely report it - "
            "which is most of the time. Never the string 'unknown'."
        ),
    )
    available_connectors: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Connectors currently free. Null unless a provider reports live availability; "
            "a 0 here would falsely mean 'none free'."
        ),
    )
    total_connectors: int | None = Field(
        default=None,
        ge=0,
        description="Connectors installed at the site. Null when the provider does not state a count.",
    )
    max_power_kw: float | None = Field(
        default=None,
        gt=0,
        description="Peak power of the fastest connector, kW. Null when no connector states a rating.",
    )
    connector_types: list[str] = Field(
        default_factory=list,
        description=(
            'Connector labels, e.g. ["CCS2", "Type2"]. Always an array - an empty list means '
            "the provider lists no connectors, which is not the same as null."
        ),
    )
    charger_type: ChargerType | None = Field(
        default=None,
        description="Derived from connector current type. Null when the data does not support a conclusion.",
    )
    price_per_kwh: Annotated[float, Field(ge=0)] | None = Field(
        default=None,
        description="Null unless a provider publishes a machine-readable per-kWh tariff.",
    )
    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="ISO 4217 code. Non-null only when pricePerKwh is non-null.",
    )
    is_open_24_hours: bool | None = Field(
        default=None,
        description="True only when opening hours explicitly say so. Null when not stated.",
    )
    hours: str | None = Field(
        default=None,
        description="Opening hours as published by the provider, verbatim. Null when not stated.",
    )
    last_updated_at: AwareDatetime | None = Field(
        default=None,
        description=(
            "When the provider last updated this record's status. Timezone-aware so the app "
            "parses it correctly. Null when unknown - never stamped with our own clock, since "
            "the app renders this to the user as a freshness claim."
        ),
    )


class NearbyStationsResponse(CamelModel):
    """Envelope returned by ``GET /api/charging-stations``.

    ``origin`` and ``radiusKm`` echo the values actually applied, which makes a
    response self-describing when debugging. The frontend service unwraps
    ``data.stations`` so the existing screens keep receiving a plain array.
    """

    stations: list[ChargingStation] = Field(description="Matching stations, nearest first.")
    origin: Origin = Field(description="The search origin the results were measured from.")
    radius_km: float = Field(gt=0, description="The search radius actually applied, km.")
