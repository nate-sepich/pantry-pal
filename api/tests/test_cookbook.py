import pytest
from fastapi.testclient import TestClient
from api.app import app
from api.cookbook.cookbook_service import get_user, get_user_id_from_token

class DummyUser:
    id = "testuser"

def override_get_user():
    return DummyUser()

def override_get_user_id_from_token():
    return "testuser"

app.dependency_overrides[get_user] = override_get_user
app.dependency_overrides[get_user_id_from_token] = override_get_user_id_from_token

client = TestClient(app)

def test_get_recipes_authenticated():
    response = client.get(
        "/cookbook",
        headers={"Authorization": "Bearer a.b.c"}
    )
    assert response.status_code in (200, 404)

def test_add_recipe_stub():
    pass

def test_delete_recipe_stub():
    pass
