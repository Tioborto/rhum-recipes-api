import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine
from app.models import Recipe, GlobalIngredient, RecipeIngredientLink, SQLModel
import json

def migrate():
    print("Creating new tables...")
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        recipes = session.exec(select(Recipe)).all()
        print(f"Found {len(recipes)} recipes to migrate.")
        
        for recipe in recipes:
            try:
                ing_list = json.loads(recipe.ingredients_json or "[]")
                if not ing_list:
                    continue
                
                print(f"Migrating recipe: {recipe.name} with {len(ing_list)} ingredients.")
                
                for ing_data in ing_list:
                    name = ing_data.get("name", "").strip()
                    if not name:
                        continue
                        
                    # Find or create GlobalIngredient
                    global_ing = session.exec(select(GlobalIngredient).where(GlobalIngredient.name == name)).first()
                    if not global_ing:
                        global_ing = GlobalIngredient(name=name)
                        session.add(global_ing)
                        session.flush() # flush to get ID
                        print(f"  Created GlobalIngredient: {name} (ID: {global_ing.id})")
                    
                    # Check if link already exists
                    existing_link = session.exec(
                        select(RecipeIngredientLink).where(
                            RecipeIngredientLink.recipe_id == recipe.id,
                            RecipeIngredientLink.ingredient_id == global_ing.id
                        )
                    ).first()
                    
                    if not existing_link:
                        link = RecipeIngredientLink(
                            recipe_id=recipe.id,
                            ingredient_id=global_ing.id,
                            quantity=float(ing_data.get("quantity", 0)),
                            unit=ing_data.get("unit", "")
                        )
                        session.add(link)
                        print(f"  Linked {name} to recipe.")
                        
            except Exception as e:
                print(f"Error migrating recipe {recipe.name}: {e}")
                
        session.commit()
        print("Migration complete!")

if __name__ == "__main__":
    migrate()
