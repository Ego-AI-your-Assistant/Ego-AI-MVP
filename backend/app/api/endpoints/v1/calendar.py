from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import httpx
import os
from typing import Optional, List
from datetime import datetime
import uuid
from fastapi.encoders import jsonable_encoder
import re
import json
from fastapi import status

from app.database.session import get_db
from app.database import models, schemas
from app.utils.deps import get_current_user
from app.services.event import EventService
from app.services.recommend import get_recommendations_for_user

router = APIRouter()

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ego-ai-ml-service:8001/chat")

class CalendarInterpretRequest(BaseModel):
    text: str
    location: str  

class ChatRequest(BaseModel):
    message: str
    calendar: Optional[list] = None

def serialize_event(event):
    return {
        "summary": event.title,
        "start": event.start_time.isoformat() if event.start_time else "",
        "end": event.end_time.isoformat() if event.end_time else "",
        "location": event.location or ""
    }

async def handle_ml_calendar_intent(ml_response_data, db, current_user):
    from app.services.event import EventService
    import uuid
    
    print(f"handle_ml_calendar_intent received: {ml_response_data}, type: {type(ml_response_data)}")
    
    event_service = EventService(db)
    user_id = uuid.UUID(str(current_user.id))

    async def add_event(event_data):
        try:
            from app.database import schemas
            event_in = schemas.EventCreate(**event_data)
            created_event = await event_service.create(event_in, user_id)
            return {"status": "added", "event": created_event}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def delete_event(event_data):
        title = event_data.get("title")
        start_time = event_data.get("start_time")
        result = await db.execute(
            models.Event.__table__.select().where(
                (models.Event.user_id == user_id) &
                (models.Event.title == title) &
                (models.Event.start_time == start_time)
            )
        )
        event = result.fetchone()
        if event:
            await event_service.delete(event.id, current_user)
            return {"status": "deleted"}
        return {"status": "not_found"}

    async def update_event(event_data):
        title = event_data.get("title")
        start_time = event_data.get("start_time")
        result = await db.execute(
            models.Event.__table__.select().where(
                (models.Event.user_id == user_id) &
                (models.Event.title == title) &
                (models.Event.start_time == start_time)
            )
        )
        event = result.fetchone()
        if event:
            try:
                from app.database import schemas
                event_in = schemas.EventUpdate(**event_data)
                updated_event = await event_service.update(event.id, event_in, current_user)
                return {"status": "changed", "event": updated_event}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "not_found"}

    # Check if it's a dictionary with intent and event
    if isinstance(ml_response_data, dict) and "intent" in ml_response_data and "event" in ml_response_data:
        print(f"Valid calendar intent detected: {ml_response_data['intent']}")
        if ml_response_data["intent"] == "add":
            return await add_event(ml_response_data["event"])
        elif ml_response_data["intent"] == "delete":
            return await delete_event(ml_response_data["event"])
        elif ml_response_data["intent"] == "update":
            return await update_event(ml_response_data["event"])
        else:
            return {"status": "unknown_intent", "message": f"Unknown intent: {ml_response_data['intent']}"}
    
    # If it's a plain text response
    if isinstance(ml_response_data, str):
        print(f"Plain text response received: {ml_response_data}")
        # Try to parse it as JSON in case it's a stringified JSON
        try:
            json_data = json.loads(ml_response_data)
            if isinstance(json_data, dict) and "intent" in json_data and "event" in json_data:
                print(f"Found JSON intent in string: {json_data['intent']}")
                if json_data["intent"] == "add":
                    return await add_event(json_data["event"])
                elif json_data["intent"] == "delete":
                    return await delete_event(json_data["event"])
                elif json_data["intent"] == "update":
                    return await update_event(json_data["event"])
                else:
                    return {"status": "unknown_intent", "message": f"Unknown intent: {json_data['intent']}"}
        except (json.JSONDecodeError, TypeError):
            # Not JSON, normal text response
            pass
    
    print(f"Invalid/non-calendar response: {ml_response_data}")
    return {"status": "invalid_response", "data": ml_response_data}

@router.post("/interpret")
async def interpret_and_create_event(
    request: CalendarInterpretRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        models.Event.__table__.select().where(models.Event.user_id == current_user.id)
    )
    events = result.fetchall()
    calendar = [serialize_event(e) for e in [row for row in events]]
    print("calendar to send:", calendar)
    user_location = request.location
    timezone_value = None
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            tz_response = await client.get(f"http://localhost:8000/timezone?location={user_location}")
            tz_response.raise_for_status()
            tz_data = tz_response.json()
            # Получаем текущее UTC время
            from datetime import datetime, timezone as dt_timezone
            now_utc = datetime.now(dt_timezone.utc)
            timezone_value = now_utc.isoformat()
    except Exception as e:
        print(f"Не удалось получить временную зону: {e}")
        timezone_value = None
    payload = {
        "message": request.text,
        "calendar": calendar,
        "timezone": timezone_value
    }
    try:
        async with httpx.AsyncClient() as client:
            print(f"Sending request to ML service: {payload}")
            response = await client.post(
                ML_SERVICE_URL,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            ml_response_data = response.json()
            print(f"ML service response: {ml_response_data}")
            
            # Check if the response data is from the response field
            if isinstance(ml_response_data, dict) and "response" in ml_response_data:
                # Extract the actual response from the ML service wrapper
                try:
                    ml_response_string = ml_response_data["response"]
                    # Try to parse the response as JSON
                    ml_response_data = json.loads(ml_response_string)
                    print(f"Parsed ML response as JSON: {ml_response_data}")
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Failed to parse ML response as JSON: {e}")
                    # If it's not valid JSON, use it as is (plain text)
                    ml_response_data = ml_response_string
    except httpx.RequestError as e:
        print(f"Error connecting to ML service: {e}")
        raise HTTPException(status_code=503, detail=f"Could not connect to the ML service: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting response from ML service: {e}")

    print(f"Handling intent with data: {ml_response_data}")
    intent_result = await handle_ml_calendar_intent(ml_response_data, db, current_user)
    print(f"Intent result: {intent_result}")

    if intent_result.get("status") in ["added", "deleted", "changed"]:
        return {"status": intent_result["status"]}
    elif intent_result.get("status") == "invalid_response":
        return {"status": "invalid_response", "data": intent_result.get("data")}
    else:
        return {"status": "error", "message": "Unexpected response from ML service."}

@router.get("/get_tasks", response_model=List[schemas.Event])
async def get_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    event_service = EventService(db)
    events = await event_service.get_events_by_user(uuid.UUID(str(current_user.id)))
    return events

@router.post("/set_task", response_model=schemas.Event)
async def set_task(
    event_in: schemas.EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    event_service = EventService(db)
    created_event = await event_service.create(event_in, uuid.UUID(str(current_user.id)))
    return created_event

@router.delete("/delete_task", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    event_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    event_service = EventService(db)
    await event_service.delete(event_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

class GetTasksByTimeRequest(BaseModel):
    start_time: datetime
    end_time: datetime

@router.post("/get_tasks_by_time", response_model=List[schemas.Event])
async def get_tasks_by_time(
    time_range: GetTasksByTimeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    event_service = EventService(db)
    events = await event_service.get_events_by_date_range(uuid.UUID(str(current_user.id)), time_range.start_time, time_range.end_time)
    return events

@router.put("/update_task/{event_id}", response_model=schemas.Event)
async def update_task(
    event_id: uuid.UUID,
    event_in: schemas.EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    event_service = EventService(db)
    updated_event = await event_service.update(event_id, event_in, current_user)
    return updated_event

@router.get("/recommend")
async def recommend(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return await get_recommendations_for_user(db, current_user)
