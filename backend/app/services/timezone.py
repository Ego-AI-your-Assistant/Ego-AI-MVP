import requests
from typing import Dict, Tuple

def parse_location(location: str) -> Tuple[str, str]:
    """
    Принимает строку вида '55.75,37.61'. Возвращает (lat, lon).
    """
    if "," in location:
        lat, lon = location.split(",")
        return lat.strip(), lon.strip()
    raise ValueError("API требует координаты в формате 'lat,lon'.")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def get_timezone_utc(location: str) -> Dict:
    """
    Получить информацию о временной зоне (UTC-смещение) по координатам через Open-Meteo.
    Возвращает JSON:
    {
        "latitude": 55.75,
        "longitude": 37.61,
        "timezone": "Europe/Moscow",
        "utc_offset_seconds": 10800,
        "timezone_abbreviation": "MSK"
    }
    """
    lat, lon = parse_location(location)
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true"
    }
    response = requests.get(OPEN_METEO_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return {
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone"),
        "utc_offset_seconds": data.get("utc_offset_seconds"),
        "timezone_abbreviation": data.get("timezone_abbreviation")
    }
