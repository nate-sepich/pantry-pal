import os
from typing import List
from models import InventoryItem, InventoryItemMacros, Recipe, RecipeMacros
import inventory_manager
import google.generativeai as genai
import re
import json
from datetime import datetime

class MealPlanner:
    def __init__(self, inventory: List[InventoryItem], markdown_file: str, api_key: str):
        self.inventory = inventory
        self.markdown_file = markdown_file
        genai.configure(api_key=api_key)

    def load_markdown(self) -> str:
        with open(self.markdown_file, 'r') as file:
            return file.read()

    def extract_recipes_from_markdown(self, markdown_content: str) -> List[Recipe]:
        # LLM call to parse Markdown and return structured recipes
        prompt = f"""
        Extract and list the recipes from the following markdown content, each with its ingredients and instructions:
        {markdown_content}

The output of this content needs to be parseable by the following python:
    def _parse_recipes(self, response_text: str) -> List[Recipe]:
        # Regex patterns to identify the different parts of the recipe
        recipe_name_pattern = re.compile(r"^\*\*Recipe \d+: (.+)\*\*$")
        ingredients_section_pattern = re.compile(r"^\* \*\*Ingredients:\*\*$")
        instructions_section_pattern = re.compile(r"^\* \*\*Instructions:\*\*$")
        ingredient_pattern = re.compile(r"\*\s*(.+?)\s*\((\d+g)\)")
        """
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        # Parse response.text into Recipe objects
        recipes = self._parse_recipes(response.text)
        
        return recipes

    def _parse_recipes(self, response_text: str) -> List[Recipe]:
        # Regex patterns to identify the different parts of the recipe
        recipe_name_pattern = re.compile(r"^\*\*Recipe \d+: (.+)\*\*$")
        ingredients_section_pattern = re.compile(r"^\* \*\*Ingredients:\*\*$")
        instructions_section_pattern = re.compile(r"^\* \*\*Instructions:\*\*$")
        ingredient_pattern = re.compile(r"\*\s*(.+?)\s*\((\d+g)\)")

        recipes = []
        lines = response_text.splitlines()
        current_recipe = None
        in_ingredients = False
        in_instructions = False
        
        for line in lines:
            # Check if the line contains a recipe name
            recipe_name_match = recipe_name_pattern.match(line)
            if recipe_name_match:
                if current_recipe:
                    recipes.append(current_recipe)
                current_recipe = Recipe(name=recipe_name_match.group(1), ingredients=[], instructions="", macros={})
                in_ingredients = False
                in_instructions = False
                continue
            
            # Check if the line indicates the start of the ingredients section
            if ingredients_section_pattern.match(line):
                in_ingredients = True
                in_instructions = False
                continue
            
            # Check if the line indicates the start of the instructions section
            if instructions_section_pattern.match(line):
                in_ingredients = False
                in_instructions = True
                continue
            
            # Add ingredients or instructions depending on the current section
            if in_ingredients and current_recipe:
                # Match ingredients with quantity in grams
                ingredient_match = ingredient_pattern.match(line)
                if ingredient_match:
                    ingredient_name = ingredient_match.group(1).strip()
                    ingredient_quantity = float(ingredient_match.group(2).strip('g'))  # Remove 'g' and convert to float
                    ingredient = InventoryItem(
                        product_name=ingredient_name, 
                        quantity=ingredient_quantity, 
                        macros=InventoryItemMacros(
                            protein=0, 
                            carbohydrates=0, 
                            fat=0, 
                            fiber=0, 
                            sugar=0, 
                            saturated_fat=0, 
                            cholesterol=0, 
                            sodium=0
                        )
                    )
                    current_recipe.ingredients.append(ingredient)
                else:
                    # Handle ingredients without specified quantity
                    ingredient_name = line.strip('* ').strip()
                    ingredient = InventoryItem(
                        product_name=ingredient_name, 
                        quantity=0,  # Default quantity
                        macros=InventoryItemMacros(
                            protein=0, 
                            carbohydrates=0, 
                            fat=0, 
                            fiber=0, 
                            sugar=0, 
                            saturated_fat=0, 
                            cholesterol=0, 
                            sodium=0
                        )
                    )
                    current_recipe.ingredients.append(ingredient)
            
            if in_instructions and current_recipe:
                current_recipe.instructions += line.strip() + "\n"
        
        if current_recipe:
            recipes.append(current_recipe)
        
        return recipes

    def infer_missing_nutritional_data(self, items: List[InventoryItem]) -> List[InventoryItem]:
        model = genai.GenerativeModel('gemini-1.5-flash')
        inferred_items = []
        batch_size = 3  # Send a few ingredients at a time
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            incomplete_items = [item for item in batch if item.macros and any(
                value == 0 for value in vars(item.macros).values()
            )]
            
            if incomplete_items:
                # Build the prompt for Gemini-1.5-Flash to infer missing data for a batch of items
                ingredients_data = [
                    {
                        "product_name": item.product_name,
                        "macros": {
                            "protein": item.macros.protein,
                            "carbohydrates": item.macros.carbohydrates,
                            "fat": item.macros.fat,
                            "fiber": item.macros.fiber,
                            "sugar": item.macros.sugar,
                            "saturated_fat": item.macros.saturated_fat,
                            "cholesterol": item.macros.cholesterol,
                            "sodium": item.macros.sodium
                        }
                    } for item in incomplete_items
                ]
                
                prompt = f"""
                For the following ingredients, fill in the missing nutritional information:
                {json.dumps(ingredients_data, indent=2)}
                
                Please respond with only the complete JSON object (that will work directly with python json.loads, not markdown) with all the fields filled in.
                """
                
                response = model.generate_content(prompt)
                
                # Parse the JSON response and update the items with inferred values
                try:
                    stripped = response.text.replace('`','').replace('json','')
                    inferred_data = json.loads(stripped)
                    for idx, inferred_item in enumerate(inferred_data):
                        item = incomplete_items[idx]
                        item.macros.protein = inferred_item['macros'].get('protein', item.macros.protein)
                        item.macros.carbohydrates = inferred_item['macros'].get('carbohydrates', item.macros.carbohydrates)
                        item.macros.fat = inferred_item['macros'].get('fat', item.macros.fat)
                        item.macros.fiber = inferred_item['macros'].get('fiber', item.macros.fiber)
                        item.macros.sugar = inferred_item['macros'].get('sugar', item.macros.sugar)
                        item.macros.saturated_fat = inferred_item['macros'].get('saturated_fat', item.macros.saturated_fat)
                        item.macros.cholesterol = inferred_item['macros'].get('cholesterol', item.macros.cholesterol)
                        item.macros.sodium = inferred_item['macros'].get('sodium', item.macros.sodium)
                except json.JSONDecodeError:
                    print("Failed to parse JSON response:", response.text)
            
            inferred_items.extend(batch)
        
        return inferred_items

    def optimize_meal_plan(self, recipes: List[Recipe]) -> List[Recipe]:
        # Placeholder for optimization logic
        return recipes

    @staticmethod
    def export_recipes(recipes: List[Recipe], filename_prefix: str = "parsed_recipes"):
        """
        Dumps the list of recipes to a JSON file for post-processing.
        :param recipes: A list of Recipe objects to be saved.
        :param filename_prefix: The prefix for the filename.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"  # Save as a JSON file
        
        file_path = os.path.join(os.path.curdir, "parsed_recipes", filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists
        
        with open(file_path, 'w') as file:
            json_data = [recipe.dict() for recipe in recipes]  # Convert to dict before serializing
            json.dump(json_data, file, indent=4)
        
        print(f"Recipes have been saved to {file_path}")
    
    def calculate_recipe_macros(self, recipe: Recipe) -> RecipeMacros:
        total_protein = 0
        total_carbohydrates = 0
        total_fat = 0
        
        for item in recipe.ingredients:
            if item.macros:
                total_protein += item.macros.protein * (item.quantity if item.quantity else 1)
                total_carbohydrates += item.macros.carbohydrates * (item.quantity if item.quantity else 1)
                total_fat += item.macros.fat * (item.quantity if item.quantity else 1)
        
        return RecipeMacros(
            total_protein=total_protein,
            total_carbohydrates=total_carbohydrates,
            total_fat=total_fat
        )

    def rollup_recipe_macros(self, recipes: List[Recipe]) -> List[Recipe]:
        for recipe in recipes:
            recipe.macros = self.calculate_recipe_macros(recipe)
        return recipes

    def run(self):
        # Step 1: Load Markdown and Extract Recipes
        markdown_content = self.load_markdown()
        recipes = self.extract_recipes_from_markdown(markdown_content)
        
        # Step 2: Infer missing nutritional data
        for recipe in recipes:
            recipe.ingredients = self.infer_missing_nutritional_data(recipe.ingredients)
        
        # Step 3: Calculate and roll up macros for each recipe
        recipes = self.rollup_recipe_macros(recipes)
        
        # Step 4: Export the recipes
        self.export_recipes(recipes)

if __name__ == '__main__':
    # Example usage
    iService = inventory_manager.InventoryService('inventory.json')
    inventory = iService.load_inventory()  # Load your inventory here
    markdown_file = r'recipes\raw_generated_recipes.txt_20240811_201216.md'
    api_key = os.getenv('API_KEY')
    
    meal_planner = MealPlanner(inventory, markdown_file, api_key)
    meal_planner.run()
