import pytest

from tests.factories import PayloadFactory

pytest_plugins = ["tests.fixtures"]


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
async def test_read_payload_success(client, db_session):
    """
    Tests the GET endpoint independently by pre-populating the database
    using Factory Boy.
    """
    fake_payload = PayloadFactory.build()
    db_session.add(fake_payload)
    await db_session.commit()

    response = await client.get(f"/payload/{fake_payload.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["output"] == fake_payload.result_text


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
