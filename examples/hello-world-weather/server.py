"""Hello World Weather - the simplest useful Glaido MCP server.

One tool, one free API (Open-Meteo), no API key, no signup. This is the folder the
Glaido "first tool" walkthrough builds. Copy it somewhere stable, put the absolute
path in mcp.json, and import it on Glaido's Tools page.
"""

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

# Server-level instructions: tells the agent what this server is for and WHEN to use it.
SERVER_INSTRUCTIONS = (
    "Use this server to get the current weather for any city in the world. "
    "Covers temperature, feels-like, humidity, wind, and conditions via the free "
    "Open-Meteo API."
)

mcp = FastMCP(name="Weather API", instructions=SERVER_INSTRUCTIONS)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes -> human-readable conditions.
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
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,     # only reads data, so Glaido can run it without asking
        destructiveHint=False,
        openWorldHint=True,    # reaches an external API
    ),
)
def get_weather(city: str) -> dict:
    """Get the current weather for a city anywhere in the world.

    Looks the city up by name and returns temperature, feels-like temperature,
    humidity, wind speed, and a plain-language description of the conditions.
    """
    with httpx.Client(timeout=10) as client:
        geo = client.get(GEOCODING_URL, params={"name": city, "count": 1}).json()
        results = geo.get("results")
        if not results:
            return {"status": "error", "message": f"No city found matching '{city}'."}
        place = results[0]

        forecast = client.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": (
                    "temperature_2m,apparent_temperature,relative_humidity_2m,"
                    "wind_speed_10m,weather_code"
                ),
            },
        ).json()

    current = forecast.get("current", {})
    return {
        "status": "ok",
        "location": {
            "city": place.get("name"),
            "region": place.get("admin1"),
            "country": place.get("country"),
        },
        "conditions": WEATHER_CODES.get(current.get("weather_code"), "Unknown"),
        "temperature_c": current.get("temperature_2m"),
        "feels_like_c": current.get("apparent_temperature"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
    }


if __name__ == "__main__":
    # stdio is the transport Glaido uses for local servers. Do not change this.
    mcp.run(transport="stdio")
