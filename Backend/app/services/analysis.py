"""Turns the model's outputs for one session into a plain-language assessment.

Pure functions (no torch): the numbers come from ``battery_model.predict`` and
``battery_model.explain``; this module only decides the display band and words.

Honesty rules baked into the wording:
* The risk band is a display aid, not a diagnosis. Fault labels in the data are
  per vehicle and single-session detection is weak.
* Sensitivities describe how the model behaves on this session. They are not
  proof of the physical cause of a fault.
"""

from __future__ import annotations

from typing import Any

HIGH_RISK = 0.5
MODERATE_RISK = 0.25
MIN_SENSITIVITY = 0.05   # below this a channel is not worth naming
MAX_REASONS = 3

CHANNEL_LABELS = {
    "voltage": "average cell voltage",
    "current": "current",
    "SOC": "state of charge",
    "max_cell_v": "highest cell voltage",
    "min_cell_v": "lowest cell voltage",
    "max_temp": "highest temperature",
    "min_temp": "lowest temperature",
    "time": "elapsed time",
}

HEADLINES = {
    "high": "Elevated fault risk",
    "moderate": "Moderate fault risk",
    "low": "Low fault risk",
}

NOTE = (
    "Risk score from a model that reads one charging session. Faults are labelled per "
    "vehicle, so this is an experimental indicator, not a diagnosis. Sensitivities show how "
    "the model behaves on this session; they are not proof of the physical cause."
)


def risk_level(fault_probability: float) -> str:
    """Display band for a fault probability."""
    if fault_probability >= HIGH_RISK:
        return "high"
    if fault_probability >= MODERATE_RISK:
        return "moderate"
    return "low"


def _attention_summary(rows: list[int] | None, step_seconds: float) -> str | None:
    if not rows:
        return None
    ordered = sorted(rows)
    start, end = ordered[0] * step_seconds, ordered[-1] * step_seconds
    listed = ", ".join(str(row) for row in ordered)
    return (
        f"The model paid most attention to time steps {listed} "
        f"(about {start:.0f} to {end:.0f} s into the session)."
    )


def build_analysis(
    prediction: dict[str, Any], explanation: dict[str, Any], step_seconds: float
) -> dict[str, Any]:
    """Combines a prediction and its explanation into display fields."""
    probability = float(prediction["fault_probability"])
    level = risk_level(probability)

    ranked = sorted(explanation["channel_sensitivity"].items(), key=lambda kv: kv[1], reverse=True)
    top = [(name, value) for name, value in ranked[:MAX_REASONS] if value >= MIN_SENSITIVITY]
    top_channels = [
        {"channel": name, "label": CHANNEL_LABELS.get(name, name), "sensitivity": round(value, 3)}
        for name, value in top
    ]

    reasons: list[str] = []
    for position, item in enumerate(top_channels):
        lead = "The fault score reacts most to" if position == 0 else "It also reacts to"
        reasons.append(
            f"{lead} the {item['label']}: setting it to its normal average moves the score "
            f"by {item['sensitivity']:.2f}."
        )
    if not reasons:
        reasons.append("No single sensor channel stands out for this session.")

    return {
        "soh_percent": prediction["soh_percent"],
        "capacity": prediction["capacity"],
        "fault_probability": probability,
        "risk_level": level,
        "headline": HEADLINES[level],
        "reasons": reasons,
        "top_channels": top_channels,
        "top_attention_rows": explanation.get("top_attention_rows"),
        "attention_summary": _attention_summary(explanation.get("top_attention_rows"), step_seconds),
        "normalisation": prediction.get("normalisation"),
        "model_name": prediction.get("model_name"),
        "note": NOTE,
    }