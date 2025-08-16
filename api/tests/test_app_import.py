"""
Test that we can import the main FastAPI app when environment variables are set.
This test only runs when proper environment is configured.
"""

import os
import pytest


@pytest.mark.skipif(
    not os.getenv("PANTRY_TABLE_NAME") or not os.getenv("AUTH_TABLE_NAME"),
    reason="Environment variables not set for app import test",
)
def test_app_can_be_imported():
    """Test that FastAPI app can be imported when environment is configured."""
    try:
        from api.app import app

        assert app is not None
        assert hasattr(app, "routes")
        assert hasattr(app, "title")
    except Exception as e:
        pytest.fail(f"Failed to import app: {e}")


@pytest.mark.skipif(
    not os.getenv("PANTRY_TABLE_NAME") or not os.getenv("AUTH_TABLE_NAME"),
    reason="Environment variables not set for app test",
)
def test_app_basic_functionality():
    """Test basic app functionality when environment is configured."""
    try:
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)

        # Test root endpoint
        response = client.get("/")
        assert response.status_code < 500  # Should not crash

        # Test OpenAPI docs
        response = client.get("/openapi.json")
        assert response.status_code < 500  # Should not crash

    except Exception as e:
        pytest.fail(f"App functionality test failed: {e}")
