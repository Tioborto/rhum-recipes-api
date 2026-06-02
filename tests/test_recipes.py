"""
Tests for the Rhum Recipes CRUD API.
Uses an in-memory SQLite DB (isolated per test session).
"""

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
    """In-memory SQLite for each test run."""
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
    """Override the DB dependency with the test session."""

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_RECIPE = {
    "name": "Rhum Vanille Réunion",
    "description": "Macération vanille Bourbon avec rhum agricole blanc.",
    "ingredients": [
        {"name": "Vanille Bourbon", "quantity": 3, "unit": "pods"},
        {"name": "Rhum agricole blanc 50°", "quantity": 70, "unit": "cl"},
        {"name": "Sucre de canne", "quantity": 50, "unit": "g"},
    ],
}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_recipe(client: TestClient):
    r = client.post("/api/v1/recipes/", json=SAMPLE_RECIPE)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == SAMPLE_RECIPE["name"]
    assert len(data["ingredients"]) == 3
    assert data["id"] is not None


def test_create_recipe_duplicate_name(client: TestClient):
    client.post("/api/v1/recipes/", json=SAMPLE_RECIPE)
    r = client.post("/api/v1/recipes/", json=SAMPLE_RECIPE)
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_recipes_empty(client: TestClient):
    r = client.get("/api/v1/recipes/")
    assert r.status_code == 200
    assert r.json() == []


def test_list_recipes(client: TestClient):
    client.post("/api/v1/recipes/", json=SAMPLE_RECIPE)
    r = client.get("/api/v1/recipes/")
    assert r.status_code == 200
    assert len(r.json()) == 1


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------


def test_get_recipe(client: TestClient):
    created = client.post("/api/v1/recipes/", json=SAMPLE_RECIPE).json()
    r = client.get(f"/api/v1/recipes/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == SAMPLE_RECIPE["name"]


def test_get_recipe_not_found(client: TestClient):
    r = client.get("/api/v1/recipes/9999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Update (PATCH)
# ---------------------------------------------------------------------------


def test_update_recipe_ingredients(client: TestClient):
    created = client.post("/api/v1/recipes/", json=SAMPLE_RECIPE).json()
    new_ingredients = [{"name": "Citron vert", "quantity": 2, "unit": "pieces"}]
    r = client.patch(
        f"/api/v1/recipes/{created['id']}",
        json={"ingredients": new_ingredients},
    )
    assert r.status_code == 200
    assert len(r.json()["ingredients"]) == 1
    assert r.json()["ingredients"][0]["name"] == "Citron vert"


def test_update_recipe_not_found(client: TestClient):
    r = client.patch("/api/v1/recipes/9999", json={"status": "finished"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_recipe(client: TestClient):
    created = client.post("/api/v1/recipes/", json=SAMPLE_RECIPE).json()
    r = client.delete(f"/api/v1/recipes/{created['id']}")
    assert r.status_code == 204
    # Confirm gone
    r2 = client.get(f"/api/v1/recipes/{created['id']}")
    assert r2.status_code == 404


def test_delete_recipe_not_found(client: TestClient):
    r = client.delete("/api/v1/recipes/9999")
    assert r.status_code == 404
