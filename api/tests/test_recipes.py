from fastapi.testclient import TestClient
from api.app import app
import recipes.like_service as like_service

app.dependency_overrides[like_service.get_user_id_from_token] = lambda: "testuser"

like_service.add_liked_recipe = lambda user_id, recipe_id: None
like_service.remove_liked_recipe = lambda user_id, recipe_id: None
like_service.read_liked_recipes = lambda user_id: []
like_service.read_pantry_items = lambda user_id: []
like_service.call_openai = lambda prompt: '[]'

client = TestClient(app)

def test_like_recipe():
    resp = client.post("/recipes/1/like")
    assert resp.status_code == 204

def test_get_recommendations():
    resp = client.get("/recipes/recommendations")
    assert resp.status_code == 200
    assert "recommendations" in resp.json()


