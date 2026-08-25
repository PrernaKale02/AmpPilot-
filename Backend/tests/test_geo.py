"""Tests for the haversine helper.

Written as plain pytest functions. pytest is a dev dependency and is not
installed by default - see the README for the dev setup.
"""

from app.core.geo import haversine_km

# Mumbai (Fort / CST area) and Viviana Mall, Thane. Roughly 19 km apart in a
# straight line, which is the figure these bounds are pinned to.
MUMBAI = (19.0760, 72.8777)
THANE = (19.2183, 72.9781)


def test_same_coordinate_is_zero() -> None:
    assert haversine_km(*MUMBAI, *MUMBAI) == 0.0


def test_mumbai_to_thane_is_about_19_km() -> None:
    distance = haversine_km(*MUMBAI, *THANE)
    assert 18.0 <= distance <= 20.0, f"expected ~19 km, got {distance}"


def test_is_symmetric() -> None:
    forward = haversine_km(*MUMBAI, *THANE)
    backward = haversine_km(*THANE, *MUMBAI)
    assert forward == backward


def test_one_degree_of_latitude_is_about_111_km() -> None:
    # Independent of the Mumbai fixtures: one degree of latitude is ~111.19 km
    # anywhere on the globe, so this pins the formula and the Earth radius.
    distance = haversine_km(0.0, 0.0, 1.0, 0.0)
    assert abs(distance - 111.19) < 0.5, f"expected ~111.19 km, got {distance}"


def test_handles_negative_and_cross_meridian_coordinates() -> None:
    # Both sides of the prime meridian, southern hemisphere: guards against a
    # sign error that a single-quadrant fixture would not catch.
    distance = haversine_km(-33.8688, 151.2093, -37.8136, 144.9631)  # Sydney -> Melbourne
    assert 700.0 <= distance <= 730.0, f"expected ~713 km, got {distance}"
