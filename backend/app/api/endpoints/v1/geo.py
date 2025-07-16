from fastapi import APIRouter, Query, HTTPException
from app.services import geo
import httpx
from app.services import weather as weather_service
import logging
import json

logger = logging.getLogger(__name__)
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
    logger.info(f"[BACKEND] Received geo_recommend request: lat={lat}, lon={lon}, age={age}, gender={gender}, goal={goal}, description={description}, weather={weather}")

    # If weather is not provided, try to get it
    if not weather:
        try:
            w = weather_service.get_current_weather(f"{lat},{lon}")
            temp = w['current_weather']['temperature']
            code = w['current_weather']['weathercode']
            weather = f"{temp}°C, code {code}"
            logger.info(f"[BACKEND] Fetched weather: {weather}")
        except Exception as e:
            weather = "unknown"
            logger.warning(f"[BACKEND] Failed to fetch weather: {e}")

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

    logger.info(f"[BACKEND] Sending payload to ML service: {payload}")

    try:
        async with httpx.AsyncClient() as client:
            logger.info("[BACKEND] Calling ML service at: http://ego-ai-ml-service:8001/recommend/")
            resp = await client.post("http://ego-ai-ml-service:8001/recommend/", json=payload, timeout=30)
            logger.info(f"[BACKEND] ML service response status: {resp.status}")
            logger.info(f"[BACKEND] ML service response headers: {dict(resp.headers)}")

            # Log raw response content
            raw_content = resp.text
            logger.info(f"[BACKEND] ML service raw response: {raw_content}")

            resp.raise_for_status()

            try:
                ml_result = resp.json()
                logger.info(f"[BACKEND] ML service parsed JSON: {ml_result}")
            except Exception as json_error:
                logger.error(f"[BACKEND] Failed to parse ML response as JSON: {json_error}")
                logger.error(f"[BACKEND] Raw response that failed to parse: {raw_content}")
                raise HTTPException(status_code=500, detail=f"ML service returned invalid JSON: {raw_content}")

            # Prepare response for frontend
            if isinstance(ml_result, dict) and "recommendations" in ml_result:
                final_response = {"recommendations": ml_result["recommendations"]}
            elif isinstance(ml_result, list):
                final_response = {"recommendations": ml_result}
            else:
                final_response = {"recommendations": [ml_result]}

            logger.info(f"[BACKEND] Sending final response to frontend: {final_response}")
            
            # Log the actual response that will be sent
            response_json = json.dumps(final_response, ensure_ascii=False)
            logger.info(f"[BACKEND] Final response JSON string: {response_json}")
            logger.info(f"[BACKEND] Final response content-type: application/json")
            
            return final_response

    except httpx.HTTPStatusError as e:
        logger.error(f"[BACKEND] ML service HTTP error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=500, detail=f"Geo ML service HTTP error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"[BACKEND] ML service error: {e}")
        raise HTTPException(status_code=500, detail=f"Geo ML service error: {e}")
