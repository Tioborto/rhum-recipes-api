"""
CRUD router for /ingredients.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, select

from app.database import get_session
from app.models import (
    GlobalIngredient,
    GlobalIngredientCreate,
    GlobalIngredientRead,
    GlobalIngredientUpdate,
    GlobalIngredientWithDetails,
    RecipeIngredientLink,
    RecipeListItem,
    Recipe,
)

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])

SessionDep = Annotated[Session, Depends(get_session)]

def _get_or_404(ingredient_id: int, session: Session) -> GlobalIngredient:
    ingredient = session.get(GlobalIngredient, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient #{ingredient_id} not found.",
        )
    return ingredient

@router.get(
    "/",
    response_model=list[GlobalIngredientWithDetails],
    summary="List all global ingredients with usage details",
)
def list_ingredients(
    session: SessionDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[dict]:
    query = select(GlobalIngredient).order_by(col(GlobalIngredient.name).asc()).offset(offset).limit(limit)
    ingredients = session.exec(query).all()
    
    result = []
    for ing in ingredients:
        # Get links
        links = session.exec(select(RecipeIngredientLink).where(RecipeIngredientLink.ingredient_id == ing.id)).all()
        usage_count = len(links)
        
        recipes = []
        for link in links:
            recipe = session.get(Recipe, link.recipe_id)
            if recipe:
                recipes.append(
                    RecipeListItem(
                        id=recipe.id, # type: ignore
                        name=recipe.name,
                        created_at=recipe.created_at
                    )
                )
        
        result.append({
            "id": ing.id,
            "name": ing.name,
            "created_at": ing.created_at,
            "updated_at": ing.updated_at,
            "usage_count": usage_count,
            "recipes": recipes
        })
        
    return result

@router.post(
    "/",
    response_model=GlobalIngredientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new global ingredient",
)
def create_ingredient(payload: GlobalIngredientCreate, session: SessionDep) -> GlobalIngredient:
    existing = session.exec(select(GlobalIngredient).where(GlobalIngredient.name == payload.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An ingredient named '{payload.name}' already exists.",
        )

    ing = GlobalIngredient(name=payload.name)
    session.add(ing)
    session.commit()
    session.refresh(ing)
    return ing

@router.patch(
    "/{ingredient_id}",
    response_model=GlobalIngredientRead,
    summary="Rename an ingredient",
)
def update_ingredient(ingredient_id: int, payload: GlobalIngredientUpdate, session: SessionDep) -> GlobalIngredient:
    ing = _get_or_404(ingredient_id, session)
    
    if payload.name and payload.name != ing.name:
        existing = session.exec(select(GlobalIngredient).where(GlobalIngredient.name == payload.name)).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An ingredient named '{payload.name}' already exists.",
            )
        ing.name = payload.name
        session.add(ing)
        session.commit()
        session.refresh(ing)
        
    return ing

@router.delete(
    "/{ingredient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an ingredient (only if unused)",
)
def delete_ingredient(ingredient_id: int, session: SessionDep) -> None:
    ing = _get_or_404(ingredient_id, session)
    
    # Check if used
    links = session.exec(select(RecipeIngredientLink).where(RecipeIngredientLink.ingredient_id == ing.id)).all()
    if links:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete ingredient because it is used in {len(links)} recipe(s)."
        )
        
    session.delete(ing)
    session.commit()
