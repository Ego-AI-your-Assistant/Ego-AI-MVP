# Ego_AI ML Services

## Description
This repository contains microservices on FastAPI for the Ego_AI intelligent assistant:
- **ML Calendar Chat API** — a chatbot for working with calendars, tasks, and productivity.
- **Geo Recommender API** — a geo-recommendation service based on location and user data.
- **Calendar Rescheduler API** — a service for optimizing the user's schedule.

---

## Structure
```
ML/
├── chat.py              # ML Calendar Chat API
├── geo_recommender.py   # Geo Recommender API
├── rescheduler.py       # Calendar Rescheduler API
├── requirements.txt
├── Dockerfile
└── audio/
```

---

## ML Calendar Chat API

**Description:**
Allows the user to communicate with an LLM assistant that:
- Answers questions about the calendar and productivity.
- Recognizes user intent (add, update, delete event) and returns structured JSON for automation.
- Supports voice input (Whisper).

**Main endpoints:**

- `POST /chat`  
  Input:  
  ```json
  {
    "message": "Add a meeting tomorrow at 3:00 p.m.",
    "calendar": [ ... ],
    "history": [ ... ],
    "timezone": "Europe/Moscow"
  }
  ```
  Output:  
  ```json
  {
    "response": "{ \"intent\": \"add\", \"event\": { ... } }"
  }
  ```

- `POST /voice`  
  Input: audio file (WAV)  
  Output: transcription and LLM response

---

## Geo Recommender API

**Description:**  
Generates recommendations for interesting places near the user, taking into account:
- Location (`position`)
- Age, gender, user description
- Weather

**Main endpoint:**

- `POST /recommend`  
  Input:  
  ```json
  {
    "position": "55.751244, 37.618423",
    "age": 25,
    "gender": "female",
    "description": "I love art",
    "weather": "sunny"
  }
  ```
  Output:  
  ```json
  {
    "recommendations": [
      {
        "name": "Tretyakov Gallery",
        "description": "Famous museum of Russian art",
        "latitude": 55.7414,
        "longitude": 37.6201,
        "confidence": 9.5
      },
      ...
    ]
  }
  ```

---

## Calendar Rescheduler API

**Description:**  
Optimizes the user's schedule by suggesting a more convenient order of events without losing any events.

**Main endpoint:**

- `POST /reschedule`  
  Input:  
  ```json
  {
    "calendar": [
      {
        "summary": "Meeting with the team",
        "start": "2025-07-15T10:00:00+03:00",
        "end": "2025-07-15T11:00:00+03:00",
        "location": "Office"
      },
      ...
    ]
  }
  ```
  Output:  
  ```json
  {
    "suggestion": "I moved the meeting with the team to 12:00 for greater convenience.",
    "new_calendar": [
      {
        "event": {
          "title": "Meeting with the team",
          "start_time": "2025-07-15T12:00:00+03:00",
          "end_time": "2025-07-15T13:00:00+03:00",
          "location": "Office",
          "type": "meeting"
        }
      },
      ...
    ]
  }
  ```

---

## Launch

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the required service:
   ```bash
   uvicorn chat:app --host 0.0.0.0 --port 8001
   uvicorn geo_recommender:app --host 0.0.0.0 --port 8003
   uvicorn rescheduler:app --host 0.0.0.0 --port 8002
   ```

3. Documentation is available at:
```
http://egoai.duckdns.org:8001/docs  
http://egoai.duckdns.org:8002/docs  
http://egoai.duckdns.org:8003/docs
```

---

## Notes

- The `GROQ_API_KEY` environment variable is required for operation.
- The `openai-whisper` package must be installed for voice input.
- All services support CORS for integration with the frontend.
