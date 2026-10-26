"""Request/response schemas for battery health prediction, explanation and RUL."""

import math
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

SensorReading = Annotated[list[float], Field(min_length=8, max_length=8)]

Normalisation = Literal["global", "per_dataset", "approximate"]


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
    dataset: Literal[1, 2, 3] | None = Field(
        None,
        description=(
            "Optional. Which training dataset (manufacturer 1-3) the session comes "
            "from. The model was trained with per-dataset scaling, so giving it "
            "reproduces the training preprocessing exactly. Without it an "
            "approximate pooled scaling is used and the response says so."
        ),
    )
    include_attention: bool = Field(
        False, description="Also return the 128 attention weights."
    )

    @field_validator("readings")
    @classmethod
    def _values_must_be_finite(cls, rows: list[list[float]]) -> list[list[float]]:
        if any(not math.isfinite(value) for row in rows for value in row):
            raise ValueError("readings must not contain NaN or infinite values.")
        return rows


class BatteryPrediction(BaseModel):
    """Model output for a single charging session."""

    capacity: float = Field(..., description="Estimated battery capacity.")
    soh_percent: float = Field(..., description="Estimated State of Health, 0-100.")
    fault_probability: float = Field(
        ...,
        description=(
            "Experimental fault risk score, 0-1. Not a diagnosis and not a yes/no: "
            "it is only meaningful when compared across cars or averaged over a "
            "car's sessions."
        ),
    )
    fault_probability_experimental: bool = True
    model_name: str = Field("", description="Name of the deployed model.")
    normalisation: Normalisation = Field(
        "global",
        description=(
            "Which normalisation constants were applied. 'approximate' means no "
            "dataset was given and the pooled constants are only an average of the "
            "per-dataset ones used in training."
        ),
    )
    attention_weights: list[float] | None = Field(
        None, description="128 attention weights (only when requested)."
    )
    top_attention_rows: list[int] | None = Field(
        None, description="Row indices with the highest attention (only when requested)."
    )


class BatteryDemoPrediction(BatteryPrediction):
    """Prediction for a bundled demo session (not the user's own battery)."""

    source: str = "bundled sample charging session"
    session_id: str | None = None
    title: str | None = None
    dataset: Literal[1, 2, 3] | None = None
    true_label: Literal[0, 1] | None = Field(
        None, description="Label from the dataset: 0 healthy, 1 faulty. Not a model output."
    )


class DemoSessionInfo(BaseModel):
    """One selectable demo session."""

    id: str
    title: str
    description: str = ""
    dataset: Literal[1, 2, 3] | None = None
    true_label: Literal[0, 1] | None = None


class ExplanationResult(BaseModel):
    """Where the model looked and which sensors the fault score reacts to, for one session."""

    fault_probability: float
    fault_probability_experimental: bool = True
    model_name: str = ""
    normalisation: Normalisation = "global"
    channel_sensitivity: dict[str, float] = Field(
        ...,
        description=(
            "Per sensor channel: how far the fault probability moves when that "
            "channel is set to its training average. A sensitivity, not a cause."
        ),
    )
    top_attention_rows: list[int] | None = Field(
        None, description="The 5 time steps (0-127) with the most attention, if the model has attention."
    )
    attention_weights: list[float] | None = None
    note: str = (
        "Illustrates the model's behaviour on this one session. It is not proof of why "
        "a fault exists."
    )


class ExplainReason(BaseModel):
    """One sensor channel the fault score reacts to, with measured context."""

    channel: str
    label: str
    effect_points: int = Field(
        ..., description="Percentage points the fault risk moves when this channel is set to its training average."
    )
    detail: str


class DemoExplanation(BaseModel):
    """Prediction and plain-language explanation for one recorded demo session."""

    session_id: str
    title: str
    dataset: Literal[1, 2, 3] | None = None
    true_label: Literal[0, 1] | None = Field(
        None, description="The dataset's label for the vehicle (0 healthy, 1 faulty), not a model output."
    )
    capacity: float
    soh_percent: float
    fault_probability: float
    fault_probability_experimental: bool = True
    model_name: str = ""
    normalisation: Normalisation = "global"
    risk_level: Literal["elevated", "low"]
    alert_probability: float = Field(..., description="Display threshold used for `risk_level`.")
    headline: str
    reasons: list[ExplainReason]
    channel_sensitivity: dict[str, float]
    observed: dict[str, float | str] = Field(
        ..., description="Facts measured directly from the session's readings."
    )
    top_attention_rows: list[int] | None = None
    top_attention_seconds: list[float] | None = Field(
        None, description="Session time (s) of the time steps the model attended to most."
    )
    context_note: str | None = None
    note: str = (
        "Shows how the model reacts on this one recorded session. It is not proof of why a "
        "fault exists, and the fault score is experimental, not a diagnosis."
    )


class ModelInfo(BaseModel):
    """What model the server has, and whether it can run."""

    loaded: bool
    model_name: str | None = None
    fault_threshold: float | None = Field(
        None, description="Validation-chosen threshold from training. Informational only: the API never applies it."
    )
    per_dataset_normalisation: bool = False
    pooled_normalisation_approximate: bool = False
    weights_file: str
    detail: str | None = None


class RulPoint(BaseModel):
    """One (mileage, State of Health) measurement of a car."""

    mileage_km: float = Field(..., ge=0, le=2_000_000)
    soh_percent: float = Field(..., ge=0, le=100)


class RulRequest(BaseModel):
    """A car's State of Health history, to fit its degradation trend."""

    history: list[RulPoint] = Field(..., min_length=5, max_length=5000)

    @model_validator(mode="after")
    def _mileage_must_vary(self) -> "RulRequest":
        if len({point.mileage_km for point in self.history}) < 2:
            raise ValueError("history must contain at least two different mileages.")
        return self


class RulEstimate(BaseModel):
    """Remaining useful life until SoH reaches the threshold, from a straight-line trend."""

    estimated_rul_km: float | None = Field(
        None, description="Kilometres left until the threshold SoH, or null if SoH is not falling."
    )
    capped: bool = Field(False, description="True when the estimate was cut to the maximum.")
    current_mileage_km: float
    current_soh_percent: float
    degradation_soh_per_1000km: float | None = None
    threshold_soh: float
    source: Literal["fit", "precomputed"]
    note: str