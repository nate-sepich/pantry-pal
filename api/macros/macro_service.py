import asyncio
import os
from fastapi import APIRouter, HTTPException
import httpx
import requests
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from models.models import InventoryItemMacros, RecipeInput, UPCResponseModel
import logging
from storage.utils import read_pantry_items

# load .env file
load_dotenv()

# Load your USDA API Key
USDA_API_KEY = os.getenv('USDA_API_KEY')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define an async function to search for food items using the USDA FoodData Central API
async def search_food_item_async(item_name: str) -> Optional[int]:
    """
    Asynchronous search for food items using the USDA FoodData Central API.
    Returns the fdcId of the first result, or None if no result is found.
    """
    search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}"
    params = {
        'query': item_name
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(search_url, params=params)
        print(response)
        if response.status_code == 200:
            search_data = response.json()
            if search_data['foods']:
                return search_data['foods'][0]['fdcId']
    return None

# Define an async function to fetch food details using the USDA FoodData Central API
async def fetch_food_details_async(fdc_id: int, format: str = 'full', nutrients: Optional[List[int]] = None) -> Optional[InventoryItemMacros]:
    """
    Asynchronous fetch of detailed food nutrient information using the FDC ID.
    Supports optional format (abridged/full) and nutrient filtering.
    """
    detail_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
    params = {
        'api_key': USDA_API_KEY,
        'format': format
    }
    if nutrients:
        params['nutrients'] = ','.join(map(str, nutrients))
    
    async with httpx.AsyncClient() as client:
        response = await client.get(detail_url, params=params)
        if response.status_code == 200:
            food_data = response.json()
            nutrients = {nutrient['nutrient']['name']: nutrient['amount'] for nutrient in food_data.get('foodNutrients', [])}
            
            return InventoryItemMacros(
                protein=nutrients.get('Protein', 0),
                carbohydrates=nutrients.get('Carbohydrate, by difference', 0),
                fiber=nutrients.get('Fiber, total dietary', 0),
                sugar=nutrients.get('Sugars, total including NLEA', 0),
                fat=nutrients.get('Total lipid (fat)', 0),
                saturated_fat=nutrients.get('Fatty acids, total saturated', 0),
                polyunsaturated_fat=nutrients.get('Fatty acids, total polyunsaturated', 0),
                monounsaturated_fat=nutrients.get('Fatty acids, total monounsaturated', 0),
                trans_fat=nutrients.get('Fatty acids, total trans', 0),
                cholesterol=nutrients.get('Cholesterol', 0),
                sodium=nutrients.get('Sodium, Na', 0),
                potassium=nutrients.get('Potassium, K', 0),
                vitamin_a=nutrients.get('Vitamin A, RAE', 0),
                vitamin_c=nutrients.get('Vitamin C, total ascorbic acid', 0),
                calcium=nutrients.get('Calcium, Ca', 0),
                iron=nutrients.get('Iron, Fe', 0),
                calories=nutrients.get('Calories', 0)  # Add calories
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
    params = {
        'api_key': USDA_API_KEY,
        'query': item_name
    }
    response = requests.get(search_url, params=params)
    
    if response.status_code == 200:
        search_data = response.json()
        if search_data['foods']:
            # Return the first food's FDC ID
            return search_data['foods'][0]['fdcId']
    return None

def fetch_food_details(fdc_id: int, format: str = 'full', nutrients: Optional[List[int]] = None) -> Optional[InventoryItemMacros]:
    """
    Fetch detailed food nutrient information using the FDC ID.
    Supports optional format (abridged/full) and nutrient filtering.
    """
    detail_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
    params = {
        'api_key': USDA_API_KEY,
        'format': format
    }
    if nutrients:
        params['nutrients'] = ','.join(map(str, nutrients))
    
    response = requests.get(detail_url, params=params)
    print(response)
    if response.status_code == 200:
        food_data = response.json()
        nutrients = {nutrient['nutrient']['name']: nutrient['amount'] for nutrient in food_data.get('foodNutrients', [])}
        
        # Map USDA nutrient data to your InventoryItemMacros model
        return InventoryItemMacros(
            protein=nutrients.get('Protein', 0),
            carbohydrates=nutrients.get('Carbohydrate, by difference', 0),
            fiber=nutrients.get('Fiber, total dietary', 0),
            sugar=nutrients.get('Sugars, total including NLEA', 0),
            fat=nutrients.get('Total lipid (fat)', 0),
            saturated_fat=nutrients.get('Fatty acids, total saturated', 0),
            polyunsaturated_fat=nutrients.get('Fatty acids, total polyunsaturated', 0),
            monounsaturated_fat=nutrients.get('Fatty acids, total monounsaturated', 0),
            trans_fat=nutrients.get('Fatty acids, total trans', 0),
            cholesterol=nutrients.get('Cholesterol', 0),
            sodium=nutrients.get('Sodium, Na', 0),
            potassium=nutrients.get('Potassium, K', 0),
            vitamin_a=nutrients.get('Vitamin A, RAE', 0),
            vitamin_c=nutrients.get('Vitamin C, total ascorbic acid', 0),
            calcium=nutrients.get('Calcium, Ca', 0),
            iron=nutrients.get('Iron, Fe', 0),
            calories=nutrients.get('Energy', 0)  # Add calories
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

@macro_router.get("/item")
def get_item_macros(item_name: str):
    """
    Endpoint to get the macro information for a given food item.
    """
    macro_data = query_food_api(item_name)
    print(macro_data)
    if macro_data:
        return macro_data
    else:
        return {"error": "Item not found or data unavailable"}
    

@macro_router.post("/recipe")
async def get_recipe_macros(recipe: RecipeInput):
    """
    Asynchronous endpoint to calculate the total macro information for a recipe based on ingredients and servings.
    """
    total_macros = InventoryItemMacros()

    # Create a list of tasks to query the API for each ingredient in parallel
    tasks = [query_food_api_async(ingredient_input.item_name) for ingredient_input in recipe.ingredients]
    
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
            total_macros.polyunsaturated_fat += macro_data.polyunsaturated_fat * (ingredient_quantity / 100)
            total_macros.monounsaturated_fat += macro_data.monounsaturated_fat * (ingredient_quantity / 100)
            total_macros.trans_fat += macro_data.trans_fat * (ingredient_quantity / 100)
            total_macros.cholesterol += macro_data.cholesterol * (ingredient_quantity / 100)
            total_macros.sodium += macro_data.sodium * (ingredient_quantity / 100)
            total_macros.potassium += macro_data.potassium * (ingredient_quantity / 100)
            total_macros.vitamin_a += macro_data.vitamin_a * (ingredient_quantity / 100)
            total_macros.vitamin_c += macro_data.vitamin_c * (ingredient_quantity / 100)
            total_macros.calcium += macro_data.calcium * (ingredient_quantity / 100)
            total_macros.iron += macro_data.iron * (ingredient_quantity / 100)
            total_macros.calories += macro_data.calories * (ingredient_quantity / 100)  # Add calories
        else:
            return {"error": f"Ingredient {recipe.ingredients[i].item_name} not found or data unavailable"}

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
            calories=total_macros.calories / recipe.servings  # Add calories
        )

    return total_macros

@macro_router.get("/item/{item_id}", response_model=InventoryItemMacros)
def get_item_macros(item_id: str, user_id: str):
    logging.info(f"Fetching macros for item ID: {item_id} for user ID: {user_id}")
    items = read_pantry_items(user_id)
    for item in items:
        if item["id"] == item_id:
            return item.get("macros", InventoryItemMacros())
    raise HTTPException(status_code=404, detail="Item not found")

@macro_router.get("/total", response_model=InventoryItemMacros)
def get_total_macros(user_id: str):
    logging.info(f"Calculating total macros for user ID: {user_id}")
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

@macro_router.get("/autocomplete")
async def autocomplete(query: str):
    logging.info(f"Providing autocomplete suggestions for query: {query}")
    """
    Provide top 5 autocomplete suggestions based on the query using USDA API.
    """
    search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}"
    params = {
        'query': query
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(search_url, params=params)
        if response.status_code == 200:
            search_data = response.json()
            suggestions = [food['brandOwner'] for food in search_data.get('foods', [])]
            return {"suggestions": suggestions[:5]}
        else:
            logging.error(f"Error fetching autocomplete suggestions: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail="Error fetching autocomplete suggestions")

@macro_router.get("/UPC", response_model=UPCResponseModel)
def get_total_macros(upc_code: str):
    fdc_id = search_food_item(upc_code)
    if fdc_id == None:
        upc_code = + upc_code
        fdc_id = search_food_item(upc_code)
    response = UPCResponseModel(fdc_id = fdc_id)
    return response