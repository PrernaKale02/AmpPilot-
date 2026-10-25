"""Route tests for /battery/*. The model is replaced, so no torch or weights."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import ModelUnavailable
from app.main import app
from app.services import battery_model

client = TestClient(app)

ROW = [4.1, -6.4, 92.2, 4.11, 4.09, 12.0, 10.0, 0.0]
PAYLOAD = {"readings": [ROW] * 128}

FAKE_RESULT = {
    "capacity": 41.2,
    "soh_percent": 95.1,
    "fault_probability": 0.123,
    "fault_probability_experimental": True,
    "model_name": "fake",
    "normalisation": "global",
}


@pytest.fixture
def fake_predict(monkeypatch):
    calls: list[dict[str, Any]] = []

    def fake(readings, dataset=None, include_attention=False):
        calls.append({"rows": len(readings), "dataset": dataset, "attention": include_attention})
        result = dict(FAKE_RESULT)
        if include_attention:
            result["attention_weights"] = [1 / 128] * 128
            result["top_attention_rows"] = [0, 1, 2, 3, 4]
        if dataset is not None:
            result["normalisation"] = "per_dataset"
        return result

    monkeypatch.setattr(battery_model, "predict", fake)
    return calls


def test_predict_returns_prediction(fake_predict):
    response = client.post("/battery/predict", json=PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["soh_percent"] == 95.1
    assert body["fault_probability"] == 0.123
    assert body["fault_probability_experimental"] is True
    assert "is_faulty" not in body and "fault_threshold" not in body
    assert body["attention_weights"] is None
    assert fake_predict == [{"rows": 128, "dataset": None, "attention": False}]


def test_predict_accepts_the_approximate_normalisation_mode(monkeypatch):
    def fake(readings, dataset=None, include_attention=False):
        return {**FAKE_RESULT, "normalisation": "approximate"}

    monkeypatch.setattr(battery_model, "predict", fake)
    response = client.post("/battery/predict", json=PAYLOAD)
    assert response.status_code == 200
    assert response.json()["normalisation"] == "approximate"


def test_predict_passes_dataset_and_attention_options(fake_predict):
    response = client.post(
        "/battery/predict", json={**PAYLOAD, "dataset": 3, "include_attention": True}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["normalisation"] == "per_dataset"
    assert len(body["attention_weights"]) == 128
    assert body["top_attention_rows"] == [0, 1, 2, 3, 4]
    assert fake_predict == [{"rows": 128, "dataset": 3, "attention": True}]


@pytest.mark.parametrize(
    "payload",
    [
        {"readings": [ROW] * 127},
        {"readings": [ROW] * 129},
        {"readings": [ROW[:7]] * 128},
        {"readings": [ROW] * 127 + [ROW + [1.0]]},
        {"readings": [ROW] * 128, "dataset": 4},
        {},
    ],
)
def test_predict_rejects_bad_payloads(fake_predict, payload):
    assert client.post("/battery/predict", json=payload).status_code == 422
    assert fake_predict == []


def test_predict_rejects_nan_values(fake_predict):
    row = "[NaN, -6.4, 92.2, 4.11, 4.09, 12.0, 10.0, 0.0]"
    body = '{"readings": [' + ",".join([row] + ["[4.1,-6.4,92.2,4.11,4.09,12,10,0]"] * 127) + "]}"
    response = client.post(
        "/battery/predict", content=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert fake_predict == []


def test_predict_returns_503_when_model_is_unavailable(monkeypatch):
    def boom(*args, **kwargs):
        raise ModelUnavailable("Model weights not found: /secret/server/path.pt")

    monkeypatch.setattr(battery_model, "predict", boom)
    response = client.post("/battery/predict", json=PAYLOAD)
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["code"] == "MODEL_UNAVAILABLE"
    assert "/secret/server/path.pt" not in response.text  # no server paths leak


def test_demo_predicts_the_bundled_session(fake_predict):
    response = client.get("/battery/demo")
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "bundled sample charging session"
    assert body["soh_percent"] == 95.1
    assert fake_predict == [{"rows": 128, "dataset": None, "attention": False}]


def test_demo_returns_503_when_model_is_unavailable(monkeypatch):
    def boom(*args, **kwargs):
        raise ModelUnavailable("missing")

    monkeypatch.setattr(battery_model, "predict", boom)
    assert client.get("/battery/demo").status_code == 503


def test_model_info_reports_without_raising(monkeypatch):
    monkeypatch.setattr(
        battery_model,
        "model_info",
        lambda: {
            "loaded": False,
            "model_name": "m",
            "fault_threshold": 0.5,
            "per_dataset_normalisation": False,
            "weights_file": "m.pt",
            "detail": "Weights file not found on the server.",
        },
    )
    response = client.get("/battery/model-info")
    assert response.status_code == 200
    assert response.json()["loaded"] is False


def test_real_service_reports_missing_weights_instead_of_crashing(tmp_path, monkeypatch):
    """Without the .pt file the service answers 503; the app still boots."""
    from app.core import config

    monkeypatch.setenv("MODEL_WEIGHTS_FILE", "definitely_missing.pt")
    config.get_settings.cache_clear()
    battery_model.reset_model_cache()
    try:
        assert client.post("/battery/predict", json=PAYLOAD).status_code == 503
        info = client.get("/battery/model-info").json()
        assert info["loaded"] is False
        assert info["weights_file"] == "definitely_missing.pt"
        assert client.get("/health").json() == {"status": "ok"}
    finally:
        config.get_settings.cache_clear()


def test_app_starts_and_serves_with_the_startup_hook(monkeypatch):
    """The lifespan warm-up must not block or break start-up when weights are missing."""
    from app.core import config

    monkeypatch.setenv("MODEL_WEIGHTS_FILE", "definitely_missing.pt")
    config.get_settings.cache_clear()
    battery_model.reset_model_cache()
    try:
        with TestClient(app) as started:
            assert started.get("/health").json() == {"status": "ok"}
    finally:
        config.get_settings.cache_clear()


# ---- /battery/explain and /battery/rul ------------------------------------------

def test_explain_returns_sensitivity_and_attention(monkeypatch):
    seen = {}

    def fake(readings, dataset=None, include_attention=False):
        seen.update(rows=len(readings), dataset=dataset, attention=include_attention)
        return {
            "fault_probability": 1.0,
            "fault_probability_experimental": True,
            "model_name": "fake",
            "normalisation": "per_dataset",
            "channel_sensitivity": {"max_cell_v": 0.984, "voltage": 0.0018},
            "top_attention_rows": [0, 1, 2, 3, 4],
            "attention_weights": None,
        }

    monkeypatch.setattr(battery_model, "explain", fake)
    response = client.post("/battery/explain", json={**PAYLOAD, "dataset": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["channel_sensitivity"]["max_cell_v"] == 0.984
    assert body["top_attention_rows"] == [0, 1, 2, 3, 4]
    assert "not proof" in body["note"]
    assert seen == {"rows": 128, "dataset": 3, "attention": False}


def test_explain_rejects_bad_payload_and_reports_503(monkeypatch):
    assert client.post("/battery/explain", json={"readings": [ROW] * 5}).status_code == 422

    def boom(*args, **kwargs):
        raise ModelUnavailable("missing")

    monkeypatch.setattr(battery_model, "explain", boom)
    assert client.post("/battery/explain", json=PAYLOAD).status_code == 503


def _history(slope=-1e-4, n=10, start_soh=100.0, step=10_000):
    return [{"mileage_km": i * step, "soh_percent": start_soh + slope * i * step} for i in range(n)]


def test_rul_fit_route_estimates_from_history():
    response = client.post("/battery/rul", json={"history": _history()})
    assert response.status_code == 200
    body = response.json()
    # SoH 100 - 1e-4 * km reaches 80 at 200,000 km; the last point is 90,000 km
    assert body["estimated_rul_km"] == pytest.approx(110_000, abs=1)
    assert body["capped"] is False
    assert body["source"] == "fit"
    assert body["threshold_soh"] == 80.0
    assert body["current_mileage_km"] == 90_000


def test_rul_fit_route_caps_absurd_values():
    response = client.post("/battery/rul", json={"history": _history(slope=-1e-7)})
    body = response.json()
    assert response.status_code == 200
    assert body["capped"] is True
    assert body["estimated_rul_km"] == 500_000


def test_rul_fit_route_with_rising_soh_has_no_estimate():
    body = client.post("/battery/rul", json={"history": _history(slope=1e-4, start_soh=80.0)}).json()
    assert body["estimated_rul_km"] is None
    assert "not decreasing" in body["note"]


@pytest.mark.parametrize(
    "history",
    [
        _history(n=4),
        [{"mileage_km": 1000, "soh_percent": 90 - i} for i in range(6)],  # all the same mileage
        [{"mileage_km": -5, "soh_percent": 90}] * 6,
        [{"mileage_km": 1000 * i, "soh_percent": 140} for i in range(6)],
    ],
)
def test_rul_fit_route_rejects_bad_history(history):
    assert client.post("/battery/rul", json={"history": history}).status_code == 422


def test_rul_precomputed_route(monkeypatch):
    from app.services import rul

    def fake(car_id, path, threshold_soh=80.0, cap_km=500_000.0):
        if car_id == "1_105":
            return {
                "estimated_rul_km": 241_549.7, "capped": False, "current_mileage_km": 172_858.9,
                "current_soh_percent": 92.17, "degradation_soh_per_1000km": -0.047,
                "threshold_soh": threshold_soh, "source": "precomputed", "note": "x",
            }
        from app.core.exceptions import RulNotFound
        raise RulNotFound(car_id)

    monkeypatch.setattr(rul, "lookup_precomputed", fake)
    body = client.get("/battery/rul/1_105").json()
    assert body["source"] == "precomputed" and body["estimated_rul_km"] == 241_549.7
    missing = client.get("/battery/rul/9_999")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "RUL_NOT_FOUND"
    assert client.get("/battery/rul/bad id!").status_code in (404, 422)