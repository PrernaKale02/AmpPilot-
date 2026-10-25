"""Request and response models for the local development simulation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SimulationConfig(BaseModel):
    """Controls accepted when a virtual EV session starts."""

    model_config = ConfigDict(populate_by_name=True)

    duration_minutes: int = Field(ge=1, le=60, alias="durationMinutes")
    speed_multiplier: Literal[1, 2, 5, 10, 30] = Field(alias="speedMultiplier")
    telemetry_interval_seconds: Literal[0.5, 1.0, 5.0] = Field(
        alias="telemetryIntervalSeconds"
    )
    warning_temperature_c: float = Field(42, ge=25, le=70, alias="warningTemperatureC")
    critical_temperature_c: float = Field(50, ge=25, le=80, alias="criticalTemperatureC")
    warning_soc_percent: float = Field(20, ge=1, le=99, alias="warningSocPercent")
    critical_soc_percent: float = Field(10, ge=0, le=99, alias="criticalSocPercent")
    demo_session_id: str | None = Field(
        None,
        alias="demoSessionId",
        pattern=r"^[A-Za-z0-9_-]{1,64}$",
        description=(
            "Id of a recorded demo session (see GET /battery/demo-sessions). When set, the "
            "simulation replays that real charging session instead of generating readings."
        ),
    )

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "SimulationConfig":
        if self.critical_temperature_c <= self.warning_temperature_c:
            raise ValueError("criticalTemperatureC must be higher than warningTemperatureC.")
        if self.critical_soc_percent >= self.warning_soc_percent:
            raise ValueError("criticalSocPercent must be lower than warningSocPercent.")
        return self


class SimulatedTelemetry(BaseModel):
    """One battery reading: generated, or replayed from a recorded dataset session.

    It is never live telemetry from the user's own vehicle.
    """

    model_config = ConfigDict(populate_by_name=True)

    simulated_seconds: float = Field(alias="simulatedSeconds")
    state_of_charge_percent: float = Field(alias="stateOfChargePercent")
    voltage_v: float = Field(alias="voltageV")
    current_a: float = Field(alias="currentA")
    temperature_c: float = Field(alias="temperatureC")
    direction: Literal["charging", "discharging", "idle"]
    battery_status: Literal["normal", "warning", "critical"] = Field(alias="batteryStatus")


class SimulationEvent(BaseModel):
    """A timestamped, generated session or threshold-crossing event."""

    model_config = ConfigDict(populate_by_name=True)

    timestamp: str
    simulated_seconds: float = Field(alias="simulatedSeconds")
    kind: Literal["session", "warning", "critical"]
    message: str


class SimulationStatus(BaseModel):
    """Current lifecycle state, with all elapsed values measured in seconds."""

    model_config = ConfigDict(populate_by_name=True)

    status: Literal["idle", "running", "paused", "completed"]
    config: SimulationConfig | None = None
    elapsed_real_seconds: float = Field(0, alias="elapsedRealSeconds")
    elapsed_simulated_seconds: float = Field(0, alias="elapsedSimulatedSeconds")
    remaining_real_seconds: float = Field(0, alias="remainingRealSeconds")
    started_at: str | None = Field(None, alias="startedAt")
    paused_at: str | None = Field(None, alias="pausedAt")
    resumed_at: str | None = Field(None, alias="resumedAt")
    stopped_at: str | None = Field(None, alias="stoppedAt")
    data_source: Literal["generated", "recorded"] = Field("generated", alias="dataSource")
    replay_total_seconds: float | None = Field(None, alias="replayTotalSeconds")
    latest_telemetry: SimulatedTelemetry | None = Field(None, alias="latestTelemetry")
    telemetry_history: list[SimulatedTelemetry] = Field(
        default_factory=list, alias="telemetryHistory"
    )
    events: list[SimulationEvent] = Field(default_factory=list)