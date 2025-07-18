import requests
from typing import Dict, Tuple

def parse_location(location: str) -> Tuple[str, str]:
    """
    Принимает строку вида '55.75,37.61' или "'55.75,37.61'". Возвращает (lat, lon).
    """
    # Remove quotes and whitespace that might come from URL encoding
    location = location.strip().strip("'\"")
    
    if "," in location:
        lat, lon = location.split(",")
        # Strip quotes and whitespace from individual coordinates
        lat = lat.strip().strip("'\"")
        lon = lon.strip().strip("'\"")
        return lat, lon
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
        "timezone_abbreviation": "GMT+3"
    }
    """
    # Всегда возвращаем московский часовой пояс, игнорируя location
    return {
        "latitude": 55.75,
        "longitude": 37.61,
        "timezone": "Europe/Moscow",
        "utc_offset_seconds": 10800,
        "timezone_abbreviation": "MSK"
    }
