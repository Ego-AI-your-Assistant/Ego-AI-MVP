from fastapi import APIRouter, Query, HTTPException
from app.services import geo
import httpx
from app.services import weather as weather_service

router = APIRouter()

@router.get("/geo/forward", summary="Forward geocoding (city to coordinates)", tags=["geo"])
def forward_geocode(
    city: str = Query(..., description="City name (e.g. 'Moscow')")
):
    """
    Get coordinates by city name using Nominatim (OpenStreetMap).
    Returns JSON:
    {
        "lat": "55.7504461",
        "lon": "37.6174943",
        "display_name": "Moscow, Central Federal District, Russia"
    }
    """
    try:
        return geo.forward_geocode(city)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/geo/reverse", summary="Reverse geocoding (coordinates to city)", tags=["geo"])
def reverse_geocode(
    lat: str = Query(..., description="Latitude (e.g. '55.75')"),
    lon: str = Query(..., description="Longitude (e.g. '37.61')")
):
    """
    Get city and country by coordinates using Nominatim (OpenStreetMap).
    Returns JSON:
    {
        "city": "Moscow",
        "country": "Russia",
        "display_name": "Moscow, Central Federal District, Russia"
    }
    """
    try:
        return geo.reverse_geocode(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/geo/recommend", summary="Personalized place recommendations", tags=["geo"])
async def geo_recommend(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    age: int = Query(None),
    gender: str = Query(None),
    goal: str = Query(None, description="User's goal or activity"),
    description: str = Query(None, description="Additional user description"),
    weather: str = Query(None, description="Weather description")
):
    # If weather is not provided, try to get it

    if not weather:
        try:
            w = weather_service.get_current_weather(f"{lat},{lon}")
            temp = w['current_weather']['temperature']
            code = w['current_weather']['weathercode']
            weather = f"{temp}°C, code {code}"
        except Exception:
            weather = "unknown"

    # Compose description
    desc = description or ""
    if goal:
        desc += f" Goal: {goal}."

    # Compose position string
    position = f"{lat},{lon}"

    payload = {
        "position": position,
        "age": age,
        "gender": gender,
        "description": desc,
        "weather": weather
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post("http://localhost:8003/recommend", json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:

        raise HTTPException(status_code=500, detail=f"Geo ML service error: {e}")
