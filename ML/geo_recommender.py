import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from chat import Chat
import os


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
    latitude: float
    longitude: float
    city: Optional[str] = None
    district: Optional[str] = None
    weather: Optional[str] = None
    purpose: Optional[str] = None  


class GeoRecommendationResponse(BaseModel):
    suggestion: str


def build_geo_prompt(data: GeoRecommendationRequest) -> dict:
    now = datetime.datetime.now()
    day_of_week = now.strftime("%A")
    date_str = now.strftime("%B %d, %Y")
    location_str = f"{data.city or 'Unknown city'}, {data.district or 'Unknown district'}"
    prompt = (
        f"You are a friendly and knowledgeable local guide. The user is currently in {location_str} "
        f"at coordinates {data.latitude:.4f}, {data.longitude:.4f}. "
        f"Today is {day_of_week}, {date_str}, and the weather is: {data.weather or 'unknown'}. "
        f"They're looking for things to do related to: {data.purpose or 'general interest'}."
        f"Suggest 3 interesting places to visit nearby. For each place, include a short description. "
        f"Consider the weather, the day of the week, and the user's mood or interest."
        f"Return only the plain text recommendations — no bullet points, no markdown, no headings."
    )

    return {"role": "system", "content": prompt}


@app.post("/recommend", response_model=GeoRecommendationResponse)
def recommend(req: GeoRecommendationRequest):
    try:
        system_prompt = build_geo_prompt(req)
        messages = [system_prompt, {"role": "user", "content": "Where would you recommend I go?"}]
        suggestion = model.chat(messages)
        return GeoRecommendationResponse(suggestion=suggestion.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("geo_recommender:app", host="0.0.0.0", port=8003, reload=True)
