from sqlalchemy.orm import Session
from uuid import UUID
from app.database.models.models import UserProfile
from app.database.schemas.schemas import UserProfileCreate, UserProfileUpdate
from fastapi import HTTPException

def create_profile(db: Session, profile: UserProfileCreate):
    db_profile = db.query(UserProfile).filter(UserProfile.user_id == profile.user_id).first()
    if db_profile:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")
    new_profile = UserProfile(**profile.model_dump())
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile

def get_profile(db: Session, user_id: UUID):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

def update_profile(db: Session, user_id: UUID, update: UserProfileUpdate):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def get_profile_with_weather(db: Session, user_id: UUID):
    from app.services import weather as weather_service
    profile = get_profile(db, user_id)
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
