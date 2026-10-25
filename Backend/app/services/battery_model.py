"""Battery health model service.

Everything that depends on *which* trained model is deployed lives in two
files next to this package, in ``app/ml_models/``:

* ``model_config.json``: normalisation constants, target scaling, thresholds.
  Either this repo's own format or the file the v2 training notebook writes
  (``processed_v2/model_config.json``); both load.
* ``models.py``: the network definitions, copied from the notebook so layers
  and checkpoint keys always match.

Swapping in a newly trained model is therefore: drop the new ``.pt``,
``model_config.json`` (and ``models.py`` if the architecture changed) into that
folder and restart. No code change.

Design notes
------------
* ``torch`` is imported lazily, on the first prediction. The API (and the test
  suite) starts without torch or the weights file; the model endpoints then
  answer 503 ``MODEL_UNAVAILABLE`` instead of the whole server failing to boot.
* The pure-numpy parts (``load_config``, ``normalise``, ``finalise``, the
  helpers) never touch torch, so they are unit-tested directly.
* Training normalised each channel with per-dataset (per-manufacturer)
  constants. The model does not receive the manufacturer, so the server can
  only reproduce that exactly if the caller states the dataset (``dataset``
  field). Without it a pooled fallback is used and the response says so
  (``normalisation``): ``"global"`` for constants computed on pooled data,
  ``"approximate"`` when the notebook saved only per-dataset constants and the
  pooled ones are their average.
* The fault output is an experimental risk score. The API deliberately does
  not turn it into a yes/no: single-session fault detection is weak, the
  notebook's validation-chosen threshold flags almost every session, and the
  fault label is a vehicle-level outcome.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import math
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import get_settings
from app.core.exceptions import DemoSessionNotFound, ModelUnavailable

logger = logging.getLogger(__name__)

ML_DIR = Path(__file__).resolve().parent.parent / "ml_models"
MODELS_FILE = ML_DIR / "models.py"
SAMPLE_SESSION_PATH = ML_DIR / "sample_session.json"
DEMO_DIR = ML_DIR / "demo"
SAMPLE_SESSION_ID = "sample_session"
_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

N_STEPS = 128
N_CHANNELS = 8
TOP_ATTENTION_ROWS = 5
DEFAULT_CHANNELS = ("voltage", "current", "SOC", "max_cell_v", "min_cell_v", "max_temp", "min_temp", "time")

# Constants of the originally deployed model (final_model_no_mfg): pooled
# normalisation over all three datasets. Used only when model_config.json is
# missing, so the service behaves exactly as before.
_DEFAULT_CONFIG: dict[str, Any] = {
    "model_name": "final_model_no_mfg",
    "arch": "BiLSTM+Attn",
    "architecture": {"input_size": 8},
    "channels": list(DEFAULT_CHANNELS),
    "sensor_mean": [
        3.94499135017395, -9.583528518676758, 70.92549896240234, 3.952288866043091,
        3.902657985687256, 29.018632888793945, 25.83769989013672, 634.0243530273438,
    ],
    "sensor_std": [
        0.2569948434829712, 7.840857028961182, 25.75346565246582, 0.2583308815956116,
        0.25116822123527527, 8.011555671691895, 8.574789047241211, 369.41412353515625,
    ],
    "per_dataset": {},
    "capacity_mean": 41.01803,
    "capacity_std": 1.9790907,
    "soh_mean": 95.37797,
    "soh_std": 3.4451575,
    "fault_threshold": 0.5,
    "rul_threshold_soh": 80.0,
}


@dataclass(frozen=True)
class ModelConfig:
    """Everything the service needs to know about the deployed model."""

    model_name: str
    arch: str
    input_size: int
    channels: tuple[str, ...]
    sensor_mean: np.ndarray
    sensor_std: np.ndarray
    capacity_mean: float
    capacity_std: float
    soh_mean: float
    soh_std: float
    fault_threshold: float
    rul_threshold_soh: float
    # {"1": (mean, std), ...}; empty when the config has no per-dataset stats.
    per_dataset: dict[str, tuple[np.ndarray, np.ndarray]] = field(default_factory=dict)
    # True when sensor_mean/sensor_std are not the training pooled constants but
    # an average of the per-dataset ones (the v2 notebook saves only the latter).
    pooled_is_approximate: bool = False


def _channel_vector(values: Any, name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float32)
    if arr.shape != (N_CHANNELS,) or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be {N_CHANNELS} finite numbers.")
    return arr


def _from_notebook_config(raw: dict[str, Any]) -> dict[str, Any]:
    """Converts the dict written by the v2 training notebook into this module's format.

    The notebook stores ``ds_mean``/``ds_std`` (per dataset) and no pooled
    constants, so the pooled fallback is the plain average of the datasets.
    """
    keys = sorted(str(k) for k in raw["ds_mean"])
    ds_mean = {str(k): v for k, v in raw["ds_mean"].items()}
    ds_std = {str(k): v for k, v in raw["ds_std"].items()}
    converted = {
        "model_name": raw.get("model_name", "bilstm_no_mfg_v2"),
        "arch": raw.get("arch", "BiLSTM+Attn"),
        "architecture": {"input_size": int(raw.get("input_size", 8))},
        "sensor_mean": np.mean([ds_mean[k] for k in keys], axis=0).tolist(),
        "sensor_std": np.mean([ds_std[k] for k in keys], axis=0).tolist(),
        "per_dataset": {k: {"sensor_mean": ds_mean[k], "sensor_std": ds_std[k]} for k in keys},
        "pooled_is_approximate": True,
        "capacity_mean": raw["cap_mean"],
        "capacity_std": raw["cap_std"],
        "soh_mean": raw["soh_mean"],
        "soh_std": raw["soh_std"],
        "fault_threshold": raw["fault_threshold"],
    }
    if "channels" in raw:
        converted["channels"] = raw["channels"]
    if "rul_threshold_soh" in raw:
        converted["rul_threshold_soh"] = raw["rul_threshold_soh"]
    return converted


def load_config(path: Path | None = None) -> ModelConfig:
    """Reads ``model_config.json``; falls back to the original constants.

    :raises ValueError: when the file exists but is malformed, or describes a
        model this API cannot serve (for example one with a manufacturer flag).
    """
    raw = dict(_DEFAULT_CONFIG)
    if path is not None and path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name} is not valid JSON: {exc}") from exc
        if "ds_mean" in loaded:  # written by the v2 notebook
            try:
                loaded = _from_notebook_config(loaded)
            except KeyError as exc:
                raise ValueError(f"{path.name} is missing {exc}.") from exc
        raw.update(loaded)
    elif path is not None:
        logger.warning("%s not found; using built-in constants.", path)

    input_size = int({**_DEFAULT_CONFIG["architecture"], **raw.get("architecture", {})}["input_size"])
    if input_size != N_CHANNELS:
        raise ValueError(
            f"This API serves models with {N_CHANNELS} sensor inputs; the config says {input_size} "
            "(a model with a manufacturer flag is not supported)."
        )
    channels = tuple(str(c) for c in raw.get("channels", DEFAULT_CHANNELS))
    if len(channels) != N_CHANNELS:
        raise ValueError(f"channels must list {N_CHANNELS} names.")
    sensor_std = _channel_vector(raw["sensor_std"], "sensor_std")
    if np.any(sensor_std <= 0):
        raise ValueError("sensor_std must be positive.")

    per_dataset: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for key, stats in (raw.get("per_dataset") or {}).items():
        std = _channel_vector(stats["sensor_std"], f"per_dataset[{key}].sensor_std")
        if np.any(std <= 0):
            raise ValueError(f"per_dataset[{key}].sensor_std must be positive.")
        per_dataset[str(key)] = (_channel_vector(stats["sensor_mean"], f"per_dataset[{key}].sensor_mean"), std)

    return ModelConfig(
        model_name=str(raw["model_name"]),
        arch=str(raw["arch"]),
        input_size=input_size,
        channels=channels,
        sensor_mean=_channel_vector(raw["sensor_mean"], "sensor_mean"),
        sensor_std=sensor_std,
        capacity_mean=float(raw["capacity_mean"]),
        capacity_std=float(raw["capacity_std"]),
        soh_mean=float(raw["soh_mean"]),
        soh_std=float(raw["soh_std"]),
        fault_threshold=float(raw["fault_threshold"]),
        rul_threshold_soh=float(raw["rul_threshold_soh"]),
        per_dataset=per_dataset,
        pooled_is_approximate=bool(raw.get("pooled_is_approximate", False)),
    )


def normalise(
    readings: list[list[float]], config: ModelConfig, dataset: int | None = None
) -> tuple[np.ndarray, str]:
    """Standardises a 128 x 8 session. Returns (array, normalisation mode).

    Uses the per-dataset constants only when the caller names a dataset *and*
    the config has them for it; otherwise the pooled constants ("approximate"
    when those are only an average of the per-dataset ones).
    """
    arr = np.asarray(readings, dtype=np.float32)
    if arr.shape != (N_STEPS, N_CHANNELS):
        raise ValueError(f"Expected {N_STEPS} x {N_CHANNELS} readings, got {arr.shape}.")
    if dataset is not None and str(dataset) in config.per_dataset:
        mean, std = config.per_dataset[str(dataset)]
        return (arr - mean) / std, "per_dataset"
    mode = "approximate" if config.pooled_is_approximate else "global"
    return (arr - config.sensor_mean) / config.sensor_std, mode


def finalise(capacity_n: float, soh_n: float, fault_logit: float, config: ModelConfig) -> dict[str, Any]:
    """Turns raw network outputs (standardised / logit) into real units.

    No yes/no fault decision is made: the probability is an experimental risk score.
    """
    capacity = capacity_n * config.capacity_std + config.capacity_mean
    soh = float(np.clip(soh_n * config.soh_std + config.soh_mean, 0.0, 100.0))
    fault_prob = float(1.0 / (1.0 + np.exp(-np.clip(fault_logit, -50.0, 50.0))))
    return {
        "capacity": round(float(capacity), 2),
        "soh_percent": round(soh, 2),
        "fault_probability": round(fault_prob, 3),
        "fault_probability_experimental": True,
        "model_name": config.model_name,
    }


def top_rows(weights: list[float], k: int = TOP_ATTENTION_ROWS) -> list[int]:
    """Indices of the k largest attention weights, largest first."""
    return [int(i) for i in np.argsort(weights)[::-1][:k]]


def channel_sensitivities(
    base_prob: float, ablated_probs: list[float], names: tuple[str, ...]
) -> dict[str, float]:
    """How much the fault probability moves when each channel is neutralised."""
    return {name: round(abs(prob - base_prob), 4) for name, prob in zip(names, ablated_probs, strict=True)}


# --------------------------------------------------------------------------
# torch-dependent part (lazy)
# --------------------------------------------------------------------------

_lock = threading.Lock()
_loaded: tuple[Any, Any, ModelConfig] | None = None  # (torch, model, config)


def remap_state_dict_keys(state: dict[str, Any]) -> dict[str, Any]:
    """Accepts checkpoints from both training notebooks.

    The first notebook named the capacity head ``capacity_head``; the v2
    notebook (``models.py``) calls it ``cap_head``. Same layers, different name.
    """
    return {
        ("cap_head." + key[len("capacity_head."):] if key.startswith("capacity_head.") else key): value
        for key, value in state.items()
    }


def _build_network(config: ModelConfig) -> Any:
    """Builds the network from ``ml_models/models.py`` (the notebook's own file)."""
    if not MODELS_FILE.is_file():
        raise ModelUnavailable(f"Network definitions not found: {MODELS_FILE}")
    spec = importlib.util.spec_from_file_location("amppilot_models", MODELS_FILE)
    if spec is None or spec.loader is None:
        raise ModelUnavailable("models.py could not be loaded.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.build_model(config.arch, config.input_size)
    except KeyError as exc:
        raise ModelUnavailable(f"models.py has no architecture named {config.arch!r}.") from exc


def _paths() -> tuple[Path, Path]:
    settings = get_settings()
    return ML_DIR / settings.model_weights_file, ML_DIR / settings.model_config_file


def get_config() -> ModelConfig:
    """The deployed model's config. Needs neither torch nor the weights.

    :raises ModelUnavailable: when model_config.json exists but is invalid.
    """
    try:
        return load_config(_paths()[1])
    except ValueError as exc:
        raise ModelUnavailable(f"model_config.json is invalid: {exc}") from exc


def _get_loaded() -> tuple[Any, Any, ModelConfig]:
    """Loads weights + config on first use. Failures are not cached, so
    dropping the files in place works without a restart."""
    global _loaded
    if _loaded is not None:
        return _loaded
    with _lock:
        if _loaded is not None:
            return _loaded
        weights_path, _ = _paths()
        if not weights_path.is_file():
            raise ModelUnavailable(f"Model weights not found: {weights_path}")
        config = get_config()
        try:
            import torch  # noqa: PLC0415 - deliberately lazy

            model = _build_network(config)
            model.load_state_dict(remap_state_dict_keys(torch.load(weights_path, map_location="cpu")))
            model.eval()
        except ModelUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Could not load the battery model")
            raise ModelUnavailable(f"Could not load the battery model: {type(exc).__name__}") from exc
        _loaded = (torch, model, config)
        logger.info("Battery model '%s' loaded from %s", config.model_name, weights_path.name)
        return _loaded


def warm_up() -> bool:
    """Loads the model ahead of the first request. Never raises.

    Called in the background at server start so the first prediction does not
    pay for importing torch and reading the weights. Returns whether it loaded.
    """
    try:
        _get_loaded()
    except ModelUnavailable as exc:
        logger.warning("Battery model not loaded at start-up: %s", exc)
        return False
    return True


def reset_model_cache() -> None:
    """Forgets the loaded model (used by tests and after swapping files)."""
    global _loaded
    with _lock:
        _loaded = None


def model_info() -> dict[str, Any]:
    """Describes the deployed model without raising."""
    weights_path, config_path = _paths()
    info: dict[str, Any] = {
        "loaded": False,
        "model_name": None,
        "fault_threshold": None,
        "per_dataset_normalisation": False,
        "pooled_normalisation_approximate": False,
        "weights_file": weights_path.name,
        "detail": None,
    }
    try:
        config = load_config(config_path)
    except ValueError as exc:
        info["detail"] = str(exc)
        return info
    info.update(
        model_name=config.model_name,
        fault_threshold=config.fault_threshold,
        per_dataset_normalisation=bool(config.per_dataset),
        pooled_normalisation_approximate=config.pooled_is_approximate,
    )
    if not weights_path.is_file():
        info["detail"] = "Weights file not found on the server."
        return info
    try:
        _get_loaded()
        info["loaded"] = True
    except ModelUnavailable as exc:
        info["detail"] = "Model could not be loaded."
        logger.error("model_info: %s", exc)
    return info


def predict(
    readings: list[list[float]],
    dataset: int | None = None,
    include_attention: bool = False,
) -> dict[str, Any]:
    """Runs one 128 x 8 charging session through the model.

    :raises ModelUnavailable: when the weights or config cannot be loaded.
    """
    torch, model, config = _get_loaded()
    arr_norm, mode = normalise(readings, config, dataset)
    x = torch.tensor(arr_norm[None, :, :], dtype=torch.float32)

    with torch.no_grad():
        out = model(x, return_attention=True)
    cap, soh, fault_logit = out[0], out[1], out[2]
    attn = out[3] if len(out) > 3 else None  # only the attention architecture has weights

    result = finalise(cap.item(), soh.item(), fault_logit.item(), config)
    result["normalisation"] = mode
    if include_attention and attn is not None:
        weights = attn.squeeze(0).tolist()
        result["attention_weights"] = [round(w, 5) for w in weights]
        result["top_attention_rows"] = top_rows(weights)
    return result


def explain(
    readings: list[list[float]],
    dataset: int | None = None,
    include_attention: bool = False,
) -> dict[str, Any]:
    """Shows where the model looked and which sensor channels the fault score reacts to.

    Same method as the training notebook: set one channel at a time to its
    training mean (0 after standardising) and measure how far the fault
    probability moves. All eight variants run in one batch.

    :raises ModelUnavailable: when the weights or config cannot be loaded.
    """
    torch, model, config = _get_loaded()
    arr_norm, mode = normalise(readings, config, dataset)
    base = torch.tensor(arr_norm[None, :, :], dtype=torch.float32)
    batch = base.repeat(1 + N_CHANNELS, 1, 1)
    for channel in range(N_CHANNELS):
        batch[1 + channel, :, channel] = 0.0

    with torch.no_grad():
        out = model(batch, return_attention=True)
    probs = torch.sigmoid(out[2]).tolist()
    result: dict[str, Any] = {
        "fault_probability": round(probs[0], 3),
        "fault_probability_experimental": True,
        "model_name": config.model_name,
        "normalisation": mode,
        "channel_sensitivity": channel_sensitivities(probs[0], probs[1:], config.channels),
        "top_attention_rows": None,
        "attention_weights": None,
    }
    if len(out) > 3:
        weights = out[3][0].tolist()
        result["top_attention_rows"] = top_rows(weights)
        if include_attention:
            result["attention_weights"] = [round(w, 5) for w in weights]
    return result


def _read_demo_file(path: Path) -> dict[str, Any]:
    """Reads and validates one demo session file.

    A demo file is the same JSON you would paste into ``POST /battery/predict``
    (``readings`` and optionally ``dataset``) plus display fields: ``title``,
    ``description`` and ``true_label`` (0 healthy, 1 faulty, from the dataset).
    Extra keys are ignored by the predict endpoint, so a demo file can also be
    pasted into Swagger unchanged.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data["readings"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ModelUnavailable(f"Demo session file is unreadable: {path.name}") from exc
    valid_shape = (
        isinstance(rows, list)
        and len(rows) == N_STEPS
        and all(isinstance(r, list) and len(r) == N_CHANNELS for r in rows)
    )
    if not valid_shape or any(
        not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v)
        for r in rows
        for v in r
    ):
        raise ModelUnavailable(f"Demo session has invalid readings: {path.name}")
    dataset = data.get("dataset")
    true_label = data.get("true_label")
    return {
        "id": path.stem,
        "title": str(data.get("title") or path.stem.replace("_", " ")),
        "description": str(data.get("description") or ""),
        "dataset": dataset if dataset in (1, 2, 3) else None,
        "true_label": true_label if true_label in (0, 1) else None,
        "readings": rows,
    }


def _demo_path(session_id: str) -> Path:
    if session_id == SAMPLE_SESSION_ID:
        return SAMPLE_SESSION_PATH
    if not _SESSION_ID_RE.fullmatch(session_id):
        raise DemoSessionNotFound(session_id)
    path = DEMO_DIR / f"{session_id}.json"
    if not path.is_file():
        raise DemoSessionNotFound(session_id)
    return path


def load_demo_session(session_id: str = SAMPLE_SESSION_ID) -> dict[str, Any]:
    """One demo session by id (``sample_session`` or a file in ``ml_models/demo``).

    :raises DemoSessionNotFound: unknown or malformed id.
    :raises ModelUnavailable: the file exists but is not a valid session.
    """
    return _read_demo_file(_demo_path(session_id))


def list_demo_sessions() -> list[dict[str, Any]]:
    """Ids and labels of all demo sessions (no readings). Invalid files are skipped."""
    paths = [SAMPLE_SESSION_PATH] if SAMPLE_SESSION_PATH.is_file() else []
    if DEMO_DIR.is_dir():
        paths += sorted(DEMO_DIR.glob("*.json"))
    sessions = []
    for path in paths:
        try:
            session = _read_demo_file(path)
        except ModelUnavailable as exc:
            logger.warning("Skipping demo session: %s", exc)
            continue
        session.pop("readings")
        if path == SAMPLE_SESSION_PATH:
            session.update(id=SAMPLE_SESSION_ID, title="Sample charging session")
        sessions.append(session)
    return sessions


def load_sample_session() -> list[list[float]]:
    """The bundled sample charging session (kept for backwards compatibility)."""
    return load_demo_session(SAMPLE_SESSION_ID)["readings"]