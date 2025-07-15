from fastapi import APIRouter, Query, HTTPException
from app.services import timezone

router = APIRouter()

@router.get("/timezone", summary="Получить информацию о временной зоне по координатам", tags=["timezone"])
def get_timezone(
    location: str = Query(..., description="Координаты 'lat,lon' (например, '55.75,37.61')")
):
    """
    Возвращает информацию о временной зоне (UTC-смещение, аббревиатура и др.) для заданных координат.
    Пример ответа:
    {
        "latitude": 55.75,
        "longitude": 37.61,
        "timezone": "Europe/Moscow",
        "utc_offset_seconds": 10800,
        "timezone_abbreviation": "MSK"
    }
    """
    try:
        return timezone.get_timezone_utc(location)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
