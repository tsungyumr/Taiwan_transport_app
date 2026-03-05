# 台灣交通時刻表 App (Taiwan Transport App)

一個使用 Flutter + FastAPI 開發的台灣交通時刻表查詢應用程式，支援大台北公車、台鐵、高鐵時刻表查詢。

## 📱 功能總覽

| 功能 | 說明 |
|------|------|
| 🚌 大台北公車 | 查詢台北市、新北市公車路線及時刻表 |
| 🚂 台灣鐵路 | 查詢台灣鐵路各站時刻表（自強、區間車、莒光等） |
| 🚄 台灣高鐵 | 查詢台灣高鐵時刻表（含座位剩餘資訊） |
| ⏰ 即時到站 | 公車即時到站資訊查詢 |

---

## 🏗️ 專案架構

```
taiwan-transport-app/
├── backend/                      # FastAPI 後端伺服器
│   ├── main.py                   # 主程式 (含 API 端點與爬蟲)
│   ├── requirements.txt          # Python 依賴
│   └── README.md                # 後端說明
│
├── transport_flutter/            # Flutter App (主要版本)
│   ├── lib/
│   │   ├── main.dart             # App 入口點
│   │   ├── models/
│   │   │   └── models.dart       # 資料模型
│   │   ├── screens/
│   │   │   ├── home_screen.dart      # 首頁
│   │   │   ├── bus_screen.dart       # 公車查詢
│   │   │   ├── railway_screen.dart   # 台鐵查詢
│   │   │   └── thsr_screen.dart      # 高鐵查詢
│   │   └── services/
│   │       └── api_service.dart       # API 服務
│   ├── pubspec.yaml              # Flutter 依賴
│   └── README.md
│
│
└── README.md                     # 本文件
```

---

## 📁 檔案列表與功能說明

### 後端 (Backend)

| 檔案 | 功能說明 |
|------|----------|
| `main.py` | FastAPI 伺服器，包含所有 API 端點與爬蟲邏輯 |
| `requirements.txt` | Python 依賴套件列表 |
| `TRA_scraper.py` | 台鐵爬蟲模組（舊版） |
| `analyze_sites.py` | 網站分析工具 |
| `test_tra_scraper.py` | 台鐵爬蟲測試 |
| `test_playwright.py` | Playwright 測試 |

### 前端 (Flutter App)

| 檔案 | 功能說明 |
|------|----------|
| `lib/main.dart` | App 入口點，定義 MaterialApp |
| `lib/models/models.dart` | 資料模型（BusRoute, TrainStation, TrainTimeEntry 等） |
| `lib/screens/home_screen.dart` | 首頁，導航到各功能畫面 |
| `lib/screens/bus_screen.dart` | 公車查詢畫面 |
| `lib/screens/railway_screen.dart` | 台鐵查詢畫面 |
| `lib/screens/thsr_screen.dart` | 高鐵查詢畫面 |
| `lib/services/api_service.dart` | API 呼叫服務 |

---

## 🛠️ 後端技術棧

| 技術 | 用途 |
|------|------|
| **FastAPI** | Web 框架 |
| **Playwright** | 自動化瀏覽器爬蟲（高鐵、台鐵） |
| **httpx** | HTTP 客戶端 |
| **Pydantic** | 資料驗證 |
| **uvicorn** | ASGI 伺服器 |

### API 端點

#### 🔌 健康檢查
```
GET /api/health
```

#### 🚌 公車 API
| 端點 | 說明 | 參數 |
|------|------|------|
| `GET /api/bus/routes` | 取得公車路線列表 | `route_name` (可選) |
| `GET /api/bus/timetable/{route_id}` | 取得公車時刻表 | - |
| `GET /api/bus/realtime/{route_id}` | 取得公車即時到站 | `stop_name` (可選) |

#### 🚂 台鐵 API
| 端點 | 說明 | 參數 |
|------|------|------|
| `GET /api/railway/stations` | 取得台鐵車站列表 | - |
| `GET /api/railway/timetable` | 查詢台鐵時刻表 | `from_station`, `to_station`, `date`, `time` |

#### 🚄 高鐵 API
| 端點 | 說明 | 參數 |
|------|------|------|
| `GET /api/thsr/stations` | 取得高鐵車站列表 | - |
| `GET /api/thsr/timetable` | 查詢高鐵時刻表 | `from_station`, `to_station`, `date` |

### 台鐵車站代碼
| 代碼 | 站名 | 代碼 | 站名 |
|------|------|------|------|
| 108 | 台北 | 110 | 板橋 |
| 115 | 桃園 | 117 | 中壢 |
| 122 | 新竹 | 212 | 台中 |
| 217 | 彰化 | 220 | 員林 |
| 226 | 斗六 | 232 | 嘉義 |
| 244 | 台南 | 270 | 高雄 |
| 300 | 花蓮 | 326 | 台東 |

### 高鐵車站代碼
| 代碼 | 站名 |
|------|------|
| NAG | 南港 |
| TPE | 台北 |
| BAQ | 板橋 |
| TYC | 桃園 |
| HSC | 新竹 |
| MLC | 苗栗 |
| TCH | 台中 |
| CHU | 彰化 |
| YLH | 雲林 |
| CYI | 嘉義 |
| TNN | 台南 |
| ZUY | 左營 |

---

## 📱 Flutter App 技術棧

| 技術 | 用途 |
|------|------|
| **Flutter 3.x** | UI 框架 |
| **Dart** | 程式語言 |
| **http** | HTTP 客戶端 |
| **Provider** | 狀態管理 |
| **intl** | 日期/時間格式化 |
| **Material Design 3** | UI 設計系統 |

### 資料模型

```dart
// 公車路線
class BusRoute {
  final String routeId;
  final String routeName;
  final String departureStop;
  final String arrivalStop;
  final String operator;
}

// 火車站
class TrainStation {
  final String stationCode;
  final String stationName;
  final String stationNameEn;
}

// 台鐵時刻表
class TrainTimeEntry {
  final String trainNo;
  final String trainType;
  final String departureStation;
  final String arrivalStation;
  final String departureTime;
  final String arrivalTime;
  final String duration;
  final bool transferable;
}

// 高鐵時刻表
class THSRTrainEntry {
  final String trainNo;
  final String departureStation;
  final String arrivalStation;
  final String departureTime;
  final String arrivalTime;
  final String duration;
  final bool businessSeatAvailable;
  final bool standardSeatAvailable;
  final bool freeSeatAvailable;
}
```

---

## 🔧 編譯與安裝說明

### 後端伺服器

```bash
# 1. 進入後端目錄
cd backend

# 2. 建立虛擬環境
python3 -m venv venv

# 3. 啟動虛擬環境
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

# 4. 安裝依賴
pip install -r requirements.txt

# 5. 安裝 Playwright 瀏覽器
playwright install chromium
```

### Flutter App

```bash
# 1. 進入 Flutter 目錄
cd transport_flutter

# 2. 安裝依賴
flutter pub get

# 3. 執行 App (需要先啟動後端)
flutter run
```

---

## 🚀 如何啟動與測試

### 1. 啟動後端伺服器

```bash
cd backend
source venv/bin/activate  # 如果尚未啟動
python main.py
```

伺服器將在 `http://localhost:8000` 啟動

### 2. 測試 API

```bash
# 健康檢查
curl http://localhost:8000/api/health

# 取得公車路線
curl http://localhost:8000/api/bus/routes

# 取得台鐵車站
curl http://localhost:8000/api/railway/stations

# 查詢台鐵時刻表 (台北 → 台中)
curl "http://localhost:8000/api/railway/timetable?from_station=108&to_station=212"

# 查詢高鐵時刻表 (台北 → 台中)
curl "http://localhost:8000/api/thsr/timetable?from_station=TPE&to_station=TCH"
```

### 3. 啟動 Flutter App

```bash
cd transport_flutter

# Android 模擬器
flutter run -d emulator-5554

# iOS 模擬器
flutter run -d "iPhone 15"

# 指定後端 URL
# 修改 lib/services/api_service.dart 中的 baseUrl
```

### 環境設定

| 環境 | baseUrl 設定 |
|------|--------------|
| Android 模擬器 | `http://10.0.2.2:8000/api` |
| iOS 模擬器 | `http://localhost:8000/api` |
| 真機 (同一網域) | `http://<電腦IP>:8000/api` |

---

## 📋 已知問題與限制

1. **高鐵/台鐵爬蟲**：使用 Playwright 爬取官方網站，若官方網站改版可能需要更新爬蟲邏輯
2. **公車資料**：部分使用預設資料，實際資料由台北市 Open Data API 提供
3. **CORS**：後端已開放所有 CORS 來源用於開發環境

---

## 📄 授權

MIT License

---

## 🔗 相關連結

- [台灣高鐵](https://www.thsrc.com.tw/)
- [台灣鐵路管理局](https://www.railway.gov.tw/)
- [台北市公車資訊](https://www.5284.gov.taipei/)
- [台北市 Open Data](https://data.taipei/)
