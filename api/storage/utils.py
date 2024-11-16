import json
import os

# Directory to store user-specific data
USER_DATA_DIR = "user_data"

def get_user_file_path(user_id: str, file_name: str) -> str:
    """Construct the file path for a user's data file."""
    user_dir = os.path.join(USER_DATA_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, file_name)

def read_pantry_items(user_id: str):
    file_path = get_user_file_path(user_id, "pantry_database.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            items = json.load(file)
    else:
        items = []
    return items

def write_pantry_items(user_id: str, items):
    file_path = get_user_file_path(user_id, "pantry_database.json")
    with open(file_path, "w") as file:
        json.dump(items, file)

def read_recipe_items(user_id: str):
    file_path = get_user_file_path(user_id, "recipe_database.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            items = json.load(file)
    else:
        items = []
    return items

def write_recipe_items(user_id: str, items):
    file_path = get_user_file_path(user_id, "recipe_database.json")
    with open(file_path, "w") as file:
        json.dump(items, file)

def read_users():
    file_path = os.path.join(USER_DATA_DIR, "users.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            users = json.load(file)
    else:
        users = []
    return users

def write_users(users):
    file_path = os.path.join(USER_DATA_DIR, "users.json")
    with open(file_path, "w") as file:
        json.dump(users, file)