from typing import List
from fastapi import APIRouter, BackgroundTasks
from storage.utils import read_pantry_items, write_pantry_items
from models.models import InventoryItem
import httpx

pantry_router = APIRouter(prefix="/pantry")

@pantry_router.get("/items", response_model=List[InventoryItem])
def get_items():
    """
    Get all items in the pantry.
    """
    items = read_pantry_items()
    return items

@pantry_router.get("/items/{item_id}", response_model=InventoryItem)
def get_item(item_id: str):
    """
    Get a specific item from the pantry based on its ID.
    """
    items = read_pantry_items()
    for item in items:
        if item["id"] == item_id:
            return item
    return {"error": "Item not found"}

async def call_get_item_macros(item_name: str, item_id: str = None):
    """
    Asynchronously call an external API to get the macros (nutritional information) of an item.
    Update the item in the pantry with the macros.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8000/macros/item?item_name={item_name}")
        # Handle the response if needed
        print(response.json())
        
        # Update the item in the pantry with the macros
        items = read_pantry_items()
        for i, item in enumerate(items):
            if item["id"] == item_id:
                items[i]["macros"] = response.json()
                write_pantry_items(items)
                return items[i]

@pantry_router.post("/items", response_model=InventoryItem)
def create_item(item: InventoryItem, background_tasks: BackgroundTasks):
    """
    Create a new item in the pantry.
    Add a background task to asynchronously fetch the macros for the item.
    """
    print(item)
    items = read_pantry_items()
    item_dict = item.dict()
    items.append(item_dict)
    write_pantry_items(items)
    
    # Add the background task
    background_tasks.add_task(call_get_item_macros, item.product_name, item.id)
    
    return item

@pantry_router.put("/items/{item_id}", response_model=InventoryItem)
def update_item(item_id: str, item: InventoryItem):
    """
    Update an existing item in the pantry based on its ID.
    """
    items = read_pantry_items()
    for i, existing_item in enumerate(items):
        if existing_item["id"] == item_id:
            items[i] = item.dict()
            items[i]["id"] = item_id  # Ensure the ID remains the same
            write_pantry_items(items)
            return item
    return {"error": "Item not found"}

@pantry_router.delete("/items/{item_id}")
def delete_item(item_id: str):
    """
    Delete an item from the pantry based on its ID.
    """
    items = read_pantry_items()
    for i, item in enumerate(items):
        if item["id"] == item_id:
            del items[i]
            write_pantry_items(items)
            return {"message": "Item deleted"}
    return {"error": "Item not found"}