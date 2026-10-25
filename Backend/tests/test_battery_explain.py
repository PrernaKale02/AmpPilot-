"""Plain-language explanation of a recorded demo session (no torch, no weights)."""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import ModelUnavailable
from app.main import app
from app.services import battery_model as bm

client = TestClient(app)
REAL_FAULTY = bm.DEMO_DIR / "faulty_3_515.json"

# voltage, current, SOC, max cell V, min cell V, max temp, min temp, time
ROW = [4.23, 0.0, 100.0, 4.314, 4.063, 33.0, 32.0, 0.0]


def _session(folder, name: str, **fields: Any) -> None:
    rows = [[*ROW[:7], i * 10.0] for i in range(128)]
    (folder / f"{name}.json").write_text(
        json.dumps({"readings": rows, **fields}), encoding="utf-8"
    )


@pytest.fixture
def demo_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(bm, "DEMO_DIR", tmp_path)
    return tmp_path


def _fake_model(monkeypatch, probability: float, sensitivity: dict[str, float]) -> None:
    def fake_predict(readings, dataset=None, include_attention=False):
        return {
            "capacity": 41.0,
            "soh_percent": 93.5,
            "fault_probability": probability,
            "fault_probability_experimental": True,
            "model_name": "fake",
            "normalisation": "per_dataset",
        }

    def fake_explain(readings, dataset=None, include_attention=False):
        return {
            "fault_probability": probability,
            "channel_sensitivity": sensitivity,
            "top_attention_rows": [3, 1, 2, 0, 4],
        }

    monkeypatch.setattr(bm, "predict", fake_predict)
    monkeypatch.setattr(bm, "explain", fake_explain)


SENSITIVITY = {
    "voltage": 0.0,
    "current": 0.0,
    "SOC": 0.004,
    "max_cell_v": 0.984,
    "min_cell_v": 0.31,
    "max_temp": 0.02,
    "min_temp": 0.0,
    "time": 0.0,
}


# ---- pure helpers ----------------------------------------------------------

def test_observed_signals_reports_the_cell_voltage_gap():
    obs = bm.observed_signals([ROW] * 128)
    assert obs["state"] == "idle"
    assert obs["cell_voltage_spread_mv"] == 251
    assert obs["highest_cell_v"] == 4.314 and obs["lowest_cell_v"] == 4.063
    assert obs["soc_start_percent"] == 100 == obs["soc_end_percent"]


def test_observed_signals_detects_charging_from_negative_current():
    rows = [[4.0, -20.0, 50.0, 4.0, 3.99, 30.0, 28.0, i * 10.0] for i in range(128)]
    obs = bm.observed_signals(rows)
    assert obs["state"] == "charging" and obs["mean_current_a"] == -20
    assert obs["session_minutes"] == pytest.approx(21.2, abs=0.1)


def test_observed_signals_rejects_wrong_shape():
    with pytest.raises(ValueError):
        bm.observed_signals([ROW] * 5)


def test_reasons_are_ranked_capped_and_skip_tiny_effects():
    reasons = bm.build_reasons(SENSITIVITY, bm.observed_signals([ROW] * 128))
    assert [r["channel"] for r in reasons] == ["max_cell_v", "min_cell_v", "max_temp"]
    assert reasons[0]["effect_points"] == 98
    assert reasons[0]["label"] == "Highest cell voltage"
    assert "251 mV" in reasons[0]["detail"]
    assert "98 points" in reasons[0]["detail"]
    assert all(r["channel"] != "SOC" for r in reasons)  # 0.004 is below the minimum effect


def test_no_reasons_when_nothing_moves_the_score():
    quiet = dict.fromkeys(bm.DEFAULT_CHANNELS, 0.001)
    assert bm.build_reasons(quiet, bm.observed_signals([ROW] * 128)) == []


def test_risk_level_uses_the_display_threshold():
    assert bm.risk_level(0.5, 0.5) == "elevated"
    assert bm.risk_level(0.49, 0.5) == "low"


def test_context_note_flags_disagreement_with_the_dataset_label():
    assert "whole vehicle" in bm.context_note("low", 1)
    assert "experimental" in bm.context_note("elevated", 0)
    assert bm.context_note("elevated", 1) is None
    assert bm.context_note("low", 0) is None
    assert bm.context_note("low", None) is None


@pytest.mark.skipif(not REAL_FAULTY.is_file(), reason="demo file not present")
def test_real_faulty_car_shows_the_large_cell_voltage_gap():
    obs = bm.observed_signals(json.loads(REAL_FAULTY.read_text())["readings"])
    assert obs["cell_voltage_spread_mv"] == 251


# ---- orchestration and route -----------------------------------------------

def test_explain_demo_session_combines_prediction_and_reasons(demo_dir, monkeypatch):
    _session(demo_dir, "faulty_3_515", title="Faulty car 3_515", dataset=3, true_label=1)
    _fake_model(monkeypatch, 0.99, SENSITIVITY)
    result = bm.explain_demo_session("faulty_3_515", alert_probability=0.5)
    assert result["risk_level"] == "elevated"
    assert result["headline"] == "Elevated fault risk"
    assert result["soh_percent"] == 93.5 and result["true_label"] == 1
    assert result["reasons"][0]["channel"] == "max_cell_v"
    assert result["top_attention_rows"] == [3, 1, 2, 0, 4]
    assert result["top_attention_seconds"] == [30.0, 10.0, 20.0, 0.0, 40.0]
    assert result["context_note"] is None


def test_route_returns_the_explanation(demo_dir, monkeypatch):
    _session(demo_dir, "faulty_3_515", title="Faulty car 3_515", dataset=3, true_label=1)
    _fake_model(monkeypatch, 0.99, SENSITIVITY)
    response = client.get("/battery/demo-sessions/faulty_3_515/explain")
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "elevated" and body["alert_probability"] == 0.5
    assert body["fault_probability_experimental"] is True
    assert body["reasons"][0]["effect_points"] == 98
    assert body["observed"]["cell_voltage_spread_mv"] == 251
    assert "not proof" in body["note"]


def test_route_explains_a_low_score_on_a_faulty_labelled_car(demo_dir, monkeypatch):
    _session(demo_dir, "faulty_ds1_a", title="Faulty car", dataset=1, true_label=1)
    _fake_model(monkeypatch, 0.08, {**SENSITIVITY, "max_cell_v": 0.03})
    body = client.get("/battery/demo-sessions/faulty_ds1_a/explain").json()
    assert body["risk_level"] == "low" and body["headline"] == "Low fault risk"
    assert "whole vehicle" in body["context_note"]


def test_route_unknown_session_is_404(demo_dir):
    response = client.get("/battery/demo-sessions/nope/explain")
    assert response.status_code == 404


def test_route_without_a_model_is_503(demo_dir, monkeypatch):
    _session(demo_dir, "faulty_ds1_a", title="Faulty car", dataset=1, true_label=1)

    def unavailable(*args, **kwargs):
        raise ModelUnavailable("no weights")

    monkeypatch.setattr(bm, "predict", unavailable)
    response = client.get("/battery/demo-sessions/faulty_ds1_a/explain")
    assert response.status_code == 503