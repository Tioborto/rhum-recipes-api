"""
CRUD router for /stock.

A stock entry represents a physical bottle (or set of bottles) on the shelf —
either a commercial rhum purchase or a homemade batch from a recipe.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, select

from app.database import get_session
from app.models import (
    RhumOrigin,
    StockEntry,
    StockEntryCreate,
    StockEntryRead,
    StockEntryUpdate,
)

router = APIRouter(prefix="/stock", tags=["Stock"])

SessionDep = Annotated[Session, Depends(get_session)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_or_404(entry_id: int, session: Session) -> StockEntry:
    entry = session.get(StockEntry, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock entry #{entry_id} not found.",
        )
    return entry


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=StockEntryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a bottle (or batch of bottles) to the stock",
)
def create_stock_entry(payload: StockEntryCreate, session: SessionDep) -> StockEntryRead:
    entry = StockEntry(**payload.model_dump())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return StockEntryRead.model_validate(entry)


@router.get(
    "/",
    response_model=list[StockEntryRead],
    summary="List all stock entries",
)
def list_stock(
    session: SessionDep,
    origin: RhumOrigin | None = Query(default=None),
    recipe_id: int | None = Query(default=None, description="Filter by linked recipe"),
    in_stock_only: bool = Query(default=False, description="Only entries with quantity > 0"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[StockEntryRead]:
    query = select(StockEntry)
    if origin:
        query = query.where(StockEntry.origin == origin)
    if recipe_id is not None:
        query = query.where(StockEntry.recipe_id == recipe_id)
    if in_stock_only:
        query = query.where(StockEntry.quantity > 0)
    query = query.order_by(col(StockEntry.created_at).desc()).offset(offset).limit(limit)
    entries = session.exec(query).all()
    return [StockEntryRead.model_validate(e) for e in entries]


@router.get(
    "/{entry_id}",
    response_model=StockEntryRead,
    summary="Get a stock entry by ID",
)
def get_stock_entry(entry_id: int, session: SessionDep) -> StockEntryRead:
    return StockEntryRead.model_validate(_get_or_404(entry_id, session))


@router.patch(
    "/{entry_id}",
    response_model=StockEntryRead,
    summary="Partially update a stock entry (e.g. adjust quantity)",
)
def update_stock_entry(
    entry_id: int, payload: StockEntryUpdate, session: SessionDep
) -> StockEntryRead:
    entry = _get_or_404(entry_id, session)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    entry.updated_at = datetime.now(UTC)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return StockEntryRead.model_validate(entry)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a stock entry",
)
def delete_stock_entry(entry_id: int, session: SessionDep) -> None:
    entry = _get_or_404(entry_id, session)
    session.delete(entry)
    session.commit()
