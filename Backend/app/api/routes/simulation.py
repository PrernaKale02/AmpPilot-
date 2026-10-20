"""Local virtual-EV simulation endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.simulation import SimulationConfig, SimulationStatus
from app.services.simulation import simulation_service

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


def _perform(action: str) -> SimulationStatus:
    try:
        return getattr(simulation_service, action)()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/start", response_model=SimulationStatus)
async def start_simulation(config: SimulationConfig) -> SimulationStatus:
    return simulation_service.start(config)


@router.post("/pause", response_model=SimulationStatus)
async def pause_simulation() -> SimulationStatus:
    return _perform("pause")


@router.post("/resume", response_model=SimulationStatus)
async def resume_simulation() -> SimulationStatus:
    return _perform("resume")


@router.post("/stop", response_model=SimulationStatus)
async def stop_simulation() -> SimulationStatus:
    return simulation_service.stop()


@router.get("/status", response_model=SimulationStatus)
async def get_simulation_status() -> SimulationStatus:
    return simulation_service.status()
