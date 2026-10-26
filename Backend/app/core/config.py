"""Application settings, read once from the environment and `Backend/.env`.

The Open Charge Map key is optional *as a field* so the app still boots (and
`/health` still answers) without it, but it is never faked or defaulted.
`require_open_charge_map_api_key()` is the only way to read it and raises
`UpstreamNotConfigured` when it is absent, which the HTTP layer turns into a
503 on the charging endpoint alone.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import UpstreamNotConfigured

# app/core/config.py -> app/core -> app -> Backend
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables or `.env`."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    open_charge_map_api_key: str | None = None
    open_charge_map_timeout_seconds: float = 6.0
    open_charge_map_max_results: int = 50
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_fallback_models: str = "gemini-3.8-flash,gemini-3.7-flash"

    # Kept as a raw string rather than `list[str]`: pydantic-settings parses
    # complex field types out of the environment with `json.loads`, so a plain
    # comma-separated value would raise before any validator could split it.
    cors_allow_origins: str = ""

    environment: Literal["development", "production"] = "development"

    # Battery health model files, resolved inside app/ml_models/. To deploy a
    # different trained model, drop its .pt and the exported config next to the
    # old ones and point these at them (no code change needed).
    model_weights_file: str = "final_model.pt"
    model_config_file: str = "model_config.json"

    # Remaining useful life (RUL). The precomputed per-car table written by the
    # training notebook, and the largest RUL the API will report. Linear
    # extrapolation of a nearly flat SoH trend gives absurd numbers, so larger
    # values are cut to the cap and flagged `capped`.
    rul_file: str = "rul_estimates.csv"
    rul_cap_km: float = 500_000.0

    # Display band for the experimental fault score. At or above this value the
    # app shows "elevated fault risk" and opens the explanation by default.
    # It is a presentation choice, not a diagnosis threshold: the notebook's
    # validation threshold (about 0.012) flags almost every session.
    fault_alert_probability: float = 0.5

    @property
    def cors_allow_origins_list(self) -> list[str]:
        """`CORS_ALLOW_ORIGINS` split into origins, blanks discarded."""
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    def require_open_charge_map_api_key(self) -> str:
        """Returns the Open Charge Map API key, or raises if it is not set.

        :raises UpstreamNotConfigured: when the key is unset or blank.
        """
        key = (self.open_charge_map_api_key or "").strip()
        if not key:
            raise UpstreamNotConfigured(
                "OPEN_CHARGE_MAP_API_KEY is not set. Copy Backend/.env.example "
                "to Backend/.env and add a key from openchargemap.org."
            )
        return key


@lru_cache
def get_settings() -> Settings:
    """Returns the process-wide settings, parsed on first use."""
    return Settings()