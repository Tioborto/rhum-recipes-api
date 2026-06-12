  # 🍹 Black Sails API

A CRUD REST API to manage your homemade rhum recipes — ingredients, maceration dates, bottle counts, and production status.

**Stack:** Python 3.12 · FastAPI · SQLModel (SQLite) · uv · mise

---

## Prerequisites

| Tool | Install |
|------|---------|
| [mise](https://mise.jdx.dev) | `curl https://mise.run \| sh` |
| uv | installed automatically by mise |

---

## Quick Start

```bash
# 1. Let mise install Python + uv and activate the virtualenv
mise install

# 2. Install Python dependencies
mise run install

# 3. Start the API (auto-reloads on file changes)
mise run dev
```

The API is now live at **http://localhost:8000**

- Interactive docs (Swagger UI): http://localhost:8000/docs
- Alternative docs (ReDoc):      http://localhost:8000/redoc

---

## Mise Tasks

| Task | Description |
|------|-------------|
| `mise run install` | Install Python dependencies via uv |
| `mise run dev`     | **Start dev server** with hot-reload (watches file changes) |
| `mise run run`     | Start production server (no reload) |
| `mise run test`    | Run test suite with pytest |
| `mise run lint`    | Lint & format code with ruff |
| `mise run db-reset`| Delete the SQLite database (fresh start) |

---

## API Reference

Base path: `/api/v1`

### Recipe fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique recipe name |
| `description` | string? | Free-text notes |
| `ingredients` | array | `[{name, quantity, unit}]` |
| `bottles_planned` | int | Number of bottles intended |
| `bottles_filled` | int | Bottles already filled |
| `abv` | float? | Alcohol % by volume |
| `preparation_date` | date? | When maceration started (YYYY-MM-DD) |
| `status` | enum | `draft` · `in_progress` · `resting` · `bottled` · `finished` |

### Endpoints

```
POST   /api/v1/recipes/          Create a recipe
GET    /api/v1/recipes/          List recipes (filter by ?status=, pagination with ?offset=&limit=)
GET    /api/v1/recipes/{id}      Get a recipe by ID (full detail with ingredients)
PATCH  /api/v1/recipes/{id}      Partially update a recipe
DELETE /api/v1/recipes/{id}      Delete a recipe

GET    /health                   Health check
```

### Example — Create a recipe

```bash
curl -s -X POST http://localhost:8000/api/v1/recipes/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rhum Vanille Réunion",
    "description": "Macération vanille Bourbon avec rhum agricole blanc.",
    "ingredients": [
      {"name": "Vanille Bourbon", "quantity": 3, "unit": "pods"},
      {"name": "Rhum agricole blanc 50°", "quantity": 70, "unit": "cl"},
      {"name": "Sucre de canne", "quantity": 50, "unit": "g"}
    ],
    "bottles_planned": 2,
    "abv": 50.0,
    "preparation_date": "2024-11-01",
    "status": "in_progress"
  }' | jq
```

### Example — Update status + bottles filled

```bash
curl -s -X PATCH http://localhost:8000/api/v1/recipes/1 \
  -H "Content-Type: application/json" \
  -d '{"bottles_filled": 2, "status": "bottled"}' | jq
```

### Example — Filter in-progress recipes

```bash
curl -s "http://localhost:8000/api/v1/recipes/?status=in_progress" | jq
```

---

## Project Structure

```
black-sails-api/
├── .mise.toml          # Tool versions + task definitions
├── pyproject.toml      # uv dependencies + tool config
├── app/
│   ├── main.py         # FastAPI app, lifespan, routers
│   ├── database.py     # SQLite engine + session dependency
│   ├── models.py       # SQLModel table + request/response schemas
│   └── routers/
│       └── recipes.py  # CRUD endpoints
└── tests/
    └── test_recipes.py # pytest test suite
```

---

## Running Tests

```bash
mise run test
```

Tests use an isolated **in-memory SQLite** database — no cleanup needed.
