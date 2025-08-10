"""
Minimal pytest configuration for basic testing.
This avoids complex AWS mocking until we're ready to build real tests.
"""

import pytest
import os


@pytest.fixture(scope="session")
def test_environment():
    """Set up minimal test environment."""
    # Set any required environment variables for testing
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    return "test"


# Configure pytest to skip tests that require external dependencies
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "smoke: mark test as smoke test")
    config.addinivalue_line("markers", "slow: mark test as slow running")