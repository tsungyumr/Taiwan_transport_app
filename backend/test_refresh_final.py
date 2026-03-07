"""
測試重新整理功能是否正常運作
"""
import httpx
import time

BASE_URL = "http://127.0.0.1:8001"

def test_refresh():
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
    data1 = r1.json()
    print(f"   站數: {len(data1.get('stops', []))}")

    # 第二次請求（帶時間戳，模擬重新整理）
    print(f"\n2. 第二次請求（帶時間戳，模擬重新整理）")
    timestamp = int(time.time() * 1000)
    url2 = f"{BASE_URL}/api/bus/{route}?direction={direction}&_t={timestamp}"
    start = time.time()
    r2 = httpx.get(url2, timeout=30)
    t2 = (time.time() - start) * 1000
    print(f"   URL: {url2}")
    print(f"   狀態: {r2.status_code}, 時間: {t2:.1f}ms")
    data2 = r2.json()
    print(f"   站數: {len(data2.get('stops', []))}")

    # 第三次請求（無時間戳，應該命中快取）
    print(f"\n3. 第三次請求（無時間戳，應該命中快取）")
    start = time.time()
    r3 = httpx.get(url1, timeout=30)
    t3 = (time.time() - start) * 1000
    print(f"   狀態: {r3.status_code}, 時間: {t3:.1f}ms")
    data3 = r3.json()
    print(f"   站數: {len(data3.get('stops', []))}")

    print("\n" + "=" * 70)
    print("測試結果分析：")
    print("=" * 70)

    # 分析結果
    if t3 < t1 * 0.5:
        print("✅ 第三次請求明顯快於第一次，快取命中有效")
    else:
        print("⚠️ 第三次請求沒有明顯快於第一次")

    if data1.get('updated') == data2.get('updated'):
        print("✅ 第一次和第二次請求的 updated 時間相同（都是新資料）")
    else:
        print(f"📝 第一次 updated: {data1.get('updated')}")
        print(f"📝 第二次 updated: {data2.get('updated')}")

    if data1.get('updated') == data3.get('updated'):
        print("✅ 第三次請求返回快取資料（與第一次相同）")
    else:
        print(f"📝 第三次請求可能是新資料")

    print("\n預期行為：")
    print("  - 第一次：正常載入（無快取）")
    print("  - 第二次（帶 _t）：強制重新整理，繞過快取")
    print("  - 第三次（無 _t）：應該命中快取（很快）")

if __name__ == "__main__":
    test_refresh()
