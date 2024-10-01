import google.generativeai as genai
import os
from typing import List
from datetime import datetime
from models import InventoryItem, Recipe
import json

class RecipeService:
    def __init__(self, inventory: List[InventoryItem], macro_goals: dict, api_key: str):
        self.inventory = inventory
        self.macro_goals = macro_goals
        genai.configure(api_key=api_key)

    def generate_recipes(self, max_prep_time: int = 30) -> List[Recipe]:
        prompt = self._create_prompt(max_prep_time)
        
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        # Assuming the response is in plain text and needs parsing
        return self._parse_response(response.text)

    def _create_prompt(self, max_prep_time: int) -> str:
        inventory_list = "\n".join([f"{item.product_name}: {item.quantity} available" for item in self.inventory])

        prompt = f"""
        Generate 3 recipes that meet the following macro goals: {self.macro_goals}, with a prep time under {max_prep_time} minutes.
        Consider the following inventory:
        {inventory_list}
        You may include additional ingredients if necessary.
        Please provide recipes with detailed ingredients and preparation instructions.
        """

        return prompt

    def _parse_response(self, response_text: str) -> str:
        """
        Passthrough function to return the entire response text without parsing.
        :param response_text: The raw text response from the model.
        :return: The raw response text.
        """
        return response_text

    def export_recipes(self, response_text: str, filename_prefix: str = "generated_recipes"):
        """
        Dumps the entire Markdown response to a file for post-processing.
        :param response_text: The raw text response from the model (in Markdown format).
        :param filename_prefix: The prefix for the filename.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.md"  # Save as a Markdown file
        
        with open(os.path.join(os.path.curdir, "recipes", filename), "w") as file:
            file.write(response_text)
        
        print(f"Markdown recipe text has been saved to {filename}")

    @staticmethod
    def from_json_files(inventory_file: str, goals: dict, api_key: str) -> 'RecipeService':
        with open(inventory_file, 'r') as file:
            inventory_data = json.load(file)
        inventory = [InventoryItem(**item) for item in inventory_data["inventory"]]

        return RecipeService(inventory, goals, api_key)
