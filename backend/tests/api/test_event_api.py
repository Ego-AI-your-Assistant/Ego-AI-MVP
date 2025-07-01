# tests/api/test_event_api.py
import pytest
from fastapi import status
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_event_crud_lifecycle(client):
    now = datetime.utcnow().isoformat()
    later = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    # CREATE
    create_res = client.post(
        "/api/v1/events/", json={
            "title": "Evt", "description": "Desc", 
            "start_time": now, "end_time": later
        }
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    evt = create_res.json()
    evt_id = evt["id"]

    # LIST
    list_res = client.get("/api/v1/events/?skip=0&limit=10")
    assert list_res.status_code == 200
    assert any(e["id"] == evt_id for e in list_res.json())

    # GET ONE
    get_res = client.get(f"/api/v1/events/{evt_id}")
    assert get_res.status_code == 200

    # UPDATE
    upd_res = client.put(
        f"/api/v1/events/{evt_id}", json={"description": "NewDesc"}
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["description"] == "NewDesc"

    # DELETE
    del_res = client.delete(f"/api/v1/events/{evt_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT
