import json
import os
import logging
from openai import OpenAI
from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.responses import StreamingResponse
from storage.utils import read_pantry_items
from models.models import InventoryItemMacros, LLMChatRequest
from datetime import datetime
import pytz  # Import pytz for timezone conversion

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

# AI Router for OpenAI-powered recipe recommendations
openai_router = APIRouter(prefix="/openai")

# Initialize OpenAI Client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logging.warning("OpenAI API key not found. OpenAI service will not function properly.")

openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
openai_client = OpenAI(api_key=api_key)

def check_api_key():
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

@openai_router.get("/meal_recommendation")
def get_recipe_recommendations(user_id: str):
    """Get OpenAI-powered recipe recommendations based on the user's pantry items."""
    check_api_key()
    logging.info(f"Generating OpenAI recipe recommendations for user ID: {user_id}")
    items = read_pantry_items(user_id)
    prompt = generate_recipe_prompt(items)
    
    try:
        logging.info(f"OpenAI meal generation starting for: {user_id}")
        response = openai_client.chat.completions.create(
            model=openai_model,
            messages=[{"role": "system", "content": "You are a helpful culinary assistant."},
                     {"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )
        recipes = response.choices[0].message.content
        return recipes
    except Exception as e:
        logging.error(f"Error generating recipes with OpenAI: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recipes: {str(e)}")

@openai_router.post("/meal_suggestions")
def get_meal_suggestions(user_id: str, daily_macro_goals: InventoryItemMacros):
    """Get OpenAI-powered meal suggestions based on the user's pantry items and daily macro goals."""
    check_api_key()
    logging.info(f"Generating OpenAI meal suggestions for user ID: {user_id} with daily macro goals: {daily_macro_goals}")
    items = read_pantry_items(user_id)
    prompt = generate_meal_suggestion_prompt(items, daily_macro_goals)
    
    try:
        logging.info(f"OpenAI meal suggestion generation starting for: {user_id}")
        response = openai_client.chat.completions.create(
            model=openai_model,
            messages=[{"role": "system", "content": "You are a nutrition expert and chef."},
                     {"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        meal_suggestions = response.choices[0].message.content
        return meal_suggestions
    except Exception as e:
        logging.error(f"Error generating meal suggestions with OpenAI: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate meal suggestions: {str(e)}")

@openai_router.post("/llm_chat")
def llm_chat(request: LLMChatRequest):
    """Send a prompt to OpenAI and get a response."""
    check_api_key()
    prompt = request.prompt
    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt provided")
    
    try:
        response = openai_client.chat.completions.create(
            model=openai_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        logging.error(f"Error communicating with OpenAI: {e}")
        raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI: {str(e)}")

def generate_recipe_prompt(items):
    """Generate a prompt for the OpenAI model to create recipes based on pantry items with macros."""
    logging.info("Generating recipe prompt for OpenAI model with macros")
    item_details = ""
    for item in items:
        macros = item.get('macros', {})
        # Format macros as a string
        macros_str = ", ".join(f"{key}: {value}" for key, value in macros.items() if value)
        item_detail = f"- {item['product_name']}: {macros_str}"
        item_details += item_detail + "\n"
    
    # Add current date and time in US Central Time to the prompt
    central = pytz.timezone('US/Central')
    current_time = datetime.now(central).strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = (
        f"Current Date and Time: {current_time}\n\n"
        "Using the following pantry items with their nutritional information, create a recipe.\n"
        "Provide the recipe name, ingredients, instructions, and estimated nutritional information.\n\n"
        "Pantry Items:\n"
        f"{item_details}"
    )
    return prompt

def generate_meal_suggestion_prompt(items, daily_macro_goals):
    """Generate a prompt for the OpenAI model to create meal suggestions based on pantry items and daily macro goals."""
    logging.info("Generating meal suggestion prompt for OpenAI model with macros")
    item_details = ""
    for item in items:
        macros = item.get('macros', {})
        macros_str = ", ".join(f"{key}: {value}" for key, value in macros.items() if value)
        item_detail = f"- {item['product_name']}: {macros_str}"
        item_details += item_detail + "\n"
    
    # Add current date and time in US Central Time to the prompt
    central = pytz.timezone('US/Central')
    current_time = datetime.now(central).strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = (
        f"Current Date and Time: {current_time}\n\n"
        "Using the following pantry items with their nutritional information, create meal suggestions that meet the specified daily macro goals.\n"
        "Provide the meal name, ingredients, instructions, and how it fits within the macro goals.\n\n"
        f"Daily Macro Goals:\n"
        f"Calories: {daily_macro_goals.calories}, Protein: {daily_macro_goals.protein}g, "
        f"Carbohydrates: {daily_macro_goals.carbohydrates}g, Fat: {daily_macro_goals.fat}g\n\n"
        "Pantry Items:\n"
        f"{item_details}"
    )
    return prompt
