"""Tests for memo endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
import os

# Use test database from environment variable
TEST_DB_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DB_URL:
    pytest.skip("TEST_DATABASE_URL environment variable is required for database tests", allow_module_level=True)

engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_create_memo(setup_database):
    """Test creating a memo."""
    response = client.post(
        "/api/memos",
        json={"title": "Test Memo", "content": "Test content"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Memo"
    assert data["content"] == "Test content"
    assert "id" in data
    assert "created_at" in data


def test_get_memos(setup_database):
    """Test getting all memos."""
    # Create a memo first
    client.post("/api/memos", json={"title": "Test Memo", "content": "Test"})
    
    response = client.get("/api/memos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_delete_memo(setup_database):
    """Test deleting a memo."""
    # Create a memo first
    create_response = client.post(
        "/api/memos",
        json={"title": "Test Memo", "content": "Test"}
    )
    memo_id = create_response.json()["id"]
    
    # Delete the memo
    delete_response = client.delete(f"/api/memos/{memo_id}")
    assert delete_response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get("/api/memos")
    memos = get_response.json()
    assert not any(m["id"] == memo_id for m in memos)


def test_delete_nonexistent_memo(setup_database):
    """Test deleting a non-existent memo."""
    response = client.delete("/api/memos/99999")
    assert response.status_code == 404

