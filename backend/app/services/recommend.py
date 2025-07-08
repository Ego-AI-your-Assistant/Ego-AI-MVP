from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models.models import User, UserProfile
import httpx

async def get_recommendations_for_user(db: AsyncSession, user: User):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    weather = None
    try:
        from app.services import weather as weather_service
        w = weather_service.get_current_weather(profile.hometown)
        temp = w['current_weather']['temperature']
        code = w['current_weather']['weathercode']
        weather = f"{temp}°C, code {code}"
    except Exception:
        weather = None

    payload = {
        "position": profile.hometown,
        "age": profile.age,
        "gender": profile.sex,
        "description": profile.description or "",
        "weather": weather or ""
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/recommend",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            ml_response = response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ML service error: {e}")

    return ml_response
