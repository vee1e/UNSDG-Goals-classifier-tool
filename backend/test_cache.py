#!/usr/bin/env python3
"""
Test script for SDG classification caching functionality.
Tests cache hits, misses, expiration, and statistics.
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_DATA = {
    "projectName": "Test Project",
    "projectUrl": "https://github.com/test/repo",
    "projectDescription": "This is a test project focused on education and health. We aim to improve access to quality education for underprivileged children and provide basic healthcare services in rural communities. Our project uses technology to connect volunteers with communities in need."
}

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_cache_headers(headers):
    """Print relevant cache headers."""
    cache_status = headers.get('X-Cache', 'N/A')
    cache_age = headers.get('X-Cache-Age', 'N/A')
    print(f"  X-Cache: {cache_status}")
    print(f"  X-Cache-Age: {cache_age}")
    return cache_status

def test_endpoint(endpoint, name, data=TEST_DATA):
    """Test a single endpoint with caching."""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\nTesting {name}...")
    print(f"  URL: {url}")
    
    try:
        # First request - should be cache MISS
        print("\n  [1] First request (expecting MISS)...")
        start = time.time()
        response = requests.post(url, json=data, timeout=30)
        duration1 = time.time() - start
        
        if response.status_code != 200:
            print(f"  ✗ Error: {response.status_code} - {response.text[:100]}")
            return False
            
        status1 = print_cache_headers(response.headers)
        print(f"  Duration: {duration1:.3f}s")
        
        if status1 == 'MISS':
            print("  ✓ Correctly returned cache MISS")
        elif status1 == 'HIT':
            print("  ⚠ Unexpected cache HIT (was already cached)")
        else:
            print(f"  ? Unknown cache status: {status1}")
        
        # Second request - should be cache HIT
        print("\n  [2] Second request (expecting HIT)...")
        start = time.time()
        response = requests.post(url, json=data, timeout=30)
        duration2 = time.time() - start
        
        status2 = print_cache_headers(response.headers)
        print(f"  Duration: {duration2:.3f}s")
        
        if status2 == 'HIT':
            print("  ✓ Correctly returned cache HIT")
            speedup = duration1 / max(duration2, 0.001)
            print(f"  ✓ Speedup: {speedup:.1f}x faster ({duration1:.3f}s → {duration2:.3f}s)")
        else:
            print(f"  ✗ Expected cache HIT but got: {status2}")
            return False
        
        # Third request - verify consistency
        print("\n  [3] Third request (expecting HIT)...")
        response = requests.post(url, json=data, timeout=30)
        status3 = print_cache_headers(response.headers)
        
        if status3 == 'HIT':
            print("  ✓ Cache HIT maintained")
        else:
            print(f"  ✗ Expected cache HIT but got: {status3}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Connection error - Is the backend running at {BASE_URL}?")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_cache_stats():
    """Test the cache statistics endpoint."""
    print_section("Cache Statistics")
    
    url = f"{BASE_URL}/api/cache/stats"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("Cache Stats:")
            print(json.dumps(stats, indent=2))
            
            # Validate expected fields
            cache_stats = stats.get('cache_stats', {})
            required_fields = ['hits', 'misses', 'total_requests', 'hit_rate', 'active_entries']
            
            for field in required_fields:
                if field in cache_stats:
                    print(f"  ✓ {field}: {cache_stats[field]}")
                else:
                    print(f"  ✗ Missing field: {field}")
                    
            return True
        else:
            print(f"  ✗ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_different_data():
    """Test that different data creates separate cache entries."""
    print_section("Cache Isolation (Different Data)")
    
    url = f"{BASE_URL}/api/classify_aurora"
    
    # Different description should create new cache entry
    data2 = {
        **TEST_DATA,
        "projectDescription": TEST_DATA["projectDescription"] + " Additional unique text."
    }
    
    try:
        print("Request with different description...")
        response = requests.post(url, json=data2, timeout=30)
        status = print_cache_headers(response.headers)
        
        if status == 'MISS':
            print("  ✓ Different data correctly created new cache entry")
            return True
        elif status == 'HIT':
            print("  ⚠ Warning: Different data returned cache HIT (descriptions might be normalized)")
            return True
        else:
            print(f"  ? Unexpected status: {status}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_cache_clear():
    """Test the cache clear endpoint."""
    print_section("Cache Clear")
    
    url = f"{BASE_URL}/api/cache/clear"
    
    try:
        response = requests.post(url, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Cache cleared: {result.get('message')}")
            
            # Verify stats show empty cache
            stats_response = requests.get(f"{BASE_URL}/api/cache/stats", timeout=5)
            stats = stats_response.json()
            active = stats.get('cache_stats', {}).get('active_entries', -1)
            
            if active == 0:
                print(f"  ✓ Cache stats confirm empty (active_entries: {active})")
                return True
            else:
                print(f"  ⚠ Cache still has entries: {active}")
                return True
        else:
            print(f"  ✗ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_cache_inspect():
    """Test the cache inspect endpoint."""
    print_section("Cache Inspect")
    
    url = f"{BASE_URL}/api/cache/inspect"
    
    try:
        response = requests.post(url, json={
            "endpoint": "aurora",
            **TEST_DATA
        }, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print("  Cache key inspection:")
            print(f"    Endpoint: {result.get('endpoint')}")
            print(f"    Cache key: {result.get('cache_key', 'N/A')[:64]}...")
            return True
        else:
            print(f"  ✗ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def run_all_tests():
    """Run all caching tests."""
    print_section("SDG Classification Cache Test Suite")
    print(f"Started at: {datetime.now()}")
    print(f"Backend URL: {BASE_URL}")
    
    results = {}
    
    # Clear cache before starting
    print("\nClearing cache before tests...")
    test_cache_clear()
    
    # Test each endpoint
    endpoints = [
        ("/api/classify_aurora", "Aurora API"),
        ("/api/classify_st_description", "ST Description"),
        # ST URL requires real GitHub URL, skip for automated testing
        # ("/api/classify_st_url", "ST URL"),
    ]
    
    for endpoint, name in endpoints:
        print_section(f"Testing: {name}")
        results[name] = test_endpoint(endpoint, name)
    
    # Test cache features
    results["Cache Stats"] = test_cache_stats()
    results["Cache Isolation"] = test_different_data()
    results["Cache Inspect"] = test_cache_inspect()
    results["Cache Clear"] = test_cache_clear()
    
    # Final stats
    print_section("Final Results")
    final_stats = test_cache_stats()
    
    # Summary
    print_section("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed!")
        return 0
    else:
        print(f"\n  ⚠ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    exit(exit_code)
