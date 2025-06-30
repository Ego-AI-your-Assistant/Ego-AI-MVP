from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
import os 

from app.database import schemas

router = APIRouter()

MONGO_URI = os.getenv("MONGO_URL")

client = AsyncIOMotorClient(MONGO_URI)
db = client["ego_ai_db"]
collection = db["chat_history"]

@router.post("/add_message")
async def add_message(data: schemas.AddMessageRequest):
    try:
        print(f"Adding message for user {data.user_id}: {data.role} - {data.content[:50]}...")
        chat = await collection.find_one({"user_id": data.user_id})
        message = {
            "role": data.role, 
            "content": data.content
        }
        if chat:
            print(f"Updating existing chat for user {data.user_id}")
            await collection.update_one(
                {"user_id": data.user_id},
                {"$push": {"messages": message}}
            )
        else:
            print(f"Creating new chat for user {data.user_id}")
            await collection.insert_one({
                "user_id": data.user_id,
                "messages": [message]
            })
        return {"success": True}
    except Exception as e:
        print(f"Error adding message for user {data.user_id}: {str(e)}")
        # Return success to keep chat working even if storage fails
        return {"success": True, "warning": f"Message not stored: {str(e)}"}

@router.get("/get_messages")
async def get_message(
    user_id: str = Query(...),
    collection = Depends(get_chat_collection)
):
    try:
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
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")

@router.delete("/delete_messages")
async def delete_messages(user_id: str = Query(...)):
    try:
        print(f"Deleting messages for user {user_id}")
        result = await collection.delete_one({"user_id": user_id})
        print(f"Deleted {result.deleted_count} chat records for user {user_id}")
        return {"success": True, "deleted_count": result.deleted_count}
    except Exception as e:
        print(f"Error deleting messages for user {user_id}: {str(e)}")
        # Return success even if deletion fails
        return {"success": True, "warning": f"Delete operation failed: {str(e)}"}