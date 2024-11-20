import logging
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from storage.utils import read_pantry_items, write_pantry_items, read_users
from models.models import InventoryItem, User
import httpx

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

pantry_router = APIRouter(prefix="/pantry")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_user(token: str = Depends(oauth2_scheme)) -> User:
    logging.info(f"Decoding JWT token to get user: {token}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logging.info(f"JWT payload: {payload}")
        user_id: str = payload.get("sub")
        if user_id is None:
            logging.warning("Token does not contain user ID")
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        users = read_users()
        for user in users:
            if user["id"] == user_id:
                logging.info(f"User found: {user}")
                return User(**user)
        logging.warning("User not found")
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
def create_item(item: InventoryItem, background_tasks: BackgroundTasks, user: User = Depends(get_user)) -> InventoryItem:
    logging.info(f"Creating new item '{item.product_name}' for user ID: {user.id}")
    """
    Create a new item in the pantry for a specific user.
    Add a background task to asynchronously fetch the macros for the item.
    """
    item.user_id = user.id  # Link the item to the user
    items = read_pantry_items(user.id)
    item_dict = item.dict()
    items.append(item_dict)
    write_pantry_items(user.id, items)
    
    # Add the background task
    background_tasks.add_task(call_get_item_macros, item.product_name, item.id, user.id)
    
    return item

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
    logging.info(f"Deleting item ID: {item_id} for user ID: {user.id}")
    """
    Delete an item from the pantry based on its ID for a specific user.
    """
    items = read_pantry_items(user.id)
    for i, item in enumerate(items):
        if item["id"] == item_id:
            del items[i]
            write_pantry_items(user.id, items)
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")

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