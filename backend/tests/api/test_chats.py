import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_chats_crud(client):
    # Create chat
    rc = client.post("/api/v1/chats/", json={"title":"Chat1"})
    assert rc.status_code==200
    c = rc.json(); cid=c['id']
    # List
    rl = client.get("/api/v1/chats/?skip=0&limit=3")
    assert cid in [x['id'] for x in rl.json()]
    # Get
    rg = client.get(f"/api/v1/chats/{cid}")
    assert rg.status_code==200
    # Update
    ru = client.put(f"/api/v1/chats/{cid}", json={"title":"X"})
    assert ru.status_code==200 and ru.json()['title']=='X'
    # Delete
    rd = client.delete(f"/api/v1/chats/{cid}")
    assert rd.status_code==200
