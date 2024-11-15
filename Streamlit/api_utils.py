# api_utils.py
import os
import requests
import streamlit as st

# Set the API URL
API_URL = os.getenv("API_BASE", "http://localhost:8000/pantry/items")

def fetch_pantry_items():
    """Fetch pantry items from the API."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching pantry items: {e}")
        return []

def add_pantry_item(name, quantity):
    """Add a new item to the pantry via the API."""
    item = {"product_name": name, "quantity": quantity}
    try:
        response = requests.post(API_URL, json=item)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error adding pantry item: {e}")
        return None

def delete_pantry_item(item_id):
    """Delete an item from the pantry via the API."""
    try:
        response = requests.delete(f"{API_URL}/{item_id}")
        response.raise_for_status()
        return response.status_code
    except requests.RequestException as e:
        st.error(f"Error deleting pantry item: {e}")
        return None
