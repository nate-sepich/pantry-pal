import pytest
from fastapi.testclient import TestClient
from api.app import app
import cookbook.cookbook_service as cookbook_service
from cookbook.cookbook_service import get_user, get_user_id_from_token
from models.models import Recipe

class DummyUser:
    id = "testuser"

def override_get_user():
    return DummyUser()

def override_get_user_id_from_token():
    return "testuser"

app.dependency_overrides[get_user] = override_get_user
app.dependency_overrides[get_user_id_from_token] = override_get_user_id_from_token

cookbook_service.read_recipe_items = lambda user_id: []
cookbook_service.write_recipe_items = lambda user_id, items: None

client = TestClient(app)

def test_get_recipes_authenticated():
    response = client.get(
        "/cookbook",
        headers={"Authorization": "Bearer a.b.c"}
    )
    assert response.status_code in (200, 404)


def test_import_recipe_success():
    class DummyScraper:
        def title(self):
            return "Test Recipe"

        def ingredients(self):
            return ["1 cup rice"]

        def instructions(self):
            return "Cook it"

        def image(self):
            return None

        def total_time(self):
            return 10

        def tags(self):
            return ["test"]

    cookbook_service.scrape_me = lambda url: DummyScraper()
    resp = client.post("/cookbook/import", json={"url": "http://example.com"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Recipe"

def test_add_recipe_stub():
    pass

def test_delete_recipe_stub():
    pass
