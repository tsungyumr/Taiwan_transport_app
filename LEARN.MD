# 台灣交通時刻表 App - 學習手冊

> 這是一份給開發者的學習指南，用白話文解釋這個專案的技術架構、我們遇到的挑戰、以及如何解決它們。

---

## 📱 專案簡介：這是什麼？

想像你站在台北街頭，想知道「下一班 307 公車什麼時候來？」這個 App 就是你的答案。

**台灣交通時刻表 App** 是一個 Flutter 手機應用，提供：
- 🚌 大台北公車即時動態（路線、到站時間、車輛位置）
- 🚂 台鐵時刻表查詢
- 🚄 高鐵時刻表查詢

### 為什麼要做這個？

官方的交通 App 常常：
- 介面複雜，長輩不會用
- 資料不即時，等半天車不來
- 廣告太多，體驗很差

我們想做一個**簡單、快速、沒有廣告**的替代方案。

---

## 🏗️ 技術架構：房子怎麼蓋的？

把這個 App 想像成一間餐廳：

```
┌─────────────────────────────────────────────────────────────┐
│                    顧客（使用者）                            │
│                      使用手機 App                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  外場服務生（Flutter App）                                   │
│  - 接收顧客點餐（使用者操作）                                │
│  - 展示菜單和食物（UI 畫面）                                 │
│  - 把訂單送進廚房（呼叫 API）                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  內場廚房（FastAPI 後端）                                    │
│  - 接到訂單（接收 API 請求）                                 │
│  - 去市場買食材（爬蟲抓取網站資料）                          │
│  - 烹飪上菜（回傳 JSON 資料）                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  市場供應商（政府交通網站）                                  │
│  - eBus.gov.taipei（公車）                                   │
│  - railway.gov.tw（台鐵）                                    │
│  - thsrc.com.tw（高鐵）                                      │
└─────────────────────────────────────────────────────────────┘
```

### 前端（Flutter）— 外場服務生

**用什麼技術？**
- **Flutter 3.x**：Google 的跨平台框架，寫一次 code，iOS 和 Android 都能跑
- **Dart**：Flutter 的程式語言，長得像 JavaScript + Java 的混合體
- **Provider + Riverpod**：狀態管理，想像成「記住顧客點了什麼」的便條紙系統

**為什麼選 Flutter？**
- 一套 code 跑雙平台，省時間
- 效能接近原生，滑起來順
- 熱重載（Hot Reload）超快，改 code 馬上看到效果

### 後端（FastAPI）— 內場廚房

**用什麼技術？**
- **Python 3.13**：語法簡潔，套件豐富
- **FastAPI**：現代化的 Python Web 框架，自動生成 API 文件
- **Playwright**：微軟的自動化瀏覽器工具，專門對付 JavaScript 渲染的網站
- **BeautifulSoup4**：HTML 解析器，從網頁中挖出我們要的資料

**為什麼需要 Playwright？**

這是最關鍵的決定！現代網站大多用 JavaScript 動態載入內容，傳統的 `requests` 抓下來只有空殼子。Playwright 就像一個真的瀏覽器，會：
1. 打開網頁
2. 等 JavaScript 跑完
3. 再抓取完整的 HTML

---

## 🚌 公車功能的技術深度解析

### 挑戰 1：網站結構複雜

**問題**：eBus 網站的 HTML 結構複雜，資料分散在不同元素中

**解決方案**：我們寫了一個強大的解析器，處理多種情況：

```python
# 從站點元素中提取資料的策略
1. 先找 data-stop 屬性（最準確）
2. 如果沒有，從 class 名稱解析（如 stop-15 表示第 15 站）
3. 從相鄰元素的內容交叉驗證
```

**學到的經驗**：
> 網頁爬蟲要像偵探一樣，從蛛絲馬跡中找線索。不要只依賴單一標記，要有 fallback 策略。

### 挑戰 2：即時更新 vs 效能

**問題**：公車位置每秒都在變，但一直爬蟲會：
- 把對方網站爬掛（不道德）
- 自己伺服器負擔過重
- 使用者手機電量消耗快

**解決方案**：聰明的快取策略

```python
# 記憶體快取 + TTL（Time To Live）
class TaipeiBusScraper:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 30  # 30 秒內不重複爬蟲

    async def get_route_data(self, route_name):
        # 檢查快取是否有效
        if self._cache_valid(route_name):
            return self._cache[route_name]['data']

        # 快取過期，重新爬蟲
        data = await self._scrape(route_name)
        self._cache[route_name] = {
            'data': data,
            'timestamp': time.time()
        }
        return data
```

**學到的經驗**：
> 快取是效能的救星，但要設計好失效策略。公車資料 30 秒更新一次是合理的平衡點。

### 挑戰 3：兩種資料來源的整合

**問題**：同一個頁面有兩種車輛資訊：
- HTML 中直接嵌入的（車牌、座位數）
- API 動態載入的（位置、ETA）

**解決方案**：Flutter 端支援兩種資料模型

```dart
// 站點內的車輛資訊（從 HTML 解析）
class StopBusInfo {
  final String plateNumber;  // 車牌
  final String busType;      // 車種
  final String? remainingSeats;  // 座位數
}

// 獨立的車輛動態資訊（從 API 取得）
class BusVehicle {
  final String plateNumber;
  final int atStop;          // 在第幾站
  final String etaNext;      // 到下一站時間
  final int headingTo;       // 正前往哪一站
}
```

在 UI 層，我們讓兩種資料可以互相補充：

```dart
List<dynamic> _getBusesAtStop(BusRouteData? data, int stopIndex) {
  // 優先使用 HTML 中的車輛資訊
  if (stop.buses.isNotEmpty) {
    return stop.buses;
  }
  // 如果沒有，從 vehicles 列表中找
  return data.buses.where((bus) => bus.atStop == stopIndex).toList();
}
```

---

## 🔧 遇到的問題與如何修復

### 問題 1：Flutter 顯示「站序 1、站序 2」而不是真實站名

**症狀**：UI 上只顯示數字，沒有站名

**原因**：解析器把 `data-stop` 屬性（數字）當成站名了

**修復**：
```dart
// 錯誤的寫法
name: stopElement.attributes['data-stop'] ?? '站點 $sequence'

// 正確的寫法：優先從元素內文取站名
name: stopElement.text.trim().isNotEmpty
    ? stopElement.text.trim()
    : (stopElement.attributes['data-stop'] ?? '站點 $sequence')
```

**學到什麼**：
> HTML 元素的屬性（attribute）和內文（text）是不同的東西。`data-stop` 通常是給程式用的 ID，顯示給人看的是元素內文。

### 問題 2：模擬器連不上後端

**症狀**：App 顯示「網路連接錯誤」

**原因**：Android 模擬器的 `localhost` 和電腦的不一樣

**修復**：
```dart
// Android 模擬器要用 10.0.2.2 才能連到主機的 localhost
static const String _baseUrl = 'http://10.0.2.2:8001/api';
// 而不是 http://localhost:8001/api
```

**學到什麼**：
> Android 模擬器是獨立的虛擬機，它有自己獨立的網路空間。`10.0.2.2` 是 Android 模擬器的特殊 IP，指向主機電腦。

### 問題 3：Playwright 瀏覽器實例耗盡記憶體

**症狀**：伺服器跑一陣子後變慢，最後當掉

**原因**：每次爬蟲都開新瀏覽器，沒有正確關閉

**修復**：使用瀏覽器池（Browser Pool）

```python
class TaipeiBusScraper:
    def __init__(self):
        self._playwright = None
        self._browser = None

    async def _ensure_browser(self):
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch()
        return self._browser

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
```

**學到什麼**：
> 資源管理是後端開發的核心。開啟的資源（瀏覽器、資料庫連線、檔案）一定要確保關閉，最好使用 context manager 模式。

---

## 🎨 UI/UX 設計決策

### 公車路線頁面的時間軸設計

**為什麼用垂直時間軸？**

公車路線是線性的，從 A 站到 B 站。時間軸是最直覺的呈現方式：

```
●─────── 東方山河社區
│         進站中
│         🚌 EAL-3359 一般公車 20席
│
○─────── 大豐街
│         約 3 分
│
○─────── 下寮里
          未發車
```

**設計細節**：
- **藍色圓圈（○）**：普通站點，還沒有公車到
- **橘色圓圈（●）**：有公車在此站，吸引使用者注意
- **脈動動畫**：公車圖示會輕微脈動，暗示「進行中」
- **資訊標籤**：車牌、車種、座位數，一次看清

### 顏色的心理學

```dart
// 有公車的站點 - 暖色調，緊急、注意
Colors.orange[50]  // 背景
Colors.orange      // 圓圈和公車圖示

// 無公車的站點 - 冷色調，平靜、等待
Colors.white       // 背景
Colors.blue        // 圓圈
```

---

## 📁 專案結構：檔案都放在哪？

```
Taiwan_transport_app/
├── backend/                          # 後端廚房
│   ├── main.py                       # 主程式入口
│   ├── scrapers/                     # 爬蟲工具們
│   │   └── taipei_bus_scraper.py     # 公車爬蟲
│   ├── TRA_scraper.py                # 台鐵爬蟲
│   ├── THSR_scraper.py               # 高鐵爬蟲
│   └── requirements.txt              # Python 套件清單
│
├── transport_flutter/                # 前端外場
│   ├── lib/
│   │   ├── main.dart                 # App 入口
│   │   ├── models/                   # 資料模型
│   │   │   └── bus_route.dart        # 公車相關模型
│   │   ├── screens/                  # 畫面頁面
│   │   │   ├── home_screen.dart      # 首頁
│   │   │   ├── bus_list_screen.dart  # 公車列表
│   │   │   └── bus_route_screen.dart # 公車路線詳情
│   │   ├── providers/                # 狀態管理
│   │   │   └── bus_provider.dart     # 公車資料狀態
│   │   └── services/                 # API 服務
│   │       └── bus_api_service.dart  # 呼叫後端 API
│   │
│   └── pubspec.yaml                  # Flutter 套件清單
│
├── CLAUDE.md                         # 專案開發規範
├── LEARN.md                          # 這份文件
└── README.md                         # 專案簡介
```

---

## 🚀 如何開始開發？

### 環境設定

**後端（Python）**：
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
python main.py
```

**前端（Flutter）**：
```bash
cd transport_flutter
flutter pub get
flutter run
```

### 開發流程

我們遵循**後端優先**的策略：

1. **先確保 API 正常**：用 curl 或 Postman 測試後端
2. **再串接前端**：Flutter 呼叫本地 API
3. **最後調整 UI**：讓畫面好看好用

為什麼這樣做？因為如果後端資料結構錯了，前端改再多也沒用。

---

## 🧠 優秀工程師的思考方式

從這個專案，我們可以學到：

### 1. 分層思考

不要把所有東西塞在一起。資料層、邏輯層、呈現層要分開：

```
資料（後端爬蟲）
    ↓
模型（Dart class）
    ↓
狀態（Provider）
    ↓
畫面（Widget）
```

這樣要改任何一層，其他層不受影響。

### 2. 防禦性程式設計

假設所有東西都會出錯：
- API 會掛 → 加 try-catch
- 資料格式不對 → 加 null check
- 網路會斷 → 加重試機制

```dart
// 好的寫法：優雅處理錯誤
try {
  data = await BusApiService.fetchBusRouteData(route);
} catch (e) {
  // 顯示友善的錯誤訊息，而不是讓 App 閃退
  _error = '暫時無法取得資料，請稍後再試';
}
```

### 3. 漸進式開發

不要想一次做到完美。我們的開發順序是：

1. **MVP（最小可行產品）**：能顯示站名就好
2. **加入 ETA**：顯示到站時間
3. **加入車輛位置**：標記公車在哪
4. **優化 UI**：動畫、顏色、互動

每個階段都能 demo，每個階段都有價值。

---

## 🐛 常見錯誤與避免方法

| 錯誤 | 原因 | 解決方案 |
|------|------|----------|
| `SocketException` | 後端沒開或 IP 錯誤 | 確認後端運行中，Android 用 10.0.2.2 |
| `FormatException` | JSON 解析失敗 | 檢查後端回傳格式，加日誌除錯 |
| 畫面不更新 | 忘了 `notifyListeners()` | Provider 模式要手動通知 |
| 爬蟲抓不到資料 | 網站結構改變 | 定期檢查，設計彈性的解析器 |
| 記憶體洩漏 | 資源沒關閉 | 使用 `dispose()` 和 context manager |

---

## 🔮 未來可以怎麼擴充？

### 短期（1-2 週）
- [ ] 加入「我的最愛」功能，儲存常搭路線
- [ ] 到站推播通知
- [ ] 離線模式（快取最近查詢）

### 中期（1-2 月）
- [ ] 支援更多城市（台中、高雄公車）
- [ ] 整合捷運時刻表
- [ ] 路線規劃（多段轉乘）

### 長期（3-6 月）
- [ ] 機器學習預測到站時間
- [ ] 擁擠度預測
- [ ] iOS Widget 小工具

---

## 📚 推薦學習資源

### Flutter
- [Flutter 官方文件](https://docs.flutter.dev/) - 最權威的參考
- [Flutter Gallery](https://gallery.flutter.dev/) - 看別人怎麼設計 UI

### Python / FastAPI
- [FastAPI 官方教學](https://fastapi.tiangolo.com/tutorial/) - 中文文件很棒
- [Playwright 文件](https://playwright.dev/python/) - 爬蟲必學

### 網頁爬蟲
- [BeautifulSoup 文件](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Selector 語法](https://www.w3schools.com/cssref/css_selectors.php) - 爬蟲的基礎

---

## 💬 結語

這個專案教會我們：**好的軟體不是一次寫出來的，是迭代出來的。**

從最初的 mock data，到真實的 Playwright 爬蟲，再到精緻的 UI，每一步都在解決真實的問題。遇到 bug 不要氣餒，每個錯誤都是學習的機會。

如果你要接手這個專案，記得：
1. **先讀 CLAUDE.md** - 了解開發規範
2. **從小改動開始** - 不要一次改太多
3. **測試、測試、再測試** - 尤其是爬蟲部分
4. **保持簡單** - 不要過度設計

祝你開發順利！🚀

---

**文件版本**: v1.0
**最後更新**: 2026-03-05
**作者**: Claude Code
**專案**: 台灣交通時刻表 App
