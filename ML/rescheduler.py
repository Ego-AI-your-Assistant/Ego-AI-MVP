import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import re, json
from chat import Chat
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

model = Chat("llama3-70b-8192", GROQ_API_KEY)

app = FastAPI(title="ML Calendar Rescheduler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CalendarEvent(BaseModel):
    summary: str
    start: str 
    end: str    
    location: Optional[str] = None

class RescheduleEvent(BaseModel):
    event: CalendarEvent

class RescheduleRequest(BaseModel):
    calendar: List[CalendarEvent]

class RescheduleResponse(BaseModel):
    suggestion: str
    new_calendar: Optional[List[RescheduleEvent]] = None

def build_reschedule_prompt(calendar_data: List[dict]) -> dict:
    today = datetime.datetime.now().strftime("%B %d, %Y")
    events = []
    for e in calendar_data:
        start = datetime.datetime.fromisoformat(e["start"].replace("Z", "+00:00")).strftime("%B %d, %Y %I:%M %p")
        end = datetime.datetime.fromisoformat(e["end"].replace("Z", "+00:00")).strftime("%I:%M %p")
        location = e.get("location", "Unknown location") or "Unknown location"
        events.append(f"- {e['summary']} from {start} to {end} at {location}")
    calendar_context = "\n".join(events)
    content = (
        "Reschedule task between 6 am and 11 pm"
        "You are an expert time-management assistant. "
        "Analyze the user's calendar and suggest a slightly more convenient or balanced schedule. "
        "Do not focus only on maximum productivity. "
        "All events from the original calendar must be preserved — you may only change their order or time, but do not remove or add events. "
        "Give a short summary of your suggestion (1–2 sentences). "
        "In your summary, clearly specify what exactly was changed (e.g., which events were moved or swapped). "
        "Then return the new optimized calendar as a JSON array of events, using the following format:\n\n"
        "[\n"
        "  {\n"
        "    \"event\": {\n"
        "      \"summary\": \"Event title\",\n"
        "      \"start\": \"YYYY-MM-DDTHH:MM\",\n"
        "      \"end\": \"YYYY-MM-DDTHH:MM\",\n"
        "      \"location\": \"Event location\"\n"
        "    }\n"
        "  },\n"
        "  ...\n"
        "]\n\n"
        "Only return the JSON — do not include anything else after it.\n"
        f"Today: {today}\n"
        f"User's calendar:\n\n{calendar_context}"
    )
    return {"role": "system", "content": content}

@app.post("/", response_model=RescheduleResponse)
def reschedule(req: RescheduleRequest):
    try:
        system_prompt = build_reschedule_prompt([e.model_dump() for e in req.calendar])
        messages = [system_prompt, {"role": "user", "content": "Please optimize my schedule for maximum productivity."}]
        suggestion_full = model.chat(messages)
        json_match = re.search(r'(\[.*\])', suggestion_full, re.DOTALL)
        new_calendar = None
        if json_match:
            try:
                raw_calendar = json.loads(json_match.group(1))
                # The AI is expected to return a list of {"event": {...}}
                # We just need to validate it matches our Pydantic models
                if raw_calendar and isinstance(raw_calendar[0], dict) and 'event' in raw_calendar[0]:
                     new_calendar = raw_calendar
                else: # If the AI returns a flat list, wrap it
                    new_calendar = [{"event": item} for item in raw_calendar]

            except Exception:
                new_calendar = None
        short_suggestion = suggestion_full.split('\n')[0]
        return RescheduleResponse(suggestion=short_suggestion, new_calendar=new_calendar)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
