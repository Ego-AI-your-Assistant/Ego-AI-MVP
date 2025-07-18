from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import logging
import json
import time

from app.core import settings
from app.core.logging import logger
from app.api import api_router
from app.core.exception_handlers import add_exception_handlers
from fastapi import Request, Response

# Alembic теперь управляет созданием таблиц, поэтому эта строка не нужна
# from app.database import Base, engine 
# Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")
logger.info("[APP] FastAPI app is starting up...")


app = FastAPI(
    title=settings.PROJECT_NAME
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url} - Headers: {dict(request.headers)}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Response status: {response.status_code} - Time: {process_time:.4f}s")
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        # Return a proper CORS response even on error
        response = Response(
            content=f"Internal server error: {str(e)}", 
            status_code=500,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        )
        return response
    
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
)

@app.options("/{path:path}")
async def handle_options(path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

add_exception_handlers(app)

cors_origins = [
    "http://localhost:3000",
    "http://localhost:8000", 
    "http://185.207.133.14:3000",
    "http://185.207.133.14:8000",
    "http://localhost:3000",
    "http://localhost:8000",
    "https://localhost:3000",
    "https://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def on_startup():
    logger.info(f"Starting {settings.PROJECT_NAME}")

