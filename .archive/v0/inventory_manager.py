# inventory.py

from pydantic import ValidationError
import json
from typing import List, Optional, Dict
from models import InventoryItem  # Assuming InventoryItem is defined in models.py

class InventoryService:
    def __init__(self, inventory_file: str):
        self.inventory_file = inventory_file
    
    def load_inventory(self) -> List[InventoryItem]:
        try:
            with open(self.inventory_file, 'r') as file:
                inventory_data = json.load(file)
            return [InventoryItem(**item) for item in inventory_data['inventory']]
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Error loading inventory: {e}")
            return []

    def save_inventory(self, inventory: List[InventoryItem]):
        try:
            with open(self.inventory_file, 'w') as file:
                json.dump({"inventory": [item.dict() for item in inventory]}, file, indent=4)
        except Exception as e:
            print(f"Error saving inventory: {e}")

    def get_item_by_upc(self, upc: str) -> Optional[InventoryItem]:
        inventory = self.load_inventory()
        for item in inventory:
            if item.upc == upc:
                return item
        return None
    
    def add_item(self, item: InventoryItem):
        inventory = self.load_inventory()
        inventory.append(item)
        self.save_inventory(inventory)
    
    def update_item(self, upc: str, updated_item: InventoryItem) -> bool:
        inventory = self.load_inventory()
        for i, item in enumerate(inventory):
            if item.upc == upc:
                inventory[i] = updated_item
                self.save_inventory(inventory)
                return True
        return False
    
    def remove_item(self, upc: str) -> bool:
        inventory = self.load_inventory()
        initial_len = len(inventory)
        inventory = [item for item in inventory if item.upc != upc]
        if len(inventory) < initial_len:
            self.save_inventory(inventory)
            return True
        return False

    def check_availability(self, required_items: Dict[str, float]) -> Dict[str, bool]:
        """
        Check if the inventory has the required items in the necessary quantities.
        :param required_items: A dictionary with item names as keys and required quantities as values.
        :return: A dictionary with item names as keys and a boolean indicating availability.
        """
        inventory = self.load_inventory()
        available = {}
        for item_name, required_qty in required_items.items():
            available[item_name] = any(
                item.product_name == item_name and item.quantity >= required_qty for item in inventory
            )
        return available
