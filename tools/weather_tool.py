import requests

GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
)
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}

def weather_tool(city: str):
    # -------------------------
    # 1. Geocoding
    # -------------------------
    geo_response = requests.get(
        GEOCODING_URL,
        params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        },
        timeout=10,
    )
    geo_response.raise_for_status()
    geo_data = geo_response.json()
    results = geo_data.get("results")
    if not results:
        raise ValueError(
            f"Could not find location: {city}"
        )
    location = results[0]
    latitude = location["latitude"]
    longitude = location["longitude"]
    location_name = location["name"]
    country = location.get(
        "country",
        ""
    )
    # -------------------------
    # 2. Weather API
    # -------------------------
    weather_response = requests.get(
        WEATHER_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "timezone": "auto",
        },
        timeout=10,
    )
    weather_response.raise_for_status()
    weather_data = weather_response.json()
    current = weather_data.get("current")
    if not current:
        raise ValueError(
            "Weather data was not returned."
        )
    weather_code = current[
        "weather_code"
    ]
    return {
        "location":
        f"{location_name}, {country}",
        "condition":
        WEATHER_CODES.get(
            weather_code,
            "Unknown"
        ),
        "temperature_c":
        current["temperature_2m"],
        "feels_like_c":
        current["apparent_temperature"],
        "humidity_percent":
        current["relative_humidity_2m"],
        "wind_speed_kmh":
        current["wind_speed_10m"],
        "weather_code":
        weather_code,
    }