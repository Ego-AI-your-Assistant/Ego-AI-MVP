from app.services.geo import forward_geocode
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
    location: Optional[str] = None

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
    from app.database import schemas

    print(f"handle_ml_calendar_intent received: {ml_response_data}, type: {type(ml_response_data)}")

    event_service = EventService(db)
    user_id = uuid.UUID(str(current_user.id))

    def validate_event_data(event_data):
        # Only require start_time, title is optional for fallback logic
        required_fields = ["start_time"]
        for field in required_fields:
            if field not in event_data:
                return False, f"Missing required field: {field}"
        return True, ""

    async def add_event(event_data):
        is_valid, error_message = validate_event_data(event_data)
        if not is_valid:
            return {"status": "error", "message": error_message}
        from dateutil import parser
        # Parse and normalize start_time and end_time
        for field in ["start_time", "end_time"]:
            if field in event_data and isinstance(event_data[field], str):
                try:
                    dt = parser.parse(event_data[field])
                    event_data[field] = dt
                except Exception:
                    return {"status": "error", "message": f"Invalid {field} format: {event_data[field]}"}
        try:
            event_in = schemas.EventCreate(**event_data)
            created_event = await event_service.create(event_in, user_id)
            return {"status": "added", "event": created_event}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def delete_event(event_data):
        is_valid, error_message = validate_event_data(event_data)
        if not is_valid:
            return {"status": "error", "message": error_message}
        from dateutil import parser
        from datetime import timezone
        import zoneinfo
        title = event_data.get("title")
        start_time = event_data.get("start_time")
        if isinstance(start_time, str):
            try:
                start_time = parser.parse(start_time)
            except Exception:
                return {"status": "error", "message": "Invalid start_time format"}
        # Always convert to UTC for comparison
        if start_time.tzinfo is None:
            try:
                moscow_tz = zoneinfo.ZoneInfo("Europe/Moscow")
                start_time = start_time.replace(tzinfo=moscow_tz)
            except Exception:
                start_time = start_time.replace(tzinfo=timezone.utc)
        start_time_utc = start_time.astimezone(timezone.utc)
        
        # Get all user events for searching
        result = await db.execute(
            models.Event.__table__.select().where(
                (models.Event.user_id == user_id)
            )
        )
        all_events = result.fetchall()
        
        # If title is present, try various matching strategies
        if title:
            title_lower = title.lower()
            
            # Strategy 1: Exact title and time match
            for event in all_events:
                if event.title and event.title.lower() == title_lower:
                    db_start_time = event.start_time
                    if db_start_time is not None and db_start_time.astimezone(timezone.utc) == start_time_utc:
                        await event_service.delete(event.id, current_user)
                        return {"status": "deleted", "message": "Deleted by exact title and time match"}
            
            # Strategy 2: Fuzzy title match with time match
            for event in all_events:
                event_title_lower = event.title.lower() if event.title else ""
                db_start_time = event.start_time
                
                # Check if titles have significant overlap (either contains the other)
                if (title_lower in event_title_lower or event_title_lower in title_lower) and \
                   db_start_time is not None and db_start_time.astimezone(timezone.utc) == start_time_utc:
                    await event_service.delete(event.id, current_user)
                    return {"status": "deleted", "message": "Deleted by fuzzy title and time match"}
            
            # Strategy 3: Fuzzy title match WITHOUT exact time match (for when user specifies wrong time)
            # Find events that contain the target title or vice versa
            matching_events = []
            for event in all_events:
                event_title_lower = event.title.lower() if event.title else ""
                # Check if titles have significant overlap (either contains the other)
                if title_lower in event_title_lower or event_title_lower in title_lower:
                    matching_events.append(event)
            
            if len(matching_events) == 1:
                # If only one event matches the title pattern, delete it regardless of time
                await event_service.delete(matching_events[0].id, current_user)
                return {"status": "deleted", "message": "Deleted by title match (time mismatch ignored)"}
            elif len(matching_events) > 1:
                # If multiple events match, try to use time to disambiguate
                for event in matching_events:
                    db_start_time = event.start_time
                    if db_start_time is not None and db_start_time.astimezone(timezone.utc) == start_time_utc:
                        await event_service.delete(event.id, current_user)
                        return {"status": "deleted", "message": "Deleted by title match with time disambiguation"}
                # If no time match, return error asking for clarification
                return {"status": "error", "message": f"Multiple events found with similar titles. Found {len(matching_events)} events. Please be more specific."}
            
            # Strategy 4: Exact time match without title consideration
            matching_events = [event for event in all_events if event.start_time is not None and event.start_time.astimezone(timezone.utc) == start_time_utc]
            if len(matching_events) == 1:
                await event_service.delete(matching_events[0].id, current_user)
                return {"status": "deleted", "message": "Deleted by time match (title mismatch ignored)"}
            
            return {"status": "not_found"}
        else:
            # Fallback: match by start_time only (warn if multiple)
            matching_events = [event for event in all_events if event.start_time is not None and event.start_time.astimezone(timezone.utc) == start_time_utc]
            if not matching_events:
                return {"status": "not_found"}
            if len(matching_events) > 1:
                return {"status": "error", "message": "Multiple events found at this time. Please specify the title."}
            await event_service.delete(matching_events[0].id, current_user)
            return {"status": "deleted", "message": "Deleted by start_time only (no title provided)"}

    async def update_event(event_data):
        is_valid, error_message = validate_event_data(event_data)
        if not is_valid:
            return {"status": "error", "message": error_message}
        from dateutil import parser
        from datetime import timezone
        import zoneinfo
        title = event_data.get("title")
        start_time = event_data.get("start_time")
        if isinstance(start_time, str):
            try:
                start_time = parser.parse(start_time)
            except Exception:
                return {"status": "error", "message": "Invalid start_time format"}
        # Always convert to UTC for comparison
        if start_time.tzinfo is None:
            try:
                moscow_tz = zoneinfo.ZoneInfo("Europe/Moscow")
                start_time = start_time.replace(tzinfo=moscow_tz)
            except Exception:
                start_time = start_time.replace(tzinfo=timezone.utc)
        start_time_utc = start_time.astimezone(timezone.utc)
        
        # Get all user events for searching
        result = await db.execute(
            models.Event.__table__.select().where(
                (models.Event.user_id == user_id)
            )
        )
        all_events = result.fetchall()
        
        # If title is present, try various matching strategies
        if title:
            title_lower = title.lower()
            
            # Strategy 1: Exact title and time match
            for event in all_events:
                if event.title and event.title.lower() == title_lower:
                    db_start_time = event.start_time
                    if db_start_time is not None and db_start_time.astimezone(timezone.utc) == start_time_utc:
                        try:
                            event_in = schemas.EventUpdate(**event_data)
                            updated_event = await event_service.update(event.id, event_in, current_user)
                            return {"status": "changed", "event": updated_event}
                        except Exception as e:
                            return {"status": "error", "message": str(e)}
            
            # Strategy 2: Fuzzy title match with time match
            for event in all_events:
                event_title_lower = event.title.lower() if event.title else ""
                db_start_time = event.start_time
                
                # Check if titles have significant overlap (either contains the other)
                if (title_lower in event_title_lower or event_title_lower in title_lower) and \
                   db_start_time is not None and db_start_time.astimezone(timezone.utc) == start_time_utc:
                    try:
                        event_in = schemas.EventUpdate(**event_data)
                        updated_event = await event_service.update(event.id, event_in, current_user)
                        return {"status": "changed", "event": updated_event}
                    except Exception as e:
                        return {"status": "error", "message": str(e)}
            
            # Strategy 3: Fuzzy title match WITHOUT exact time match (for when user specifies wrong time)
            # Find events that contain the target title or vice versa
            matching_events = []
            for event in all_events:
                event_title_lower = event.title.lower() if event.title else ""
                # Check if titles have significant overlap (either contains the other)
                if title_lower in event_title_lower or event_title_lower in title_lower:
                    matching_events.append(event)
            
            if len(matching_events) == 1:
                # If only one event matches the title pattern, update it regardless of time
                try:
                    event_in = schemas.EventUpdate(**event_data)
                    updated_event = await event_service.update(matching_events[0].id, event_in, current_user)
                    return {"status": "changed", "event": updated_event, "message": "Updated by title match (time mismatch ignored)"}
                except Exception as e:
                    return {"status": "error", "message": str(e)}
            elif len(matching_events) > 1:
                # If multiple events match, try to use time to disambiguate
                for event in matching_events:
                    db_start_time = event.start_time
                    if db_start_time is not None and db_start_time.astimezone(timezone.utc) == start_time_utc:
                        try:
                            event_in = schemas.EventUpdate(**event_data)
                            updated_event = await event_service.update(event.id, event_in, current_user)
                            return {"status": "changed", "event": updated_event}
                        except Exception as e:
                            return {"status": "error", "message": str(e)}
                # If no time match, return error asking for clarification
                return {"status": "error", "message": f"Multiple events found with similar titles. Found {len(matching_events)} events. Please be more specific."}
            
            # Strategy 4: Exact time match without title consideration
            matching_events = [event for event in all_events if event.start_time is not None and event.start_time.astimezone(timezone.utc) == start_time_utc]
            if len(matching_events) == 1:
                try:
                    event_in = schemas.EventUpdate(**event_data)
                    updated_event = await event_service.update(matching_events[0].id, event_in, current_user)
                    return {"status": "changed", "event": updated_event, "message": "Updated by time match (title mismatch ignored)"}
                except Exception as e:
                    return {"status": "error", "message": str(e)}
            
            return {"status": "not_found"}
        else:
            # Fallback: match by start_time only (warn if multiple)
            matching_events = [event for event in all_events if event.start_time is not None and event.start_time.astimezone(timezone.utc) == start_time_utc]
            if not matching_events:
                return {"status": "not_found"}
            if len(matching_events) > 1:
                return {"status": "error", "message": "Multiple events found at this time. Please specify the title."}
            try:
                event_in = schemas.EventUpdate(**event_data)
                updated_event = await event_service.update(matching_events[0].id, event_in, current_user)
                return {"status": "changed", "event": updated_event, "message": "Updated by start_time only (no title provided)"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

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

    return {"status": "error", "message": "Invalid response format"}


@router.post("/interpret")
async def interpret_and_create_event(
    request: CalendarInterpretRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # If the request text contains the word 'delete', try to parse and call delete_task directly
    if 'delete' in request.text.lower():
        try:
            # Try to extract event info from JSON in the text, if present
            ml_response_data = None
            try:
                ml_response_data = json.loads(request.text)
            except Exception:
                pass
            if ml_response_data and isinstance(ml_response_data, dict) and 'event' in ml_response_data:
                # Use the fallback delete_event logic from handle_ml_calendar_intent
                intent_result = await handle_ml_calendar_intent({"intent": "delete", "event": ml_response_data["event"]}, db, current_user)
                if intent_result.get("status") == "deleted":
                    return {"status": "deleted"}
                elif intent_result.get("status") == "not_found":
                    return {"status": "not_found"}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=intent_result.get("message", "Failed to delete event.")
                    )
            # If not JSON, fallback to ML logic below
        except Exception as e:
            print(f"Direct delete intent failed: {e}")
            # Fallback to ML logic below

    # Try to parse the request text as JSON first
    try:
        ml_response_data = json.loads(request.text)
        print(f"Request text is a JSON object: {ml_response_data}")
        # If it's a valid JSON, we can bypass the ML service call
        intent_result = await handle_ml_calendar_intent(ml_response_data, db, current_user)
        print(f"Intent result from direct JSON: {intent_result}")

        if intent_result.get("status") in ["added", "deleted", "changed"]:
            return {"status": intent_result["status"], "event": intent_result.get("event")}
        elif intent_result.get("status") == "not_found":
            return {"status": "not_found"}
        else: # Handle errors from handle_ml_calendar_intent
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=intent_result.get("message", "Failed to process calendar event.")
            )
    except (json.JSONDecodeError, TypeError):
        # If it's not a JSON, proceed with the original logic
        print("Request text is not a JSON, calling ML service.")

    result = await db.execute(
        models.Event.__table__.select().where(models.Event.user_id == current_user.id)
    )
    events = result.fetchall()
    calendar = [serialize_event(e) for e in events]
    print("calendar to send:", calendar)
    user_location = request.location
    timezone_value = None
    # If location is not provided, try to get city from user profile
    if not user_location or user_location == "UTC":
        # Get user's city from profile
        profile_result = await db.execute(
            models.User.__table__.select().where(models.User.id == current_user.id)
        )
        user_row = profile_result.fetchone()
        user_city = getattr(user_row, "hometown", None) if user_row else None
        if user_city:
            # Geocode city to coordinates
            try:
                async with httpx.AsyncClient() as client:
                    geo_resp = await client.get(
                        f"http://egoai.duckdns.org:8000/api/v1/geocode?city={user_city}"
                    )
                    geo_resp.raise_for_status()
                    geo_data = geo_resp.json()
                    lat = geo_data.get("lat")
                    lon = geo_data.get("lon")
                    if lat and lon:
                        user_location = f"{lat},{lon}"
            except Exception as e:
                print(f"Не удалось получить координаты города пользователя: {e}")
    try:
        async with httpx.AsyncClient() as client:
            tz_response = await client.get(f"http://egoai.duckdns.org:8000/api/v1/timezone?location={user_location or 'UTC'}")
            tz_response.raise_for_status()
            tz_data = tz_response.json()
            timezone_value = tz_data.get("timezone")
    except Exception as e:
        print(f"Не удалось получить временную зону: {e}")
        timezone_value = None
    payload = {
        "message": request.text,
        "calendar": calendar,
        "timezone": timezone_value
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
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
        return {"status": intent_result["status"], "event": intent_result.get("event")}
    elif intent_result.get("status") == "invalid_response":
        return {"status": "invalid_response", "data": intent_result.get("data")}
    elif intent_result.get("status") == "not_found":
        return {"status": "not_found"}
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=intent_result.get("message", "Unexpected response from ML service.")
        )

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

@router.get("/geocode")
async def geocode_city(city: str):
    """
    Geocode a city name to latitude and longitude.
    Returns: {"lat": float, "lon": float} or 404 if not found.
    """
    try:
        geo_data = forward_geocode(city)
        if geo_data and "lat" in geo_data and "lon" in geo_data:
            return {"lat": geo_data["lat"], "lon": geo_data["lon"]}
        else:
            raise HTTPException(status_code=404, detail="City not found or could not geocode.")
    except Exception as e:
        print(f"Geocoding error: {e}")
        raise HTTPException(status_code=500, detail="Internal geocoding error.")
