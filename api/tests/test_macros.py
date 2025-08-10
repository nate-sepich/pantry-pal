import pytest
from fastapi.testclient import TestClient
from api.app import app
from api.macros import macro_service
from api.pantry.pantry_service import get_user, get_user_id_from_token
from models.models import InventoryItemMacros, FoodSuggestion, FoodCategory


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


@pytest.fixture
def mock_query(monkeypatch):
    async def dummy(item_name: str):
        return InventoryItemMacros(calories=100, protein=10)

    monkeypatch.setattr(macro_service, "query_food_api_async", dummy)


@pytest.fixture
def mock_search(monkeypatch):
    async def dummy(query: str):
        return [
            {"description": "Milk", "fdcId": 1, "foodCategory": "Dairy"},
            {"description": "Almond Milk", "fdcId": 2, "foodCategory": "Dairy"},
        ]

    monkeypatch.setattr(macro_service, "search_food_items_async", dummy)


@pytest.fixture
def mock_upc(monkeypatch):
    monkeypatch.setattr(macro_service, "search_food_item", lambda upc: None)


def test_item_quantity_scaling(mock_query):
    resp = client.post("/macros/item", json={"item_name": "Milk", "quantity": 200, "unit": "g"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["calories"] == 200
    assert data["protein"] == 20


def test_autocomplete_with_category(mock_search):
    resp = client.get("/macros/autocomplete", params={"query": "milk", "category": "dairy"})
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    assert items[0]["category"] == FoodCategory.DAIRY.value


def test_upc_not_found(mock_upc):
    resp = client.get("/macros/upc", params={"upc": "0000"})
    assert resp.status_code == 404
