"""Remaining useful life (RUL) from a car's State of Health vs mileage history.

Same method as the training notebook: a straight line through the (mileage, SoH)
points, extended until it reaches the threshold SoH (80% by default). It is a
trend estimate, not a prediction of the neural network.

Two ways to get an estimate:
* ``fit_rul``: fit the line from a history sent by the caller.
* ``lookup_precomputed``: read the per-car table the notebook saved
  (``rul_estimates.csv``).
Large values are cut to ``cap_km`` and flagged, because a nearly flat SoH trend
extrapolates to absurd distances.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import numpy as np

from app.core.exceptions import ModelUnavailable, RulNotFound

MIN_POINTS = 5


def _result(
    rul_km: float | None,
    cap_km: float,
    mileage_km: float,
    soh: float,
    slope_per_km: float | None,
    threshold_soh: float,
    source: str,
    note: str,
) -> dict[str, Any]:
    capped = rul_km is not None and rul_km > cap_km
    return {
        "estimated_rul_km": None if rul_km is None else round(min(rul_km, cap_km), 1),
        "capped": capped,
        "current_mileage_km": round(float(mileage_km), 1),
        "current_soh_percent": round(float(soh), 2),
        "degradation_soh_per_1000km": None if slope_per_km is None else round(slope_per_km * 1000, 4),
        "threshold_soh": threshold_soh,
        "source": source,
        "note": note,
    }


def fit_rul(
    mileage_km: list[float],
    soh_percent: list[float],
    threshold_soh: float = 80.0,
    cap_km: float = 500_000.0,
) -> dict[str, Any]:
    """Fits SoH = intercept + slope * mileage and extends it to the threshold.

    :raises ValueError: fewer than 5 valid points, or all at the same mileage.
    """
    m = np.asarray(mileage_km, dtype=float)
    s = np.asarray(soh_percent, dtype=float)
    if m.shape != s.shape:
        raise ValueError("mileage_km and soh_percent must have the same length.")
    keep = np.isfinite(m) & np.isfinite(s)
    m, s = m[keep], s[keep]
    if len(m) < MIN_POINTS:
        raise ValueError(f"At least {MIN_POINTS} valid (mileage, SoH) points are needed.")
    if np.ptp(m) == 0:
        raise ValueError("The mileage values must not all be the same.")

    order = np.argsort(m)
    m, s = m[order], s[order]
    slope, intercept = np.polyfit(m, s, 1)
    if slope >= 0:
        return _result(None, cap_km, m[-1], s[-1], float(slope), threshold_soh, "fit",
                       "SoH is not decreasing with mileage, so no estimate is possible.")
    rul = max((threshold_soh - intercept) / slope - m[-1], 0.0)
    note = "Straight-line trend estimate, not a guarantee."
    if rul > cap_km:
        note = f"Trend is very flat; the estimate is cut to {cap_km:,.0f} km."
    return _result(float(rul), cap_km, m[-1], s[-1], float(slope), threshold_soh, "fit", note)


def lookup_precomputed(
    car_id: str,
    path: Path,
    threshold_soh: float = 80.0,
    cap_km: float = 500_000.0,
) -> dict[str, Any]:
    """Reads one car's estimate from the notebook's ``rul_estimates.csv``.

    :raises RulNotFound: the car has no estimate in the table.
    :raises ModelUnavailable: the table is missing or malformed.
    """
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("car") != car_id:
                    continue
                rul = float(row["estimated_RUL_km"])
                values = (rul, float(row["current_mileage"]), float(row["current_soh"]),
                          float(row["degradation_rate_per_km"]))
                if not all(math.isfinite(v) for v in values):
                    raise ValueError("non-finite value")
                return _result(rul, cap_km, values[1], values[2], values[3], threshold_soh,
                               "precomputed", "Straight-line trend estimate, not a guarantee.")
    except (OSError, KeyError, ValueError) as exc:
        raise ModelUnavailable(f"RUL table is missing or unreadable: {path.name}") from exc
    raise RulNotFound(car_id)