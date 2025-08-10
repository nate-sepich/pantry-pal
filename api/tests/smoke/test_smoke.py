import pytest
import requests
import os

# Smoke tests - minimal tests to verify basic functionality after deployment


@pytest.fixture
def api_base_url():
    """Get API base URL from environment"""
    url = os.getenv("API_BASE_URL", "https://bo1uqpm579.execute-api.us-east-1.amazonaws.com/Prod")
    return url.rstrip("/")


class TestSmoke:
    """Critical smoke tests that must pass after deployment"""

    def test_api_is_responding(self, api_base_url):
        """Test that API is responding to requests"""
        response = requests.get(f"{api_base_url}/", timeout=30)
        assert response.status_code == 200, f"API not responding: {response.status_code}"

    def test_api_returns_expected_message(self, api_base_url):
        """Test that API returns expected welcome message"""
        response = requests.get(f"{api_base_url}/", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "Welcome to Pantry Pal API" in data.get("message", "")

    def test_openapi_docs_available(self, api_base_url):
        """Test that API documentation is available"""
        response = requests.get(f"{api_base_url}/openapi.json", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data

    def test_basic_endpoints_responding(self, api_base_url):
        """Test that basic endpoints are responding (even if requiring auth)"""
        endpoints = ["/pantry/items", "/cookbook", "/auth/login"]

        for endpoint in endpoints:
            response = requests.get(f"{api_base_url}{endpoint}", timeout=30)
            # Should get 401/403 (auth required) or 200, not 500 or timeout
            assert (
                response.status_code < 500
            ), f"Endpoint {endpoint} returning server error: {response.status_code}"
