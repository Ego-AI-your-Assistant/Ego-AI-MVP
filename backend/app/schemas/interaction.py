from pydantic import BaseModel
from datetime import datetime

class AI_InteractionResponse(BaseModel):
    id: int
    user_id: int
    intent: str
    user_message: str
    ai_response: str
    created_at: datetime
    
    class Config:
        from_attributes = True
