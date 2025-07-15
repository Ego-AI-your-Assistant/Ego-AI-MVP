import requests
from typing import Dict, Any
import os
import httpx
import logging

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "ego-ai-bot/1.0"}

OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY", "5ae2e3f221c38a28845f05b606e6fed2627f1b0f42f69117f9af9d07")
OPENTRIPMAP_URL = "https://api.opentripmap.com/0.1/ru/places/radius"

logger = logging.getLogger(__name__)

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
    logger.info(f"[geo] Forward geocoding city: {city}")
    params = {
        "q": city,
        "format": "json",
        "limit": 1
    }
    try:
        response = requests.get(f"{NOMINATIM_URL}/search", params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if not data:
            logger.warning(f"[geo] City not found: {city}")
            raise ValueError("City not found")
        logger.info(f"[geo] Geocoded city '{city}' to: {data[0]}")
        return {"lat": data[0]["lat"], "lon": data[0]["lon"], "display_name": data[0]["display_name"]}
    except Exception as e:
        logger.error(f"[geo] Error in forward_geocode for city '{city}': {e}", exc_info=True)
        raise

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
    logger.info(f"[geo] Reverse geocoding lat: {lat}, lon: {lon}")
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }
    try:
        response = requests.get(f"{NOMINATIM_URL}/reverse", params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        logger.info(f"[geo] Reverse geocoded {lat},{lon} to: {data}")
        return {
            "city": data.get("address", {}).get("city") or data.get("address", {}).get("town") or data.get("address", {}).get("village"),
            "country": data.get("address", {}).get("country"),
            "display_name": data.get("display_name")
        }
    except Exception as e:
        logger.error(f"[geo] Error in reverse_geocode for {lat},{lon}: {e}", exc_info=True)
        raise

async def fetch_poi_opentripmap(lat: float, lon: float, radius: int = 1000, limit: int = 20):
    """
    Получить POI из OpenTripMap API по координатам.
    Возвращает список POI (dict).
    """
    logger.info(f"[geo] Fetching POI from OpenTripMap: lat={lat}, lon={lon}, radius={radius}, limit={limit}")
    params = {
        "radius": radius,
        "lon": lon,
        "lat": lat,
        "apikey": OPENTRIPMAP_API_KEY,
        "limit": limit,
        "format": "json"
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(OPENTRIPMAP_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"[geo] Got {len(data)} POI from OpenTripMap for {lat},{lon} radius={radius}")
            return data
    except Exception as e:
        logger.error(f"[geo] Error fetching POI from OpenTripMap: {e}", exc_info=True)
        raise

# Пример вызова:
# pois = await fetch_poi_opentripmap(55.75, 37.61) 