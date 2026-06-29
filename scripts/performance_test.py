#!/usr/bin/env python3
"""
API Performance Testing Module
Tests response times and concurrent request handling for Smart Career Advisor APIs
Generates real performance metrics from actual HTTP requests
"""
import asyncio
import json
import time
import statistics
from datetime import datetime
from pathlib import Path
import sys

try:
    import aiohttp
    import requests
except ImportError:
    print("Missing dependencies. Install with: pip install aiohttp requests")
    sys.exit(1)


BASE_URL = "http://localhost:3000"
PERF_OUTPUT_DIR = Path("performance_results")
PERF_OUTPUT_DIR.mkdir(exist_ok=True)

# Test user credentials (adjust as needed for your setup)
TEST_CREDENTIALS = {
    "email": "testuser@example.com",
    "password": "testpass123",
    "name": "Performance Test User"
}


class APIPerformanceTester:
    """Test API performance and response times"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.results = {}
        self.token = None
        
    def register_user(self):
        """Register a test user"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json=TEST_CREDENTIALS,
                timeout=10
            )
            if response.status_code in [201, 400]:  # Created or already exists
                return response.json()
            return None
        except Exception as e:
            print(f"Registration error: {e}")
            return None
    
    def login_user(self):
        """Login and get auth token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "email": TEST_CREDENTIALS["email"],
                    "password": TEST_CREDENTIALS["password"]
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                return self.token
            return None
        except Exception as e:
            print(f"Login error: {e}")
            return None
    
    def get_headers(self):
        """Get authorization headers"""
        if not self.token:
            self.login_user()
        return {"Authorization": f"Bearer {self.token}"}
    
    def measure_endpoint(self, method, endpoint, name=None, data=None, repeat=10):
        """
        Measure response time for an endpoint
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            name: Display name for results
            data: Request body (for POST/PUT)
            repeat: Number of times to measure
        """
        if not name:
            name = f"{method} {endpoint}"
        
        times = []
        success_count = 0
        error_count = 0
        
        print(f"\nTesting: {name}")
        print(f"  Repeats: {repeat} times")
        
        for i in range(repeat):
            try:
                url = f"{self.base_url}{endpoint}"
                start = time.time()
                
                if method == "GET":
                    response = requests.get(url, headers=self.get_headers(), timeout=10)
                elif method == "POST":
                    response = requests.post(url, json=data, headers=self.get_headers(), timeout=10)
                elif method == "PUT":
                    response = requests.put(url, json=data, headers=self.get_headers(), timeout=10)
                
                elapsed = (time.time() - start) * 1000  # Convert to ms
                times.append(elapsed)
                
                if 200 <= response.status_code < 300:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"    ✗ Request {i+1} failed: {e}")
        
        if times:
            result = {
                "endpoint": endpoint,
                "method": method,
                "repeat_count": repeat,
                "success_count": success_count,
                "error_count": error_count,
                "success_rate": (success_count / repeat) * 100,
                "response_times_ms": times,
                "min_ms": min(times),
                "max_ms": max(times),
                "mean_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
            }
            
            self.results[name] = result
            print(f"  ✓ Completed: Mean={result['mean_ms']:.2f}ms, Median={result['median_ms']:.2f}ms, StdDev={result['std_dev_ms']:.2f}ms")
            return result
        
        return None
    
    async def async_request(self, session, method, url, headers, data=None):
        """Make async HTTP request"""
        try:
            async with session.request(method, url, json=data, headers=headers, timeout=10) as response:
                start = time.time()
                await response.json()
                return (time.time() - start) * 1000  # Return time in ms
        except Exception as e:
            return None
    
    def test_concurrent_requests(self, endpoint, method="GET", concurrent_users=10, requests_per_user=5):
        """
        Test concurrent request handling
        
        Args:
            endpoint: API endpoint to test
            method: HTTP method
            concurrent_users: Number of concurrent users
            requests_per_user: Requests each user makes
        """
        print(f"\nTesting Concurrent Requests: {method} {endpoint}")
        print(f"  Concurrent Users: {concurrent_users}")
        print(f"  Requests per User: {requests_per_user}")
        
        async def run_concurrent_test():
            times = []
            url = f"{self.base_url}{endpoint}"
            headers = self.get_headers()
            
            async with aiohttp.ClientSession() as session:
                # Create tasks for all requests
                tasks = []
                for _ in range(concurrent_users):
                    for _ in range(requests_per_user):
                        tasks.append(self.async_request(session, method, url, headers))
                
                # Run all tasks concurrently
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                total_time = time.time() - start_time
                
                # Filter out None results (failed requests)
                times = [t for t in results if t is not None]
                
                return times, total_time
        
        try:
            times, total_time = asyncio.run(run_concurrent_test())
            
            if times:
                result = {
                    "endpoint": endpoint,
                    "method": method,
                    "concurrent_users": concurrent_users,
                    "requests_per_user": requests_per_user,
                    "total_requests": concurrent_users * requests_per_user,
                    "successful_requests": len(times),
                    "failed_requests": (concurrent_users * requests_per_user) - len(times),
                    "success_rate": (len(times) / (concurrent_users * requests_per_user)) * 100,
                    "total_time_sec": total_time,
                    "requests_per_sec": (concurrent_users * requests_per_user) / total_time,
                    "response_times_ms": times,
                    "mean_response_time_ms": statistics.mean(times),
                    "median_response_time_ms": statistics.median(times),
                    "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
                }
                
                test_name = f"Concurrent {concurrent_users}u {endpoint}"
                self.results[test_name] = result
                
                print(f"  ✓ Completed: {result['requests_per_sec']:.2f} req/s, Mean={result['mean_response_time_ms']:.2f}ms")
                return result
            
        except Exception as e:
            print(f"  ✗ Concurrent test failed: {e}")
        
        return None
    
    def run_full_test_suite(self):
        """Run comprehensive API performance tests"""
        print("=" * 80)
        print("API PERFORMANCE TESTING SUITE")
        print("=" * 80)
        
        # Setup
        print("\n[Setup] Registering and authenticating test user...")
        self.register_user()
        if not self.login_user():
            print("✗ Failed to authenticate. Exiting.")
            return False
        print("✓ Authentication successful")
        
        # Basic endpoint tests
        print("\n" + "=" * 80)
        print("[Test Phase 1] Basic Endpoint Response Times")
        print("=" * 80)
        
        self.measure_endpoint("GET", "/api/status", "Status Check", repeat=10)
        self.measure_endpoint("GET", "/api/profile", "Get Profile", repeat=10)
        self.measure_endpoint("GET", "/api/skills", "Get Skills", repeat=10)
        self.measure_endpoint("GET", "/api/courses", "Get Courses", repeat=10)
        self.measure_endpoint("GET", "/api/jobs", "Get Jobs", repeat=10)
        
        # POST requests with data
        print("\n" + "=" * 80)
        print("[Test Phase 2] POST Endpoints")
        print("=" * 80)
        
        self.measure_endpoint(
            "POST", 
            "/api/skills", 
            "Add Skill",
            data={"name": "TestSkill", "category": "technical", "level": "Intermediate"},
            repeat=8
        )
        
        self.measure_endpoint(
            "POST",
            "/api/goals",
            "Create Learning Goal",
            data={"title": "Test Goal", "skills": ["Python", "React"], "targetDate": "2026-09-01"},
            repeat=8
        )
        
        # Concurrent tests
        print("\n" + "=" * 80)
        print("[Test Phase 3] Concurrent Request Handling")
        print("=" * 80)
        
        self.test_concurrent_requests("/api/profile", method="GET", concurrent_users=10, requests_per_user=5)
        self.test_concurrent_requests("/api/courses", method="GET", concurrent_users=15, requests_per_user=3)
        self.test_concurrent_requests("/api/jobs", method="GET", concurrent_users=20, requests_per_user=2)
        
        # Generate summary
        print("\n" + "=" * 80)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 80)
        
        return True
    
    def save_results(self):
        """Save all test results to JSON"""
        if not self.results:
            print("No results to save")
            return
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "tests": self.results,
            "summary": {
                "total_tests": len(self.results),
                "average_response_time_ms": statistics.mean([
                    r.get("mean_ms") or r.get("mean_response_time_ms") 
                    for r in self.results.values() 
                    if r.get("mean_ms") or r.get("mean_response_time_ms")
                ]) if self.results else 0,
            }
        }
        
        # Save to JSON
        json_path = PERF_OUTPUT_DIR / "api_performance_results.json"
        with open(json_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n✓ Saved results to: {json_path}")
        
        # Save summary to CSV
        import csv
        csv_path = PERF_OUTPUT_DIR / "performance_summary.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "test_name", "endpoint", "mean_response_ms", "median_response_ms", 
                "success_rate", "requests_per_sec"
            ])
            writer.writeheader()
            
            for test_name, result in self.results.items():
                writer.writerow({
                    "test_name": test_name,
                    "endpoint": result.get("endpoint", "N/A"),
                    "mean_response_ms": result.get("mean_ms") or result.get("mean_response_time_ms"),
                    "median_response_ms": result.get("median_ms") or result.get("median_response_time_ms"),
                    "success_rate": result.get("success_rate", "N/A"),
                    "requests_per_sec": result.get("requests_per_sec", "N/A"),
                })
        print(f"✓ Saved summary to: {csv_path}")
        
        print("\n" + "=" * 80)
        print(f"All performance results saved to: {PERF_OUTPUT_DIR}")
        print("=" * 80)


def main():
    print("Waiting 2 seconds for server to be ready...")
    time.sleep(2)
    
    tester = APIPerformanceTester()
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        print(f"✓ Server is running: {response.status_code}")
    except Exception as e:
        print(f"✗ Cannot connect to server at {BASE_URL}")
        print(f"  Error: {e}")
        print("  Make sure the development server is running with: npm run dev")
        return 1
    
    # Run tests
    if tester.run_full_test_suite():
        tester.save_results()
        return 0
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
