# api_utils.py
import os
import requests
import streamlit as st

# Set the API URL
API_URL = os.getenv("API_BASE", "http://localhost:8000")

def fetch_pantry_items(user_id):
    """Fetch pantry items from the API."""
    try:
        response = requests.get(f"{API_URL}/pantry/items", params={"user_id": user_id})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching pantry items: {e}")
        return []

def add_pantry_item(user_id, name, quantity):
    """Add a new item to the pantry via the API."""
    item = {"product_name": name, "quantity": quantity}
    try:
        response = requests.post(f"{API_URL}/pantry/items", json=item, params={"user_id": user_id})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error adding pantry item: {e}")
        return None

def delete_pantry_item(user_id, item_id):
    """Delete an item from the pantry via the API."""
    try:
        response = requests.delete(f"{API_URL}/pantry/items/{item_id}", params={"user_id": user_id})
        response.raise_for_status()
        return response.status_code
    except requests.RequestException as e:
        st.error(f"Error deleting pantry item: {e}")
        return None

def authenticate_user(username, password):
    """Authenticate user with the API."""
    try:
        response = requests.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error authenticating user: {e}")
        return None

def calculate_roi_metrics(user_id):
    """Calculate ROI metrics for the user."""
    try:
        response = requests.get(f"{API_URL}/roi/metrics", params={"user_id": user_id})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error calculating ROI metrics: {e}")
        return {"health_roi": "N/A", "financial_roi": "N/A", "environmental_roi": "N/A"}

def get_ai_meal_recommendation(user_id):
    """Get AI-powered recommendations for the user."""
    try:
        response = requests.get(f"{API_URL}/ai/meal_recommendation", params={"user_id": user_id})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching AI meal recommendation: {e}")
        return []
