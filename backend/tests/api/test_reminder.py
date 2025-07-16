import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_reminder_crud(client):
    # create event first
    ev = client.post("/api/v1/events/", json={"title":"R","description":"D","start_time":"2025-07-02T00:00:00Z","end_time":"2025-07-02T01:00:00Z"}).json()
    rid = client.post("/api/v1/reminders/reminders/", json={"event_id":ev['id'],"time":"2025-07-02T00:30:00Z","message":"M"}).json()['id']
    lr = client.get(f"/api/v1/reminders/reminders/event/{ev['id']}")
    assert rid in [x['id'] for x in lr.json()]
    gr = client.get(f"/api/v1/reminders/reminders/{rid}")
    assert gr.status_code==200
    ur = client.put(f"/api/v1/reminders/reminders/{rid}", json={"message":"N"})
    assert ur.status_code==200 and ur.json()["message"]=="N"
    dr = client.delete(f"/api/v1/reminders/reminders/{rid}")
    assert dr.status_code==200
