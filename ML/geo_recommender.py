import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from chat import Chat
import os
import re
<<<<<<< HEAD
from pydantic import Field
=======
>>>>>>> 64b7834fc257c8d787521c0d7bb28e9118ab132c
import json


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
<<<<<<< HEAD
    position: Optional[str] = Field(..., example="43.445,39.956")
    age: Optional[int] = Field(None, example=30)
    gender: Optional[str] = Field(None, example="male")
    description: Optional[str] = Field(None, example="active tourist who loves hiking and history")
    weather: Optional[str] = Field(None, example="sunny")

=======
    position: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    weather: Optional[str] = None
>>>>>>> 64b7834fc257c8d787521c0d7bb28e9118ab132c
   

class RecommendationItem(BaseModel):
    name: str
    description: str
    latitude: float
    longitude: float
<<<<<<< HEAD
    confidence: float = Field(..., ge=0, le=10)

=======
    confidence: float 
>>>>>>> 64b7834fc257c8d787521c0d7bb28e9118ab132c


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

    prompt = (
        f"You are a helpful and knowledgeable local guide.\n"
        f"The user is currently located at: {data.position or 'Unknown location'}.\n"
        f"Today is {day_of_week}, {date_str}, and the weather is: {data.weather or 'unknown'}.\n\n"
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



@app.post("/recommend", response_model=GeoRecommendationResponse)
def recommend(req: GeoRecommendationRequest):
    try:
        system_prompt = build_geo_prompt(req)
        messages = [system_prompt, {"role": "user", "content": "Please suggest places."}]
        response = model.chat(messages)

        json_match = re.search(r'(\[\s*{.*}\s*\])', response, re.DOTALL)
        if not json_match:
            raise ValueError("No valid JSON found in model response")

        parsed = json.loads(json_match.group(1))
        return GeoRecommendationResponse(recommendations=parsed)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("geo_recommender:app", host="0.0.0.0", port=8003, reload=True)
