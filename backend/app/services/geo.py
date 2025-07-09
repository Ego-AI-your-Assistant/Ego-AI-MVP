import requests
from typing import Dict, Any

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "ego-ai-bot/1.0"}

def forward_geocode(city: str) -> Dict[str, Any]:
    """
    Returns coordinates (latitude, longitude) by city name.
    Returns JSON:
    {
        "lat": "55.7504461",
        "lon": "37.6174943",
        "display_name": "Moscow, Central Federal District, Russia"
    }
    """
    params = {
        "q": city,
        "format": "json",
        "limit": 1
    }
    response = requests.get(f"{NOMINATIM_URL}/search", params=params, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError("City not found")
    return {"lat": data[0]["lat"], "lon": data[0]["lon"], "display_name": data[0]["display_name"]}

def reverse_geocode(lat: str, lon: str) -> Dict[str, Any]:
    """
    Returns city, country and display_name by coordinates.
    Returns JSON:
    {
        "city": "Moscow",
        "country": "Russia",
        "display_name": "Moscow, Central Federal District, Russia"
    }
    """
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }
    response = requests.get(f"{NOMINATIM_URL}/reverse", params=params, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return {
        "city": data.get("address", {}).get("city") or data.get("address", {}).get("town") or data.get("address", {}).get("village"),
        "country": data.get("address", {}).get("country"),
        "display_name": data.get("display_name")
    } 