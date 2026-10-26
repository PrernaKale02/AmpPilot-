"""Plain-language assessment built from the model's outputs (pure functions)."""

import pytest

from app.services import analysis


def _prediction(p=0.9):
    return {"soh_percent": 94.2, "capacity": 37.38, "fault_probability": p,
            "normalisation": "per_dataset", "model_name": "bilstm_no_mfg_v2"}


def _explanation(**shifts):
    base = {"voltage": 0.0018, "current": 0.003, "SOC": 0.0048, "max_cell_v": 0.0,
            "min_cell_v": 0.0024, "max_temp": 0.0, "min_temp": 0.0027, "time": 0.0}
    base.update(shifts)
    return {"channel_sensitivity": base, "top_attention_rows": [3, 0, 1, 2, 4]}


@pytest.mark.parametrize(
    ("probability", "level"),
    [(0.0, "low"), (0.249, "low"), (0.25, "moderate"), (0.499, "moderate"), (0.5, "high"), (1.0, "high")],
)
def test_risk_bands(probability, level):
    assert analysis.risk_level(probability) == level


def test_high_risk_explains_the_dominant_channel():
    out = analysis.build_analysis(_prediction(1.0), _explanation(max_cell_v=0.984), 10.0)
    assert out["risk_level"] == "high" and out["headline"] == "Elevated fault risk"
    assert out["top_channels"] == [
        {"channel": "max_cell_v", "label": "highest cell voltage", "sensitivity": 0.984}
    ]
    assert out["reasons"][0].startswith("The fault score reacts most to the highest cell voltage")
    assert "0.98" in out["reasons"][0]
    assert len(out["reasons"]) == 1   # the other channels are far below the 0.05 floor


def test_up_to_three_channels_are_named_in_order():
    out = analysis.build_analysis(
        _prediction(), _explanation(max_cell_v=0.6, min_cell_v=0.3, voltage=0.1, current=0.07), 10.0
    )
    assert [c["channel"] for c in out["top_channels"]] == ["max_cell_v", "min_cell_v", "voltage"]
    assert out["reasons"][1].startswith("It also reacts to the lowest cell voltage")


def test_no_stand_out_channel_is_said_plainly():
    out = analysis.build_analysis(_prediction(0.1), _explanation(), 10.0)
    assert out["risk_level"] == "low" and out["top_channels"] == []
    assert out["reasons"] == ["No single sensor channel stands out for this session."]


def test_attention_summary_uses_the_time_step_length():
    out = analysis.build_analysis(_prediction(), _explanation(), 10.0)
    assert out["attention_summary"] == (
        "The model paid most attention to time steps 0, 1, 2, 3, 4 (about 0 to 40 s into the session)."
    )
    assert analysis.build_analysis(_prediction(), {**_explanation(), "top_attention_rows": None}, 10.0)[
        "attention_summary"
    ] is None


def test_unknown_channel_names_fall_back_to_the_raw_name():
    out = analysis.build_analysis(_prediction(), {"channel_sensitivity": {"mystery": 0.9}}, 10.0)
    assert out["top_channels"][0]["label"] == "mystery"


def test_the_note_never_claims_a_diagnosis_or_a_cause():
    note = analysis.build_analysis(_prediction(), _explanation(), 10.0)["note"]
    assert "not a diagnosis" in note and "not proof" in note