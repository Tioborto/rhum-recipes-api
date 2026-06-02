"""
CRUD router for /recipes.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, select, delete

from app.database import get_session
from app.models import (
    Recipe,
    RecipeCreate,
    RecipeListItem,
    RecipeRead,
    RecipeUpdate,
    GlobalIngredient,
    RecipeIngredientLink,
)

router = APIRouter(prefix="/recipes", tags=["Recipes"])

SessionDep = Annotated[Session, Depends(get_session)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_or_404(recipe_id: int, session: Session) -> Recipe:
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe #{recipe_id} not found.",
        )
    return recipe


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=RecipeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new rhum recipe",
)
def create_recipe(payload: RecipeCreate, session: SessionDep) -> RecipeRead:
    # Check uniqueness
    existing = session.exec(select(Recipe).where(Recipe.name == payload.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A recipe named '{payload.name}' already exists.",
        )

    recipe = Recipe(
        name=payload.name,
        description=payload.description,
    )
    
    session.add(recipe)
    session.flush() # get recipe.id

    for ing_data in payload.ingredients:
        name = ing_data.name.strip()
        if not name:
            continue
            
        global_ing = session.exec(select(GlobalIngredient).where(GlobalIngredient.name == name)).first()
        if not global_ing:
            global_ing = GlobalIngredient(name=name)
            session.add(global_ing)
            session.flush()
            
        link = RecipeIngredientLink(
            recipe_id=recipe.id,
            ingredient_id=global_ing.id,
            quantity=ing_data.quantity,
            unit=ing_data.unit
        )
        session.add(link)

    session.commit()
    session.refresh(recipe)
    return RecipeRead.from_orm_recipe(recipe)


@router.get(
    "/",
    response_model=list[RecipeListItem],
    summary="List all recipes (summary view)",
)
def list_recipes(
    session: SessionDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[RecipeListItem]:
    query = select(Recipe).order_by(col(Recipe.created_at).desc()).offset(offset).limit(limit)
    recipes = session.exec(query).all()
    return [
        RecipeListItem(
            id=r.id,  # type: ignore[arg-type]
            name=r.name,
            created_at=r.created_at,
        )
        for r in recipes
    ]


@router.get(
    "/{recipe_id}",
    response_model=RecipeRead,
    summary="Get a recipe by ID",
)
def get_recipe(recipe_id: int, session: SessionDep) -> RecipeRead:
    return RecipeRead.from_orm_recipe(_get_or_404(recipe_id, session))


@router.patch(
    "/{recipe_id}",
    response_model=RecipeRead,
    summary="Partially update a recipe",
)
def update_recipe(recipe_id: int, payload: RecipeUpdate, session: SessionDep) -> RecipeRead:
    recipe = _get_or_404(recipe_id, session)

    update_data = payload.model_dump(exclude_unset=True)

    # Handle ingredients
    if payload.ingredients is not None:
        # delete existing links
        session.exec(delete(RecipeIngredientLink).where(RecipeIngredientLink.recipe_id == recipe.id))
        
        for ing_data in payload.ingredients:
            name = ing_data.name.strip()
            if not name:
                continue
                
            global_ing = session.exec(select(GlobalIngredient).where(GlobalIngredient.name == name)).first()
            if not global_ing:
                global_ing = GlobalIngredient(name=name)
                session.add(global_ing)
                session.flush()
                
            link = RecipeIngredientLink(
                recipe_id=recipe.id,
                ingredient_id=global_ing.id,
                quantity=ing_data.quantity,
                unit=ing_data.unit
            )
            session.add(link)
            
        update_data.pop("ingredients", None)

    for field, value in update_data.items():
        setattr(recipe, field, value)

    recipe.updated_at = datetime.now(UTC)
    session.add(recipe)
    session.commit()
    session.refresh(recipe)
    return RecipeRead.from_orm_recipe(recipe)


@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a recipe",
)
def delete_recipe(recipe_id: int, session: SessionDep) -> None:
    recipe = _get_or_404(recipe_id, session)
    session.delete(recipe)
    session.commit()
