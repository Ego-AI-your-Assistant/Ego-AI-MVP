from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.database.models.models import UserProfile
from app.database.schemas.schemas import UserProfile, UserProfileCreate, UserProfileUpdate
from app.database.session import get_db
from app.services import profile as profile_service
from app.database.models.models import User
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/users/profile/weather")
def get_profile_with_weather_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return profile_service.get_profile_with_weather(db, current_user.id)

@router.post("/users/profile", response_model=UserProfile)
def create_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    return profile_service.create_profile(db, profile)

@router.get("/users/profile", response_model=UserProfile)
def get_own_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = profile_service.get_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/users/profile", response_model=UserProfile)
def update_own_profile(update: UserProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return profile_service.update_profile(db, current_user.id, update)
