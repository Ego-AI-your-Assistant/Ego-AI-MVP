# tests/services/test_event_service.py
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from app.services.event import EventService
from app.database.schemas import EventCreate, EventUpdate
from app.core.exception_handlers import ForbiddenError, NotFoundError

@pytest.mark.asyncio
async def test_event_crud(db_session):
    svc = EventService(db_session)
    user_id = uuid4()
    now = datetime.utcnow()
    ev_in = EventCreate(
        title="Test",
        description="Desc",
        start_time=now,
        end_time=now + timedelta(hours=1)
    )
    ev = await svc.create(ev_in, user_id=user_id)
    assert ev.title == "Test"
    assert ev.user_id == user_id

    # Authorized fetch
    fetched = await svc.get_by_id(ev.id, current_user=type("U", (), {"id": user_id}))
    assert fetched.id == ev.id

    # Unauthorized access
    fake_user = type("U", (), {"id": uuid4()})
    with pytest.raises(ForbiddenError):
        await svc.get_by_id(ev.id, current_user=fake_user)

    # Update
    updated = await svc.update(ev.id, EventUpdate(description="Updated"), current_user=type("U", (), {"id": user_id}))
    assert updated.description == "Updated"

    # Delete and verify
    await svc.delete(ev.id, current_user=type("U", (), {"id": user_id}))
    with pytest.raises(NotFoundError):
        await svc.get_by_id(ev.id, current_user=type("U", (), {"id": user_id}))
