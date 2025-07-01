from fastapi import APIRouter, Query, HTTPException
from app.services import geo

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
