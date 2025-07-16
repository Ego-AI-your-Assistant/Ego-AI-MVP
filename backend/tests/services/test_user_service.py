# tests/services/test_user_service.py
import pytest
from uuid import uuid4
from app.services.user import UserService
from app.database.schemas import UserCreate, UserUpdate
from app.core.exception_handlers import BadRequestError, ForbiddenError, NotFoundError

@pytest.mark.asyncio
async def test_create_and_get_user(db_session):
    svc = UserService(db_session)
    user_in = UserCreate(email="test@example.com", password="secret")
    user = await svc.create(user_in=user_in)
    assert user.email == "test@example.com"
    assert hasattr(user, "id")

    # Duplicate email should raise BadRequestError
    with pytest.raises(BadRequestError):
        await svc.create(user_in=user_in)

    # Fetch by ID and email
    fetched = await svc.get_by_id(user.id)
    assert fetched.email == user.email
    by_email = await svc.get_by_email(user.email)
    assert by_email.id == user.id

@pytest.mark.asyncio
async def test_update_and_delete_user(db_session):
    svc = UserService(db_session)
    user_in = UserCreate(email="update@example.com", password="pass")
    user = await svc.create(user_in=user_in)

    other = UserCreate(email="other@example.com", password="pass2")
    other_user = await svc.create(user_in=other)

    # Unauthorized update
    with pytest.raises(ForbiddenError):
        await svc.update(user.id, UserUpdate(full_name="Name"), current_user=other_user)

    # Authorized update
    updated = await svc.update(user.id, UserUpdate(full_name="New Name"), current_user=user)
    assert updated.full_name == "New Name"

    # Unauthorized delete
    with pytest.raises(ForbiddenError):
        await svc.delete(user.id, current_user=other_user)

    # Authorized delete
    await svc.delete(user.id, current_user=user)
    with pytest.raises(NotFoundError):
        await svc.get_by_id(user.id)
