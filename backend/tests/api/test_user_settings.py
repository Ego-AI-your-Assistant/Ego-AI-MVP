import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_user_settings_crud(client):
    # get defaults
    gd = client.get("/api/v1/user_settings/")
    assert gd.status_code==200
    # update
    up = client.put("/api/v1/user_settings/", json={"theme":"dark"})
    assert up.status_code==200 and up.json().get('theme')=='dark'
