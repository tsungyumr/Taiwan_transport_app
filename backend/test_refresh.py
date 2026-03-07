"""
測試 Flutter 重新整理功能是否正常運作
"""
import httpx
import time

BASE_URL = "http://127.0.0.1:8001"

def test_refresh_functionality():
    """測試重新整理功能 - 帶時間戳的請求應該繞過快取"""

    print("=" * 70)
    print("測試重新整理功能 (forceRefresh)")
    print("=" * 70)

    route = "935"
    direction = 0

    # 第一次請求（正常）
    print(f"\n1. 第一次請求 {route} 方向 {direction}")
    url1 = f"{BASE_URL}/api/bus/{route}?direction={direction}"
    start = time.time()
    r1 = httpx.get(url1, timeout=30)
    t1 = (time.time() - start) * 1000
    print(f"   狀態: {r1.status_code}, 時間: {t1:.1f}ms")

    # 第二次請求（帶時間戳，模擬重新整理）
    print(f"\n2. 第二次請求（帶時間戳，模擬重新整理）")
    timestamp = int(time.time() * 1000)
    url2 = f"{BASE_URL}/api/bus/{route}?direction={direction}&_t={timestamp}"
    start = time.time()
    r2 = httpx.get(url2, timeout=30)
    t2 = (time.time() - start) * 1000
    print(f"   URL: {url2}")
    print(f"   狀態: {r2.status_code}, 時間: {t2:.1f}ms")

    # 第三次請求（相同時間戳，應該是新的請求）
    print(f"\n3. 第三次請求（新的時間戳）")
    timestamp2 = int(time.time() * 1000) + 1
    url3 = f"{BASE_URL}/api/bus/{route}?direction={direction}&_t={timestamp2}"
    start = time.time()
    r3 = httpx.get(url3, timeout=30)
    t3 = (time.time() - start) * 1000
    print(f"   URL: {url3}")
    print(f"   狀態: {r3.status_code}, 時間: {t3:.1f}ms")

    # 第四次請求（無時間戳，應該命中快取）
    print(f"\n4. 第四次請求（無時間戳，應該命中快取）")
    start = time.time()
    r4 = httpx.get(url1, timeout=30)
    t4 = (time.time() - start) * 1000
    print(f"   狀態: {r4.status_code}, 時間: {t4:.1f}ms")

    print("\n" + "=" * 70)
    print("測試完成！")
    print("=" * 70)
    print("\n預期結果：")
    print("  - 第一次請求：正常載入（可能較慢）")
    print("  - 第二次請求（帶時間戳）：應該繞過快取，拿到最新資料")
    print("  - 第三次請求（新時間戳）：應該繞過快取")
    print("  - 第四次請求（無時間戳）：應該命中快取（很快）")

if __name__ == "__main__":
    test_refresh_functionality()
