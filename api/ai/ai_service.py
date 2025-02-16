import json
import os
from ollama import Client
import logging
from fastapi import APIRouter, Depends, Request
from starlette.responses import StreamingResponse
from storage.utils import read_pantry_items
from models.models import InventoryItemMacros, LLMChatRequest
from datetime import datetime
import pytz  # Import pytz for timezone conversion

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

# AI Router for recipe recommendations
ai_router = APIRouter(prefix="/ai")

# Initialize Ollama Client with FP16 precision to reduce memory usage
ollama_model = os.getenv('AI_OLLAMA_MODEL', 'mistral')
llm_client_base = os.getenv('LLM_CLIENT_BASE', 'http://ollama:11434')
client = Client(host=llm_client_base)

def initialize_model():
    logging.info(f'Pulling Ollama Model: {ollama_model}')
    client.pull(ollama_model)
    sample = client.generate(model=ollama_model, prompt='Hello! Respond with only Hello.')
    logging.info(f'Model Pull Status: {sample}')

# Ensure the model is initialized only once on startup
# initialize_model()

@ai_router.get("/meal_recommendation")
def get_recipe_recommendations(user_id: str):
    """Get AI-powered recipe recommendations based on the user's pantry items."""
    logging.info(f"Generating recipe recommendations for user ID: {user_id}")
    items = read_pantry_items(user_id)
    prompt = generate_recipe_prompt(items)
    
    try:
        logging.info(f"Meal generation starting for: {user_id}")
        response = client.generate(model=ollama_model, prompt=prompt)
        recipes = parse_recipe_response(response)
        return recipes
    except Exception as e:
        logging.error(f"Error generating recipes: {e}")
        return {"error": "Failed to generate recipes"}

@ai_router.post("/meal_suggestions")
def get_meal_suggestions(user_id: str, daily_macro_goals: InventoryItemMacros):
    """Get AI-powered meal suggestions based on the user's pantry items and daily macro goals."""
    logging.info(f"Generating meal suggestions for user ID: {user_id} with daily macro goals: {daily_macro_goals}")
    items = read_pantry_items(user_id)
    prompt = generate_meal_suggestion_prompt(items, daily_macro_goals)
    
    try:
        logging.info(f"Meal suggestion generation starting for: {user_id}")
        response = client.generate(model=ollama_model, prompt=prompt)
        meal_suggestions = parse_meal_suggestion_response(response)
        return meal_suggestions
    except Exception as e:
        logging.error(f"Error generating meal suggestions: {e}")
        return {"error": "Failed to generate meal suggestions"}

@ai_router.post("/llm_chat")
def llm_chat(request: LLMChatRequest):
    prompt = request.prompt
    if not prompt:
        return {"error": "No prompt provided"}
    
    def generate():
        try:
            response = client.generate(model=ollama_model, prompt=prompt, stream=True)
            for line in response:
                yield line.get('response', '')
        except Exception as e:
            logging.error(f"Error communicating with the LLM: {e}")
            yield f"Error communicating with the LLM: {str(e)}"
    
    return StreamingResponse(generate(), media_type="text/plain")

def generate_recipe_prompt(items):
    """Generate a prompt for the AI model to create recipes based on pantry items with macros."""
    logging.info("Generating recipe prompt for AI model with macros")
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
        "Provide the recipe name, ingredients, and instructions.\n\n"
        "Pantry Items:\n"
        f"{item_details}"
    )
    return prompt

def generate_meal_suggestion_prompt(items, daily_macro_goals):
    """Generate a prompt for the AI model to create meal suggestions based on pantry items and daily macro goals."""
    logging.info("Generating meal suggestion prompt for AI model with macros")
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
        "Provide the meal name, ingredients, and instructions.\n\n"
        f"Daily Macro Goals:\n"
        f"Calories: {daily_macro_goals.calories}, Protein: {daily_macro_goals.protein}g, "
        f"Carbohydrates: {daily_macro_goals.carbohydrates}g, Fat: {daily_macro_goals.fat}g\n\n"
        "Pantry Items:\n"
        f"{item_details}"
    )
    return prompt

def parse_recipe_response(response):
    """Parse the AI model's response to extract recipe information."""
    logging.info("Parsing AI model response for recipes")
    content = response.get('response', '')
    
    try:
        recipes = content
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response: {e}")
        recipes = [{"error": "Failed to parse recipes"}]
    
    return recipes

def parse_meal_suggestion_response(response):
    """Parse the AI model's response to extract meal suggestion information."""
    logging.info("Parsing AI model response for meal suggestions")
    content = response.get('response', '')
    
    try:
        meal_suggestions = content
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response: {e}")
        meal_suggestions = [{"error": "Failed to parse meal suggestions"}]
    
    return meal_suggestions
