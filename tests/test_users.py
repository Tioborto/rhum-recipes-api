import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_me_default(client: TestClient):
    """Test retrieving the current user profile (defaults to admin/system)."""
    r = client.get("/api/v1/users/me")
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "admin"
    assert data["theme"] == "system"

def test_update_theme_valid(client: TestClient):
    """Test updating the theme with a valid value."""
    # 1. Update theme to dark
    r = client.patch("/api/v1/users/me", json={"theme": "dark"})
    assert r.status_code == 200
    assert r.json()["theme"] == "dark"
    
    # 2. Retrieve again to confirm persistence
    r2 = client.get("/api/v1/users/me")
    assert r2.status_code == 200
    assert r2.json()["theme"] == "dark"

def test_update_theme_invalid(client: TestClient):
    """Test endpoint payload validation strictly enforces valid themes."""
    r = client.patch("/api/v1/users/me", json={"theme": "neon"})
    # FastAPI returns 422 Unprocessable Entity for Enum validation failure
    assert r.status_code == 422
    
    # Confirm it wasn't modified (still defaults to system)
    r2 = client.get("/api/v1/users/me")
    assert r2.status_code == 200
    assert r2.json()["theme"] == "system"
