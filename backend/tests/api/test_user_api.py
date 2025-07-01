import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_user_flow(client):
    # Create
    res = client.post("/api/v1/users/", json={"email":"u@x.com","password":"pw"})
    assert res.status_code == status.HTTP_201_CREATED
    u = res.json()
    uid = u["id"]
    token = u["token"]
    hdr = {"Authorization": f"Bearer {token}"}
    # List
    lr = client.get("/api/v1/users/", headers=hdr)
    assert lr.status_code==200 and any(x['id']==uid for x in lr.json())
    # Me
    mr = client.get("/api/v1/users/me", headers=hdr)
    assert mr.status_code==200 and mr.json()["id"]==uid
    # Get one
    gr = client.get(f"/api/v1/users/{uid}", headers=hdr)
    assert gr.status_code==200
    # Update
    ur = client.put(f"/api/v1/users/{uid}", headers=hdr, json={"full_name":"New"})
    assert ur.status_code==200 and ur.json()["full_name"]=="New"
    # Delete
    dr = client.delete(f"/api/v1/users/{uid}", headers=hdr)
    assert dr.status_code==status.HTTP_204_NO_CONTENT
