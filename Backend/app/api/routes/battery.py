"""Battery health prediction, explanation and remaining-useful-life endpoints."""

import re

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.battery import (
    BatteryDemoPrediction,
    BatteryPrediction,
    ChargingSessionInput,
    DemoExplanation,
    DemoSessionInfo,
    ExplanationResult,
    ModelInfo,
    RulEstimate,
    RulRequest,
)
from app.services import battery_model, rul

router = APIRouter(prefix="/battery", tags=["battery"])

_CAR_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


@router.post("/predict", response_model=BatteryPrediction)
async def predict_battery_health(payload: ChargingSessionInput) -> BatteryPrediction:
    """Runs one charging session through the trained model.

    Capacity and State of Health are estimates. `fault_probability` is an
    experimental risk score, not a diagnosis. Send real sensor sessions only:
    simulated readings can fall outside the range the model was trained on.
    """
    result = battery_model.predict(
        payload.readings,
        dataset=payload.dataset,
        include_attention=payload.include_attention,
    )
    return BatteryPrediction(**result)


@router.post("/explain", response_model=ExplanationResult)
async def explain_battery_prediction(payload: ChargingSessionInput) -> ExplanationResult:
    """Where the model looked and which sensors its fault score reacts to (one session)."""
    result = battery_model.explain(
        payload.readings,
        dataset=payload.dataset,
        include_attention=payload.include_attention,
    )
    return ExplanationResult(**result)


@router.get("/model-info", response_model=ModelInfo)
async def get_model_info() -> ModelInfo:
    """Reports the deployed model and whether it loaded. Never errors."""
    return ModelInfo(**battery_model.model_info())


def _predict_demo(session_id: str) -> BatteryDemoPrediction:
    session = battery_model.load_demo_session(session_id)
    result = battery_model.predict(session["readings"], dataset=session["dataset"])
    source = (
        "bundled sample charging session"
        if session["id"] == battery_model.SAMPLE_SESSION_ID
        else "recorded demo session"
    )
    return BatteryDemoPrediction(
        **result,
        source=source,
        session_id=session["id"],
        title=session["title"],
        dataset=session["dataset"],
        true_label=session["true_label"],
    )


@router.get("/demo", response_model=BatteryDemoPrediction)
async def predict_demo_session() -> BatteryDemoPrediction:
    """Predicts the bundled sample session (the first demo session)."""
    return _predict_demo(battery_model.SAMPLE_SESSION_ID)


@router.get("/demo-sessions", response_model=list[DemoSessionInfo])
async def list_demo_sessions() -> list[DemoSessionInfo]:
    """Lists the sessions available for demos: the sample plus any files in
    `app/ml_models/demo/` (healthy and faulty cars exported from the notebook)."""
    return [DemoSessionInfo(**s) for s in battery_model.list_demo_sessions()]


@router.get("/demo-sessions/{session_id}", response_model=BatteryDemoPrediction)
async def predict_demo_session_by_id(session_id: str) -> BatteryDemoPrediction:
    """Predicts one demo session. `true_label` is the dataset's label, not the model's."""
    return _predict_demo(session_id)


@router.get("/demo-sessions/{session_id}/explain", response_model=DemoExplanation)
async def explain_demo_session(session_id: str) -> DemoExplanation:
    """Prediction plus a plain-language explanation for one recorded demo session.

    Lists the sensors the fault score reacts to most, with measured facts from the
    session (for example the gap between the highest and lowest cell voltage).
    `risk_level` compares the experimental fault score with `FAULT_ALERT_PROBABILITY`;
    it is a display band, not a diagnosis.
    """
    settings = get_settings()
    return DemoExplanation(
        **battery_model.explain_demo_session(session_id, settings.fault_alert_probability)
    )


@router.post("/rul", response_model=RulEstimate)
async def estimate_remaining_life(payload: RulRequest) -> RulEstimate:
    """Remaining useful life from a car's own State of Health history.

    A straight line through the (mileage, SoH) points, extended to the threshold
    SoH. It does not use the neural network. Needs at least 5 points.
    """
    settings = get_settings()
    config = battery_model.get_config()
    try:
        result = rul.fit_rul(
            [point.mileage_km for point in payload.history],
            [point.soh_percent for point in payload.history],
            threshold_soh=config.rul_threshold_soh,
            cap_km=settings.rul_cap_km,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RulEstimate(**result)


@router.get("/rul/{car_id}", response_model=RulEstimate)
async def get_precomputed_remaining_life(car_id: str) -> RulEstimate:
    """The per-car estimate the training notebook computed (`rul_estimates.csv`).

    Car ids look like `1_105` (dataset, car). Cars with fewer than 5 sessions or
    a SoH that is not falling have no entry.
    """
    if not _CAR_ID_RE.fullmatch(car_id):
        raise HTTPException(status_code=422, detail="Invalid car id.")
    settings = get_settings()
    config = battery_model.get_config()
    result = rul.lookup_precomputed(
        car_id,
        battery_model.ML_DIR / settings.rul_file,
        threshold_soh=config.rul_threshold_soh,
        cap_km=settings.rul_cap_km,
    )
    return RulEstimate(**result)