import json
import os
from ollama import Client
import logging
from fastapi import APIRouter, Depends
from storage.utils import read_pantry_items
from models.models import InventoryItemMacros, User

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
    item_names = [item['product_name'] for item in items]
    prompt = generate_recipe_prompt(item_names)
    
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
    item_names = [item['product_name'] for item in items]
    prompt = generate_meal_suggestion_prompt(item_names, daily_macro_goals)
    
    try:
        logging.info(f"Meal suggestion generation starting for: {user_id}")
        response = client.generate(model=ollama_model, prompt=prompt)
        meal_suggestions = parse_meal_suggestion_response(response)
        return meal_suggestions
    except Exception as e:
        logging.error(f"Error generating meal suggestions: {e}")
        return {"error": "Failed to generate meal suggestions"}

def generate_recipe_prompt(item_names):
    """Generate a prompt for the AI model to create recipes based on pantry items."""
    logging.info("Generating recipe prompt for AI model")
    item_list = ", ".join(item_names)
    prompt = f"Create a recipe using the following pantry items: {item_list}. Provide the recipe name, ingredients, and instructions."
    return prompt

def generate_meal_suggestion_prompt(item_names, daily_macro_goals):
    """Generate a prompt for the AI model to create meal suggestions based on pantry items and daily macro goals."""
    logging.info("Generating meal suggestion prompt for AI model")
    item_list = ", ".join(item_names)
    prompt = (f"Create meal suggestions using the following pantry items: {item_list}. "
              f"The meals should meet the following daily macro goals: "
              f"Calories: {daily_macro_goals.calories}, Protein: {daily_macro_goals.protein}g, "
              f"Carbohydrates: {daily_macro_goals.carbohydrates}g, Fat: {daily_macro_goals.fat}g. "
              "Provide the meal name, ingredients, and instructions.")
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
