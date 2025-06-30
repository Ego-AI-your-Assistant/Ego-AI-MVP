from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
import os 
import asyncio

from app.database import schemas
from app.core.logging import logger

router = APIRouter()

MONGO_URI = os.getenv("MONGO_URL")

# Initialize MongoDB client with connection pooling and error handling
client = AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,  # 5 second timeout
    connectTimeoutMS=10000,         # 10 second connection timeout
    socketTimeoutMS=5000,           # 5 second socket timeout
    maxPoolSize=10                  # Maximum 10 connections in pool
)
db = client["ego_ai_db"]
collection = db["chat_history"]

async def verify_mongo_connection():
    """Verify MongoDB connection"""
    try:
        await client.admin.command('ping')
        logger.info("MongoDB connection verified successfully")
        return True
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return False

def get_chat_collection():
    """Dependency to get the chat collection"""
    return collection

@router.post("/add_message")
async def add_message(
    data: schemas.AddMessageRequest,
    collection = Depends(get_chat_collection)
):
    try:
        # Verify connection before proceeding
        if not await verify_mongo_connection():
            logger.warning("MongoDB not available, returning success to keep chat working")
            return {"success": True, "warning": "Message not stored - database unavailable"}
        
        logger.info(f"Adding message for user {data.user_id}: {data.role} - {data.content[:50]}...")
        chat = await collection.find_one({"user_id": data.user_id})
        message = {
            "role": data.role, 
            "content": data.content
        }
        if chat:
            logger.info(f"Updating existing chat for user {data.user_id}")
            await collection.update_one(
                {"user_id": data.user_id},
                {"$push": {"messages": message}}
            )
        else:
            logger.info(f"Creating new chat for user {data.user_id}")
            await collection.insert_one({
                "user_id": data.user_id,
                "messages": [message]
            })
        return {"success": True}
    except Exception as e:
        logger.error(f"Error adding message for user {data.user_id}: {str(e)}")
        # Return success to keep chat working even if storage fails
        return {"success": True, "warning": f"Message not stored: {str(e)}"}

@router.get("/get_messages")
async def get_message(
    user_id: str = Query(...),
    collection = Depends(get_chat_collection)
):
    try:
        # Verify connection before proceeding
        if not await verify_mongo_connection():
            logger.warning("MongoDB not available, returning empty messages")
            return []
        
        logger.info(f"Getting messages for user {user_id}")
        chat = await collection.find_one({"user_id": user_id})
        if chat:
            messages = chat.get("messages", [])
            logger.info(f"Found {len(messages)} messages for user {user_id}")
            return messages
        else:
            logger.info(f"No chat found for user {user_id}")
            return []
    except Exception as e:
        logger.error(f"Error getting messages for user {user_id}: {str(e)}")
        # Return empty list instead of 500 error to keep chat working
        logger.warning("Returning empty messages list due to database error")
        return []

@router.delete("/delete_messages")
async def delete_messages(
    user_id: str = Query(...),
    collection = Depends(get_chat_collection)
):
    try:
        # Verify connection before proceeding
        if not await verify_mongo_connection():
            logger.warning("MongoDB not available, returning success")
            return {"success": True, "warning": "Delete operation not performed - database unavailable"}
        
        logger.info(f"Deleting messages for user {user_id}")
        result = await collection.delete_one({"user_id": user_id})
        logger.info(f"Deleted {result.deleted_count} chat records for user {user_id}")
        return {"success": True, "deleted_count": result.deleted_count}
    except Exception as e:
        logger.error(f"Error deleting messages for user {user_id}: {str(e)}")
        # Return success even if deletion fails
        return {"success": True, "warning": f"Delete operation failed: {str(e)}"}

@router.get("/health")
async def chat_health_check():
    """Health check endpoint for chat service"""
    try:
        mongo_status = await verify_mongo_connection()
        return {
            "status": "healthy" if mongo_status else "degraded",
            "mongodb": "connected" if mongo_status else "disconnected",
            "service": "chat"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "mongodb": "error",
            "service": "chat",
            "error": str(e)
        }

# Startup verification
@router.on_event("startup")
async def startup_event():
    """Verify MongoDB connection on startup"""
    logger.info("Verifying MongoDB connection on chat service startup...")
    if await verify_mongo_connection():
        logger.info("Chat service started successfully with MongoDB connection")
    else:
        logger.warning("Chat service started but MongoDB connection failed - will continue with degraded functionality")