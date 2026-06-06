"""
Rhum Recipes API — entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import create_db_and_tables
from app.routers.recipes import router as recipes_router
from app.routers.stock import router as stock_router
from app.routers.orders import router as orders_router
from app.routers.ingredients import router as ingredients_router
from app.routers.clients import router as clients_router
from app.routers.users import router as users_router

# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist
    create_db_and_tables()
    yield
    # Shutdown: nothing special needed for SQLite


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


app = FastAPI(
    title="🍹 Rhum Recipes API",
    description=(
        "Manage your homemade rhum recipes and your rhum stock: "
        "ingredients, maceration dates, bottle counts, production status, "
        "and physical inventory of commercial & homemade bottles."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(recipes_router, prefix="/api/v1")
app.include_router(stock_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(ingredients_router, prefix="/api/v1")
app.include_router(clients_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
def root() -> JSONResponse:
    return JSONResponse(
        {
            "name": "Rhum Recipes API",
            "version": "0.1.0",
            "docs": "/docs",
            "redoc": "/redoc",
        }
    )


@app.get("/health", tags=["Health"], summary="Health check")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
