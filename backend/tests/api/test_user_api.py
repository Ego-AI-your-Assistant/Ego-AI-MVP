# tests/api/test_user_api.py
import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_user_crud_lifecycle(client):
    # CREATE
    res = client.post(
        "/api/v1/users/", json={"email": "foo@bar.com", "password": "pwd"}
    )
    assert res.status_code == status.HTTP_201_CREATED
    user = res.json()
    user_id = user["id"]

    # READ LIST
    list_res = client.get("/api/v1/users/",)
    assert list_res.status_code == 200
    assert any(u["id"] == user_id for u in list_res.json())

    # READ ME
    me_res = client.get("/api/v1/users/me")
    assert me_res.status_code == 200
    assert me_res.json()["id"] == user_id

    # READ ONE
    get_res = client.get(f"/api/v1/users/{user_id}")
    assert get_res.status_code == 200

    # UPDATE
    upd_res = client.put(
        f"/api/v1/users/{user_id}", json={"full_name": "NewName"}
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["full_name"] == "NewName"

    # DELETE
    del_res = client.delete(f"/api/v1/users/{user_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT
