import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from models.models import Recipe
from storage.utils import read_recipe_items, write_recipe_items, pantry_table
from auth.auth_service import get_current_user, get_user_id_from_token

get_user = get_current_user
get_user_id = get_user_id_from_token

cookbook_router = APIRouter(prefix="/cookbook")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@cookbook_router.get("", response_model=List[Recipe])
def list_recipes(user_id: str = Depends(get_user_id)) -> List[Recipe]:
    """List all recipes for the authenticated user."""
    return read_recipe_items(user_id)

@cookbook_router.post("", response_model=Recipe)
def add_recipe(recipe: Recipe, user_id: str = Depends(get_user_id)) -> Recipe:
    """Save a recipe for the authenticated user."""
    try:
        write_recipe_items(user_id, [recipe])
        return recipe
    except Exception as e:
        logging.error(f"Error saving recipe: {e}")
        raise HTTPException(status_code=500, detail="Failed to save recipe")

@cookbook_router.delete("/{recipe_id}")
def delete_recipe(recipe_id: str, user_id: str = Depends(get_user_id)) -> dict:
    """Delete a recipe for the authenticated user."""
    pk = f"USER#{user_id}"
    sk = f"RECIPE#{recipe_id}"
    try:
        pantry_table.delete_item(Key={"PK": pk, "SK": sk})
        return {"message": "Recipe deleted"}
    except Exception as e:
        logging.error(f"Error deleting recipe: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete recipe")
