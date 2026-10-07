import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import Base

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def override_get_db():
    """Yields a test async database session and ensures it closes after the request."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Replace the production database dependency with testing session
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_database():
    """Creates a fresh database schema before each test and drops it afterward."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Provides an asynchronous HTTP client for testing FastAPI endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_payload_success(client):
    """Verifies that a valid POST request successfully generates a payload ID."""
    payload = {"list_1": ["apple", "banana"], "list_2": ["cherry", "orange"]}
    response = await client.post("/payload", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Payload successfully generated."


@pytest.mark.asyncio
async def test_create_payload_length_mismatch(client):
    """Ensures the API rejects requests where the input lists have different lengths."""
    payload = {"list_1": ["apple", "banana"], "list_2": ["cherry"]}
    response = await client.post("/payload", json=payload)

    assert response.status_code == 422
    assert "list_1 and list_2 must have the same length" in response.text


@pytest.mark.asyncio
async def test_read_payload_success(client):
    """
    Tests the full lifecycle: creating a payload and successfully retrieving it.
    Validates the interleaving and transformation logic.
    """
    payload = {"list_1": ["apple", "banana"], "list_2": ["cherry", "orange"]}
    post_response = await client.post("/payload", json=payload)
    payload_id = post_response.json()["id"]
    get_response = await client.get(f"/payload/{payload_id}")

    assert get_response.status_code == 200
    data = get_response.json()

    expected_output = "APPLE, CHERRY, BANANA, ORANGE"
    assert data["output"] == expected_output


@pytest.mark.asyncio
async def test_read_payload_not_found(client):
    """Verifies that requesting a non-existent payload ID returns a 404 error."""
    response = await client.get("/payload/fake-uuid-123")

    assert response.status_code == 404
    assert response.json()["detail"] == "Payload not found."


@pytest.mark.asyncio
async def test_payload_caching(client):
    """
    Ensures that submitting the exact same input lists twice
    reuses the cached payload identifier instead of creating a new one.
    """
    payload = {"list_1": ["apple", "banana"], "list_2": ["cherry", "orange"]}

    response1 = await client.post("/payload", json=payload)
    id1 = response1.json()["id"]

    response2 = await client.post("/payload", json=payload)
    id2 = response2.json()["id"]

    assert response1.status_code == 201
    assert response2.status_code == 201
    assert id1 == id2
