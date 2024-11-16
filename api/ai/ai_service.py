import json
import os
from ollama import Client
import logging
from fastapi import APIRouter, Depends
from storage.utils import read_pantry_items
from models.models import User

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Ollama Client with FP16 precision to reduce memory usage
ollama_model = os.getenv('AI_OLLAMA_MODEL', 'mistral')

logging.info(f'Pulling Ollama Model: {ollama_model}')
client = Client(host='http://ollama:11434')
logging.info(f'Model Pull Status: {client.pull(ollama_model)}')
sample = client.generate(model=ollama_model, prompt='Hello! Respond with only Hello.')

# AI Router for recipe recommendations
ai_router = APIRouter(prefix="/ai")

@ai_router.get("/meal_recommendation")
def get_recipe_recommendations(user_id: str):
    logging.info(f"Generating recipe recommendations for user ID: {user_id}")
    """Get AI-powered recipe recommendations based on the user's pantry items."""
    items = read_pantry_items(user_id)
    item_names = [item['product_name'] for item in items]
    prompt = generate_recipe_prompt(item_names)
    
    try:
        response = client.generate(model=ollama_model, prompt=prompt)
        recipes = parse_recipe_response(response)
        return recipes
    except Exception as e:
        logging.error(f"Error generating recipes: {e}")
        return {"error": "Failed to generate recipes"}

def generate_recipe_prompt(item_names):
    logging.info("Generating recipe prompt for AI model")
    """Generate a prompt for the AI model to create recipes based on pantry items."""
    item_list = ", ".join(item_names)
    prompt = f"Create a recipe using the following pantry items: {item_list}. Provide the recipe name, ingredients, and instructions."
    return prompt

def parse_recipe_response(response):
    logging.info("Parsing AI model response for recipes")
    """Parse the AI model's response to extract recipe information."""
    content = response.get('response', '')
      
    try:
        recipes = content
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response: {e}")
        recipes = [{"error": "Failed to parse recipes"}]
    
    return recipes
