import os
from recipe import RecipeService
from models import InventoryItem

def main():
    # Load inventory from the JSON file
    inventory_file = 'inventory.json'
    goals = {
        "protein": 190,  # Example macro goal
        "carbs": 477,
        "fat": 126
    }
    
    # Initialize the RecipeService with the inventory, goals, and API key
    api_key = os.getenv('API_KEY')  # Ensure your API key is set in your environment variables
    recipe_service = RecipeService.from_json_files(inventory_file, goals, api_key)
    
    # Generate recipes based on the current inventory and goals
    recipes = recipe_service.generate_recipes(max_prep_time=30)
    
    # Export the raw recipes to a text file
    recipe_service.export_recipes(recipes, "raw_generated_recipes.txt")

if __name__ == '__main__':
    main()
