import pytest
from datetime import date, datetime
from fastapi import status

@pytest.mark.asyncio
async def test_calendar_endpoint(client):
    # Expect calendar returns list or structure
    r = client.get("/api/v1/calendar/")
    assert r.status_code==200
    assert isinstance(r.json(), list)
