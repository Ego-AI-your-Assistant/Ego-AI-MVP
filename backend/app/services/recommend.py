from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models.models import User, UserProfile
import httpx
import datetime
from app.services import timezone as timezone_service
from app.services import places as places_service

DEFAULT_POSITION = "55.7558,37.6173"  # Москва

# Типы мест, которые будем искать (можно расширить)
POI_TYPES = [
    "cafe", "restaurant", "bar", "pub", "fast_food", "park", "playground", "garden", "exhibition_center", "museum", "art_gallery", "theatre", "cinema", "library", "attraction", "zoo", "aquarium", "theme_park", "shopping", "supermarket", "convenience", "bakery", "clothes", "shoes", "gift", "sports_shop", "hotel", "hostel", "motel", "guest_house", "camp_site", "caravan_site", "hospital", "clinic", "pharmacy", "doctors", "dentist", "veterinary", "school", "university", "college", "kindergarten", "bank", "atm", "post_office", "police", "fire_station", "fuel", "parking", "charging_station", "bus_station", "taxi", "train_station", "subway_entrance", "airport", "ferry_terminal", "marketplace", "stadium", "sports_centre", "swimming_pool", "fitness_centre", "nightclub", "casino", "beach", "viewpoint", "water_park", "sauna", "spa", "bowling_alley", "ice_rink", "golf_course", "miniature_golf", "dog_park", "community_centre", "place_of_worship", "church", "mosque", "synagogue", "temple", "monastery", "embassy", "courthouse", "townhall", "public_building", "memorial", "monument", "ruins", "castle", "fort", "archaeological_site"
]

async def get_recommendations_for_user(db: AsyncSession, user: User):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Определяем position
    position = profile.hometown or DEFAULT_POSITION

    # Получаем погоду
    try:
        from app.services import weather as weather_service
        w = weather_service.get_current_weather(position)
        temp = w['current_weather']['temperature']
        code = w['current_weather']['weathercode']
        weather = f"{temp}°C, code {code}"
    except Exception:
        weather = "unknown"

    # Получаем локальное время и временную зону
    try:
        tz_info = timezone_service.get_timezone_utc(position)
        utc_offset = tz_info.get("utc_offset_seconds", 0)
        now_utc = datetime.datetime.utcnow()
        local_time = now_utc + datetime.timedelta(seconds=utc_offset)
        local_time_str = local_time.strftime("%Y-%m-%d %H:%M:%S")
        timezone_name = tz_info.get("timezone", "")
    except Exception:
        local_time_str = ""
        timezone_name = ""

    # Получаем реальные POI через places.py
    nearby_places = []
    try:
        lat, lon = position.split(",") if "," in position else (None, None)
        if lat and lon:
            for poi_type in POI_TYPES:
                try:
                    pois = places_service.nearby_places(lat, lon, poi_type)
                    for poi in pois:
                        nearby_places.append({
                            "name": poi.get("name", ""),
                            "type": poi_type,
                            "lat": poi.get("lat"),
                            "lon": poi.get("lon"),
                            "address": poi.get("address", "")
                        })
                except Exception:
                    continue
    except Exception:
        nearby_places = []

    payload = {
        "position": position,
        "age": profile.age if profile.age is not None else None,
        "gender": profile.sex or "",
        "description": profile.description or "",
        "weather": weather,
        "local_time": local_time_str,
        "timezone": timezone_name,
        "nearby_places": nearby_places[:50]  # Ограничим до 50 мест
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/recommend",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            ml_response = response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ML service error: {e}")

    return ml_response
