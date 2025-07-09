import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_ai_interaction(client):
    ai = client.post("/api/v1/ai/ai-interactions/", json={"prompt":"Hello"}).json()
    assert "id" in ai
    lid = client.get(f"/api/v1/ai/ai-interactions/user/{ai['user_id']}")
    assert lid.status_code==200
