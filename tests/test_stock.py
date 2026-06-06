"""
Tests for the Stock CRUD API.
Uses an in-memory SQLite DB (isolated per test session).
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app


# ---------------------------------------------------------------------------
# Fixtures (mirror test_recipes.py — each test gets a clean in-memory DB)
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
# Sample payloads
# ---------------------------------------------------------------------------

COMMERCIAL_BOTTLE = {
    "name": "Rhum J.M Blanc 50°",
    "origin": "commercial",
    "volume_ml": 700,
    "quantity": 3,
    "vintage": 2022,
    "purchase_date": "2024-06-15",
    "notes": "Floral and grassy, from Martinique.",
}

HOMEMADE_BOTTLE = {
    "name": "Vanille Bourbon maison",
    "origin": "homemade",
    "volume_ml": 500,
    "quantity": 6,
    "preparation_date": "2024-11-01",
    "notes": "Batch from November 2024.",
}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_commercial_stock_entry(client: TestClient):
    r = client.post("/api/v1/stock/", json=COMMERCIAL_BOTTLE)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == COMMERCIAL_BOTTLE["name"]
    assert data["origin"] == "commercial"
    assert data["volume_ml"] == 700
    assert data["quantity"] == 3
    assert data["vintage"] == 2022
    assert data["purchase_date"] == "2024-06-15"
    assert data["id"] is not None
    assert data["recipe_id"] is None


def test_create_homemade_stock_entry(client: TestClient):
    r = client.post("/api/v1/stock/", json=HOMEMADE_BOTTLE)
    assert r.status_code == 201
    data = r.json()
    assert data["origin"] == "homemade"
    assert data["vintage"] is None
    assert data["purchase_date"] is None
    assert data["preparation_date"] == "2024-11-01"


def test_create_stock_entry_linked_to_recipe(client: TestClient):
    """A homemade stock entry can be linked to an existing recipe."""
    # First create a recipe
    recipe_payload = {
        "name": "Vanille Bourbon",
        "ingredients": [{"name": "Vanille", "quantity": 3, "unit": "pods"}],
        "bottles_planned": 6,
        "status": "bottled",
    }
    recipe = client.post("/api/v1/recipes/", json=recipe_payload).json()
    recipe_id = recipe["id"]

    stock_payload = {**HOMEMADE_BOTTLE, "recipe_id": recipe_id}
    r = client.post("/api/v1/stock/", json=stock_payload)
    assert r.status_code == 201
    assert r.json()["recipe_id"] == recipe_id


def test_create_stock_entry_invalid_quantity(client: TestClient):
    """quantity must be >= 0."""
    bad = {**COMMERCIAL_BOTTLE, "quantity": -1}
    r = client.post("/api/v1/stock/", json=bad)
    assert r.status_code == 422


def test_create_stock_entry_invalid_volume(client: TestClient):
    """volume_ml must be > 0."""
    bad = {**COMMERCIAL_BOTTLE, "volume_ml": 0}
    r = client.post("/api/v1/stock/", json=bad)
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_stock_empty(client: TestClient):
    r = client.get("/api/v1/stock/")
    assert r.status_code == 200
    assert r.json() == []


def test_list_stock(client: TestClient):
    client.post("/api/v1/stock/", json=COMMERCIAL_BOTTLE)
    client.post("/api/v1/stock/", json=HOMEMADE_BOTTLE)
    r = client.get("/api/v1/stock/")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_stock_filter_by_origin(client: TestClient):
    client.post("/api/v1/stock/", json=COMMERCIAL_BOTTLE)
    client.post("/api/v1/stock/", json=HOMEMADE_BOTTLE)

    r = client.get("/api/v1/stock/?origin=commercial")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["origin"] == "commercial"


def test_list_stock_in_stock_only(client: TestClient):
    """in_stock_only=true filters out entries with quantity=0."""
    client.post("/api/v1/stock/", json=COMMERCIAL_BOTTLE)
    client.post("/api/v1/stock/", json={**HOMEMADE_BOTTLE, "quantity": 0})

    r = client.get("/api/v1/stock/?in_stock_only=true")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["quantity"] > 0


def test_list_stock_filter_by_recipe_id(client: TestClient):
    # Create recipe
    recipe = client.post(
        "/api/v1/recipes/",
        json={
            "name": "Coco rhum",
            "ingredients": [{"name": "Coco", "quantity": 1, "unit": "piece"}],
            "bottles_planned": 2,
        },
    ).json()

    client.post("/api/v1/stock/", json={**HOMEMADE_BOTTLE, "recipe_id": recipe["id"]})
    client.post("/api/v1/stock/", json=COMMERCIAL_BOTTLE)

    r = client.get(f"/api/v1/stock/?recipe_id={recipe['id']}")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["recipe_id"] == recipe["id"]


def test_list_stock_pagination(client: TestClient):
    for i in range(5):
        client.post("/api/v1/stock/", json={**COMMERCIAL_BOTTLE, "name": f"Bottle {i}"})

    r = client.get("/api/v1/stock/?offset=0&limit=3")
    assert r.status_code == 200
    assert len(r.json()) == 3

    r2 = client.get("/api/v1/stock/?offset=3&limit=3")
    assert r2.status_code == 200
    assert len(r2.json()) == 2


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------


def test_get_stock_entry(client: TestClient):
    created = client.post("/api/v1/stock/", json=COMMERCIAL_BOTTLE).json()
    r = client.get(f"/api/v1/stock/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == COMMERCIAL_BOTTLE["name"]


def test_get_stock_entry_not_found(client: TestClient):
    r = client.get("/api/v1/stock/9999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Update (PATCH)
# ---------------------------------------------------------------------------


def test_update_stock_entry_quantity(client: TestClient):
    """Most common update: consuming a bottle from the stock."""
    created = client.post("/api/v1/stock/", json=COMMERCIAL_BOTTLE).json()
    r = client.patch(f"/api/v1/stock/{created['id']}", json={"quantity": 1})
    assert r.status_code == 200
    assert r.json()["quantity"] == 1


def test_update_stock_entry_notes(client: TestClient):
    created = client.post("/api/v1/stock/", json=COMMERCIAL_BOTTLE).json()
    r = client.patch(
        f"/api/v1/stock/{created['id']}",
        json={"notes": "Opened first bottle — excellent on the rocks.", "preparation_date": "2025-01-01"},
    )
    assert r.status_code == 200
    assert "excellent" in r.json()["notes"]
    assert r.json()["preparation_date"] == "2025-01-01"


def test_update_stock_entry_link_recipe(client: TestClient):
    """Retroactively link a homemade stock entry to a recipe."""
    recipe = client.post(
        "/api/v1/recipes/",
        json={
            "name": "Gingembre rhum",
            "ingredients": [{"name": "Gingembre", "quantity": 50, "unit": "g"}],
            "bottles_planned": 4,
        },
    ).json()

    entry = client.post("/api/v1/stock/", json=HOMEMADE_BOTTLE).json()
    r = client.patch(f"/api/v1/stock/{entry['id']}", json={"recipe_id": recipe["id"]})
    assert r.status_code == 200
    assert r.json()["recipe_id"] == recipe["id"]


def test_update_stock_entry_not_found(client: TestClient):
    r = client.patch("/api/v1/stock/9999", json={"quantity": 0})
    assert r.status_code == 404


def test_update_stock_entry_invalid_quantity(client: TestClient):
    created = client.post("/api/v1/stock/", json=COMMERCIAL_BOTTLE).json()
    r = client.patch(f"/api/v1/stock/{created['id']}", json={"quantity": -5})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_stock_entry(client: TestClient):
    created = client.post("/api/v1/stock/", json=COMMERCIAL_BOTTLE).json()
    r = client.delete(f"/api/v1/stock/{created['id']}")
    assert r.status_code == 204
    # Confirm gone
    r2 = client.get(f"/api/v1/stock/{created['id']}")
    assert r2.status_code == 404


def test_delete_stock_entry_not_found(client: TestClient):
    r = client.delete("/api/v1/stock/9999")
    assert r.status_code == 404
