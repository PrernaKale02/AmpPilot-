"""AmpPilot backend entrypoint: app construction and wiring only.

No business logic lives here. Routers own their endpoints, services own their
I/O, and this module assembles them and maps domain errors onto HTTP.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import assistant, battery, charging, simulation
from app.core.config import get_settings
from app.core.exceptions import (
    AmpPilotError,
    DemoSessionNotFound,
    ModelUnavailable,
    RulNotFound,
    UpstreamError,
    UpstreamNotConfigured,
    UpstreamTimeout,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Warms the battery model in the background; the API serves while it loads."""
    from app.services import battery_model  # noqa: PLC0415 - keeps import order simple

    warm_up_task = asyncio.create_task(asyncio.to_thread(battery_model.warm_up))
    try:
        yield
    finally:
        warm_up_task.cancel()


app = FastAPI(
    title="AmpPilot API",
    version="0.2.0",
    summary="Backend for the AmpPilot EV companion app.",
    lifespan=lifespan,
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
app.include_router(simulation.router)
app.include_router(assistant.router)

#: Domain error -> (HTTP status, stable code, message safe to show a user).
#: Ordered most-specific first; `UpstreamTimeout` subclasses `UpstreamError`.
_ERROR_MAP: tuple[tuple[type[AmpPilotError], int, str, str], ...] = (
    (
        RulNotFound,
        404,
        "RUL_NOT_FOUND",
        "No remaining-life estimate is available for that car.",
    ),
    (
        DemoSessionNotFound,
        404,
        "DEMO_SESSION_NOT_FOUND",
        "That demo session does not exist.",
    ),
    (
        ModelUnavailable,
        503,
        "MODEL_UNAVAILABLE",
        "The battery health model is not available on the server.",
    ),
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


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 with FastAPI's usual `detail` list, minus the echoed request input.

    The default handler copies each offending value back into the body. A NaN
    or infinite number cannot be encoded as JSON, so a bad payload would turn
    into a 500 instead of a 422 (and large payloads would be echoed in full).
    """
    errors = [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    if request.url.path.startswith("/api/assistant"):
        logger.warning(
            "AI voice assistant request validation failed",
            extra={"assistant_stage": "request_validation", "path": request.url.path},
        )
    return JSONResponse(status_code=422, content={"detail": errors})


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