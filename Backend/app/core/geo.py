"""Great-circle distance. Pure standard library, no I/O, no dependencies."""

from math import asin, cos, radians, sin, sqrt

# IUGG mean Earth radius. Good to ~0.5% for the short urban distances this
# endpoint deals with, which is well inside the 0.1 km the frontend displays.
EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points, in kilometres.

    Straight-line distance over the sphere, not driving distance.

    :param lat1: First point's latitude, decimal degrees.
    :param lon1: First point's longitude, decimal degrees.
    :param lat2: Second point's latitude, decimal degrees.
    :param lon2: Second point's longitude, decimal degrees.
    :returns: Distance in kilometres, always non-negative.
    """
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = lat2_rad - lat1_rad
    delta_lon = radians(lon2 - lon1)

    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2

    # Clamp: floating point can nudge `a` a hair above 1 for antipodal points,
    # which would make sqrt/asin blow up on a domain error.
    return 2 * EARTH_RADIUS_KM * asin(sqrt(min(1.0, a)))
