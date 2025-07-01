from fastapi import APIRouter, Depends
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models import AI_Interaction, User
from app.schemas import AI_Interaction as AI_InteractionSchema
from app.utils.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[AI_InteractionSchema])
async def get_interaction_history(
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    interaction_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[AI_InteractionSchema]:
    query = select(AI_Interaction).where(AI_Interaction.user_id == current_user.id)

    if start_date:
        query = query.where(AI_Interaction.created_at >= start_date)
    if end_date:
        query = query.where(AI_Interaction.created_at <= end_date)
    if interaction_type:
        query = query.where(AI_Interaction.intent == interaction_type)

    result = await db.execute(query)
    return result.scalars().all()
