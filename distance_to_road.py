import requests
from math import radians, sin, cos, sqrt, atan2
from api import ORS_API_KEY


# -------------------------
# Distance calculation
# -------------------------
def haversine(lat1, lon1, lat2, lon2):
    """Compute distance between two lat/lon points in meters."""
    R = 6371000  # Earth radius in meters

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def snap_to_road(lat, lon, api_key):
    url = "https://api.openrouteservice.org/v2/snap/foot-walking"

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    body = {
        "locations": [[lon, lat]],
        "radius": 100
    }

    try:
        r = requests.post(url, headers=headers, json=body, timeout=10)
        r.raise_for_status()
        data = r.json()
        #print("ORS response:", data)

        # ✅ Correct parsing for Snap V2
        if "locations" not in data or not data["locations"]:
            print("snap_to_road error: no locations returned")
            return None, None

        snapped_lon, snapped_lat = data["locations"][0]["location"]
        return snapped_lat, snapped_lon

    except Exception as e:
        print("snap_to_road error:", e)
        return None, None


# -------------------------
# Distance to road
# -------------------------
def distance_to_road(lat, lon, api_key):
    """
    Returns:
        distance_in_meters (float) or None
        snapped_point (lat, lon) or None
    """

    # Validate input
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        print(f"Invalid coordinates: lat={lat}, lon={lon}")
        return None, None

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        print(f"Out-of-range coordinates: lat={lat}, lon={lon}")
        return None, None

    snapped_lat, snapped_lon = snap_to_road(lat, lon, api_key)

    if snapped_lat is None:
        print("distance_to_road error: snapping failed")
        return None, None

    distance_m = haversine(lat, lon, snapped_lat, snapped_lon)
    return distance_m, (snapped_lat, snapped_lon)


# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    api_key = ORS_API_KEY

    points = [
        ("Depot", 54.30163409249539, 13.015602563589717),
    ]

    for name, lat, lon in points:
        distance, snapped = distance_to_road(lat, lon, api_key)

        if distance is None:
            print(f"distance_to_road error for {name}")
        else:
            print(f"{name}: {distance:.2f} m from road (snapped at {snapped})")
