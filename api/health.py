#!/usr/bin/env python3
"""
Simple health check for deployed API.
Can be run manually or in CI/CD pipeline.
"""

import sys
import time

import requests


def check_api_health(base_url: str) -> bool:
    """Check basic API health."""
    try:
        # Remove trailing slash
        base_url = base_url.rstrip("/")

        print(f"🔍 Checking API health at: {base_url}")

        # Basic health check
        start_time = time.time()
        response = requests.get(f"{base_url}/", timeout=30)
        end_time = time.time()

        response_time = end_time - start_time

        if response.status_code == 200:
            print(f"✅ API is responding (200 OK, {response_time:.2f}s)")
            try:
                data = response.json()
                if "Welcome to Pantry Pal API" in data.get("message", ""):
                    print("✅ API returning expected welcome message")
                else:
                    print("⚠️ API responding but unexpected message format")
            except Exception:
                print("⚠️ API responding but not returning JSON")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("❌ API health check timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def check_openapi_docs(base_url: str) -> bool:
    """Check that OpenAPI documentation is available."""
    try:
        base_url = base_url.rstrip("/")
        response = requests.get(f"{base_url}/openapi.json", timeout=10)

        if response.status_code == 200:
            print("✅ OpenAPI documentation is available")
            try:
                data = response.json()
                if "openapi" in data:
                    print("✅ OpenAPI schema is valid")
                    return True
                else:
                    print("⚠️ OpenAPI endpoint responding but invalid schema")
                    return False
            except Exception:
                print("⚠️ OpenAPI endpoint not returning valid JSON")
                return False
        else:
            print(f"❌ OpenAPI docs returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"⚠️ OpenAPI check failed: {e}")
        return False


def main():
    """Main health check."""
    if len(sys.argv) != 2:
        print("Usage: python health.py <api-base-url>")
        print("Example: python health.py https://api-id.execute-api.us-east-1.amazonaws.com/Prod")
        sys.exit(1)

    base_url = sys.argv[1]

    print("🏥 PantryPal API Health Check")
    print("=" * 40)

    health_ok = check_api_health(base_url)
    docs_ok = check_openapi_docs(base_url)

    print("\n📊 Summary:")
    if health_ok and docs_ok:
        print("🎉 All health checks passed!")
        sys.exit(0)
    elif health_ok:
        print("⚠️ API is running but docs have issues")
        sys.exit(0)  # Don't fail deployment for docs issues
    else:
        print("💥 API health check failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
