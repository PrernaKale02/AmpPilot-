"""Battery health prediction endpoints."""

from fastapi import APIRouter

from app.schemas.battery import BatteryPrediction, ChargingSessionInput
from app.services import battery_model

router = APIRouter(prefix="/battery", tags=["battery"])


@router.post("/predict", response_model=BatteryPrediction)
async def predict_battery_health(payload: ChargingSessionInput) -> BatteryPrediction:
    """Runs one charging session through the trained model."""
    result = battery_model.predict(payload.readings)
    return BatteryPrediction(**result)