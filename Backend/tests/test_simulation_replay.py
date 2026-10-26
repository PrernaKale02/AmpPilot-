"""Simulation mode replaying a recorded demo session instead of generated readings."""

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.simulation import SimulationConfig
from app.services import battery_model as bm
from app.services.simulation import SimulationService, _load_replay, simulation_service

client = TestClient(app)
REPLAY_CONFIG = {
    "durationMinutes": 60,
    "speedMultiplier": 10,
    "telemetryIntervalSeconds": 1,
    "demoSessionId": "charge_a",
}


def _write(folder, name: str, current: float = -20.0, soc_start: float = 50.0, soc_end: float = 60.0):
    """128 rows, 10 s apart (0..1270 s); SOC and voltage rise linearly."""
    soc = np.linspace(soc_start, soc_end, 128)
    volt = np.linspace(3.9, 4.0, 128)
    rows = [
        [float(volt[i]), current, float(soc[i]), 4.0, 3.99, 31.0, 29.0, i * 10.0]
        for i in range(128)
    ]
    data = {"readings": rows, "title": "Charging car A", "dataset": 1, "true_label": 0}
    (folder / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def demo_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(bm, "DEMO_DIR", tmp_path)
    _write(tmp_path, "charge_a")
    return tmp_path


def setup_function() -> None:
    simulation_service.stop()


def _config(**overrides) -> SimulationConfig:
    return SimulationConfig(**{**REPLAY_CONFIG, **overrides})


def test_start_replays_the_first_recorded_reading(demo_dir):
    body = client.post("/api/simulation/start", json=REPLAY_CONFIG).json()
    assert body["status"] == "running"
    assert body["dataSource"] == "recorded"
    assert body["replayTotalSeconds"] == 1270
    assert body["config"]["demoSessionId"] == "charge_a"
    first = body["latestTelemetry"]
    assert first["stateOfChargePercent"] == 50.0
    assert first["voltageV"] == 3.9
    assert first["currentA"] == -20.0
    assert first["temperatureC"] == 31.0  # the session's highest temperature channel
    assert first["direction"] == "charging"
    assert "Replaying recorded charging session: Charging car A" in body["events"][0]["message"]


def test_readings_follow_the_recording_at_the_chosen_speed(demo_dir, monkeypatch):
    ticks = iter((100.0, 100.0, 105.0))  # start, first status, status 5 s later
    monkeypatch.setattr("app.services.simulation.monotonic", lambda: next(ticks))
    client.post("/api/simulation/start", json=REPLAY_CONFIG)
    body = client.get("/api/simulation/status").json()
    # 5 real seconds x 10 = 50 simulated seconds = recorded row 5
    assert body["elapsedSimulatedSeconds"] == 50
    latest = body["latestTelemetry"]
    assert latest["simulatedSeconds"] == 50
    assert latest["stateOfChargePercent"] == pytest.approx(50 + 10 * 5 / 127, abs=0.05)
    assert latest["voltageV"] == pytest.approx(3.9 + 0.1 * 5 / 127, abs=0.001)
    # one reading per interval, none invented ahead of time
    assert [t["simulatedSeconds"] for t in body["telemetryHistory"]] == [0, 10, 20, 30, 40, 50]


def test_session_ends_when_the_recording_ends(demo_dir, monkeypatch):
    ticks = iter((100.0, 100.0, 400.0))  # far past the end of a 60-minute budget
    monkeypatch.setattr("app.services.simulation.monotonic", lambda: next(ticks))
    client.post("/api/simulation/start", json=REPLAY_CONFIG)
    body = client.get("/api/simulation/status").json()
    assert body["status"] == "completed"
    assert body["elapsedRealSeconds"] == 127  # 1270 recorded seconds at 10x
    assert body["elapsedSimulatedSeconds"] == 1270
    assert body["latestTelemetry"]["stateOfChargePercent"] == 60.0
    assert body["events"][-1]["message"] == "Simulation session completed."


def test_configured_duration_still_wins_when_shorter(demo_dir, monkeypatch):
    ticks = iter((100.0, 100.0, 400.0))
    monkeypatch.setattr("app.services.simulation.monotonic", lambda: next(ticks))
    client.post("/api/simulation/start", json={**REPLAY_CONFIG, "durationMinutes": 1})
    body = client.get("/api/simulation/status").json()
    assert body["status"] == "completed" and body["elapsedRealSeconds"] == 60
    assert body["elapsedSimulatedSeconds"] == 600  # only the first 600 s of the recording


def test_unknown_demo_session_is_404_and_keeps_the_running_session(demo_dir):
    client.post(
        "/api/simulation/start",
        json={k: v for k, v in REPLAY_CONFIG.items() if k != "demoSessionId"},
    )
    response = client.post("/api/simulation/start", json={**REPLAY_CONFIG, "demoSessionId": "nope"})
    assert response.status_code == 404
    still = client.get("/api/simulation/status").json()
    assert still["status"] == "running" and still["dataSource"] == "generated"


@pytest.mark.parametrize("bad", ["../etc/passwd", "a/b", "x y", "", "é"])
def test_unsafe_demo_ids_are_rejected(demo_dir, bad):
    response = client.post("/api/simulation/start", json={**REPLAY_CONFIG, "demoSessionId": bad})
    assert response.status_code == 422


def test_without_a_demo_id_the_generator_still_runs():
    body = client.post(
        "/api/simulation/start",
        json={"durationMinutes": 1, "speedMultiplier": 2, "telemetryIntervalSeconds": 0.5},
    ).json()
    assert body["dataSource"] == "generated" and body["replayTotalSeconds"] is None
    assert body["latestTelemetry"]["stateOfChargePercent"] == 82


def test_direction_follows_the_current_sign(demo_dir):
    config = _config()
    replay = _load_replay("charge_a")

    def direction(current: float) -> str:
        shifted = replay.readings.copy()
        shifted[:, 1] = current
        moved = type(replay)(replay.session_id, replay.title, replay.seconds, shifted)
        return SimulationService._replay_telemetry(config, moved, 0).direction

    assert direction(-20) == "charging"
    assert direction(0) == "idle"
    assert direction(0.4) == "idle"
    assert direction(35) == "discharging"


def test_low_recorded_charge_raises_the_same_alerts_as_generated_data(demo_dir):
    _write(demo_dir, "low_charge", current=0.0, soc_start=19.6, soc_end=19.6)
    low = _load_replay("low_charge")
    reading = SimulationService._replay_telemetry(_config(), low, 0)
    assert reading.battery_status == "warning"  # at or below the 20 % warning level
    _write(demo_dir, "empty", current=0.0, soc_start=8.0, soc_end=8.0)
    reading = SimulationService._replay_telemetry(_config(), _load_replay("empty"), 0)
    assert reading.battery_status == "critical"  # at or below the 10 % critical level


def test_readings_after_the_recording_hold_the_last_value(demo_dir):
    replay = _load_replay("charge_a")
    reading = SimulationService._replay_telemetry(_config(), replay, 99_999)
    assert reading.simulated_seconds == 1270 and reading.state_of_charge_percent == 60.0


def test_a_file_without_a_usable_time_column_uses_even_spacing(demo_dir):
    data = json.loads((demo_dir / "charge_a.json").read_text())
    for row in data["readings"]:
        row[7] = 0.0  # time column unusable
    (demo_dir / "no_time.json").write_text(json.dumps(data), encoding="utf-8")
    replay = _load_replay("no_time")
    assert replay.total_seconds == 1270  # 127 steps of 10 s


REAL_DEMO_FILES = sorted(bm.DEMO_DIR.glob("*.json"))


@pytest.mark.skipif(not REAL_DEMO_FILES, reason="no demo files present")
@pytest.mark.parametrize("path", REAL_DEMO_FILES, ids=lambda p: p.stem)
def test_every_shipped_demo_session_replays_cleanly(path):
    replay = _load_replay(path.stem)
    config = _config(demoSessionId=path.stem)
    start = SimulationService._replay_telemetry(config, replay, 0)
    end = SimulationService._replay_telemetry(config, replay, replay.total_seconds)
    last = replay.readings[-1]
    assert start.state_of_charge_percent == pytest.approx(replay.readings[0][2], abs=0.05)
    assert end.state_of_charge_percent == pytest.approx(last[2], abs=0.05)
    assert end.voltage_v == pytest.approx(last[0], abs=0.001)
    assert 0 <= end.state_of_charge_percent <= 100