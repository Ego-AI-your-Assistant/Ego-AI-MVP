import os
import requests
from typing import List, Dict, Any

from app.core.config import settings
from fastapi import HTTPException

class LLMChatService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model_name = "llama3-70b-8192"

    def interpret_command(self, message: str) -> Dict[str, Any]:
        """
        Интерпретирует текстовую команду и возвращает действие и параметры.
        """
        if "update name of task" in message:
            parts = message.split(" ")
            time_index = parts.index("at") + 1
            new_name_index = parts.index("to") + 1

            # Extract event_id if provided in the message (e.g., "update task 123 at 15:00 to work")
            event_id = None
            if "task" in parts:
                task_index = parts.index("task") + 1
                if task_index < len(parts):
                    event_id = parts[task_index]

            return {
                "action": "update_task",
                "event_id": event_id,
                "time": parts[time_index],
                "new_name": " ".join(parts[new_name_index:])
            }

        return {"action": "unknown"}

    def chat(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set in the .env")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        json_data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.5
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=json_data)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

            # Проверка на команды календаря
            last_message = messages[-1]["content"]
            command = self.interpret_command(last_message)

            if command["action"] == "update_task":
                payload = {
                    "event_id": "some_event_id",  # Здесь нужно получить event_id из базы данных или другого источника
                    "time": command["time"],
                    "new_name": command["new_name"]
                }
                return self.handle_calendar_commands("update_task", payload)

            return response.json()['choices'][0]['message']['content'].strip()
        except requests.exceptions.RequestException as e:
            # Log the error and re-raise or handle as appropriate for your application
            print(f"Error interacting with Groq API: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get response from LLM: {e}")
        except KeyError as e:
            print(f"KeyError in parsing LLM response: {e}. Full response: {response.json()}")
            raise HTTPException(status_code=500, detail=f"Unexpected LLM response format: {e}")

    def handle_calendar_commands(self, command: str, payload: Dict[str, Any]) -> str:
        calendar_api_url = f"{settings.API_BASE_URL}/api/v1/calendar"

        try:
            if command == "update_task":
                event_id = payload.get("event_id")
                if not event_id:
                    raise ValueError("Missing event_id in payload")

                # Fetch event_id from database if not provided
                if event_id == "some_event_id":
                    # Simulate fetching event_id from database or another source
                    event_id = "retrieved_event_id"  # Replace with actual retrieval logic

                response = requests.put(f"{calendar_api_url}/update_task/{event_id}", json=payload)
                response.raise_for_status()
                return "Task updated successfully."

            elif command == "add_task":
                response = requests.post(f"{calendar_api_url}/set_task", json=payload)
                response.raise_for_status()
                return "Task added successfully."

            elif command == "delete_task":
                response = requests.delete(f"{calendar_api_url}/delete_task", json=payload)
                response.raise_for_status()
                return "Task deleted successfully."

            elif command == "get_calendar":
                response = requests.get(f"{calendar_api_url}/get_tasks")
                response.raise_for_status()
                return response.json()

            else:
                return "Unknown command."

        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Calendar API request failed: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
