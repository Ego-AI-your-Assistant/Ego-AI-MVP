from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services import weather

router = APIRouter()

'''
Examples:
GET /weather/current?location=55.75,37.61
GET /weather/forecast?location=55.75,37.61&date=2024-06-15
'''

@router.get("/weather/current", summary="Current weather", tags=["weather"])
def get_current_weather(
    location: str = Query(..., description="Coordinates 'lat,lon' (e.g. '55.75,37.61')")
):
    """
    Returns JSON:
    {
        "latitude": 55.75,
        "longitude": 37.61,
        ...,
        "current_weather": {
            "temperature": 21.3,         # Temperature (°C)
            "windspeed": 3.6,            # Wind speed (km/h)
            "winddirection": 180,        # Wind direction (degrees)
            "weathercode": 1,            # Weather code (see Open-Meteo documentation)
            "is_day": 1,                 # 1 — day, 0 — night
            "time": "2024-06-15T12:00"  # Time of measurement
        }
    }
    """
    try:
        return weather.get_current_weather(location)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/weather/forecast", summary="Weather forecast", tags=["weather"])
def get_weather_forecast(
    location: str = Query(..., description="Coordinates 'lat,lon' (e.g. '55.75,37.61')"),
    date: Optional[str] = Query(None, description="Date in format YYYY-MM-DD for filtering forecast (optional)")
):
    """
    Get hourly weather forecast by coordinates using Open-Meteo.
    Returns JSON:
    {
        "latitude": 55.75,
        "longitude": 37.61,
        ...,
        "hourly": {
            "time": ["2024-06-15T00:00", ...],
            "temperature_2m": [17.2, ...],         # Temperature by hours (°C)
            "precipitation": [0.0, ...],           # Precipitation by hours (mm)
            "weathercode": [1, ...],               # Weather code (see Open-Meteo documentation)
            "cloudcover": [20, ...],               # Cloud cover (%)
            "windspeed_10m": [2.5, ...]            # Wind speed (km/h)
        }
    }
    If date (YYYY-MM-DD) is provided, forecast is only for that day.
    """
    try:
        return weather.get_weather_forecast(location, date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/weather/summary", summary="Weather summary (current + short-term forecast)", tags=["weather"])
def get_weather_summary(
    location: str = Query(..., description="Coordinates 'lat,lon' (e.g. '55.75,37.61')")
):
    """
    Get weather summary: current weather + short-term forecast (next 3 hours).
    Returns JSON:
    {
        "current": { ... },  # as in /weather/current
        "forecast": [
            {
                "time": "2024-06-15T13:00",
                "temperature": 22.1,
                "precipitation": 0.0,
                "weathercode": 1,
                "cloudcover": 10,
                "windspeed": 3.2
            },
            ...
        ]
    }
    """
    try:
        return weather.weather_summary(location)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
