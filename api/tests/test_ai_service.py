import pytest
import requests
import logging
from unittest.mock import patch  # Import patch from unittest.mock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_BASE_URL = "http://localhost:8000"

@pytest.fixture
def mock_read_pantry_items():
    with patch("storage.utils.read_pantry_items") as mock:
        yield mock

@pytest.fixture
def mock_client_generate():
    with patch("ai.ai_service.client.generate") as mock:
        yield mock

@pytest.fixture
def auth_headers():
    # Perform login to get the token
    logging.info("Attempting to log in user: testuser")
    response = requests.post(f"{API_BASE_URL}/auth/login", json={"username": "testuser", "password": "testpassword"})
    logging.info(f"Login response status: {response.status_code}")
    logging.info(f"Login response content: {response.json()}")
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.auth
def test_login():
    logging.info("Testing login endpoint")
    response = requests.post(f"{API_BASE_URL}/auth/login", json={"username": "testuser", "password": "testpassword"})
    logging.info(f"Login response status: {response.status_code}")
    logging.info(f"Login response content: {response.json()}")
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.recipe
def test_get_recipe_recommendations(mock_read_pantry_items, mock_client_generate, auth_headers):
    logging.info("Testing get_recipe_recommendations endpoint")
    mock_read_pantry_items.return_value = [{"product_name": "Tomato"}, {"product_name": "Cheese"}]
    mock_client_generate.return_value = {"response": "Recipe: Tomato Cheese Salad"}

    response = requests.get(f"{API_BASE_URL}/ai/meal_recommendation?user_id=testuser", headers=auth_headers)
    logging.info(f"get_recipe_recommendations response status: {response.status_code}")
    logging.info(f"get_recipe_recommendations response content: {response.text}")
    assert response.status_code == 200
    assert "Recipe" in response.text

@pytest.mark.meal
def test_get_meal_suggestions(mock_read_pantry_items, mock_client_generate, auth_headers):
    logging.info("Testing get_meal_suggestions endpoint")
    mock_read_pantry_items.return_value = [{"product_name": "Tomato"}, {"product_name": "Cheese"}]
    mock_client_generate.return_value = {"response": "Meal: Tomato Cheese Sandwich"}

    daily_macro_goals = {
        "calories": 2000,
        "protein": 150,
        "carbohydrates": 250,
        "fat": 70
    }
    response = requests.post(f"{API_BASE_URL}/ai/meal_suggestions?user_id=testuser", json=daily_macro_goals, headers=auth_headers)
    logging.info(f"get_meal_suggestions response status: {response.status_code}")
    logging.info(f"get_meal_suggestions response content: {response.text}")
    assert response.status_code == 200
    assert "Meal" in response.text