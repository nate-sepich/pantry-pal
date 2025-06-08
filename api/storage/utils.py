import os
import logging
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from datetime import datetime
from decimal import Decimal
from models.models import InventoryItem, InventoryItemMacros, Recipe, User
from dotenv import load_dotenv
load_dotenv()

# Environment‑driven table names
PANTRY_TABLE_NAME = os.getenv("PANTRY_TABLE_NAME")
AUTH_TABLE_NAME   = os.getenv("AUTH_TABLE_NAME")
if not PANTRY_TABLE_NAME or not AUTH_TABLE_NAME:
    raise ValueError("Both PANTRY_TABLE_NAME and AUTH_TABLE_NAME must be set")

# DynamoDB tables
dynamodb     = boto3.resource("dynamodb")
pantry_table = dynamodb.Table(PANTRY_TABLE_NAME)
auth_table   = dynamodb.Table(AUTH_TABLE_NAME)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ─── Utility Functions ──────────────────────────────────────────────────────────

def convert_to_decimal(data):
    """Recursively convert float values in a dictionary to Decimal."""
    if isinstance(data, list):
        return [convert_to_decimal(item) for item in data]
    elif isinstance(data, dict):
        return {k: convert_to_decimal(v) for k, v in data.items()}
    elif isinstance(data, float):
        return Decimal(str(data))
    return data


# ─── Pantry CRUD ─────────────────────────────────────────────────────────────────

def read_pantry_items(user_id: str) -> list[InventoryItem]:
    """Fetch all pantry items for a given user_id."""
    pk = f"USER#{user_id}"
    try:
        resp = pantry_table.query(
            KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with("PANTRY#")
        )
        items: list[InventoryItem] = []
        for raw in resp.get("Items", []):
            # Build macros object if present
            macros_data = raw.get("macros") or {}
            macros = InventoryItemMacros(**macros_data) if macros_data else None

            item = InventoryItem(
                id                   = raw["id"],
                user_id              = user_id,
                product_name         = raw.get("product_name", ""),
                quantity             = int(raw.get("quantity", 1)),
                upc                  = raw.get("upc", ""),
                macros               = macros,
                cost                 = Decimal(str(raw.get("cost", 0))),
                expiration_date      = raw.get("expiration_date", None),
                environmental_impact = Decimal(str(raw.get("environmental_impact", 0))),
                image_url            = raw.get("image_url", None),  # Persisted S3 URL
                active               = raw.get("active", True),
            )
            items.append(item)
        return items

    except ClientError as e:
        logging.error("Error querying pantry items: %s", e.response["Error"]["Message"])
        raise


def write_pantry_items(user_id: str, items: list[InventoryItem]) -> None:
    """Batch write a list of InventoryItem for a given user_id."""
    pk = f"USER#{user_id}"
    try:
        with pantry_table.batch_writer() as batch:
            for item in items:
                # Ensure item is an instance of InventoryItem
                if isinstance(item, dict):
                    item = InventoryItem(**item)

                # Use the model's method to convert to a DynamoDB-compatible dictionary
                data = item.to_dynamodb_dict()

                # Compute TTL from expiration_date if provided
                expires_at = None
                if item.expiration_date:
                    dt = datetime.fromisoformat(item.expiration_date.replace("Z", "+00:00"))
                    expires_at = int(dt.timestamp())

                batch.put_item(
                    Item={
                        "PK": pk,
                        "SK": f"PANTRY#{item.id}",
                        **data,
                        "expires_at": expires_at
                    }
                )

    except ClientError as e:
        logging.error("Error writing pantry items: %s", e.response["Error"]["Message"])
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


def soft_delete_pantry_item(user_id: str, item_id: str) -> None:
    """Mark a pantry item as inactive instead of deleting it."""
    pk = f"USER#{user_id}"
    sk = f"PANTRY#{item_id}"
    try:
        pantry_table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression="SET #active = :inactive",
            ExpressionAttributeNames={"#active": "active"},
            ExpressionAttributeValues={":inactive": False}
        )
        logging.info(f"Soft deleted pantry item with ID: {item_id} for user ID: {user_id}")
    except ClientError as e:
        logging.error("Error soft deleting pantry item: %s", e.response["Error"]["Message"])
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


# ─── Recipe CRUD ─────────────────────────────────────────────────────────────────

def read_recipe_items(user_id: str) -> list[Recipe]:
    """Fetch all recipes for a given user_id."""
    pk = f"USER#{user_id}"
    try:
        resp = pantry_table.query(
            KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with("RECIPE#")
        )
        return [Recipe(**raw) for raw in resp.get("Items", [])]

    except ClientError as e:
        logging.error("Error querying recipe items: %s", e.response["Error"]["Message"])
        raise


def write_recipe_items(user_id: str, items: list[Recipe]) -> None:
    """Batch write a list of Recipe for a given user_id."""
    pk = f"USER#{user_id}"
    try:
        with pantry_table.batch_writer() as batch:
            for rec in items:
                data = rec.dict()
                # Convert float values to Decimal
                data = convert_to_decimal(data)

                batch.put_item(
                    Item={
                        "PK": pk,
                        "SK": f"RECIPE#{rec.id}",
                        **data
                    }
                )

    except ClientError as e:
        logging.error("Error writing recipe items: %s", e.response["Error"]["Message"])
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


# ─── Chat Metadata CRUD ───────────────────────────────────────────────────────

from models.models import ChatMeta, Chat


def read_chat_meta(user_id: str) -> list[ChatMeta]:
    """Return chat metadata entries for a user sorted by updatedAt desc."""
    pk = f"USER#{user_id}"
    try:
        resp = pantry_table.query(
            KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with("CHAT#")
        )
        items = [ChatMeta(**raw) for raw in resp.get("Items", [])]
        items.sort(key=lambda x: x.updatedAt, reverse=True)
        return items
    except ClientError as e:
        logging.error("Error querying chats: %s", e.response["Error"]["Message"])
        raise


def upsert_chat_meta(user_id: str, chat: ChatMeta) -> None:
    """Insert or update a chat metadata record."""
    pk = f"USER#{user_id}"
    try:
        pantry_table.put_item(
            Item={"PK": pk, "SK": f"CHAT#{chat.id}", **chat.dict()}
        )
    except ClientError as e:
        logging.error("Error writing chat meta: %s", e.response["Error"]["Message"])
        raise


def read_chat(user_id: str, chat_id: str) -> Chat | None:
    pk = f"USER#{user_id}"
    try:
        resp = pantry_table.get_item(Key={"PK": pk, "SK": f"CHATMSG#{chat_id}"})
        item = resp.get("Item")
        if not item:
            return None
        return Chat(**item)
    except ClientError as e:
        logging.error("Error reading chat: %s", e.response["Error"]["Message"])
        raise


def upsert_chat(user_id: str, chat: Chat) -> None:
    pk = f"USER#{user_id}"
    try:
        data = convert_to_decimal(chat.dict())
        pantry_table.put_item(Item={"PK": pk, "SK": f"CHATMSG#{chat.id}", **data})
    except ClientError as e:
        logging.error("Error writing chat: %s", e.response["Error"]["Message"])
        raise


def delete_chat(user_id: str, chat_id: str) -> None:
    """Delete a chat and its metadata."""
    pk = f"USER#{user_id}"
    try:
        pantry_table.delete_item(Key={"PK": pk, "SK": f"CHATMSG#{chat_id}"})
        pantry_table.delete_item(Key={"PK": pk, "SK": f"CHAT#{chat_id}"})
    except ClientError as e:
        logging.error("Error deleting chat: %s", e.response["Error"]["Message"])
        raise


# ─── Auth CRUD ───────────────────────────────────────────────────────────────────

def read_users() -> list[User]:
    """Scan all users from the auth table."""
    try:
        resp = auth_table.scan()
        return [User(**raw) for raw in resp.get("Items", [])]
    except ClientError as e:
        logging.error("Error scanning users: %s", e.response["Error"]["Message"])
        raise


def write_users(users: list[User]) -> None:
    """Batc write a list of User into the auth table."""
    try:
        with auth_table.batch_writer() as batch:
            for usr in users:
                data = usr.dict()
                # Convert float values to Decimal
                data = convert_to_decimal(data)

                batch.put_item(Item=data)
    except ClientError as e:
        logging.error("Error writing users: %s", e.response["Error"]["Message"])
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
