import logging
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from storage.utils import read_pantry_items, write_pantry_items, read_users, soft_delete_pantry_item
from models.models import InventoryItem, InventoryItemMacros, User  
import httpx
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

pantry_router = APIRouter(prefix="/pantry")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_user_id_from_token(token: str = Depends(oauth2_scheme)) -> str:
    """Extract user_id from the JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: user_id not found")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e

def get_user(token: str = Depends(oauth2_scheme)) -> User:
    logging.info(f"Decoding JWT token to get user: {token}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logging.info(f"JWT payload: {payload}")
        user_id: str = payload.get("sub")
        if user_id is None:
            logging.warning("Token does not contain user ID")
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = read_users()  # Assuming this returns a list of User objects
        for u in user:
            if u.id == user_id:  # Use attribute-style access
                return u
        logging.warning(f"User with ID {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    except JWTError as e:
        logging.error(f"JWT decoding error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@pantry_router.get("/items", response_model=List[InventoryItem])
def get_items(user: User = Depends(get_user)) -> List[InventoryItem]:
    logging.info(f"Fetching pantry items for user ID: {user.id}")
    """
    Get all items in the pantry for a specific user.
    """
    items = read_pantry_items(user.id)
    return items

@pantry_router.get("/items/{item_id}", response_model=InventoryItem)
def get_item(item_id: str, user: User = Depends(get_user)) -> InventoryItem:
    logging.info(f"Fetching item ID: {item_id} for user ID: {user.id}")
    """
    Get a specific item from the pantry based on its ID for a specific user.
    """
    items = read_pantry_items(user.id)
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

async def call_get_item_macros(item_name: str, item_id: str = None, user_id: str = None):
    logging.info(f"Fetching macros for item: {item_name}")
    """
    Asynchronously call an external API to get the macros (nutritional information) of an item.
    Update the item in the pantry with the macros for a specific user.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://op14f0voe4.execute-api.us-east-1.amazonaws.com/Prod/item?item_name={item_name}")
        macros_data = response.json()
        logging.info(f"Macros fetched for item {item_name}: {macros_data}")

        # Update the item in the pantry with the macros
        items = read_pantry_items(user_id)
        for i, item in enumerate(items):
            if item.id == item_id:  # Use attribute-style access
                item.macros = InventoryItemMacros(**macros_data)  # Update macros
                write_pantry_items(user_id, items)  # Save updated items
                return item

        logging.warning(f"Item with ID {item_id} not found for user ID {user_id}")

@pantry_router.post("/items")
def create_pantry_item(
    item: InventoryItem, 
    background_tasks: BackgroundTasks, 
    user_id: str = Depends(get_user_id_from_token)
):
    """Create a pantry item for the authenticated user."""
    try:
        # Write the pantry item to storage
        write_pantry_items(user_id, [item])
        
        # Add a background task to fetch macros for the item
        background_tasks.add_task(call_get_item_macros, item.product_name, item.id, user_id)
        
        return {"message": "Pantry item created successfully", "item": item.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create pantry item: {str(e)}")

@pantry_router.put("/items/{item_id}", response_model=InventoryItem)
def update_item(item_id: str, item: InventoryItem, user: User = Depends(get_user)) -> InventoryItem:
    logging.info(f"Updating item ID: {item_id} for user ID: {user.id}")
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
    raise HTTPException(status_code=404, detail="Item not found")

@pantry_router.delete("/items/{item_id}")
def delete_item(item_id: str, user: User = Depends(get_user)) -> dict:
    logging.info(f"Soft deleting item ID: {item_id} for user ID: {user.id}")
    """
    Mark an item as inactive in the pantry based on its ID for a specific user.
    """
    try:
        soft_delete_pantry_item(user.id, item_id)
        return {"message": "Item marked as inactive"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete pantry item: {str(e)}")

@pantry_router.get("/roi/metrics")
def get_roi_metrics(user: User = Depends(get_user)) -> dict:
    logging.info(f"Calculating ROI metrics for user ID: {user.id}")
    """Calculate ROI metrics for the user."""
    items = read_pantry_items(user.id)
    health_roi = calculate_health_roi(items)
    financial_roi = calculate_financial_roi(items)
    environmental_roi = calculate_environmental_roi(items)
    return {"health_roi": health_roi, "financial_roi": financial_roi, "environmental_roi": environmental_roi}

def calculate_health_roi(items):
    logging.info("Calculating health ROI")
    # Implement health ROI calculation logic
    return 0

def calculate_financial_roi(items):
    logging.info("Calculating financial ROI")
    # Implement financial ROI calculation logic
    return 0

def calculate_environmental_roi(items):
    logging.info("Calculating environmental ROI")
    # Implement environmental ROI calculation logic
    return 0