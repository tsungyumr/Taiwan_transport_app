"""
Test cache functionality for bus route API
"""
import asyncio
import time
import httpx

BASE_URL = "http://127.0.0.1:8001"

async def test_with_timing(client: httpx.AsyncClient, route: str, direction: int, call_num: int):
    """Test a single API call with timing"""
    url = f"{BASE_URL}/api/bus/{route}?direction={direction}"
    start = time.time()
    try:
        response = await client.get(url, timeout=30.0)
        elapsed = (time.time() - start) * 1000
        status = response.status_code
        return {
            "route": route,
            "direction": direction,
            "call": call_num,
            "status": status,
            "time_ms": round(elapsed, 2),
            "cached": elapsed < 50  # Likely cached if under 50ms
        }
    except Exception as e:
        return {
            "route": route,
            "direction": direction,
            "call": call_num,
            "error": str(e)
        }

async def main():
    print("=" * 80)
    print("Bus Route API Cache Test")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")
    print()

    # Check health
    async with httpx.AsyncClient() as client:
        health = await client.get(f"{BASE_URL}/api/health", timeout=5.0)
        print(f"Health check: {health.json()}")
        print()

    routes_to_test = [
        ("935", 0),
        ("935", 0),  # Same call - should be cached
        ("935", 0),  # Same call - should be cached
        ("786", 0),
        ("786", 0),  # Should be cached
        ("935", 1),  # Different direction
        ("935", 1),  # Should be cached
    ]

    print("Testing routes (first call should be slower, subsequent calls cached):")
    print("-" * 80)

    async with httpx.AsyncClient() as client:
        for route, direction in routes_to_test:
            result = await test_with_timing(client, route, direction, 0)

            if "error" in result:
                print(f"[ERROR] {route} dir {direction}: {result['error']}")
            else:
                cache_icon = "[CACHED]" if result['cached'] else "[NEW]"
                print(f"{cache_icon} {route} dir {direction}: {result['time_ms']}ms (HTTP {result['status']})")

            # Small delay between calls
            await asyncio.sleep(0.5)

    print("-" * 80)
    print()
    print("Cache Test Complete!")
    print("Expected behavior:")
    print("  - First call to a route: slower (loads from CSV)")
    print("  - Subsequent calls: fast (<50ms, from memory cache)")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
