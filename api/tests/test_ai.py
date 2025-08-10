from fastapi.testclient import TestClient
from api.app import app

# import overrides
import ai.openai_service as openai_service
from types import SimpleNamespace


class DummyUser:
    id = "testuser"


def override_get_user():
    return DummyUser()


# app.dependency_overrides = {}
# app.dependency_overrides[get_user_id_from_token] = override_get_user_id_from_token

app.dependency_overrides = {}
app.dependency_overrides[openai_service.get_user_id_from_token] = lambda: "testuser"


# Monkeypatch OpenAI client and pantry reader
class DummyChat:
    def create(self, *args, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="dummy recipe"))]
        )


class DummyImage:
    def generate(self, *args, **kwargs):
        return SimpleNamespace(data=[SimpleNamespace(url="http://test/image.png")])


# Apply monkeypatches
openai_service.openai_client = SimpleNamespace(
    chat=SimpleNamespace(completions=DummyChat()), images=DummyImage()
)
openai_service.read_pantry_items = lambda user_id: []

client = TestClient(app)


def test_meal_recommendation_success():
    response = client.get("/openai/meal_recommendation")
    assert response.status_code == 200
    assert response.json() == "dummy recipe"


def test_meal_suggestions_success():
    # supply minimal macro goals
    payload = {"calories": 100, "protein": 10, "carbohydrates": 20, "fat": 5}
    response = client.post("/openai/meal_suggestions", json=payload)
    assert response.status_code == 200
    assert response.json() == "dummy recipe"


def test_llm_chat_success():
    payload = {"messages": [{"role": "user", "content": "hello"}]}
    response = client.post("/openai/llm_chat", json=payload)
    assert response.status_code == 200
    assert response.json() == {"response": "dummy recipe"}


def test_generate_image_not_found():
    # No pantry items exist, so image generation should return 404
    response = client.post("/openai/generate_image", json={"item_id": "unknown"})
    assert response.status_code == 404


def test_build_recipe_prompt_servings():
    items = [{"product_name": "Rice", "quantity": 1}]
    mods = SimpleNamespace(servings=4)
    prompt = openai_service.build_recipe_prompt(items, mods)
    assert "Scale recipe to 4 servings." in prompt


def test_generate_recipe_endpoint():
    openai_service.read_pantry_items = lambda user_id: [
        {"id": "1", "product_name": "Rice", "quantity": 1}
    ]

    class DummyChat2:
        def create(self, *args, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"title":"t"}'))]
            )

    openai_service.openai_client = SimpleNamespace(
        chat=SimpleNamespace(completions=DummyChat2()), images=DummyImage()
    )
    payload = {"itemIds": ["1"], "modifiers": {"servings": 2}}
    resp = client.post("/openai/recipes/generate", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"recipe": {"title": "t"}}
