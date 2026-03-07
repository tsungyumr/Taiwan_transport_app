import httpx
import time
import asyncio

async def test_route(route, direction):
    url = f"http://127.0.0.1:8001/api/bus/{route}?direction={direction}"

    async with httpx.AsyncClient() as client:
        # First call
        start = time.time()
        try:
            r1 = await client.get(url, timeout=30)
            t1 = (time.time() - start) * 1000

            if r1.status_code != 200:
                return {
                    "route": route,
                    "dir": direction,
                    "error": f"HTTP {r1.status_code}",
                    "detail": r1.text[:200] if r1.text else "No detail"
                }

            # Second call (cached)
            start = time.time()
            r2 = await client.get(url, timeout=30)
            t2 = (time.time() - start) * 1000

            return {
                "route": route,
                "dir": direction,
                "status": r1.status_code,
                "first_ms": round(t1, 1),
                "cached_ms": round(t2, 1),
                "speedup": round(t1/t2, 1) if t2 > 0 else 0
            }
        except Exception as e:
            return {
                "route": route,
                "dir": direction,
                "error": str(e)
            }

async def main():
    routes = [("935", 0), ("935", 1), ("786", 0), ("786", 1)]

    print("=" * 70)
    print("Bus Route API Speed Test")
    print("=" * 70)

    for route, direction in routes:
        result = await test_route(route, direction)
        if "error" in result:
            print(f"ERROR {result['route']} dir {result['dir']}: {result['error']}")
            if "detail" in result:
                print(f"  Detail: {result['detail']}")
        else:
            status = "OK" if result["status"] == 200 else "FAIL"
            print(f"{status} {result['route']} dir {result['dir']}: "
                  f"first={result['first_ms']}ms, cached={result['cached_ms']}ms")

    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
