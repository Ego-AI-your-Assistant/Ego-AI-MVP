import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import re, json
from ML.chat import Chat

model = Chat("llama3-70b-8192", "key")

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

class RescheduleRequest(BaseModel):
    calendar: List[CalendarEvent]

class RescheduleResponse(BaseModel):
    suggestion: str
    new_calendar: Optional[List[CalendarEvent]] = None

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
        "You are an expert time-management assistant. "
        "Analyze the user's calendar and suggest a slightly more convenient or balanced schedule. "
        "Do not focus only on maximum productivity. "
        "All events from the original calendar must be preserved (you may only change their order or time, but do not remove or add events). "
        "Give a short summary of your suggestion (1-2 sentences). "
        "In your summary, clearly specify what exactly was changed (for example, which events were moved or swapped). "
        "Then, return the new optimized calendar as a JSON array of events with fields: summary, start, end, location. "
        f"Today: {today}\n"
        f"User's calendar:\n\n{calendar_context}"
    )
    return {"role": "system", "content": content}

@app.post("/reschedule", response_model=RescheduleResponse)
def reschedule(req: RescheduleRequest):
    try:
        system_prompt = build_reschedule_prompt([e.model_dump() for e in req.calendar])
        messages = [system_prompt, {"role": "user", "content": "Please optimize my schedule for maximum productivity."}]
        suggestion_full = model.chat(messages)
        json_match = re.search(r'(\[.*\])', suggestion_full, re.DOTALL)
        new_calendar = None
        if json_match:
            try:
                new_calendar = json.loads(json_match.group(1))
            except Exception:
                new_calendar = None

        short_suggestion = suggestion_full.split('\n')[0]
        return RescheduleResponse(suggestion=short_suggestion, new_calendar=new_calendar)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    uvicorn.run("ml_calendar_chat_api:app",
                host="0.0.0.0", port=8002, reload=True)
