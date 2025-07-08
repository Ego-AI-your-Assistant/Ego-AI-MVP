from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database.models.models import UserProfile as UserProfileModel
from app.database.schemas.schemas import UserProfileCreate, UserProfileUpdate
from fastapi import HTTPException

async def create_profile(db: AsyncSession, profile: UserProfileCreate):
    result = await db.execute(select(UserProfileModel).filter(UserProfileModel.user_id == profile.user_id))
    db_profile = result.scalar_one_or_none()
    if db_profile:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")
    new_profile = UserProfileModel(**profile.model_dump())
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile

async def get_profile(db: AsyncSession, user_id: UUID):
    result = await db.execute(select(UserProfileModel).filter(UserProfileModel.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

async def update_profile(db: AsyncSession, user_id: UUID, update: UserProfileUpdate):
    result = await db.execute(select(UserProfileModel).filter(UserProfileModel.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_profile_with_weather(db: AsyncSession, user_id: UUID):
    from app.services import weather as weather_service
    profile = await get_profile(db, user_id)
    hometown = profile.hometown
    weather = None
    if hometown:
        try:
            weather = weather_service.get_current_weather(hometown)
        except Exception as e:
            weather = {"error": str(e)}
    return {
        "age": profile.age,
        "sex": profile.sex,
        "description": profile.description,
        "hometown": profile.hometown,
        "weather": weather
    }
