import requests

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)
OSRM_URL = (
    "https://router.project-osrm.org/route/v1"
)
HEADERS = {
    "User-Agent": (
        "project2-llm-tool-agent/1.0 "
        "(student project)"
    )
}
def geocode_place(place: str):
    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": place,
            "format": "jsonv2",
            "limit": 1,
        },
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        raise ValueError(
            f"Could not find location: {place}"
        )
    location = results[0]
    return {
        "name": location["display_name"],
        "latitude": float(
            location["lat"]
        ),
        "longitude": float(
            location["lon"]
        ),
    }
def maps_tool(
    origin: str,
    destination: str,
    mode: str = "driving",
):
    # -------------------------
    # 1. Validate mode
    # -------------------------
    allowed_modes = {
        "driving",
        "walking",
        "cycling",
    }
    if mode not in allowed_modes:
        raise ValueError(
            "Mode must be driving, "
            "walking, or cycling."
        )
    # -------------------------
    # 2. Geocode origin
    # -------------------------
    origin_location = geocode_place(
        origin
    )
    # -------------------------
    # 3. Geocode destination
    # -------------------------
    destination_location = geocode_place(
        destination
    )
    # -------------------------
    # 4. Build OSRM coordinates
    # -------------------------
    origin_coordinates = (
        f"{origin_location['longitude']},"
        f"{origin_location['latitude']}"
    )
    destination_coordinates = (
        f"{destination_location['longitude']},"
        f"{destination_location['latitude']}"
    )
    coordinates = (
        f"{origin_coordinates};"
        f"{destination_coordinates}"
    )
    # -------------------------
    # 5. Request route
    # -------------------------
    route_url = (
        f"{OSRM_URL}/{mode}/"
        f"{coordinates}"
    )
    response = requests.get(
        route_url,
        params={
            "overview": "false",
            "steps": "false",
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "Ok":
        raise ValueError(
            data.get(
                "message",
                "No route found."
            )
        )
    routes = data.get("routes")
    if not routes:
        raise ValueError(
            "No route was found."
        )
    route = routes[0]
    # OSRM gives distance in meters
    # and duration in seconds.
    distance_km = (
        route["distance"] / 1000
    )
    duration_minutes = (
        route["duration"] / 60
    )
    return {
       "origin":
        origin_location["name"],
        "destination":
        destination_location["name"],
        "mode":
        mode,
        "distance_km":
        round(distance_km, 2),
        "duration_minutes":
        round(duration_minutes),
    }