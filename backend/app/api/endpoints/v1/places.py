from fastapi import APIRouter, Query, HTTPException
from app.services import places
from typing import List, Dict

router = APIRouter()

@router.get("/places/nearby", summary="Nearby places by type", tags=["places"])
def get_nearby_places(
    lat: str = Query(..., description="Latitude (e.g. '55.75')"),
    lon: str = Query(..., description="Longitude (e.g. '37.61')"),
    type: str = Query(..., description="Place type: cafe, park, library, restaurant, bar, supermarket")
) -> List[Dict]:
    """
    Get a list of nearby places of the given type using Overpass API (OpenStreetMap).
    Returns JSON:
    [
        {
            "name": "Coffee House",
            "type": "cafe",
            "lat": "55.751244",
            "lon": "37.618423",
            "address": "Tverskaya St, 1, Moscow"
        },
        ...
    ]
    """
    try:
        return places.nearby_places(lat, lon, type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
