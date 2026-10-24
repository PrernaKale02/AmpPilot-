"""Voice-assistant endpoints: a text or recorded question in, a short spoken-style reply out."""

import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.assistant import ask_assistant, transcribe_audio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["assistant"])

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # about 10 MB, far more than a spoken question
AUDIO_TYPES = {
    ".m4a": "audio/mp4",  # what iOS/Android record by default
    ".mp4": "audio/mp4",
    ".aac": "audio/aac",
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
}


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)


class AssistantResponse(BaseModel):
    reply: str
    action: str | None = None


class VoiceAssistantResponse(AssistantResponse):
    transcript: str


@router.post("/assistant", response_model=AssistantResponse, summary="Ask the AmpPilot assistant")
async def ask(request: AssistantRequest) -> AssistantResponse:
    try:
        reply, action = await ask_assistant(request.message, request.latitude, request.longitude)
    except Exception as exc:
        logger.exception("Assistant request failed")
        raise HTTPException(status_code=502, detail="The assistant is unavailable right now.") from exc
    return AssistantResponse(reply=reply, action=action)


@router.post(
    "/assistant/voice",
    response_model=VoiceAssistantResponse,
    summary="Ask the AmpPilot assistant with a voice recording",
)
async def ask_by_voice(
    audio: UploadFile = File(...),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
) -> VoiceAssistantResponse:
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="The recording is empty.")
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="The recording is too long.")

    extension = Path(audio.filename or "").suffix.lower()
    content_type = audio.content_type or ""
    mime_type = AUDIO_TYPES.get(extension) or (content_type if content_type.startswith("audio/") else "audio/mp4")

    try:
        transcript = await transcribe_audio(data, mime_type)
        if not transcript:
            return VoiceAssistantResponse(
                transcript="", reply="Sorry, I didn't catch that. Please try again.", action=None
            )
        reply, action = await ask_assistant(transcript, latitude, longitude)
    except Exception as exc:
        logger.exception("Voice assistant request failed")
        raise HTTPException(status_code=502, detail="The assistant is unavailable right now.") from exc
    return VoiceAssistantResponse(transcript=transcript, reply=reply, action=action)