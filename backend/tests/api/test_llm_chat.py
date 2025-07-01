import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_llm_chat_flow(client):
    # send llm message
    msg = client.post("/api/v1/llm_chat/", json={"message":"Hi"})
    assert msg.status_code==200
    res = msg.json()
    assert 'response' in res
