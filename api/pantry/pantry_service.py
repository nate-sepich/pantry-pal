import os
import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from storage.utils import read_pantry_items, write_pantry_items, read_users, soft_delete_pantry_item
from models.models import InventoryItem, InventoryItemMacros, User  
from ai.openai_service import openai_client, check_api_key  
import boto3
import requests
from storage.utils import pantry_table
from auth.auth_service import get_current_user, get_user_id_from_token

# Alias to get_current_user for test overrides
get_user = get_current_user
get_user_id = get_user_id_from_token

# Router for pantry-related operations
pantry_router = APIRouter(prefix="/pantry")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# SQS client for hydration jobs
MACRO_QUEUE_URL = os.getenv("MACRO_QUEUE_URL")
IMAGE_QUEUE_URL = os.getenv("IMAGE_QUEUE_URL")
sqs = boto3.client("sqs")

@pantry_router.get("/items", response_model=List[InventoryItem])
def get_items(user_id: str = Depends(get_user_id_from_token)) -> List[InventoryItem]:
    """
    Retrieve all pantry items for the authenticated user.
    """
    logging.info(f"Fetching pantry items for user ID: {user_id}")
    items = read_pantry_items(user_id)
    return items

@pantry_router.get("/items/{item_id}", response_model=InventoryItem)
def get_item(item_id: str, user_id: str = Depends(get_user_id_from_token)) -> InventoryItem:
    """
    Retrieve a specific pantry item by its ID for the authenticated user.
    """
    logging.info(f"Fetching item ID: {item_id} for user ID: {user_id}")
    pk = f"USER#{user_id}"
    sk = f"PANTRY#{item_id}"
    try:
        resp = pantry_table.get_item(Key={"PK": pk, "SK": sk})
    except Exception as e:
        logging.error(f"Error fetching pantry item: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving item")
    raw = resp.get("Item")
    if not raw or not raw.get("active", True):
        raise HTTPException(status_code=404, detail="Item not found")
    # Build InventoryItem with macros
    macros_data = raw.get("macros") or {}
    macros = InventoryItemMacros(**macros_data) if macros_data else None
    item = InventoryItem(
        id=raw["id"],
        user_id=user_id,
        product_name=raw.get("product_name", ""),
        quantity=int(raw.get("quantity", 1)),
        upc=raw.get("upc"),
        macros=macros,
        cost=raw.get("cost", 0),
        expiration_date=raw.get("expiration_date"),
        environmental_impact=raw.get("environmental_impact", 0),
        image_url=raw.get("image_url"),
        active=raw.get("active", True),
    )
    return item

@pantry_router.post("/items")
def create_pantry_item(item: InventoryItem, user_id: str = Depends(get_user_id_from_token)):
    """
    Create a new pantry item for the authenticated user.
    """
    try:
        # Save new item record
        write_pantry_items(user_id, [item])
        # Hydration job for macros
        if MACRO_QUEUE_URL:
            sqs.send_message(
                QueueUrl=MACRO_QUEUE_URL,
                MessageBody=json.dumps({"jobType":"ITEM","payload":{"user_id":user_id,"item_id":item.id,"item_name":item.product_name}})
            )
        else:
            logging.warning("MACRO_QUEUE_URL not set; skipping SQS send_message")

        # Enqueue image generation job asynchronously
        item_dict = item.dict()
        try:
            if IMAGE_QUEUE_URL:
                sqs.send_message(
                    QueueUrl=IMAGE_QUEUE_URL,
                    MessageBody=json.dumps({
                        "jobType": "IMAGE",
                        "payload": {
                            "user_id": user_id,
                            "item_id": item.id,
                            "item_name": item.product_name
                        }
                    })
                )
            else:
                logging.warning("IMAGE_QUEUE_URL not set; skipping image generation job")
        except Exception as img_e:
            logging.warning(f"Failed to send image generation SQS message for item {item.id}: {img_e}")

        return {"message":"Pantry item created successfully","item":item_dict}
    except Exception as e:
        logging.error(f"Error creating pantry item: user_id={user_id}, item={item}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create pantry item: {str(e)}")

@pantry_router.put("/items/{item_id}", response_model=InventoryItem)
def update_item(item_id: str, item: InventoryItem, user_id: str = Depends(get_user_id_from_token)) -> InventoryItem:
    """
    Update an existing pantry item by its ID for the authenticated user.
    """
    logging.info(f"Updating item ID: {item_id} for user ID: {user_id}")
    items = read_pantry_items(user_id)
    for i, existing_item in enumerate(items):
        if existing_item["id"] == item_id:
            items[i] = item.dict()
            items[i]["id"] = item_id
            write_pantry_items(user_id, items)
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@pantry_router.delete("/items/{item_id}")
def delete_item(item_id: str, user_id: str = Depends(get_user_id_from_token)) -> dict:
    """
    Mark a pantry item as inactive (soft delete) by its ID for the authenticated user.
    """
    logging.info(f"Soft deleting item ID: {item_id} for user ID: {user_id}")
    try:
        soft_delete_pantry_item(user_id, item_id)
        return {"message": "Item marked as inactive"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete pantry item: {str(e)}")

@pantry_router.get("/roi/metrics")
def get_roi_metrics(user_id: str = Depends(get_user_id_from_token)) -> dict:
    """
    Calculate and return ROI (Return on Investment) metrics for the authenticated user's pantry.
    """
    logging.info(f"Calculating ROI metrics for user ID: {user_id}")
    items = read_pantry_items(user_id)
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
