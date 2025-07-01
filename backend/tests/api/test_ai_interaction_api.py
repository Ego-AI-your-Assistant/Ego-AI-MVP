import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_ai_interaction_endpoints(client, test_user):
    # CREATE AI interaction
    ai_res = client.post(
        "/api/v1/ai/ai-interactions/", 
        json={"prompt": "Hello AI"}
    )
    assert ai_res.status_code == status.HTTP_200_OK
    ai_obj = ai_res.json()
    assert "id" in ai_obj
    uid = ai_obj.get("user_id") or ai_obj.get("id")

    # LIST by user
    list_res = client.get(f"/api/v1/ai/ai-interactions/user/{test_user.id}")
    assert list_res.status_code == status.HTTP_200_OK
    assert isinstance(list_res.json(), list)

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database.session import get_db
from app.database.models import Base

# Use SQLite in-memory for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
async def init_db():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session

@pytest.fixture
def client(monkeypatch):
    # Override the get_db dependency to use in-memory session
    async def override_get_db():
        async with AsyncSessionLocal() as session:
            yield session
    monkeypatch.setattr("app.database.session.get_db", override_get_db)
    return TestClient(app)
