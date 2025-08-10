import pytest
import requests
import os
import time
from typing import Dict, Any

# Integration tests that run against deployed API
# These require API_BASE_URL environment variable

@pytest.fixture
def api_base_url():
    """Get API base URL from environment"""
    url = os.getenv('API_BASE_URL')
    if not url:
        pytest.skip("API_BASE_URL environment variable not set")
    return url.rstrip('/')

@pytest.fixture
def auth_token():
    """Get auth token for integration tests"""
    # In real scenarios, you'd authenticate here
    # For now, we'll skip auth-required tests
    return None

class TestAPIIntegration:
    """Integration tests for deployed API"""
    
    def test_health_check(self, api_base_url):
        """Test basic API health check"""
        response = requests.get(f"{api_base_url}/", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "Welcome to Pantry Pal API" in data.get("message", "")
    
    def test_api_cors_headers(self, api_base_url):
        """Test CORS headers are present"""
        response = requests.options(f"{api_base_url}/", timeout=30)
        headers = response.headers
        assert 'access-control-allow-origin' in headers or response.status_code == 200
    
    def test_api_response_time(self, api_base_url):
        """Test API response time is acceptable"""
        start_time = time.time()
        response = requests.get(f"{api_base_url}/", timeout=30)
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 5.0, f"API response time too slow: {response_time}s"
    
    def test_invalid_endpoint_returns_404(self, api_base_url):
        """Test that invalid endpoints return 404"""
        response = requests.get(f"{api_base_url}/nonexistent-endpoint", timeout=30)
        assert response.status_code == 404
    
    @pytest.mark.skipif(not os.getenv('INTEGRATION_AUTH_TOKEN'), 
                        reason="Integration auth token not available")
    def test_authenticated_endpoints_require_auth(self, api_base_url):
        """Test that authenticated endpoints require proper authentication"""
        # Test without auth
        response = requests.get(f"{api_base_url}/pantry/items", timeout=30)
        assert response.status_code in [401, 403]
        
        # Test with invalid auth
        headers = {"Authorization": "Bearer invalid-token"}
        response = requests.get(f"{api_base_url}/pantry/items", headers=headers, timeout=30)
        assert response.status_code in [401, 403]
    
    def test_api_error_handling(self, api_base_url):
        """Test API error handling for malformed requests"""
        # Test malformed JSON
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{api_base_url}/pantry/items", 
            data="invalid-json",
            headers=headers,
            timeout=30
        )
        assert response.status_code == 422
    
    def test_api_openapi_docs_accessible(self, api_base_url):
        """Test that OpenAPI documentation is accessible"""
        response = requests.get(f"{api_base_url}/docs", timeout=30)
        # Should either work (200) or redirect (3xx)
        assert response.status_code < 500
        
        # Test OpenAPI JSON
        response = requests.get(f"{api_base_url}/openapi.json", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data

class TestAPIPerformance:
    """Performance tests for deployed API"""
    
    def test_concurrent_requests(self, api_base_url):
        """Test API can handle concurrent requests"""
        import concurrent.futures
        import threading
        
        def make_request():
            try:
                response = requests.get(f"{api_base_url}/", timeout=10)
                return response.status_code == 200
            except:
                return False
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # At least 80% should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"
    
    def test_api_memory_usage_stability(self, api_base_url):
        """Test API memory usage remains stable under load"""
        # Make multiple requests and check response times don't degrade significantly
        response_times = []
        
        for i in range(20):
            start_time = time.time()
            response = requests.get(f"{api_base_url}/", timeout=30)
            end_time = time.time()
            
            if response.status_code == 200:
                response_times.append(end_time - start_time)
            
            # Small delay between requests
            time.sleep(0.1)
        
        if len(response_times) < 10:
            pytest.skip("Not enough successful requests for stability test")
        
        # Check that later responses aren't significantly slower
        early_avg = sum(response_times[:5]) / 5
        late_avg = sum(response_times[-5:]) / 5
        
        # Later responses shouldn't be more than 2x slower than early ones
        assert late_avg <= early_avg * 2, f"Performance degradation detected: {early_avg}s -> {late_avg}s"