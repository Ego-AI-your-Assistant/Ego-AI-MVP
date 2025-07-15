from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Импортируем роутеры из модулей
from geo_recommender import app as geo_app
from rescheduler import app as rescheduler_app
from chat import app as chat_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified ML API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/geo", geo_app)
app.mount("/rescheduler", rescheduler_app)
app.mount("/chat", chat_app)

# Теперь запускать только этот файл: uvicorn ml_api:app --host 0.0.0.0 --port 8001 