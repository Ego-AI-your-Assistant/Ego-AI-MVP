from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database.models.models import UserProfile as UserProfileModel
from app.database.schemas.schemas import UserProfile, UserProfileCreate, UserProfileUpdate
from app.database.session import get_db
from app.services import profile as profile_service
from app.database.models.models import User
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/users/profile/weather")
async def get_profile_with_weather_endpoint(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await profile_service.get_profile_with_weather(db, current_user.id)

@router.post("/users/profile", response_model=UserProfile)
async def create_profile(profile: UserProfileCreate, db: AsyncSession = Depends(get_db)):
    return await profile_service.create_profile(db, profile)

@router.get("/users/profile", response_model=UserProfile)
async def get_own_profile(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = await profile_service.get_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/users/profile", response_model=UserProfile)
async def update_own_profile(update: UserProfileUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await profile_service.update_profile(db, current_user.id, update)
