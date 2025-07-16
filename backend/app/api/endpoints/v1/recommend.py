from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.deps import get_current_user, get_db
from app.database.models.models import User
from app.services.recommend import get_recommendations_for_user

router = APIRouter()

@router.post("/recommend", summary="Personalized place recommendations", tags=["recommend"])
async def recommend(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_recommendations_for_user(db, current_user) 
