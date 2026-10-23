"""AmpPilot voice-assistant brain.

Gemini interprets the question and may *request* a tool; this module runs the
tool against AmpPilot's own data and returns the result. Gemini never reads
data or controls anything directly.
"""

import logging

from google import genai
from google.genai import types

from app.api.routes.charging import get_nearby_charging_stations
from app.core.config import get_settings
from app.services.simulation import simulation_service

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3

SYSTEM_INSTRUCTION = (
    "You are AmpPilot, the voice assistant in an EV battery app. "
    "Your answers are spoken aloud: reply in one or two short sentences, plain text, "
    "no markdown or lists. Reply in the language the user used "
    "(English, Hindi or Marathi). "
    "For any battery reading or charging station, call a tool; never guess numbers. "
    "Battery readings come from a simulation, not a real vehicle; say so if asked. "
    "If a tool returns an error, briefly say that information is unavailable."
)

TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_battery_status",
            description=(
                "Current simulated battery readings: state of charge (%), voltage, "
                "current, temperature, charging/discharging direction and "
                "normal/warning/critical status."
            ),
        ),
        types.FunctionDeclaration(
            name="find_nearby_charging_stations",
            description=(
                "EV charging stations nearest the user's current location, nearest "
                "first. Use for any question about chargers or where to charge. "
                "Calling this also opens the station map in the app."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "radius_km": types.Schema(
                        type=types.Type.NUMBER,
                        description="Search radius in km (default 10, max 50).",
                    )
                },
            ),
        ),
    ]
)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        key = (get_settings().gemini_api_key or "").strip()
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set in Backend/.env.")
        _client = genai.Client(api_key=key)
    return _client


def _battery_status() -> dict:
    status = simulation_service.status()
    telemetry = status.latest_telemetry
    if telemetry is None:
        return {"available": False, "reason": "No simulation session has produced readings yet."}
    return {"available": True, "session": status.status, **telemetry.model_dump()}


async def _nearby_stations(latitude, longitude, radius_km) -> dict:
    if latitude is None or longitude is None:
        return {"error": "The app did not send the user's location."}
    radius = min(max(float(radius_km or 10), 1.0), 50.0)
    try:
        result = await get_nearby_charging_stations(
            latitude=latitude, longitude=longitude, radius_km=radius
        )
    except Exception as exc:
        logger.warning("Assistant station lookup failed: %s", exc)
        return {"error": "Charging station lookup is unavailable right now."}
    nearest = [
        station.model_dump(include={"name", "distance_km", "status"})
        for station in result.stations[:3]
    ]
    return {"radius_km": radius, "count": len(result.stations), "nearest": nearest}


async def ask_assistant(message: str, latitude=None, longitude=None) -> tuple[str, str | None]:
    """Returns (spoken reply, optional app action such as 'show_stations')."""
    client = _get_client()
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[TOOLS],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=message)])]
    action = None

    for _ in range(MAX_TOOL_ROUNDS):
        response = await client.aio.models.generate_content(
            model=get_settings().gemini_model, contents=contents, config=config
        )
        calls = response.function_calls or []
        if not calls:
            return (response.text or "Sorry, I couldn't answer that.").strip(), action

        contents.append(response.candidates[0].content)
        parts = []
        for call in calls:
            args = dict(call.args or {})
            if call.name == "get_battery_status":
                result = _battery_status()
            elif call.name == "find_nearby_charging_stations":
                result = await _nearby_stations(latitude, longitude, args.get("radius_km"))
                if "error" not in result:
                    action = "show_stations"
            else:
                result = {"error": f"Unknown tool {call.name}."}
            parts.append(types.Part.from_function_response(name=call.name, response=result))
        contents.append(types.Content(role="user", parts=parts))

    return "Sorry, that took too many steps. Please try again.", action