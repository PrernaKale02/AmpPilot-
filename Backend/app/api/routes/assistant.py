"""Voice-assistant endpoint: a text question in, a short spoken-style reply out."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.assistant import ask_assistant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["assistant"])


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)


class AssistantResponse(BaseModel):
    reply: str
    action: str | None = None


@router.post("/assistant", response_model=AssistantResponse, summary="Ask the AmpPilot assistant")
async def ask(request: AssistantRequest) -> AssistantResponse:
    try:
        reply, action = await ask_assistant(request.message, request.latitude, request.longitude)
    except Exception as exc:
        logger.exception("Assistant request failed")
        raise HTTPException(status_code=502, detail="The assistant is unavailable right now.") from exc
    return AssistantResponse(reply=reply, action=action)
