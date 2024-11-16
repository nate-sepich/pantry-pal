# api_utils.py
import os
import requests
import streamlit as st
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the API URL
API_URL = os.getenv("API_BASE", "http://localhost:8000")

def fetch_pantry_items(user_id, token):
    """Fetch pantry items from the API."""
    logging.info(f"Fetching pantry items for user ID: {user_id} with token: {token}")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_URL}/pantry/items", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching pantry items: {e}")
        st.error(f"Error fetching pantry items: {e}")
        return []

def add_pantry_item(user_id, name, quantity, token):
    """Add a new item to the pantry via the API."""
    logging.info(f"Adding item '{name}' (quantity: {quantity}) for user ID: {user_id}")
    headers = {"Authorization": f"Bearer {token}"}
    item = {"user_id":user_id, "product_name": name, "quantity": quantity}
    try:
        response = requests.post(f"{API_URL}/pantry/items", json=item, headers=headers)
        logging.info(f"Response status code: {response.status_code}")
        logging.info(f"Response content: {response.content}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error adding pantry item: {e}")
        return None

def delete_pantry_item(user_id, item_id, token):
    """Delete an item from the pantry via the API."""
    logging.info(f"Deleting item ID: {item_id} for user ID: {user_id}")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.delete(f"{API_URL}/pantry/items/{item_id}", headers=headers)
        response.raise_for_status()
        return response.status_code
    except requests.RequestException as e:
        st.error(f"Error deleting pantry item: {e}")
        return None

def authenticate_user(username, password):
    """Authenticate user with the API."""
    logging.info(f"Authenticating user: {username}")
    try:
        response = requests.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
        response.raise_for_status()
        data = response.json()
        logging.info(f"Authentication response: {data}")
        if "access_token" in data:
            st.session_state["token"] = data["access_token"]
        else:
            st.error("Authentication failed: No access token in response")
        return data
    except requests.RequestException as e:
        st.error(f"Error authenticating user: {e}")
        return None

def calculate_roi_metrics(user_id, token):
    """Calculate ROI metrics for the user."""
    logging.info(f"Calculating ROI metrics for user ID: {user_id}")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_URL}/roi/metrics", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error calculating ROI metrics: {e}")
        return {"health_roi": "N/A", "financial_roi": "N/A", "environmental_roi": "N/A"}

def get_ai_meal_recommendation(user_id, token):
    """Get AI-powered recommendations for the user."""
    logging.info(f"Fetching AI meal recommendation for user ID: {user_id}")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_URL}/ai/meal_recommendation", headers=headers, params={"user_id": user_id})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching AI meal recommendation: {e}")
        return []
