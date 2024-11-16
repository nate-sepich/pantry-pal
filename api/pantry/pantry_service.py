from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends
from storage.utils import read_pantry_items, write_pantry_items
from models.models import InventoryItem, User
import httpx

pantry_router = APIRouter(prefix="/pantry")

def get_user() -> User:
    # Simulate retrieving a user from a database or authentication system
    return User(id="user123", username="testuser", email="testuser@example.com")

@pantry_router.get("/items", response_model=List[InventoryItem])
def get_items(user: User = Depends(get_user)):
    """
    Get all items in the pantry for a specific user.
    """
    items = read_pantry_items(user.id)
    return items

@pantry_router.get("/items/{item_id}", response_model=InventoryItem)
def get_item(item_id: str, user: User = Depends(get_user)):
    """
    Get a specific item from the pantry based on its ID for a specific user.
    """
    items = read_pantry_items(user.id)
    for item in items:
        if item["id"] == item_id:
            return item
    return {"error": "Item not found"}

async def call_get_item_macros(item_name: str, item_id: str = None, user_id: str = None):
    """
    Asynchronously call an external API to get the macros (nutritional information) of an item.
    Update the item in the pantry with the macros for a specific user.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8000/macros/item?item_name={item_name}")
        # Handle the response if needed
        print(response.json())
        
        # Update the item in the pantry with the macros
        items = read_pantry_items(user_id)
        for i, item in enumerate(items):
            if item["id"] == item_id:
                items[i]["macros"] = response.json()
                write_pantry_items(user_id, items)
                return items[i]

@pantry_router.post("/items", response_model=InventoryItem)
def create_item(item: InventoryItem, background_tasks: BackgroundTasks, user: User = Depends(get_user)):
    """
    Create a new item in the pantry for a specific user.
    Add a background task to asynchronously fetch the macros for the item.
    """
    print(item)
    items = read_pantry_items(user.id)
    item_dict = item.dict()
    items.append(item_dict)
    write_pantry_items(user.id, items)
    
    # Add the background task
    background_tasks.add_task(call_get_item_macros, item.product_name, item.id, user.id)
    
    return item

@pantry_router.put("/items/{item_id}", response_model=InventoryItem)
def update_item(item_id: str, item: InventoryItem, user: User = Depends(get_user)):
    """
    Update an existing item in the pantry based on its ID for a specific user.
    """
    items = read_pantry_items(user.id)
    for i, existing_item in enumerate(items):
        if existing_item["id"] == item_id:
            items[i] = item.dict()
            items[i]["id"] = item_id  # Ensure the ID remains the same
            write_pantry_items(user.id, items)
            return item
    return {"error": "Item not found"}

@pantry_router.delete("/items/{item_id}")
def delete_item(item_id: str, user: User = Depends(get_user)):
    """
    Delete an item from the pantry based on its ID for a specific user.
    """
    items = read_pantry_items(user.id)
    for i, item in enumerate(items):
        if item["id"] == item_id:
            del items[i]
            write_pantry_items(user.id, items)
            return {"message": "Item deleted"}
    return {"error": "Item not found"}

@pantry_router.get("/roi/metrics")
def get_roi_metrics(user: User = Depends(get_user)):
    """Calculate ROI metrics for the user."""
    items = read_pantry_items(user.id)
    health_roi = calculate_health_roi(items)
    financial_roi = calculate_financial_roi(items)
    environmental_roi = calculate_environmental_roi(items)
    return {"health_roi": health_roi, "financial_roi": financial_roi, "environmental_roi": environmental_roi}

def calculate_health_roi(items):
    # Implement health ROI calculation logic
    return 0

def calculate_financial_roi(items):
    # Implement financial ROI calculation logic
    return 0

def calculate_environmental_roi(items):
    # Implement environmental ROI calculation logic
    return 0