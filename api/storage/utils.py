import json
import os
import logging

# Directory to store user-specific data
USER_DATA_DIR = "user_data"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_user_file_path(user_id: str, file_name: str) -> str:
    logging.info(f"Constructing file path for user ID: {user_id}, file: {file_name}")
    user_dir = os.path.join(USER_DATA_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, file_name)

def read_pantry_items(user_id: str):
    logging.info(f"Reading pantry items for user ID: {user_id}")
    file_path = get_user_file_path(user_id, "pantry_database.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            items = json.load(file)
    else:
        items = []
    return items

def write_pantry_items(user_id: str, items):
    logging.info(f"Writing pantry items for user ID: {user_id}")
    file_path = get_user_file_path(user_id, "pantry_database.json")
    with open(file_path, "w") as file:
        json.dump(items, file)

def read_recipe_items(user_id: str):
    logging.info(f"Reading recipe items for user ID: {user_id}")
    file_path = get_user_file_path(user_id, "recipe_database.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            items = json.load(file)
    else:
        items = []
    return items

def write_recipe_items(user_id: str, items):
    logging.info(f"Writing recipe items for user ID: {user_id}")
    file_path = get_user_file_path(user_id, "recipe_database.json")
    with open(file_path, "w") as file:
        json.dump(items, file)

def read_users():
    logging.info("Reading users data")
    file_path = os.path.join(USER_DATA_DIR, "users.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            users = json.load(file)
    else:
        users = []
    return users

def write_users(users):
    logging.info("Writing users data")
    file_path = os.path.join(USER_DATA_DIR, "users.json")
    with open(file_path, "w") as file:
        json.dump(users, file)