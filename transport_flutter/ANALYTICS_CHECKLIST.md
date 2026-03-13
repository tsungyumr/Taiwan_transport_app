# Firebase Analytics 實作檢查清單

## ✅ 已完成項目

### 1. Analytics Widgets (`lib/widgets/analytics_widgets.dart`)
- ✅ `AnalyticsScreenTracking` mixin - 頁面瀏覽追蹤 + 停留時間
- ✅ `AnalyticsTabBar` - Tab 點擊追蹤
- ✅ `AnalyticsTabBarView` - Tab 切換和停留時間追蹤
- ✅ `AnalyticsButton` - 按鈕點擊追蹤
- ✅ `AnalyticsIconButton` - 圖示按鈕點擊追蹤
- ✅ `AnalyticsListTile` - 列表項目點擊追蹤
- ✅ `AnalyticsInkWell` - 點擊區域追蹤
- ✅ `AnalyticsTextField` - 文字輸入框焦點和搜尋追蹤
- ✅ `FeatureAnalytics` - 功能使用、搜尋、篩選、分享、導航、錯誤追蹤工具類別
- ✅ `UserAnalytics` - 使用者屬性設定工具類別

### 2. Firebase Service (`lib/services/firebase_service.dart`)
- ✅ `logEvent()` - 事件記錄
- ✅ `setCurrentScreen()` - 頁面瀏覽
- ✅ `setUserProperty()` - 使用者屬性
- ✅ `recordError()` - 錯誤記錄
- ✅ Crashlytics 整合

### 3. 畫面統計追蹤實作
- ✅ `bus_screen.dart` - 公車搜尋、路線選擇、清除歷史、頁面瀏覽追蹤
- ✅ `railway_screen.dart` - 台鐵時刻表搜尋、車站選擇、車種篩選追蹤
- ✅ `thsr_screen.dart` - 高鐵時刻表搜尋、車站選擇追蹤
- ✅ `bike_screen.dart` - YouBike 站點搜尋、站點選擇、地圖查看追蹤
- ✅ `bike_map_screen.dart` - 地圖站點搜尋、站點選擇追蹤
- ✅ `main_tab_screen.dart` - AI 規劃開始/完成/失敗/重試、遊戲空間、Tab 切換追蹤
- ✅ `settings_screen.dart` - 語言切換追蹤

---

## 📊 已實作的統計項目

### 第 1 優先：核心功能統計 ✅

#### 公車功能 (`bus_screen.dart`)
- ✅ 公車路線搜尋 (`search` 事件)
- ✅ 路線選擇 (`feature_use` 事件)
- ✅ 清除歷史 (`feature_use` 事件)
- ✅ 頁面瀏覽追蹤 (`AnalyticsScreenTracking`)

#### 台鐵功能 (`railway_screen.dart`)
- ✅ 時刻表搜尋 (`search` 事件)
- ✅ 出發站選擇 (`feature_use` 事件)
- ✅ 抵達站選擇 (`feature_use` 事件)
- ✅ 車種篩選 (`filter_use` 事件)

#### 高鐵功能 (`thsr_screen.dart`)
- ✅ 時刻表搜尋 (`search` 事件)
- ✅ 出發站選擇 (`feature_use` 事件)
- ✅ 抵達站選擇 (`feature_use` 事件)

#### YouBike 功能 (`bike_screen.dart`, `bike_map_screen.dart`)
- ✅ 站點搜尋 (`search` 事件)
- ✅ 站點選擇 (`feature_use` 事件)
- ✅ 地圖查看 (`feature_use` 事件)
- ✅ 地圖站點選擇 (`feature_use` 事件)
- ✅ 地圖搜尋 (`search` 事件)

### 第 2 優先：AI 功能統計 ✅

#### AI 規劃 (`main_tab_screen.dart`)
- ✅ AI 規劃開始 (`feature_use` 事件)
- ✅ AI 規劃完成 (`feature_use` 事件)
- ✅ AI 規劃失敗 (`feature_use` 事件)
- ✅ AI 重新規劃 (`feature_use` 事件)
- ✅ Tab 切換 (`feature_use` 事件)

### 第 3 優先：設定與其他 ✅

#### 設定頁面 (`settings_screen.dart`)
- ✅ 語言切換 (`feature_use` 事件 + `UserAnalytics.setLanguage`)

#### 遊戲空間 (`main_tab_screen.dart`)
- ✅ 遊戲空間點擊 (`feature_use` 事件)

---

## 📊 已實作的統計項目

### 核心功能統計 ✅

| 功能 | 檔案 | 追蹤項目 |
|------|------|----------|
| 公車 | `bus_screen.dart` | 路線搜尋、路線選擇、清除歷史、頁面瀏覽 |
| 台鐵 | `railway_screen.dart` | 時刻表搜尋、車站選擇、車種篩選 |
| 高鐵 | `thsr_screen.dart` | 時刻表搜尋、車站選擇 |
| YouBike | `bike_screen.dart` | 站點搜尋、站點選擇、地圖查看 |
| YouBike 地圖 | `bike_map_screen.dart` | 地圖搜尋、地圖站點選擇 |

### AI 功能統計 ✅

| 功能 | 檔案 | 追蹤項目 |
|------|------|----------|
| AI 規劃 | `main_tab_screen.dart` | 規劃開始、規劃完成、規劃失敗、重新規劃 |
| Tab 切換 | `main_tab_screen.dart` | Tab 切換事件 |

### 使用者行為統計 ✅

| 功能 | 檔案 | 追蹤項目 |
|------|------|----------|
| 語言切換 | `settings_screen.dart` | 語言變更、使用者屬性更新 |
| 遊戲空間 | `main_tab_screen.dart` | 遊戲空間點擊 |

---

## 🔍 事件類型總覽

### search 事件
- `bus_route` - 公車路線搜尋
- `tra_timetable` - 台鐵時刻表搜尋
- `thsr_timetable` - 高鐵時刻表搜尋
- `bike_station` - YouBike 站點搜尋
- `bike_map_station` - YouBike 地圖搜尋

### feature_use 事件
- `view_bus_route` - 查看公車路線
- `clear_bus_history` - 清除公車歷史
- `select_tra_station` - 選擇台鐵車站
- `select_thsr_station` - 選擇高鐵車站
- `view_bike_station` - 查看 YouBike 站點
- `bike_map_view` - 查看 YouBike 地圖
- `bike_map_station_select` - 選擇地圖站點
- `ai_plan_start` - AI 規劃開始
- `ai_plan_complete` - AI 規劃完成
- `ai_plan_failed` - AI 規劃失敗
- `ai_plan_retry` - AI 重新規劃
- `game_space_click` - 遊戲空間點擊
- `change_language` - 語言切換
- `tab_switch` - Tab 切換

### filter_use 事件
- `train_type` - 車種篩選

### screen_view 事件（由 AnalyticsScreenTracking mixin 自動追蹤）
- `BusScreen` - 公車頁面瀏覽

---

## 🔧 測試驗證

1. **使用 Firebase Console DebugView**
   - 開啟 App 並操作各項功能
   - 在 DebugView 中確認事件正確發送

2. **確認事件參數**
   - 檢查 `search` 事件的 `query` 和 `result_count`
   - 檢查 `feature_use` 事件的 `feature_name` 和 `feature_type`
   - 檢查 `filter_use` 事件的 `filter_type` 和 `filter_value`

3. **驗證使用者屬性**
   - 切換語言後檢查 `preferred_language` 屬性

---

## 📝 注意事項

1. **避免過度追蹤**
   - 搜尋事件只在有查詢字串時發送
   - 相同操作在短時間內不會重複追蹤

2. **參數命名規範**
   - 使用 snake_case
   - 事件名稱長度不超過 40 字元
   - 參數值長度不超過 100 字元

3. **隱私保護**
   - 不追蹤個人識別資訊
   - 不追蹤精確位置
   - 所有追蹤均為匿名
