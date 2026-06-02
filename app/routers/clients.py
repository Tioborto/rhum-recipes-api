"""
CRUD router for /clients.

A client is a person who buys bottles.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, select

from app.database import get_session
from app.models import (
    Client,
    ClientCreate,
    ClientRead,
    ClientUpdate,
)

router = APIRouter(prefix="/clients", tags=["Clients"])

SessionDep = Annotated[Session, Depends(get_session)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_or_404(client_id: int, session: Session) -> Client:
    entry = session.get(Client, client_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client #{client_id} not found.",
        )
    return entry


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=ClientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a client",
)
def create_client(payload: ClientCreate, session: SessionDep) -> ClientRead:
    entry = Client(**payload.model_dump())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return ClientRead.model_validate(entry)


@router.get(
    "/",
    response_model=list[ClientRead],
    summary="List all clients",
)
def list_clients(
    session: SessionDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ClientRead]:
    query = select(Client)
    query = query.order_by(col(Client.created_at).desc()).offset(offset).limit(limit)
    entries = session.exec(query).all()
    return [ClientRead.model_validate(e) for e in entries]


@router.get(
    "/{client_id}",
    response_model=ClientRead,
    summary="Get a client by ID",
)
def get_client(client_id: int, session: SessionDep) -> ClientRead:
    return ClientRead.model_validate(_get_or_404(client_id, session))


@router.patch(
    "/{client_id}",
    response_model=ClientRead,
    summary="Partially update a client",
)
def update_client(
    client_id: int, payload: ClientUpdate, session: SessionDep
) -> ClientRead:
    entry = _get_or_404(client_id, session)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    entry.updated_at = datetime.now(UTC)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return ClientRead.model_validate(entry)


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a client",
)
def delete_client(client_id: int, session: SessionDep) -> None:
    entry = _get_or_404(client_id, session)
    session.delete(entry)
    session.commit()
