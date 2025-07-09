import pytest
from datetime import datetime, timedelta
from fastapi import status

@pytest.mark.asyncio
async def test_event_crud(client):
    start = datetime.utcnow().isoformat()
    end = (datetime.utcnow()+timedelta(hours=1)).isoformat()
    cr = client.post("/api/v1/events/", json={"title":"T","description":"D","start_time":start,"end_time":end})
    assert cr.status_code==status.HTTP_201_CREATED
    ev = cr.json(); eid = ev['id']
    lr = client.get("/api/v1/events/?skip=0&limit=5")
    assert lr.status_code==200 and any(x['id']==eid for x in lr.json())
    gr = client.get(f"/api/v1/events/{eid}")
    assert gr.status_code==200
    ur = client.put(f"/api/v1/events/{eid}", json={"description":"X"})
    assert ur.status_code==200 and ur.json()["description"]=="X"
    dr = client.delete(f"/api/v1/events/{eid}")
    assert dr.status_code==status.HTTP_204_NO_CONTENT
