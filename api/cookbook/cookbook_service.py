import logging
import os
import uuid
from typing import List
import boto3
import requests
from fastapi import APIRouter, Depends, HTTPException, Body
from recipe_scrapers import scrape_me

from models.models import Recipe
from storage.utils import read_recipe_items, write_recipe_items, pantry_table
from storage.utils import read_recipe_items, write_recipe_items, pantry_table, soft_delete_recipe_item
from auth.auth_service import get_current_user, get_user_id_from_token

get_user = get_current_user
get_user_id = get_user_id_from_token

cookbook_router = APIRouter(prefix="/cookbook")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

S3_BUCKET_NAME = os.getenv("IMAGE_BUCKET_NAME", "ppal-images")
s3 = boto3.client("s3")

def _ensure_bucket(bucket_name: str):
    try:
        s3.head_bucket(Bucket=bucket_name)
    except s3.exceptions.NoSuchBucket:
        s3.create_bucket(Bucket=bucket_name)

def _upload_recipe_image(img_data: bytes) -> str:
    _ensure_bucket(S3_BUCKET_NAME)
    key = f"recipes/{uuid.uuid4()}.jpg"
    s3.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=img_data, ContentType="image/jpeg")
    return f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{key}"

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
    try:
        soft_delete_recipe_item(user_id, recipe_id)
        return {"message": "Recipe soft deleted"}
    except Exception as e:
        logging.error(f"Error soft deleting recipe: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete recipe")


@cookbook_router.post("/import", response_model=Recipe)
def import_recipe(payload: dict = Body(...), user_id: str = Depends(get_user_id)) -> Recipe:
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        scraper = scrape_me(url)
        name = scraper.title() or "Imported recipe"
        ingredients = scraper.ingredients()
        instructions = scraper.instructions()
        img = scraper.image()
        cook_time = str(scraper.total_time()) if hasattr(scraper, "total_time") else None
        tags = scraper.tags() if hasattr(scraper, "tags") else None
    except Exception as e:
        logging.error(f"Scraping failed for {url}: {e}")
        raise HTTPException(status_code=400, detail="Unsupported or unstructured recipe URL")

    image_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/recipes/default.jpg"
    if img:
        try:
            resp = requests.get(img, timeout=10)
            resp.raise_for_status()
            image_url = _upload_recipe_image(resp.content)
        except Exception as e:
            logging.warning(f"Image fetch/upload failed: {e}; using placeholder")

    recipe = Recipe(
        name=name,
        ingredients=ingredients,
        instructions=instructions,
        image_url=image_url,
        cook_time=cook_time,
        tags=tags,
    )

    try:
        write_recipe_items(user_id, [recipe])
    except Exception as e:
        logging.error(f"Error saving imported recipe: {e}")
        raise HTTPException(status_code=500, detail="Failed to save recipe")

    return recipe
