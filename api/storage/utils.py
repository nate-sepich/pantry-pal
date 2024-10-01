import json

# Simulated pantry database stored in a JSON file

PANTRY_DATABASE_FILE = "pantry_database.json"
RECIPE_DATABASE_FILE = "recipe_database.json"

def read_pantry_items():
    with open(PANTRY_DATABASE_FILE, "r") as file:
        items = json.load(file)
    return items

def write_pantry_items(items):
    with open(PANTRY_DATABASE_FILE, "w") as file:
        json.dump(items, file)

def read_recipe_items():
    with open(RECIPE_DATABASE_FILE, "r") as file:
        items = json.load(file)
    return items

def write_recipe_items(items):
    with open(RECIPE_DATABASE_FILE, "w") as file:
        json.dump(items, file)