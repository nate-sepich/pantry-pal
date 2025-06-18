import os
import json
from fastapi import APIRouter, Depends, HTTPException
from auth.auth_service import get_user_id_from_token
from storage.utils import (
    add_liked_recipe,
    remove_liked_recipe,
    read_liked_recipes,
    read_pantry_items,
)
from ai.openai_service import build_recipe_prompt, call_openai

# Load sample recipes for offline demos
SAMPLE_FILE = os.path.join(os.path.dirname(__file__), "example", "recipes.json")
if os.path.exists(SAMPLE_FILE):
    with open(SAMPLE_FILE) as fh:
        SAMPLE_RECIPES = json.load(fh)
else:
    SAMPLE_RECIPES = []

recipes_router = APIRouter(prefix="/recipes")

@recipes_router.post("/{recipe_id}/like", status_code=204)
def like_recipe(recipe_id: str, user_id: str = Depends(get_user_id_from_token)):
    """Mark a recipe as liked for the authenticated user."""
    add_liked_recipe(user_id, recipe_id)
    return None

@recipes_router.delete("/{recipe_id}/like", status_code=204)
def unlike_recipe(recipe_id: str, user_id: str = Depends(get_user_id_from_token)):
    """Remove a recipe from the user's liked list."""
    remove_liked_recipe(user_id, recipe_id)
    return None

@recipes_router.get("/recommendations")
def get_recommendations(user_id: str = Depends(get_user_id_from_token)):
    """Return recipe suggestions using pantry items and liked history."""
    items = [it.dict() if hasattr(it, "dict") else it for it in read_pantry_items(user_id)]
    prompt = build_recipe_prompt(items)
    try:
        raw = call_openai(prompt)
        suggestions = json.loads(raw)
    except Exception:
        suggestions = []
    if not suggestions:
        suggestions = SAMPLE_RECIPES
    liked = [r.recipe_id for r in read_liked_recipes(user_id)]
    return {"liked": liked, "recommendations": suggestions}
