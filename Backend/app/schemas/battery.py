"""Request/response schemas for battery health prediction."""

from typing import Annotated

from pydantic import BaseModel, Field

SensorReading = Annotated[list[float], Field(min_length=8, max_length=8)]


class ChargingSessionInput(BaseModel):
    """One charging session: 128 timesteps x 8 sensor channels.

    Channel order: voltage, current, SOC, max_cell_voltage,
    min_cell_voltage, max_temp, min_temp, time_seconds.
    """

    readings: list[SensorReading] = Field(
        ...,
        description="128 rows of 8 sensor values each.",
        min_length=128,
        max_length=128,
    )


class BatteryPrediction(BaseModel):
    """Model output for a single charging session."""

    capacity: float = Field(..., description="Estimated battery capacity.")
    soh_percent: float = Field(..., description="Estimated State of Health, 0-100.")
    fault_probability: float = Field(..., description="Probability of fault, 0-1.")
    is_faulty: bool = Field(..., description="fault_probability > 0.5")
