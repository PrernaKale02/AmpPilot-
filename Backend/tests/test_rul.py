"""Remaining-useful-life service (numpy + csv only)."""

import pytest

from app.core.exceptions import ModelUnavailable, RulNotFound
from app.services import rul


def _line(slope, n=10, start=100.0, step=10_000):
    mileage = [i * step for i in range(n)]
    return mileage, [start + slope * m for m in mileage]


def test_fit_reaches_the_threshold_at_the_expected_distance():
    mileage, soh = _line(-1e-4)
    out = rul.fit_rul(mileage, soh, threshold_soh=80.0)
    assert out["estimated_rul_km"] == pytest.approx(110_000, abs=1)  # 200,000 km minus 90,000 km driven
    assert out["capped"] is False
    assert out["current_soh_percent"] == pytest.approx(91.0)
    assert out["degradation_soh_per_1000km"] == pytest.approx(-0.1, abs=1e-3)


def test_fit_ignores_input_order():
    mileage, soh = _line(-1e-4)
    forward = rul.fit_rul(mileage, soh)
    backward = rul.fit_rul(mileage[::-1], soh[::-1])
    assert backward["estimated_rul_km"] == forward["estimated_rul_km"]


def test_fit_is_zero_when_already_below_the_threshold():
    mileage, soh = _line(-1e-4, start=82.0)
    assert rul.fit_rul(mileage, soh)["estimated_rul_km"] == 0.0


def test_fit_caps_and_flags_a_very_flat_trend():
    mileage, soh = _line(-1e-8)
    out = rul.fit_rul(mileage, soh, cap_km=300_000)
    assert out["capped"] is True and out["estimated_rul_km"] == 300_000
    assert "cut to" in out["note"]


def test_fit_has_no_estimate_when_soh_does_not_fall():
    mileage, soh = _line(2e-4, start=80.0)
    out = rul.fit_rul(mileage, soh)
    assert out["estimated_rul_km"] is None and out["capped"] is False


def test_fit_skips_non_finite_points_then_checks_the_minimum():
    mileage, soh = _line(-1e-4, n=5)
    soh[1] = float("nan")  # only 4 valid points are left
    with pytest.raises(ValueError, match="At least 5"):
        rul.fit_rul(mileage, soh)

    mileage, soh = _line(-1e-4, n=6)
    soh[1] = float("nan")  # 5 valid points remain: still fine
    assert rul.fit_rul(mileage, soh)["estimated_rul_km"] is not None


def test_fit_rejects_constant_mileage_and_length_mismatch():
    with pytest.raises(ValueError, match="same"):
        rul.fit_rul([1000.0] * 6, [90, 89, 88, 87, 86, 85])
    with pytest.raises(ValueError, match="length"):
        rul.fit_rul([1, 2, 3], [1, 2])


CSV = (
    "car,dataset,current_mileage,current_soh,degradation_rate_per_km,estimated_RUL_km\n"
    "1_105,1,172858.859375,92.174423,-4.7e-05,241549.719269\n"
    "1_107,1,154669.890625,88.729164,-0.0002,38865.835120\n"
    "1_999,1,100000,90,-1e-9,99000000.0\n"
)


def test_precomputed_lookup(tmp_path):
    path = tmp_path / "rul_estimates.csv"
    path.write_text(CSV, encoding="utf-8")
    out = rul.lookup_precomputed("1_107", path)
    assert out["source"] == "precomputed"
    assert out["estimated_rul_km"] == pytest.approx(38_865.8, abs=0.1)
    assert out["current_soh_percent"] == pytest.approx(88.73)
    assert out["degradation_soh_per_1000km"] == pytest.approx(-0.2)


def test_precomputed_lookup_caps_absurd_values(tmp_path):
    path = tmp_path / "rul_estimates.csv"
    path.write_text(CSV, encoding="utf-8")
    out = rul.lookup_precomputed("1_999", path, cap_km=500_000)
    assert out["capped"] is True and out["estimated_rul_km"] == 500_000


def test_precomputed_lookup_unknown_car_and_bad_files(tmp_path):
    path = tmp_path / "rul_estimates.csv"
    path.write_text(CSV, encoding="utf-8")
    with pytest.raises(RulNotFound):
        rul.lookup_precomputed("3_1", path)
    with pytest.raises(ModelUnavailable):
        rul.lookup_precomputed("1_105", tmp_path / "missing.csv")
    broken = tmp_path / "broken.csv"
    broken.write_text("car,other\n1_105,5\n", encoding="utf-8")
    with pytest.raises(ModelUnavailable):
        rul.lookup_precomputed("1_105", broken)