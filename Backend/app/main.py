"""AmpPilot backend entrypoint: app construction and wiring only.

No business logic lives here. Routers own their endpoints, services own their
I/O, and this module assembles them and maps domain errors onto HTTP.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import battery, charging
from app.core.config import get_settings
from app.core.exceptions import (
    AmpPilotError,
    UpstreamError,
    UpstreamNotConfigured,
    UpstreamTimeout,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="AmpPilot API",
    version="0.2.0",
    summary="Backend for the AmpPilot EV companion app.",
)

# React Native on iOS/Android is not a browser and does not enforce CORS, so
# this exists only for Expo Web (`npm run web`) and browser tooling such as
# Swagger UI. Origins come from CORS_ALLOW_ORIGINS; when that is empty the
# middleware is not installed at all, which is the right default for a
# native-only deployment.
allowed_origins = settings.cors_allow_origins_list
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

app.include_router(charging.router)
app.include_router(battery.router)

#: Domain error -> (HTTP status, stable code, message safe to show a user).
#: Ordered most-specific first; `UpstreamTimeout` subclasses `UpstreamError`.
_ERROR_MAP: tuple[tuple[type[AmpPilotError], int, str, str], ...] = (
    (
        UpstreamNotConfigured,
        503,
        "PROVIDER_NOT_CONFIGURED",
        "Charging station lookup is not configured on the server.",
    ),
    (
        UpstreamTimeout,
        504,
        "UPSTREAM_TIMEOUT",
        "The charging station provider took too long to respond.",
    ),
    (
        UpstreamError,
        502,
        "UPSTREAM_ERROR",
        "The charging station provider could not be reached.",
    ),
)


@app.exception_handler(AmpPilotError)
async def handle_amppilot_error(request: Request, exc: AmpPilotError) -> JSONResponse:
    """Turns a domain error into the API's error envelope.

    The response carries a stable code and a generic message only. The
    exception's own text stays server-side: upstream detail can embed request
    parameters, and an API key must never reach a client.
    """
    for error_type, status_code, code, message in _ERROR_MAP:
        if isinstance(exc, error_type):
            logger.error("%s -> HTTP %s: %s", type(exc).__name__, status_code, exc)
            return JSONResponse(
                status_code=status_code,
                content={"detail": {"code": code, "message": message}},
            )

    logger.exception("Unhandled AmpPilotError")
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "INTERNAL_ERROR", "message": "Something went wrong."}},
    )


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness probe. Touches no external service and needs no API key."""
    return {"status": "ok"}
