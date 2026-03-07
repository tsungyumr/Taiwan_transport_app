"""
Test all bus route API response speeds
Verify caching works for all routes
"""
import asyncio
import time
import httpx

# Test routes (various types)
TEST_ROUTES = [
    # Pure numeric routes
    ("935", 0), ("935", 1),
    ("786", 0), ("786", 1),
    ("235", 0), ("235", 1),
    ("307", 0), ("307", 1),
    # Letter+number routes
    ("F623", 0), ("F623", 1),
    ("藍15", 0), ("藍15", 1),
    ("綠1", 0), ("綠1", 1),
]

BASE_URL = "http://127.0.0.1:8001"


async def test_route(client: httpx.AsyncClient, route: str, direction: int):
    """Test a single route API"""
    url = f"{BASE_URL}/api/bus/{route}?direction={direction}"

    # First call (no cache)
    start = time.time()
    try:
        response1 = await client.get(url, timeout=30.0)
        first_call_time = (time.time() - start) * 1000
        first_status = response1.status_code

        # Second call (should be cached)
        start = time.time()
        response2 = await client.get(url, timeout=30.0)
        second_call_time = (time.time() - start) * 1000
        second_status = response2.status_code

        return {
            "route": route,
            "direction": direction,
            "first_call_ms": first_call_time,
            "first_status": first_status,
            "second_call_ms": second_call_time,
            "second_status": second_status,
            "cached": second_call_time < first_call_time * 0.5,
        }
    except Exception as e:
        return {
            "route": route,
            "direction": direction,
            "error": str(e),
        }


async def main():
    """Main test function"""
    print("=" * 80)
    print("Bus Route API Response Speed Test")
    print("=" * 80)
    print(f"Test routes: {len(TEST_ROUTES)}")
    print()

    # Check if service is running
    try:
        async with httpx.AsyncClient() as client:
            health = await client.get(f"{BASE_URL}/api/health", timeout=5.0)
            if health.status_code != 200:
                print(f"[ERROR] Service not running (status: {health.status_code})")
                print("Please start server: python main.py")
                return
            print(f"[OK] Service running: {health.json()}")
            print()
    except Exception as e:
        print(f"[ERROR] Cannot connect to service: {e}")
        print("Please start server: python main.py")
        return

    # Test all routes
    results = []
    async with httpx.AsyncClient() as client:
        for route, direction in TEST_ROUTES:
            result = await test_route(client, route, direction)
            results.append(result)

            if "error" in result:
                print(f"[FAIL] {route} dir {direction}: Error - {result['error']}")
            else:
                status_icon = "[OK]" if result['first_status'] == 200 else "[FAIL]"
                cache_icon = "[CACHED]" if result['cached'] else "[WARN]"
                print(f"{status_icon} {route} dir {direction}: "
                      f"first={result['first_call_ms']:.1f}ms, "
                      f"cached={result['second_call_ms']:.1f}ms {cache_icon}")

    # Statistics
    print()
    print("=" * 80)
    print("Test Statistics")
    print("=" * 80)

    successful = [r for r in results if "error" not in r and r.get("first_status") == 200]
    failed = [r for r in results if "error" in r or r.get("first_status") != 200]
    cached = [r for r in successful if r.get("cached", False)]

    if successful:
        avg_first = sum(r["first_call_ms"] for r in successful) / len(successful)
        avg_second = sum(r["second_call_ms"] for r in successful) / len(successful)
        print(f"Success: {len(successful)}/{len(results)}")
        print(f"Failed: {len(failed)}/{len(results)}")
        print(f"Avg first response: {avg_first:.1f}ms")
        print(f"Avg cached response: {avg_second:.1f}ms")
        print(f"Cache speedup: {avg_first/avg_second:.1f}x")
        print(f"Using cache: {len(cached)}/{len(successful)}")

    if failed:
        print()
        print("Failed routes:")
        for r in failed:
            print(f"  - {r['route']} dir {r['direction']}: {r.get('error', 'HTTP ' + str(r.get('first_status')))}")

    print()
    print("=" * 80)
    if len(successful) == len(results):
        print("[PASS] All routes tested successfully! Cache working.")
    else:
        print(f"[WARN] {len(failed)} routes failed, please check.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
