from fastapi.testclient import TestClient
from api.app import app
from pantry.pantry_service import get_user, get_user_id_from_token
from macros import macro_service
from models.models import InventoryItemMacros

class DummyUser:
    id = "testuser"

def override_get_user():
    return DummyUser()

def override_get_user_id_from_token():
    return "testuser"

app.dependency_overrides[get_user] = override_get_user
app.dependency_overrides[get_user_id_from_token] = override_get_user_id_from_token

def dummy_query(name):
    if name == "Rice":
        return InventoryItemMacros(protein=1)
    return None

macro_service.query_food_api = dummy_query

client = TestClient(app)

def test_get_item_macros_success():
    response = client.get("/macros/item", params={"item_name": "Rice"})
    assert response.status_code == 200
    assert "protein" in response.json() or "error" in response.json()

def test_get_item_macros_not_found():
    response = client.get("/macros/item", params={"item_name": "NonExistentFood"})
    assert response.status_code == 200
    assert "error" in response.json()

def test_recipe_macros_stub():
    # TODO: Implement with valid recipe input
    pass

def test_total_macros_stub():
    # TODO: Implement with valid user_id
    pass

def test_autocomplete_stub():
    # TODO: Implement with valid query
    pass

def test_upc_stub():
    # TODO: Implement with valid upc_code
    pass 
