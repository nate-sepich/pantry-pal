import json
import logging
import os

import boto3
import requests
from auth.auth_service import get_current_user, get_user_id_from_token
from fastapi import APIRouter, Depends, HTTPException
from models.models import InventoryItem, InventoryItemMacros
from pantry.barcode_scanner import BarcodeService
from storage.utils import (
    pantry_table,
    read_pantry_items,
    soft_delete_pantry_item,
    write_pantry_items,
)

# Alias to get_current_user for test overrides
get_user = get_current_user
get_user_id = get_user_id_from_token

# Router for pantry-related operations
pantry_router = APIRouter(prefix="/pantry")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# SQS client for hydration jobs
MACRO_QUEUE_URL = os.getenv("MACRO_QUEUE_URL")
IMAGE_QUEUE_URL = os.getenv("IMAGE_QUEUE_URL")
sqs = boto3.client("sqs")


@pantry_router.get("/items", response_model=list[InventoryItem])
def get_items(user_id: str = Depends(get_user_id_from_token)) -> list[InventoryItem]:
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
                MessageBody=json.dumps(
                    {
                        "jobType": "ITEM",
                        "payload": {
                            "user_id": user_id,
                            "item_id": item.id,
                            "item_name": item.product_name,
                        },
                    }
                ),
            )
        else:
            logging.warning("MACRO_QUEUE_URL not set; skipping SQS send_message")

        # Enqueue image generation job asynchronously
        item_dict = item.dict()
        try:
            if IMAGE_QUEUE_URL:
                sqs.send_message(
                    QueueUrl=IMAGE_QUEUE_URL,
                    MessageBody=json.dumps(
                        {
                            "jobType": "IMAGE",
                            "payload": {
                                "user_id": user_id,
                                "item_id": item.id,
                                "item_name": item.product_name,
                            },
                        }
                    ),
                )
            else:
                logging.warning("IMAGE_QUEUE_URL not set; skipping image generation job")
        except Exception as img_e:
            logging.warning(
                f"Failed to send image generation SQS message for item {item.id}: {img_e}"
            )

        return {"message": "Pantry item created successfully", "item": item_dict}
    except Exception as e:
        logging.error(f"Error creating pantry item: user_id={user_id}, item={item}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create pantry item: {str(e)}")


@pantry_router.put("/items/{item_id}", response_model=InventoryItem)
def update_item(
    item_id: str, item: InventoryItem, user_id: str = Depends(get_user_id_from_token)
) -> InventoryItem:
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
    return {
        "health_roi": health_roi,
        "financial_roi": financial_roi,
        "environmental_roi": environmental_roi,
    }


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


@pantry_router.get("/lookup/{upc}")
def lookup_item_by_upc(upc: str, user_id: str = Depends(get_user_id_from_token)) -> dict:
    """
    Look up product information by UPC/barcode.
    """
    logging.info(f"Looking up UPC: {upc} for user ID: {user_id}")

    try:
        # Use the centralized barcode service (no CV dependencies)
        product_info = BarcodeService.lookup_product_by_upc(upc)

        if product_info:
            logging.info(f"Product found for UPC {upc}: {product_info['product_name']}")
            return product_info
        else:
            logging.info(f"No product found for UPC: {upc}")
            raise HTTPException(status_code=404, detail="Product not found")

    except HTTPException:
        raise
    except requests.RequestException as e:
        logging.error(f"Error looking up UPC {upc}: {e}")
        raise HTTPException(status_code=500, detail="Failed to lookup product")
    except Exception as e:
        logging.error(f"Unexpected error looking up UPC {upc}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@pantry_router.get("/popular-items")
def get_popular_items(user_id: str = Depends(get_user_id_from_token)) -> dict:
    """
    Get popular pantry items based on user's history and global trends.
    """
    logging.info(f"Fetching popular items for user ID: {user_id}")

    try:
        # Get user's frequently added items
        user_items = read_pantry_items(user_id)

        # Count frequency of items
        item_counts = {}
        for item in user_items:
            if isinstance(item, dict):
                name = item.get("product_name", "").lower().strip()
            else:
                name = getattr(item, "product_name", "").lower().strip()

            if name:
                item_counts[name] = item_counts.get(name, 0) + 1

        # Get top user items (limit to 3)
        user_popular = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        user_popular_names = [item[0].title() for item in user_popular]

        # Default popular items
        default_popular = [
            "Milk",
            "Bread",
            "Eggs",
            "Chicken Breast",
            "Rice",
            "Bananas",
            "Apples",
            "Butter",
        ]

        # Combine user items with defaults, avoiding duplicates
        combined_items = user_popular_names.copy()
        for item in default_popular:
            if item.lower() not in [x.lower() for x in combined_items] and len(combined_items) < 8:
                combined_items.append(item)

        return {"items": combined_items[:8]}

    except Exception as e:
        logging.error(f"Error getting popular items: {e}")
        # Return defaults on error
        return {"items": ["Milk", "Bread", "Eggs", "Chicken Breast", "Rice", "Bananas"]}
