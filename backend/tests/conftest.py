import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.base    import Base
from app.database.models  import User as DBUser
from app.database.schemas import UserCreate
from app.services.user    import UserService
from app.database.session import get_db
from main                import app

# Set up in-memory SQLite for test
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
async def init_db():
    # Create all tables once
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Tear down afterwards
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="session")
async def test_user():
    # A reusable user for auth fixtures
    async with AsyncSessionLocal() as session:
        svc = UserService(session)
        user = await svc.create(UserCreate(email="test@user.com", password="testpw"))
        return user

@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session

@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch, test_user):
    # Swap out your real get_db() for the test engine
    async def override_get_db():
        async with AsyncSessionLocal() as session:
            yield session
    monkeypatch.setattr("app.database.session.get_db", override_get_db)
    
    async def override_current_user():
        return test_user
    monkeypatch.setattr("app.utils.deps.get_current_user", override_current_user)

@pytest.fixture
def client():
    return TestClient(app)
