from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional, Dict, Any, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserMe(BaseModel):
    id: UUID4
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    location: Optional[str] = None
    type: str  # 'focus', 'tasks', 'target', 'other'

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    location: Optional[str] = None
    type: Optional[str] = None

class Event(EventBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReminderBase(BaseModel):
    remind_at: datetime
    method: str

class ReminderCreate(ReminderBase):
    event_id: UUID4

class ReminderUpdate(BaseModel):
    remind_at: Optional[datetime] = None
    method: Optional[str] = None

class Reminder(ReminderBase):
    id: UUID4
    event_id: UUID4

    class Config:
        from_attributes = True


class AI_InteractionBase(BaseModel):
    input_text: str
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    response_text: str

class AI_InteractionCreate(AI_InteractionBase):
    user_id: UUID4

class AI_Interaction(AI_InteractionBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True


class User_SettingsBase(BaseModel):
    timezone: str
    language: str

class User_SettingsCreate(User_SettingsBase):
    user_id: UUID4

class User_SettingsUpdate(BaseModel):
    timezone: Optional[str] = None
    language: Optional[str] = None

class User_Settings(User_SettingsBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileBase(BaseModel):
    name: str
    surname: str
    age: str
    sex: str
    description: Optional[str] = None
    hometown: str

class UserProfileCreate(UserProfileBase):
    user_id: UUID4

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    age: Optional[str] = None
    sex: Optional[str] = None
    description: Optional[str] = None
    hometown: Optional[str] = None

class UserProfile(UserProfileBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None


class LLM_ChatRequest(BaseModel):
    message: str


class LLM_ChatResponse(BaseModel):
    response: str

class Message(BaseModel):
    role: str
    content: str

class AddMessageRequest(BaseModel):
    user_id: str
    role: str
    content: str