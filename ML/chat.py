import datetime
import whisper
import requests
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")


class Chat:
    """Wrapper for Groq LLM chat API."""

    def __init__(self, model_name, api_key):
        """
        Initialize the Chat class.

        Args:
            model_name (str): Name of the LLM model.
            api_key (str): API key for Groq.
        """
        self.model = model_name
        self.api_key = api_key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def chat(self, messages):
        """
        Sends a chat completion request to Groq API.

        Args:
            messages (list): List of message dicts for the LLM.

        Returns:
            str: Model's reply.
        """
        try:
            logger.info(f"Sending request to Groq API with {len(messages)} messages")
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.5
                },
                timeout=30
            )
            logger.info(f"Response status: {response.status_code}")
            if not response.ok:
                logger.warning(f"Response content: {response.text}")
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise
        except KeyError as e:
            logger.error(f"Response parsing error: {e}, Response: {response.text if 'response' in locals() else 'No response'}")
            raise
        except Exception as e:
            logger.exception("Unexpected error in chat method")
            raise

model = Chat("llama3-70b-8192", GROQ_API_KEY)
model_voice = whisper.load_model("tiny")


def format_event(event):
    """
    Formats a calendar event for prompt context.

    Args:
        event (dict): Event data.

    Returns:
        str: Formatted event string.
    """
    try:
        if not isinstance(event, dict):
            return f"- Invalid event format: {event}"
        start_field = event.get("start") or event.get("start_time")
        end_field = event.get("end") or event.get("end_time")
        summary = event.get("summary") or event.get("title", "Untitled event")
        if not start_field or not end_field:
            return f"- {summary} (incomplete event data)"
        start = datetime.datetime.fromisoformat(
            start_field.replace("Z", "+00:00")).strftime("%B %d, %Y %I:%M %p")
        end = datetime.datetime.fromisoformat(
            end_field.replace("Z", "+00:00")).strftime("%I:%M %p")
        location = event.get("location", "Unknown location")
        return f"- {summary} from {start} to {end} at {location}"
    except Exception as e:
        logger.error(f"Error formatting event {event}: {e}")
        summary = event.get("summary") or event.get("title", "Unknown event")
        return f"- {summary} (formatting error)"


def build_system_prompt(calendar_data=None, timezone="UTC+3"):
    """
    Builds a system prompt for the LLM based on the user's calendar.

    Args:
        calendar_data (list, optional): List of calendar events.
        timezone (str, optional): User's timezone.

    Returns:
        dict: System prompt for the LLM.
    """
    today = datetime.datetime.now().strftime("%B %d, %Y")
    try:
        if calendar_data:
            logger.info(f"Processing {len(calendar_data)} calendar events")
            calendar_context = "\n".join(format_event(e) for e in calendar_data if e)
        else:
            calendar_context = "No calendar events available"
    except Exception as e:
        logger.error(f"Error processing calendar data: {e}")
        calendar_context = "Error loading calendar events"

    content = (
        "You are a helpful assistant who answers questions about the user's calendar and general productivity tips and also just friend. "
        "Always reply in the same language as the user's message: if the user writes in English, answer in English; if in Russian, answer in Russian. "
        "You may answer any general questions, not only about the calendar. "
        "If the user asks about their calendar, provide information about upcoming events, free time, and general productivity tips. "
        "If the user wants to add, delete, or update a calendar event, respond ONLY with a valid JSON object in the following format:\n"
        "{\n"
        '  "intent": "add" | "delete" | "update",\n'
        '  "event": {\n'
        '    "title": "...",\n'
        '    "description": "...",\n'
        '    "start_time": "YYYY-MM-DD HH:MM:SS+03:00",\n'
        '    "end_time": "YYYY-MM-DD HH:MM:SS+03:00",\n'
        '    "all_day": true | false,\n'
        '    "location": "...",\n'
        '    "type": "..."\n'
        "  }\n"
        "}\n"
        "IMPORTANT: Always use the exact timezone format with colon (+03:00) for start_time and end_time fields. Never use +0300 format.\n"
        "If the user does not specify the event type, use 'other work' by default. "
        "For normal answers (not related to calendar editing), reply in plain natural language with no special formatting, no escape characters, and no code or Markdown syntax — just clean human-readable text."
        "If the user's message is a greeting (like \"Hello\", \"Hi\", etc.), respond in a friendly and natural way without mentioning the calendar or productivity, unless explicitly asked."
        "Base your answers on the provided calendar and general knowledge, but do not focus only on the calendar. "
        f"Today: {today}\n"
        f"Here is the user's calendar:\n\n{calendar_context}\n"
        "When creating or updating tasks, always use Moscow timezone (+03:00 format).\n"
        "Use only the timezone format with colon: +03:00, never +0300 or GMT+3."
    )
    return {"role": "system", "content": content}


app = FastAPI(title="ML Calendar Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    calendar: Optional[List[dict]] = None
    history: Optional[List[dict]] = None
    timezone: Optional[str] = "55.75,37.61"


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str


class VoiceResponse(BaseModel):
    """Response model for voice chat endpoint."""
    transcription: str
    response: str


@app.post("/", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Handles chat requests, builds prompt, sends to LLM, and returns the response.

    Args:
        req (ChatRequest): Incoming chat request.

    Returns:
        ChatResponse: LLM's reply.
    """
    try:
        logger.info(f"Received chat request: {req.message[:50]}...")
        if req.history:
            print(f"Chat history provided: {len(req.history)} messages")
        
        system_prompt = build_system_prompt(req.calendar, req.timezone)
        
        # Сжимаем историю, если сообщений >= 50
        messages = [system_prompt]
        history = req.history or []
        if len(history) >= 50:
            # Собираем текстовую историю для сжатия
            history_text = '\n'.join([f"{m.get('role','user')}: {m.get('content','')}" for m in history])
            compress_prompt = {
                "role": "system",
                "content": "Сожми следующую историю чата в 3-6 предложений, сохраняя суть диалога:"
            }
            compress_user = {"role": "user", "content": history_text}
            summary = model.chat([compress_prompt, compress_user])
            # Заменяем историю на одно сжатое сообщение
            messages.append({"role": "system", "content": f"История чата (сжата): {summary}"})
        else:
            for hist_msg in history:

                if isinstance(hist_msg, dict) and 'role' in hist_msg and 'content' in hist_msg:
                    role = hist_msg['role']
                    if role == 'llm':
                        role = 'assistant'
                    messages.append({"role": role, "content": hist_msg['content']})

        messages.append({"role": "user", "content": req.message})

        logger.info(f"Built messages with system prompt + history + current, total messages: {len(messages)}")
        reply = model.chat(messages)
        logger.info(f"Got reply from model: {reply[:50] if reply else 'None'}...")
        return ChatResponse(response=reply)
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ML Service Error: {str(e)}")


@app.post("/voice", response_model=VoiceResponse)
def voice_chat(file: UploadFile = File(...)):
    """
    Handles voice chat requests: transcribes audio and gets LLM response.

    Args:
        file (UploadFile): Uploaded audio file.

    Returns:
        VoiceResponse: Transcription and LLM's reply.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        result = model_voice.transcribe(tmp_path, fp16=False)
        text = result["text"].strip()

        system_prompt = build_system_prompt()
        messages = [system_prompt, {"role": "user", "content": text}]
        reply = model.chat(messages)

        return VoiceResponse(transcription=text, response=reply)
    except Exception as e:
        logger.error(f"Voice chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ML Service Error: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    logger.info(f"Starting ML service with GROQ_API_KEY: {'*' * (len(GROQ_API_KEY) - 4) + GROQ_API_KEY[-4:] if GROQ_API_KEY else 'NOT SET'}")
    uvicorn.run("chat:app",
                host="0.0.0.0", port=8001, reload=True)
