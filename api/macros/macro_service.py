import asyncio
import os
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends, Request
import httpx
import requests
from typing import Optional, List
from dotenv import load_dotenv
from models.models import (
    InventoryItemMacros,
    RecipeInput,
    UPCResponseModel,
    FoodSuggestion,
    FoodCategory,
    ItemMacroRequest,
)
import logging
from storage.utils import read_pantry_items, write_pantry_items, read_recipe_items
from pantry.pantry_service import get_current_user

# load .env file
load_dotenv()

# Load your USDA API Key
USDA_API_KEY = os.getenv("USDA_API_KEY")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CATEGORY_MAP = {
    "dairy": FoodCategory.DAIRY,
    "egg": FoodCategory.DAIRY,
    "meat": FoodCategory.MEAT,
    "poultry": FoodCategory.MEAT,
    "pork": FoodCategory.MEAT,
    "beef": FoodCategory.MEAT,
    "fish": FoodCategory.SEAFOOD,
    "seafood": FoodCategory.SEAFOOD,
    "grain": FoodCategory.CARBS,
    "cereal": FoodCategory.CARBS,
    "bakery": FoodCategory.CARBS,
    "oil": FoodCategory.FATS,
    "fat": FoodCategory.FATS,
    "vegetable": FoodCategory.VEGETABLES,
    "fruit": FoodCategory.FRUITS,
    "beverage": FoodCategory.BEVERAGES,
    "drink": FoodCategory.BEVERAGES,
}

UNIT_CONVERSIONS = {
    "g": Decimal("1"),
    "kg": Decimal("1000"),
    "oz": Decimal("28.3495"),
    "lb": Decimal("453.592"),
    "ml": Decimal("1"),
    "l": Decimal("1000"),
    "fl_oz": Decimal("29.5735"),
}


def map_food_category(raw: str) -> FoodCategory:
    lower = (raw or "").lower()
    for key, cat in CATEGORY_MAP.items():
        if key in lower:
            return cat
    return FoodCategory.OTHER


def convert_to_grams(qty: Decimal, unit: str) -> Decimal:
    factor = UNIT_CONVERSIONS.get(unit.lower())
    if factor is None:
        raise HTTPException(status_code=400, detail="Unsupported unit")
    return qty * factor


# Define an async function to search for food items using the USDA FoodData Central API
async def search_food_item_async(item_name: str) -> Optional[int]:
    """Return the FDC id for the first matching item name."""
    search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": USDA_API_KEY, "query": item_name}
    async with httpx.AsyncClient() as client:
        resp = await client.get(search_url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        foods = data.get("foods", [])
        if foods:
            return foods[0]["fdcId"]
    return None


async def search_food_items_async(query: str) -> List[dict]:
    """Return a list of USDA search results for the given query."""
    search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": USDA_API_KEY, "query": query}
    async with httpx.AsyncClient() as client:
        resp = await client.get(search_url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("foods", [])
    logging.error(f"USDA search failed: {resp.status_code}")
    raise HTTPException(status_code=resp.status_code, detail="Error fetching suggestions")


# Define an async function to fetch food details using the USDA FoodData Central API
async def fetch_food_details_async(
    fdc_id: int, format: str = "full", nutrients: Optional[List[int]] = None
) -> Optional[InventoryItemMacros]:
    """
    Asynchronous fetch of detailed food nutrient information using the FDC ID.
    Supports optional format (abridged/full) and nutrient filtering.
    """
    detail_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
    params = {"api_key": USDA_API_KEY, "format": format}
    if nutrients:
        params["nutrients"] = ",".join(map(str, nutrients))

    async with httpx.AsyncClient() as client:
        response = await client.get(detail_url, params=params)
        if response.status_code == 200:
            food_data = response.json()
            nutrients = {
                nutrient["nutrient"]["name"]: nutrient["amount"]
                for nutrient in food_data.get("foodNutrients", [])
            }

            return InventoryItemMacros(
                protein=nutrients.get("Protein", 0),
                carbohydrates=nutrients.get("Carbohydrate, by difference", 0),
                fiber=nutrients.get("Fiber, total dietary", 0),
                sugar=nutrients.get("Sugars, total including NLEA", 0),
                fat=nutrients.get("Total lipid (fat)", 0),
                saturated_fat=nutrients.get("Fatty acids, total saturated", 0),
                polyunsaturated_fat=nutrients.get("Fatty acids, total polyunsaturated", 0),
                monounsaturated_fat=nutrients.get("Fatty acids, total monounsaturated", 0),
                trans_fat=nutrients.get("Fatty acids, total trans", 0),
                cholesterol=nutrients.get("Cholesterol", 0),
                sodium=nutrients.get("Sodium, Na", 0),
                potassium=nutrients.get("Potassium, K", 0),
                vitamin_a=nutrients.get("Vitamin A, RAE", 0),
                vitamin_c=nutrients.get("Vitamin C, total ascorbic acid", 0),
                calcium=nutrients.get("Calcium, Ca", 0),
                iron=nutrients.get("Iron, Fe", 0),
                calories=nutrients.get("Calories", 0),  # Add calories
            )
    return None


# Define an async function to query the USDA FoodData Central API for macro information
async def query_food_api_async(item_name: str) -> Optional[InventoryItemMacros]:
    """
    Asynchronous query of the USDA FoodData Central API to retrieve macro information for a given food item.
    First searches for the item, then fetches detailed nutrient information using the fdcId.
    """
    fdc_id = await search_food_item_async(item_name)

    if fdc_id:
        return await fetch_food_details_async(fdc_id)

    return None


macro_router = APIRouter(prefix="/macros")


# Define a function to search for food items using the USDA FoodData Central API
def search_food_item(item_name: str) -> Optional[int]:
    """
    Search for food items using the USDA FoodData Central API.
    Returns the fdcId of the first result, or None if no result is found.
    """
    search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": USDA_API_KEY, "query": item_name}
    response = requests.get(search_url, params=params)

    if response.status_code == 200:
        search_data = response.json()
        if search_data["foods"]:
            # Return the first food's FDC ID
            return search_data["foods"][0]["fdcId"]
    return None


def fetch_food_details(
    fdc_id: int, format: str = "full", nutrients: Optional[List[int]] = None
) -> Optional[InventoryItemMacros]:
    """
    Fetch detailed food nutrient information using the FDC ID.
    Supports optional format (abridged/full) and nutrient filtering.
    """
    detail_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
    params = {"api_key": USDA_API_KEY, "format": format}
    if nutrients:
        params["nutrients"] = ",".join(map(str, nutrients))

    response = requests.get(detail_url, params=params)
    if response.status_code == 200:
        food_data = response.json()
        nutrients = {
            nutrient["nutrient"]["name"]: nutrient["amount"]
            for nutrient in food_data.get("foodNutrients", [])
        }

        # Map USDA nutrient data to your InventoryItemMacros model
        return InventoryItemMacros(
            protein=nutrients.get("Protein", 0),
            carbohydrates=nutrients.get("Carbohydrate, by difference", 0),
            fiber=nutrients.get("Fiber, total dietary", 0),
            sugar=nutrients.get("Sugars, total including NLEA", 0),
            fat=nutrients.get("Total lipid (fat)", 0),
            saturated_fat=nutrients.get("Fatty acids, total saturated", 0),
            polyunsaturated_fat=nutrients.get("Fatty acids, total polyunsaturated", 0),
            monounsaturated_fat=nutrients.get("Fatty acids, total monounsaturated", 0),
            trans_fat=nutrients.get("Fatty acids, total trans", 0),
            cholesterol=nutrients.get("Cholesterol", 0),
            sodium=nutrients.get("Sodium, Na", 0),
            potassium=nutrients.get("Potassium, K", 0),
            vitamin_a=nutrients.get("Vitamin A, RAE", 0),
            vitamin_c=nutrients.get("Vitamin C, total ascorbic acid", 0),
            calcium=nutrients.get("Calcium, Ca", 0),
            iron=nutrients.get("Iron, Fe", 0),
            calories=nutrients.get("Energy", 0),  # Add calories
        )

    return None


def query_food_api(item_name: str) -> Optional[InventoryItemMacros]:
    """
    Query the USDA FoodData Central API to retrieve macro information for a given food item.
    First searches for the item, then fetches detailed nutrient information using the fdcId.
    Portion size is in grams by default.
    """
    fdc_id = search_food_item(item_name)

    if fdc_id:
        return fetch_food_details(fdc_id)

    return None


@macro_router.post("/item", response_model=InventoryItemMacros)
async def get_item_macros(req: ItemMacroRequest):
    """Lookup macros for a single food item and scale by quantity."""
    macro_data = await query_food_api_async(req.item_name)
    if not macro_data:
        raise HTTPException(status_code=404, detail="Item not found")
    grams = convert_to_grams(req.quantity, req.unit)
    factor = grams / Decimal(100)
    return InventoryItemMacros(
        calories=macro_data.calories * factor,
        protein=macro_data.protein * factor,
        carbohydrates=macro_data.carbohydrates * factor,
        fiber=macro_data.fiber * factor,
        sugar=macro_data.sugar * factor,
        fat=macro_data.fat * factor,
        saturated_fat=macro_data.saturated_fat * factor,
        polyunsaturated_fat=macro_data.polyunsaturated_fat * factor,
        monounsaturated_fat=macro_data.monounsaturated_fat * factor,
        trans_fat=macro_data.trans_fat * factor,
        cholesterol=macro_data.cholesterol * factor,
        sodium=macro_data.sodium * factor,
        potassium=macro_data.potassium * factor,
        vitamin_a=macro_data.vitamin_a * factor,
        vitamin_c=macro_data.vitamin_c * factor,
        calcium=macro_data.calcium * factor,
        iron=macro_data.iron * factor,
    )


@macro_router.post("/recipe")
async def get_recipe_macros(recipe: RecipeInput):
    """
    Calculate the total macro-nutrient information for a recipe based on its ingredients and servings.

    Parameters:
        recipe (RecipeInput): The recipe input containing ingredients and servings (request body).
    Returns:
        InventoryItemMacros: Aggregated macro-nutrient data for the recipe, scaled by servings.
    Error Codes:
        400: Bad request if input is invalid or ingredient data is missing.
    """
    total_macros = InventoryItemMacros()

    # Create a list of tasks to query the API for each ingredient in parallel
    tasks = [
        query_food_api_async(ingredient_input.item_name) for ingredient_input in recipe.ingredients
    ]

    # Gather the results in parallel
    results = await asyncio.gather(*tasks)

    # Process the results and aggregate the macros
    for i, macro_data in enumerate(results):
        if macro_data:
            ingredient_quantity = recipe.ingredients[i].quantity
            # Scale the macros based on the quantity of the ingredient (assuming data is per 100g)
            total_macros.protein += macro_data.protein * (ingredient_quantity / 100)
            total_macros.carbohydrates += macro_data.carbohydrates * (ingredient_quantity / 100)
            total_macros.fiber += macro_data.fiber * (ingredient_quantity / 100)
            total_macros.sugar += macro_data.sugar * (ingredient_quantity / 100)
            total_macros.fat += macro_data.fat * (ingredient_quantity / 100)
            total_macros.saturated_fat += macro_data.saturated_fat * (ingredient_quantity / 100)
            total_macros.polyunsaturated_fat += macro_data.polyunsaturated_fat * (
                ingredient_quantity / 100
            )
            total_macros.monounsaturated_fat += macro_data.monounsaturated_fat * (
                ingredient_quantity / 100
            )
            total_macros.trans_fat += macro_data.trans_fat * (ingredient_quantity / 100)
            total_macros.cholesterol += macro_data.cholesterol * (ingredient_quantity / 100)
            total_macros.sodium += macro_data.sodium * (ingredient_quantity / 100)
            total_macros.potassium += macro_data.potassium * (ingredient_quantity / 100)
            total_macros.vitamin_a += macro_data.vitamin_a * (ingredient_quantity / 100)
            total_macros.vitamin_c += macro_data.vitamin_c * (ingredient_quantity / 100)
            total_macros.calcium += macro_data.calcium * (ingredient_quantity / 100)
            total_macros.iron += macro_data.iron * (ingredient_quantity / 100)
            total_macros.calories += macro_data.calories * (
                ingredient_quantity / 100
            )  # Add calories
        else:
            return {
                "error": f"Ingredient {recipe.ingredients[i].item_name} not found or data unavailable"
            }

    # Scale macros by servings
    if recipe.servings > 1:
        total_macros = InventoryItemMacros(
            protein=total_macros.protein / recipe.servings,
            carbohydrates=total_macros.carbohydrates / recipe.servings,
            fiber=total_macros.fiber / recipe.servings,
            sugar=total_macros.sugar / recipe.servings,
            fat=total_macros.fat / recipe.servings,
            saturated_fat=total_macros.saturated_fat / recipe.servings,
            polyunsaturated_fat=total_macros.polyunsaturated_fat / recipe.servings,
            monounsaturated_fat=total_macros.monounsaturated_fat / recipe.servings,
            trans_fat=total_macros.trans_fat / recipe.servings,
            cholesterol=total_macros.cholesterol / recipe.servings,
            sodium=total_macros.sodium / recipe.servings,
            potassium=total_macros.potassium / recipe.servings,
            vitamin_a=total_macros.vitamin_a / recipe.servings,
            vitamin_c=total_macros.vitamin_c / recipe.servings,
            calcium=total_macros.calcium / recipe.servings,
            iron=total_macros.iron / recipe.servings,
            calories=total_macros.calories / recipe.servings,  # Add calories
        )

    return total_macros


@macro_router.get("/item/{item_id}", response_model=InventoryItemMacros)
def get_item_macros(item_id: str, user_claims: dict = Depends(get_current_user)):
    """
    Retrieve macro-nutrient information for a specific pantry item by its ID and user ID.
    """
    user_id = user_claims["sub"]
    items = read_pantry_items(user_id)
    for item in items:
        if item["id"] == item_id:
            return item.get("macros", InventoryItemMacros())
    raise HTTPException(status_code=404, detail="Item not found")


@macro_router.get("/total", response_model=InventoryItemMacros)
def get_total_macros(user_claims: dict = Depends(get_current_user)):
    """
    Calculate the total macro-nutrient values for all pantry items belonging to a user.
    """
    user_id = user_claims["sub"]
    items = read_pantry_items(user_id)
    total_macros = InventoryItemMacros()
    for item in items:
        if item.get("macros"):
            total_macros.calories += item["macros"].get("calories", 0)
            total_macros.protein += item["macros"].get("protein", 0)
            total_macros.carbohydrates += item["macros"].get("carbohydrates", 0)
            total_macros.fiber += item["macros"].get("fiber", 0)
            total_macros.sugar += item["macros"].get("sugar", 0)
            total_macros.fat += item["macros"].get("fat", 0)
            total_macros.saturated_fat += item["macros"].get("saturated_fat", 0)
            total_macros.polyunsaturated_fat += item["macros"].get("polyunsaturated_fat", 0)
            total_macros.monounsaturated_fat += item["macros"].get("monounsaturated_fat", 0)
            total_macros.trans_fat += item["macros"].get("trans_fat", 0)
            total_macros.cholesterol += item["macros"].get("cholesterol", 0)
            total_macros.sodium += item["macros"].get("sodium", 0)
            total_macros.potassium += item["macros"].get("potassium", 0)
            total_macros.vitamin_a += item["macros"].get("vitamin_a", 0)
            total_macros.vitamin_c += item["macros"].get("vitamin_c", 0)
            total_macros.calcium += item["macros"].get("calcium", 0)
            total_macros.iron += item["macros"].get("iron", 0)
    return total_macros


@macro_router.get("/autocomplete", response_model=List[FoodSuggestion])
async def autocomplete(query: str, category: Optional[FoodCategory] = None):
    """Return up to five autocomplete suggestions."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="query cannot be blank")
    logging.info(f"Providing autocomplete suggestions for query: {query}")
    foods = await search_food_items_async(query)
    suggestions: List[FoodSuggestion] = []
    for food in foods:
        cat = map_food_category(food.get("foodCategory", ""))
        if category and cat != category:
            continue
        suggestions.append(
            FoodSuggestion(
                name=food.get("description", ""), fdc_id=str(food.get("fdcId")), category=cat
            )
        )
        if len(suggestions) >= 5:
            break
    return suggestions


@macro_router.get("/upc", response_model=UPCResponseModel)
def lookup_upc(upc: str):
    """
    Retrieve the FDC ID for a food item using its UPC code via the USDA API.

    Parameters:
        upc (str): The UPC code of the food item (query parameter).
    Returns:
        UPCResponseModel: The FDC ID for the item, or None if not found.
    Error Codes:
        404: Item not found for the given UPC code.
    """
    fdc_id = search_food_item(upc)
    if not fdc_id:
        raise HTTPException(status_code=404, detail="Item not found for UPC")
    return UPCResponseModel(fdc_id=str(fdc_id))


def enrich_item(data: dict):
    """
    Fetch macros for an item using the USDA API and update the pantry.
    """
    item_name = data["item_name"]
    user_id = data["user_id"]
    item_id = data["item_id"]

    logging.info(f"Enriching item: {item_name} for user ID: {user_id}")
    macros = query_food_api(item_name)
    if macros:
        items = read_pantry_items(user_id)
        for i, it in enumerate(items):
            if it.id == item_id:
                it.macros = macros
                write_pantry_items(user_id, [it])
                logging.info(f"Updated macros for item ID: {item_id}")
                return
    logging.warning(f"Failed to enrich item: {item_name}. No macros found.")


def enrich_recipe(data: dict):
    """
    Aggregate macros for a recipe based on its ingredients and update the recipe.
    """
    user_id = data["user_id"]
    recipe_id = data["recipe_id"]

    logging.info(f"Enriching recipe ID: {recipe_id} for user ID: {user_id}")
    recipes = read_recipe_items(user_id)
    for rec in recipes:
        if rec.id == recipe_id:
            total = InventoryItemMacros()
            for ing in rec.ingredients:
                macros = query_food_api(ing.item_name)
                if macros:
                    factor = ing.quantity / 100
                    total.protein += macros.protein * factor
                    total.carbohydrates += macros.carbohydrates * factor
                    total.fiber += macros.fiber * factor
                    total.sugar += macros.sugar * factor
                    total.fat += macros.fat * factor
                    total.saturated_fat += macros.saturated_fat * factor
                    total.polyunsaturated_fat += macros.polyunsaturated_fat * factor
                    total.monounsaturated_fat += macros.monounsaturated_fat * factor
                    total.trans_fat += macros.trans_fat * factor
                    total.cholesterol += macros.cholesterol * factor
                    total.sodium += macros.sodium * factor
                    total.potassium += macros.potassium * factor
                    total.vitamin_a += macros.vitamin_a * factor
                    total.vitamin_c += macros.vitamin_c * factor
                    total.calcium += macros.calcium * factor
                    total.iron += macros.iron * factor
            rec.total_macros = total
            write_recipe_items(user_id, [rec])
            logging.info(f"Updated macros for recipe ID: {recipe_id}")
            return
    logging.warning(f"Failed to enrich recipe ID: {recipe_id}. Recipe not found.")
