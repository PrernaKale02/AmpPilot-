"""Demo sessions: listing, loading, id safety and the routes (no torch needed)."""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import DemoSessionNotFound, ModelUnavailable
from app.main import app
from app.services import battery_model as bm

client = TestClient(app)
ROW = [4.1, -6.4, 92.2, 4.11, 4.09, 12.0, 10.0, 0.0]


def _write_session(folder, name: str, **fields: Any) -> None:
    data = {"readings": [ROW] * 128, **fields}
    (folder / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def demo_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(bm, "DEMO_DIR", tmp_path)
    return tmp_path


def test_list_starts_with_the_sample_then_demo_files(demo_dir):
    _write_session(demo_dir, "faulty_ds3_a", title="Faulty car (dataset 3)", dataset=3, true_label=1)
    _write_session(demo_dir, "healthy_ds1_a", title="Healthy car (dataset 1)", dataset=1, true_label=0)
    sessions = bm.list_demo_sessions()
    assert [s["id"] for s in sessions] == ["sample_session", "faulty_ds3_a", "healthy_ds1_a"]
    assert all("readings" not in s for s in sessions)
    assert sessions[1]["true_label"] == 1 and sessions[1]["dataset"] == 3
    assert sessions[0]["true_label"] is None  # the bundled sample has no label


def test_list_skips_invalid_files(demo_dir):
    (demo_dir / "broken.json").write_text("{nope", encoding="utf-8")
    (demo_dir / "short.json").write_text(json.dumps({"readings": [ROW] * 5}), encoding="utf-8")
    assert [s["id"] for s in bm.list_demo_sessions()] == ["sample_session"]


def test_load_returns_readings_and_labels(demo_dir):
    _write_session(demo_dir, "faulty_ds1_a", dataset=1, true_label=1)
    session = bm.load_demo_session("faulty_ds1_a")
    assert len(session["readings"]) == 128
    assert session["dataset"] == 1 and session["true_label"] == 1


def test_load_ignores_out_of_range_labels(demo_dir):
    _write_session(demo_dir, "odd", dataset=9, true_label=5)
    session = bm.load_demo_session("odd")
    assert session["dataset"] is None and session["true_label"] is None


@pytest.mark.parametrize("bad_id", ["../etc/passwd", "a/b", "..", "x.json", "", "a b", "é"])
def test_load_rejects_unsafe_ids(demo_dir, bad_id):
    with pytest.raises(DemoSessionNotFound):
        bm.load_demo_session(bad_id)


def test_load_unknown_id(demo_dir):
    with pytest.raises(DemoSessionNotFound):
        bm.load_demo_session("nope")


def test_load_rejects_invalid_readings(demo_dir):
    bad_rows = [ROW] * 127 + [ROW[:7]]
    (demo_dir / "bad.json").write_text(json.dumps({"readings": bad_rows}), encoding="utf-8")
    with pytest.raises(ModelUnavailable):
        bm.load_demo_session("bad")


# ---- routes ----------------------------------------------------------------

@pytest.fixture
def fake_predict(monkeypatch):
    calls: list[dict[str, Any]] = []

    def fake(readings, dataset=None, include_attention=False):
        calls.append({"rows": len(readings), "dataset": dataset})
        return {
            "capacity": 41.0, "soh_percent": 94.0, "fault_probability": 0.4,
            "fault_probability_experimental": True, "model_name": "fake",
            "normalisation": "per_dataset" if dataset else "global",
        }

    monkeypatch.setattr(bm, "predict", fake)
    return calls


def test_demo_sessions_route_lists(demo_dir):
    _write_session(demo_dir, "faulty_ds3_a", title="Faulty", dataset=3, true_label=1)
    response = client.get("/battery/demo-sessions")
    assert response.status_code == 200
    ids = [s["id"] for s in response.json()]
    assert ids == ["sample_session", "faulty_ds3_a"]


def test_demo_session_route_predicts_with_the_sessions_dataset(demo_dir, fake_predict):
    _write_session(demo_dir, "faulty_ds3_a", title="Faulty car", dataset=3, true_label=1)
    response = client.get("/battery/demo-sessions/faulty_ds3_a")
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "faulty_ds3_a"
    assert body["true_label"] == 1 and body["dataset"] == 3
    assert body["normalisation"] == "per_dataset"
    assert fake_predict == [{"rows": 128, "dataset": 3}]


def test_demo_session_route_404_for_unknown_id(demo_dir, fake_predict):
    response = client.get("/battery/demo-sessions/does_not_exist")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DEMO_SESSION_NOT_FOUND"
    assert fake_predict == []


def test_demo_session_route_503_when_model_missing(demo_dir, monkeypatch):
    _write_session(demo_dir, "healthy_ds1_a", dataset=1, true_label=0)

    def boom(*args, **kwargs):
        raise ModelUnavailable("missing")

    monkeypatch.setattr(bm, "predict", boom)
    assert client.get("/battery/demo-sessions/healthy_ds1_a").status_code == 503