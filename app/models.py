"""
SQLModel models — single source of truth for DB tables and API schemas.

- ingredients     : stored as a JSON array of {name, quantity, unit}

Stock entries:
- name            : label / commercial name of the rhum bottle
- origin          : homemade | commercial
- volume_ml       : bottle size in ml (optional)
- quantity        : number of bottles on hand
- vintage         : year of distillation / production (optional)
- purchase_date   : when it was bought / bottled (optional)
- notes           : free-text tasting notes, provenance, …
- recipe_id       : optional FK to a Recipe (for homemade batches)
"""


import json
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any, List

from sqlmodel import Column, Field, SQLModel, String, Relationship

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ThemePreference(StrEnum):
    light = "light"
    dark = "dark"
    system = "system"


# ---------------------------------------------------------------------------
# Ingredient helper (not a DB table — stored as JSON inside the recipe row)
# ---------------------------------------------------------------------------


class Ingredient(SQLModel):
    name: str = Field(..., description="Ingredient name (e.g. vanilla, lime zest)")
    quantity: float = Field(..., gt=0, description="Quantity")
    unit: str = Field(..., description="Unit (g, ml, cl, pieces, …)")


class GlobalIngredient(SQLModel, table=True):
    __tablename__ = "global_ingredients"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(..., unique=True, index=True, max_length=120)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RecipeIngredientLink(SQLModel, table=True):
    __tablename__ = "recipe_ingredients"

    recipe_id: int | None = Field(default=None, foreign_key="recipes.id", primary_key=True)
    ingredient_id: int | None = Field(default=None, foreign_key="global_ingredients.id", primary_key=True)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., max_length=50)

    recipe: "Recipe" = Relationship(back_populates="ingredient_links")
    ingredient: "GlobalIngredient" = Relationship()


# ---------------------------------------------------------------------------
# DB Table
# ---------------------------------------------------------------------------


class Recipe(SQLModel, table=True):
    __tablename__ = "recipes"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(..., unique=True, index=True, max_length=120)
    description: str | None = Field(default=None, max_length=2000)

    # Stored as a JSON string in SQLite
    ingredients_json: str = Field(
        default="[]",
        sa_column=Column("ingredients_json", String, nullable=False, server_default="[]"),
    )

    maceration_time_days: int | None = Field(default=None, description="Recommended maceration time in days")

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    ingredient_links: list["RecipeIngredientLink"] = Relationship(back_populates="recipe", cascade_delete=True)

    # --- ingredient helpers ---

    def get_ingredients(self) -> list[dict[str, Any]]:
        return json.loads(self.ingredients_json or "[]")

    def set_ingredients(self, ingredients: list[Ingredient]) -> None:
        self.ingredients_json = json.dumps([i.model_dump() for i in ingredients])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class RecipeCreate(SQLModel):
    name: str = Field(..., max_length=120)
    description: str | None = None
    maceration_time_days: int | None = None
    ingredients: list[Ingredient] = Field(default_factory=list)


class RecipeUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=120)
    description: str | None = None
    maceration_time_days: int | None = None
    ingredients: list[Ingredient] | None = None


class RecipeRead(SQLModel):
    id: int
    name: str
    description: str | None
    maceration_time_days: int | None
    ingredients: list[Ingredient]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_recipe(cls, recipe: "Recipe") -> "RecipeRead":
        if recipe.ingredient_links:
            ing_list = [
                Ingredient(name=link.ingredient.name, quantity=link.quantity, unit=link.unit)
                for link in recipe.ingredient_links
            ]
        else:
            ing_list = [Ingredient(**i) for i in recipe.get_ingredients()]

        return cls(
            id=recipe.id,  # type: ignore[arg-type]
            name=recipe.name,
            description=recipe.description,
            maceration_time_days=recipe.maceration_time_days,
            ingredients=ing_list,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at,
        )


class RecipeListItem(SQLModel):
    """Lighter schema for listing recipes (no full ingredient list)."""

    id: int
    name: str
    created_at: datetime
    maceration_time_days: int


class GlobalIngredientCreate(SQLModel):
    name: str = Field(..., max_length=120)


class GlobalIngredientUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=120)


class GlobalIngredientRead(SQLModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime


class GlobalIngredientWithDetails(GlobalIngredientRead):
    usage_count: int
    recipes: list[RecipeListItem]


# ===========================================================================
# Stock domain
# ===========================================================================


class RhumOrigin(StrEnum):
    homemade = "homemade"
    commercial = "commercial"

class StockState(StrEnum):
    ready = "ready"
    in_preparation = "in_preparation"


# ---------------------------------------------------------------------------
# DB Table
# ---------------------------------------------------------------------------


class StockEntry(SQLModel, table=True):
    """A bottle (or set of bottles) physically on the shelf."""

    __tablename__ = "stock_entries"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(..., max_length=200, index=True, description="Rhum label / name")
    origin: RhumOrigin = Field(default=RhumOrigin.homemade)
    state: StockState = Field(default=StockState.ready)

    volume_ml: int | None = Field(default=None, gt=0, description="Bottle size in ml")
    quantity: int = Field(default=1, ge=0, description="Number of bottles on hand")

    vintage: int | None = Field(default=None, description="Year of distillation / production")
    purchase_date: date | None = Field(default=None, description="Date purchased / bottled")
    preparation_date: date | None = Field(default=None, description="Date the preparation started")

    notes: str | None = Field(default=None, max_length=2000, description="Tasting notes, provenance, …")

    # Optional link to a homemade recipe
    recipe_id: int | None = Field(default=None, foreign_key="recipes.id", index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class StockEntryCreate(SQLModel):
    name: str = Field(..., max_length=200)
    origin: RhumOrigin = RhumOrigin.homemade
    state: StockState = StockState.ready
    volume_ml: int | None = Field(default=None, gt=0)
    quantity: int = Field(default=1, ge=0)
    vintage: int | None = None
    purchase_date: date | None = None
    preparation_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    recipe_id: int | None = None


class StockEntryUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=200)
    origin: RhumOrigin | None = None
    state: StockState | None = None
    volume_ml: int | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=0)
    vintage: int | None = None
    purchase_date: date | None = None
    preparation_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    recipe_id: int | None = None


class StockEntryRead(SQLModel):
    id: int
    name: str
    origin: RhumOrigin
    state: StockState
    volume_ml: int | None
    quantity: int
    vintage: int | None
    purchase_date: date | None
    preparation_date: date | None
    notes: str | None
    recipe_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# ===========================================================================
# Orders domain
# ===========================================================================

class OrderStatus(StrEnum):
    pending = "pending"
    paid = "paid"
    delivered = "delivered"

class BottleOrder(SQLModel, table=True):
    __tablename__ = "bottle_orders"

    id: int | None = Field(default=None, primary_key=True)
    quantity: int = Field(default=1, gt=0)
    price_per_bottle: float = Field(default=0.0, ge=0.0)
    total_price: float = Field(default=0.0, ge=0.0)
    status: OrderStatus = Field(default=OrderStatus.pending)
    
    client_id: int = Field(..., foreign_key="clients.id", index=True)
    stock_entry_id: int | None = Field(default=None, foreign_key="stock_entries.id", index=True)
    order_date: date = Field(default=date.today())

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class BottleOrderCreate(SQLModel):
    client_id: int = Field(..., index=True)
    quantity: int = Field(default=1, gt=0)
    price_per_bottle: float = Field(default=0.0, ge=0.0)
    total_price: float = Field(default=0.0, ge=0.0)
    status: OrderStatus = OrderStatus.pending
    stock_entry_id: int | None = None
    order_date: date = Field(default=date.today())

class BottleOrderUpdate(SQLModel):
    client_id: int | None = Field(default=None, index=True)
    quantity: int | None = Field(default=None, gt=0)
    price_per_bottle: float | None = Field(default=None, ge=0.0)
    total_price: float | None = Field(default=None, ge=0.0)
    status: OrderStatus | None = None
    stock_entry_id: int | None = None

class BottleOrderRead(SQLModel):
    id: int
    client_id: int
    quantity: int
    price_per_bottle: float
    total_price: float
    status: OrderStatus
    stock_entry_id: int | None
    order_date: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# ===========================================================================
# Clients domain
# ===========================================================================

class Client(SQLModel, table=True):
    __tablename__ = "clients"

    id: int | None = Field(default=None, primary_key=True)
    first_name: str = Field(..., index=True, max_length=120)
    last_name: str = Field(..., index=True, max_length=120)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # orders: list["BottleOrder"]

class ClientCreate(SQLModel):
    first_name: str = Field(..., max_length=120)
    last_name: str = Field(..., max_length=120)

class ClientRead(SQLModel):
    id: int
    first_name: str
    last_name: str
    created_at: datetime    
    updated_at: datetime
    # orders: list[BottleOrderRead]

    model_config = {"from_attributes": True}

class ClientUpdate(SQLModel):
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)

# ===========================================================================
# Users domain (for App owner)
# ===========================================================================

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(default="admin", unique=True, index=True, max_length=120)
    theme: ThemePreference = Field(default=ThemePreference.system)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class UserCreate(SQLModel):
    username: str = Field(default="admin", max_length=120)
    theme: ThemePreference = ThemePreference.system

class UserUpdate(SQLModel):
    theme: ThemePreference | None = None

class UserRead(SQLModel):
    id: int
    username: str
    theme: ThemePreference
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}