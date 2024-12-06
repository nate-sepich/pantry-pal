# api_utils.py
import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the API URL
API_URL = os.getenv("API_BASE", "http://api:8000")

async def llm_chat(prompt):
    """Send a prompt to the LLM chat API endpoint and return the response."""
    try:
        response = requests.post(f"{API_URL}/ai/llm_chat", json={"prompt": prompt})
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        logging.error(f"Error communicating with the LLM chat API: {e}")
        return f"Error communicating with the LLM chat API: {str(e)}"

def fetch_pantry_items(user_id, token):
    """Fetch pantry items from the API."""
    logging.info(f"Fetching pantry items for user ID: {user_id} with token: {token}")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_URL}/pantry/items", headers=headers)
        response.raise_for_status()
        return [item["product_name"] for item in response.json()]
    except requests.RequestException as e:
        logging.error(f"Error fetching pantry items: {e}")
        return []
    
if __name__ == "__main__":
    logging.info("Starting API server")