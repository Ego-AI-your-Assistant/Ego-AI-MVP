# tests/api/test_reminder_api.py
import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_reminder_crud_for_event(client):
    # First, create an event
    create_evt = client.post(
        "/api/v1/events/", json={
            "title": "RmtEvt", "description": "D", 
            "start_time": "2025-07-02T00:00:00Z", 
            "end_time": "2025-07-02T01:00:00Z"
        }
    )
    evt_id = create_evt.json()["id"]

    # CREATE reminder
    rem_res = client.post(
        "/api/v1/reminders/reminders/", json={
            "event_id": evt_id, "time": "2025-07-02T00:30:00Z", 
            "message": "Ping"
        }
    )
    assert rem_res.status_code == status.HTTP_200_OK
    reminder = rem_res.json()
    rem_id = reminder["id"]

    # LIST by event
    by_evt_res = client.get(f"/api/v1/reminders/reminders/event/{evt_id}")
    assert by_evt_res.status_code == 200
    assert any(r["id"] == rem_id for r in by_evt_res.json())

    # GET one
    get_res = client.get(f"/api/v1/reminders/reminders/{rem_id}")
    assert get_res.status_code == 200

    # UPDATE
    upd_res = client.put(
        f"/api/v1/reminders/reminders/{rem_id}", json={"message": "Updated"}
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["message"] == "Updated"

    # DELETE
    del_res = client.delete(f"/api/v1/reminders/reminders/{rem_id}")
    assert del_res.status_code == status.HTTP_200_OK
