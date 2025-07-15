from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models.models import User, UserProfile
import httpx
import datetime
from app.services import timezone as timezone_service
from app.services.geo import fetch_poi_opentripmap, forward_geocode

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
    print(f"[recommend] User hometown/raw position: {position}")

    # Если position не содержит запятой (т.е. это не координаты, а город), преобразуем в координаты
    if "," not in position:
        try:
            print(f"[recommend] Trying to geocode city name: {position}")
            geo_data = forward_geocode(position)
            lat = geo_data["lat"]
            lon = geo_data["lon"]
            position = f"{lat},{lon}"
            print(f"[recommend] Geocoded city '{position}' to coordinates: {lat}, {lon}")
        except Exception as e:
            print(f"[recommend] Failed to geocode city '{position}': {e}. Using default Moscow.")
            position = DEFAULT_POSITION
            lat, lon = position.split(",")
    else:
        lat, lon = position.split(",")
        print(f"[recommend] Using provided coordinates: {lat}, {lon}")

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

    # Получаем реальные POI через OpenTripMap
    nearby_places = []
    try:
        if lat and lon:
            print(f"[recommend] Fetching POI from OpenTripMap for {lat}, {lon}")
            pois = await fetch_poi_opentripmap(float(lat), float(lon), radius=1000, limit=50)
            print(f"[recommend] Got {len(pois)} POI from OpenTripMap")
            for poi in pois:
                nearby_places.append({
                    "name": poi.get("name", ""),
                    "type": poi.get("kinds", ""),
                    "lat": poi.get("point", {}).get("lat"),
                    "lon": poi.get("point", {}).get("lon"),
                    "address": poi.get("address", "")
                })
    except Exception as e:
        print(f"[recommend] Error fetching POI from OpenTripMap: {e}")
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
