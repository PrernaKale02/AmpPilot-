"""Lifecycle and validation tests for the in-memory simulation API."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.simulation import SimulationConfig
from app.services.simulation import SimulationService, simulation_service

client = TestClient(app)
CONFIG = {"durationMinutes": 1, "speedMultiplier": 2, "telemetryIntervalSeconds": 0.5}


def setup_function() -> None:
    simulation_service.stop()


def test_start_pause_resume_and_stop_lifecycle() -> None:
    started = client.post("/api/simulation/start", json=CONFIG)
    assert started.status_code == 200
    assert started.json()["status"] == "running"
    assert started.json()["latestTelemetry"]["stateOfChargePercent"] == 82
    assert started.json()["events"][0]["message"] == "Simulation session started."

    paused = client.post("/api/simulation/pause")
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"

    resumed = client.post("/api/simulation/resume")
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "running"

    stopped = client.post("/api/simulation/stop")
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "idle"


def test_invalid_configuration_is_rejected() -> None:
    for invalid in (
        {**CONFIG, "durationMinutes": 0},
        {**CONFIG, "durationMinutes": 61},
        {**CONFIG, "speedMultiplier": 3},
        {**CONFIG, "telemetryIntervalSeconds": 2},
    ):
        assert client.post("/api/simulation/start", json=invalid).status_code == 422


def test_elapsed_time_uses_active_time_and_speed(monkeypatch) -> None:
    ticks = iter((100.0, 100.0, 105.0))
    monkeypatch.setattr("app.services.simulation.monotonic", lambda: next(ticks))
    client.post("/api/simulation/start", json=CONFIG)
    body = client.get("/api/simulation/status").json()
    assert body["elapsedRealSeconds"] == 5
    assert body["elapsedSimulatedSeconds"] == 10


def test_duration_auto_completes(monkeypatch) -> None:
    ticks = iter((100.0, 100.0, 161.0))
    monkeypatch.setattr("app.services.simulation.monotonic", lambda: next(ticks))
    client.post("/api/simulation/start", json=CONFIG)
    body = client.get("/api/simulation/status").json()
    assert body["status"] == "completed"
    assert body["elapsedRealSeconds"] == 60
    assert body["remainingRealSeconds"] == 0
    assert body["events"][-1]["message"] == "Simulation session completed."


def test_telemetry_progression_is_bounded_and_uses_simulation_speed(monkeypatch) -> None:
    ticks = iter((100.0, 100.0, 110.0))
    monkeypatch.setattr("app.services.simulation.monotonic", lambda: next(ticks))
    client.post("/api/simulation/start", json={**CONFIG, "speedMultiplier": 30})
    body = client.get("/api/simulation/status").json()

    assert body["latestTelemetry"]["simulatedSeconds"] == 300
    assert body["latestTelemetry"]["stateOfChargePercent"] < 82
    assert 1 < len(body["telemetryHistory"]) <= 120


def test_pause_freezes_telemetry_until_resumed(monkeypatch) -> None:
    ticks = iter((100.0, 100.0, 105.0, 200.0, 200.0, 205.0))
    monkeypatch.setattr("app.services.simulation.monotonic", lambda: next(ticks))
    client.post("/api/simulation/start", json=CONFIG)
    paused = client.post("/api/simulation/pause").json()
    resumed = client.post("/api/simulation/resume").json()
    progressed = client.get("/api/simulation/status").json()

    assert paused["latestTelemetry"]["simulatedSeconds"] == 10
    assert resumed["elapsedRealSeconds"] == 5
    assert resumed["latestTelemetry"]["stateOfChargePercent"] == paused["latestTelemetry"]["stateOfChargePercent"]
    assert progressed["latestTelemetry"]["simulatedSeconds"] == 20
    assert progressed["latestTelemetry"]["stateOfChargePercent"] < paused["latestTelemetry"]["stateOfChargePercent"]


def test_temperature_threshold_event_is_generated_from_telemetry(monkeypatch) -> None:
    config = {**CONFIG, "durationMinutes": 60, "speedMultiplier": 30}
    ticks = iter((100.0, 100.0, 700.0))
    monkeypatch.setattr("app.services.simulation.monotonic", lambda: next(ticks))
    client.post("/api/simulation/start", json=config)
    body = client.get("/api/simulation/status").json()

    assert body["latestTelemetry"]["batteryStatus"] == "warning"
    assert any(event["kind"] == "warning" for event in body["events"])


def test_discharge_current_is_positive_and_soc_decreases() -> None:
    config = SimulationConfig(**CONFIG)
    start = SimulationService._telemetry_at(config, 0)
    later = SimulationService._telemetry_at(config, 600)

    assert start.direction == "discharging"
    assert start.current_a > 0
    assert later.state_of_charge_percent < start.state_of_charge_percent


def test_idle_current_is_zero_and_soc_is_stable() -> None:
    config = SimulationConfig(**CONFIG)
    beginning = SimulationService._telemetry_at(config, 900)
    later = SimulationService._telemetry_at(config, 1_070)

    assert beginning.direction == "idle"
    assert beginning.current_a == 0
    assert later.direction == "idle"
    assert later.state_of_charge_percent == beginning.state_of_charge_percent


def test_charge_current_is_negative_and_soc_increases_within_bounds() -> None:
    config = SimulationConfig(**CONFIG)
    beginning = SimulationService._telemetry_at(config, 1_080)
    later = SimulationService._telemetry_at(config, 1_700)

    assert beginning.direction == "charging"
    assert beginning.current_a < 0
    assert later.state_of_charge_percent > beginning.state_of_charge_percent
    assert 0 <= later.state_of_charge_percent <= 100
