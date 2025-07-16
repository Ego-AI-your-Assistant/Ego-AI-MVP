from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models.models import User, UserProfile
import httpx
import datetime
from app.services import timezone as timezone_service
from app.services.geo import fetch_poi_opentripmap, forward_geocode
import logging

logger = logging.getLogger(__name__)

DEFAULT_POSITION = "55.7558,37.6173"  # Москва

# Типы мест, которые будем искать (можно расширить)
POI_TYPES = [
    "cafe", "restaurant", "bar", "pub", "fast_food", "park", "playground", "garden", "exhibition_center", "museum", "art_gallery", "theatre", "cinema", "library", "attraction", "zoo", "aquarium", "theme_park", "shopping", "supermarket", "convenience", "bakery", "clothes", "shoes", "gift", "sports_shop", "hotel", "hostel", "motel", "guest_house", "camp_site", "caravan_site", "hospital", "clinic", "pharmacy", "doctors", "dentist", "veterinary", "school", "university", "college", "kindergarten", "bank", "atm", "post_office", "police", "fire_station", "fuel", "parking", "charging_station", "bus_station", "taxi", "train_station", "subway_entrance", "airport", "ferry_terminal", "marketplace", "stadium", "sports_centre", "swimming_pool", "fitness_centre", "nightclub", "casino", "beach", "viewpoint", "water_park", "sauna", "spa", "bowling_alley", "ice_rink", "golf_course", "miniature_golf", "dog_park", "community_centre", "place_of_worship", "church", "mosque", "synagogue", "temple", "monastery", "embassy", "courthouse", "townhall", "public_building", "memorial", "monument", "ruins", "castle", "fort", "archaeological_site"
]

def filter_poi_by_types(pois, poi_types):
    filtered = []
    for poi in pois:
        kinds = poi.get("kinds", "")
        if any(ptype in kinds for ptype in poi_types):
            filtered.append(poi)
    return filtered

async def get_recommendations_for_user(db: AsyncSession, user: User):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Определяем position
    position = profile.hometown or DEFAULT_POSITION
    logger.info(f"[recommend] User hometown/raw position: {position}")

    # Если position не содержит запятой (т.е. это не координаты, а город), преобразуем в координаты
    if "," not in position:
        try:
            logger.info(f"[recommend] Trying to geocode city name: {position}")
            geo_data = forward_geocode(position)
            lat = geo_data["lat"]
            lon = geo_data["lon"]
            position = f"{lat},{lon}"
            logger.info(f"[recommend] Geocoded city '{position}' to coordinates: {lat}, {lon}")
        except Exception as e:
            logger.error(f"[recommend] Failed to geocode city '{position}': {e}. Using default Moscow.", exc_info=True)
            position = DEFAULT_POSITION
            lat, lon = position.split(",")
    else:
        lat, lon = position.split(",")
        logger.info(f"[recommend] Using provided coordinates: {lat}, {lon}")

    # Получаем погоду
    try:
        from app.services import weather as weather_service
        w = weather_service.get_current_weather(position)
        temp = w['current_weather']['temperature']
        code = w['current_weather']['weathercode']
        weather = f"{temp}°C, code {code}"
        logger.info(f"[recommend] Weather: {weather}")
    except Exception as e:
        logger.warning(f"[recommend] Weather fetch failed: {e}")
        weather = "unknown"

    # Получаем локальное время и временную зону
    try:
        tz_info = timezone_service.get_timezone_utc(position)
        utc_offset = tz_info.get("utc_offset_seconds", 0)
        now_utc = datetime.datetime.utcnow()
        local_time = now_utc + datetime.timedelta(seconds=utc_offset)
        local_time_str = local_time.strftime("%Y-%m-%d %H:%M:%S")
        timezone_name = tz_info.get("timezone", "")
        logger.info(f"[recommend] Local time: {local_time_str}, Timezone: {timezone_name}")
    except Exception as e:
        logger.warning(f"[recommend] Timezone fetch failed: {e}")
        local_time_str = ""
        timezone_name = ""

    # Получаем реальные POI через OpenTripMap
    nearby_places = []
    pois = []
    try:
        if lat and lon:
            for radius in [25000,30000,35000,40000,45000,50000,60000,70000,80000]:
                logger.info(f"[recommend] Fetching POI from OpenTripMap for {lat}, {lon} with radius {radius}")
                pois = await fetch_poi_opentripmap(float(lat), float(lon), radius=radius, limit=50)
                pois = filter_poi_by_types(pois, POI_TYPES)
                logger.info(f"[recommend] Got {len(pois)} filtered POI from OpenTripMap with radius {radius}")
                if pois:
                    break
            if not pois:
                logger.warning("[recommend] No POI found even with large radius!")
        for poi in pois:
            nearby_places.append({
                "name": poi.get("name", ""),
                "type": poi.get("kinds", ""),
                "lat": poi.get("point", {}).get("lat"),
                "lon": poi.get("point", {}).get("lon"),
                "address": poi.get("address", "")
            })
    except Exception as e:
        logger.error(f"[recommend] Error fetching POI from OpenTripMap: {e}", exc_info=True)
        nearby_places = []

    # Если после всех попыток nearby_places пустой — логируем и отправляем пустой список в ML
    if not nearby_places:
        logger.warning("[recommend] WARNING: No relevant POI found for user, sending empty nearby_places to ML.")

    payload = {
        "position": position,
        "age": profile.age if profile.age is not None else None,
        "gender": profile.sex or "",
        "description": profile.description or "",
        "weather": weather,
        "local_time": local_time_str,
        "timezone": timezone_name,
        "nearby_places": nearby_places[:50] if nearby_places else None  # None если пусто
    }
    logger.info(f"[recommend] ML payload: {payload}")

    try:
        async with httpx.AsyncClient() as client:
            logger.info("[RECOMMEND] Calling ML service at: http://ego-ai-ml-service:8001/recommend/")
            response = await client.post(
                "http://ego-ai-ml-service:8001/recommend/",
                json=payload,
                timeout=60.0
            )
            
            # Log raw response content
            raw_content = response.text
            logger.info(f"[RECOMMEND] ML service raw response: {raw_content}")
            
            response.raise_for_status()
            
            try:
                ml_response = response.json()
                logger.info(f"[RECOMMEND] ML service parsed JSON: {ml_response}")
            except Exception as json_error:
                logger.error(f"[RECOMMEND] Failed to parse ML response as JSON: {json_error}")
                logger.error(f"[RECOMMEND] Raw response that failed to parse: {raw_content}")
                raise HTTPException(status_code=500, detail=f"ML service returned invalid JSON: {raw_content}")
            
            logger.info(f"[RECOMMEND] Final response to frontend: {ml_response}")
            
            # Transform ML response to match frontend expectations
            if isinstance(ml_response, dict) and "recommendations" in ml_response:
                recommendations = ml_response["recommendations"]
            elif isinstance(ml_response, list):
                recommendations = ml_response
            else:
                recommendations = [ml_response]
            
            # Transform each recommendation to match frontend format
            transformed_recommendations = []
            timestamp = int(datetime.datetime.now().timestamp())
            for i, rec in enumerate(recommendations):
                if isinstance(rec, dict):
                    # Extract and validate coordinates
                    try:
                        lat = float(rec.get("latitude", 0))
                        lon = float(rec.get("longitude", 0))
                        
                        # Validate coordinate ranges
                        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                            logger.warning(f"[RECOMMEND] Invalid coordinates for recommendation {i}: lat={lat}, lon={lon}")
                            continue
                            
                    except (ValueError, TypeError) as e:
                        logger.error(f"[RECOMMEND] Failed to parse coordinates for recommendation {i}: {e}")
                        continue
                    
                    transformed_rec = {
                        "id": f"rec_{timestamp}_{i}",  # Unique ID: timestamp + index
                        "title": rec.get("name", "Unknown Place"),  # ML: name → Frontend: title
                        "description": rec.get("description", ""),  # ✅ совпадает
                        "address": f"{lat:.6f}, {lon:.6f}",  # Create address from coordinates with precision
                        "lat": lat,  # ML: latitude → Frontend: lat
                        "lon": lon,  # ML: longitude → Frontend: lon
                        "category": "Recommendation",  # Default category
                        "rating": float(rec.get("confidence", 5)) / 2,  # Convert confidence (0-10) to rating (0-5)
                        "createdAt": datetime.datetime.now().isoformat(),
                        "updatedAt": datetime.datetime.now().isoformat()
                    }
                    
                    logger.info(f"[RECOMMEND] Transformed recommendation {i}: {transformed_rec}")
                    transformed_recommendations.append(transformed_rec)
            
            final_response = {
                "recommendations": transformed_recommendations
            }
            
            logger.info(f"[RECOMMEND] Transformed response for frontend: {final_response}")
            
            # Log the actual response that will be sent
            import json
            response_json = json.dumps(final_response, ensure_ascii=False)
            logger.info(f"[RECOMMEND] Final response JSON string: {response_json}")
            logger.info(f"[RECOMMEND] Final response content-type: application/json")
            
    except Exception as e:
        logger.error(f"[RECOMMEND] ML service error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"ML service error: {e}")

    return final_response
