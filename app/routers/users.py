from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Any

from app.database import get_session
from app.models import User, UserRead, UserUpdate, ThemePreference

router = APIRouter(prefix="/users", tags=["Users"])

def get_current_user(session: Session = Depends(get_session)) -> User:
    # We create a single 'admin' user since it's a single-tenant app
    user = session.exec(select(User).where(User.username == "admin")).first()
    if not user:
        user = User(username="admin", theme=ThemePreference.system)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

@router.get("/me", response_model=UserRead, summary="Get current user profile")
def get_me(current_user: User = Depends(get_current_user)) -> Any:
    return current_user

@router.patch("/me", response_model=UserRead, summary="Update current user settings")
def update_me(
    user_in: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    if user_in.theme is not None:
        # Pydantic/SQLModel handles the enum validation automatically
        current_user.theme = user_in.theme

    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user
