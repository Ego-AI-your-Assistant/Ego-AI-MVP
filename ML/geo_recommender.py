import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from chat import Chat
import os
import re
import json
import logging


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

model = Chat("llama3-70b-8192", GROQ_API_KEY)

app = FastAPI(title="Location-based Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class GeoRecommendationRequest(BaseModel):
    position: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    weather: Optional[str] = None
    local_time: Optional[str] = None
    timezone: Optional[str] = None
    nearby_places: Optional[List[dict]] = None
   

class RecommendationItem(BaseModel):
    name: str
    description: str
    latitude: float
    longitude: float
    confidence: float 


class GeoRecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]


def build_geo_prompt(data: GeoRecommendationRequest) -> dict:
    now = datetime.datetime.now()
    day_of_week = now.strftime("%A")
    date_str = now.strftime("%B %d, %Y")

    user_parts = []
    if data.age:
        user_parts.append(f"{data.age}-year-old")
    if data.gender:
        user_parts.append(data.gender)
    user_desc = " ".join(user_parts) if user_parts else "anonymous user"

    if data.description:
        user_desc += f" — {data.description.strip()}"

    # Добавляем информацию о локальном времени, если есть
    local_time_str = ""
    if hasattr(data, "local_time") and data.local_time:
        local_time_str = f"The user's local time is: {data.local_time}"
        if hasattr(data, "timezone") and data.timezone:
            local_time_str += f" ({data.timezone})"
        local_time_str += ".\n"

    # Добавляем nearby_places, если есть
    nearby_places_str = ""
    if hasattr(data, "nearby_places") and data.nearby_places:
        # Формируем краткий список POI для промпта
        poi_lines = []
        for poi in data.nearby_places:
            name = poi.get("name", "")
            poi_type = poi.get("type", "")
            address = poi.get("address", "")
            lat = poi.get("lat", "")
            lon = poi.get("lon", "")
            poi_lines.append(f"- {name} ({poi_type}), {address}, {lat},{lon}")
        nearby_places_str = (
            "Here is a list of real places nearby. Choose the best ones for the user from this list only.\n" +
            "\n".join(poi_lines) + "\n\n"
        )

    prompt = (
        f"You are a helpful and knowledgeable local guide.\n"
        f"The user is currently located at: {data.position or 'Unknown location'}.\n"
        f"Today is {day_of_week}, {date_str}, and the weather is: {data.weather or 'unknown'}.\n"
        f"{local_time_str}"
        f"{nearby_places_str}"
        f"The user is a {user_desc}.\n"
        f"Based on this information, recommend 3 interesting places nearby to visit.\n"
        f"For each place, return a valid JSON object with the following fields:\n"
        f"- name: string (the name of the place)\n"
        f"- description: string (brief description)\n"
        f"- latitude: float\n"
        f"- longitude: float\n"
        f"- confidence: float (0 to 10, how confident you are about this suggestion)\n\n"
        f"Respond ONLY with a JSON array of 3 objects like this:\n"
        f"[{{\"name\": \"...\", \"description\": \"...\", \"latitude\": ..., \"longitude\": ..., \"confidence\": ...}}, ...]"
    )

    return {"role": "system", "content": prompt}


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/recommend", response_model=GeoRecommendationResponse)
def recommend(req: GeoRecommendationRequest):
    try:
        logger.info(f"[ML] Incoming payload: {req.dict()}")
        system_prompt = build_geo_prompt(req)
        logger.info(f"[ML] Built system prompt: {system_prompt}")
        messages = [system_prompt, {"role": "user", "content": "Please suggest places."}]
        response = model.chat(messages)
        logger.info(f"[ML] LLM raw response: {response}")
        json_match = re.search(r'(\[\s*{.*}\s*\])', response, re.DOTALL)
        if not json_match:
            logger.error("[ML] No valid JSON found in model response")
            raise ValueError("No valid JSON found in model response")
        parsed = json.loads(json_match.group(1))
        logger.info(f"[ML] Parsed recommendations: {parsed}")
        return GeoRecommendationResponse(recommendations=parsed)
    except Exception as e:
        logger.error(f"[ML] Error in recommend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("geo_recommender:app", host="0.0.0.0", port=8003, reload=True)
