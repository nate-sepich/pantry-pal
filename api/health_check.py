#!/usr/bin/env python3
"""
Health check script for deployment validation and monitoring.
Can be used in CI/CD pipelines and monitoring systems.
"""

import requests
import sys
import time
import argparse
from typing import Dict, Any, List
import json


class HealthChecker:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.results: List[Dict[str, Any]] = []

    def check_endpoint(
        self,
        path: str,
        expected_status: int = 200,
        method: str = "GET",
        headers: Dict[str, str] = None,
    ) -> bool:
        """Check a single endpoint"""
        url = f"{self.base_url}{path}"
        headers = headers or {}

        try:
            start_time = time.time()

            if method.upper() == "GET":
                response = requests.get(url, timeout=self.timeout, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, timeout=self.timeout, headers=headers)
            else:
                response = requests.request(method, url, timeout=self.timeout, headers=headers)

            end_time = time.time()
            response_time = end_time - start_time

            success = response.status_code == expected_status

            result = {
                "path": path,
                "method": method,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "response_time": response_time,
                "success": success,
                "error": None,
            }

            if not success:
                result["error"] = f"Expected {expected_status}, got {response.status_code}"

        except Exception as e:
            result = {
                "path": path,
                "method": method,
                "expected_status": expected_status,
                "actual_status": None,
                "response_time": None,
                "success": False,
                "error": str(e),
            }

        self.results.append(result)
        return result["success"]

    def run_health_checks(self) -> bool:
        """Run all health checks"""
        print(f"🔍 Running health checks against {self.base_url}")

        checks = [
            # Basic API health
            {"path": "/", "expected_status": 200},
            # OpenAPI docs
            {"path": "/openapi.json", "expected_status": 200},
            {"path": "/docs", "expected_status": 200},
            # Core endpoints (should require auth)
            {"path": "/pantry/items", "expected_status": 401},  # No auth
            {"path": "/cookbook", "expected_status": 401},  # No auth
            # Auth endpoints
            {"path": "/auth/login", "expected_status": 422, "method": "POST"},  # No body
        ]

        all_passed = True

        for check in checks:
            success = self.check_endpoint(**check)
            status = "✅" if success else "❌"
            print(
                f"{status} {check['method'].upper() if 'method' in check else 'GET'} {check['path']}"
            )

            if not success:
                all_passed = False
                result = self.results[-1]
                print(f"   Error: {result['error']}")

        return all_passed

    def check_performance(self, max_response_time: float = 5.0) -> bool:
        """Check if response times are acceptable"""
        print(f"\n⏱️  Checking performance (max response time: {max_response_time}s)")

        slow_endpoints = []
        for result in self.results:
            if result["response_time"] and result["response_time"] > max_response_time:
                slow_endpoints.append(result)

        if slow_endpoints:
            print("❌ Performance check failed:")
            for endpoint in slow_endpoints:
                print(f"   {endpoint['path']}: {endpoint['response_time']:.2f}s")
            return False
        else:
            avg_time = sum(r["response_time"] for r in self.results if r["response_time"]) / len(
                [r for r in self.results if r["response_time"]]
            )
            print(f"✅ Performance check passed (avg response time: {avg_time:.2f}s)")
            return True

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health report"""
        total_checks = len(self.results)
        passed_checks = len([r for r in self.results if r["success"]])

        response_times = [r["response_time"] for r in self.results if r["response_time"]]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0

        return {
            "timestamp": time.time(),
            "base_url": self.base_url,
            "summary": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "failed_checks": total_checks - passed_checks,
                "success_rate": (passed_checks / total_checks) * 100 if total_checks > 0 else 0,
            },
            "performance": {
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
            },
            "details": self.results,
        }


def main():
    parser = argparse.ArgumentParser(description="Health check for Pantry Pal API")
    parser.add_argument("--url", required=True, help="API base URL")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument(
        "--max-response-time", type=float, default=5.0, help="Max acceptable response time"
    )
    parser.add_argument("--output", help="Output JSON report to file")
    parser.add_argument(
        "--fail-on-performance", action="store_true", help="Fail if performance check fails"
    )

    args = parser.parse_args()

    checker = HealthChecker(args.url, args.timeout)

    # Run health checks
    health_passed = checker.run_health_checks()

    # Check performance
    performance_passed = checker.check_performance(args.max_response_time)

    # Generate report
    report = checker.generate_report()

    print(f"\n📊 Health Check Summary:")
    print(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"   Avg Response Time: {report['performance']['avg_response_time']:.2f}s")
    print(f"   Max Response Time: {report['performance']['max_response_time']:.2f}s")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"📄 Report saved to {args.output}")

    # Determine exit code
    overall_success = health_passed and (performance_passed or not args.fail_on_performance)

    if overall_success:
        print("\n🎉 All health checks passed!")
        sys.exit(0)
    else:
        print("\n💥 Health checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
