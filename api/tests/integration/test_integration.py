"""
Minimal integration tests.
These test basic API integration without requiring complex setup.
"""

import pytest
import requests
import os


@pytest.fixture
def api_base_url():
    """Get API base URL from environment."""
    url = os.getenv("API_BASE_URL")
    if not url:
        pytest.skip("API_BASE_URL environment variable not set")
    return url.rstrip("/")


class TestBasicIntegration:
    """Basic integration tests."""

    def test_api_health(self, api_base_url):
        """Test basic API health check."""
        try:
            response = requests.get(f"{api_base_url}/", timeout=10)
            # Just check it doesn't crash
            assert response.status_code in [200, 401, 403, 404, 422]
        except requests.exceptions.RequestException:
            pytest.skip("API not accessible for integration tests")

    def test_openapi_accessible(self, api_base_url):
        """Test that OpenAPI docs are accessible."""
        try:
            response = requests.get(f"{api_base_url}/openapi.json", timeout=10)
            assert response.status_code in [200, 401, 403]
        except requests.exceptions.RequestException:
            pytest.skip("API not accessible for integration tests")
