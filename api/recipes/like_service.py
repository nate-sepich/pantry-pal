from fastapi import APIRouter, Depends, HTTPException
from auth.auth_service import get_user_id_from_token
from storage.utils import (
    add_liked_recipe,
    remove_liked_recipe,
    read_liked_recipes,
    read_pantry_items,
)
from ai.openai_service import build_recipe_prompt, call_openai
import json

recipes_router = APIRouter(prefix="/recipes")

@recipes_router.post("/{recipe_id}/like", status_code=204)
def like_recipe(recipe_id: str, user_id: str = Depends(get_user_id_from_token)):
    add_liked_recipe(user_id, recipe_id)
    return None

@recipes_router.delete("/{recipe_id}/like", status_code=204)
def unlike_recipe(recipe_id: str, user_id: str = Depends(get_user_id_from_token)):
    remove_liked_recipe(user_id, recipe_id)
    return None

@recipes_router.get("/recommendations")
def get_recommendations(user_id: str = Depends(get_user_id_from_token)):
    items = [it.dict() if hasattr(it, "dict") else it for it in read_pantry_items(user_id)]
    prompt = build_recipe_prompt(items)
    try:
        raw = call_openai(prompt)
        suggestions = json.loads(raw)
    except Exception:
        suggestions = []
    liked = [r.recipe_id for r in read_liked_recipes(user_id)]
    return {"liked": liked, "recommendations": suggestions}
