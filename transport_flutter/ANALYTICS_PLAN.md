# Firebase Analytics 統計追蹤規劃

## 目前已完成的統計

### 1. 基礎頁面瀏覽追蹤 ✅
- 使用 `AnalyticsScreenTracking` mixin 追蹤頁面瀏覽
- 自動計算頁面停留時間

### 2. 元件級追蹤 ✅
- `AnalyticsTabBar` - tab 點擊和切換追蹤
- `AnalyticsTabBarView` - tab 停留時間追蹤
- `AnalyticsButton` - 按鈕點擊追蹤
- `AnalyticsIconButton` - 圖示按鈕點擊追蹤
- `AnalyticsListTile` - 列表項目點擊追蹤
- `AnalyticsInkWell` - 點擊區域追蹤
- `AnalyticsTextField` - 文字輸入框焦點和搜尋追蹤

### 3. 功能工具類別 ✅
- `FeatureAnalytics` - 功能使用、搜尋、篩選、分享、導航、錯誤追蹤
- `UserAnalytics` - 使用者屬性設定

---

## 建議新增的統計追蹤

### A. App 生命週期統計

#### 1. App 安裝/首次啟動
```dart
// main.dart 中在 Firebase 初始化後追蹤
firebaseService.logEvent(
  name: 'app_first_open',
  parameters: {
    'install_source': 'organic', // 或從 platform 取得
    'app_version': '1.0.0',
    'os_version': 'Android 14',
  },
);
```

#### 2. App 啟動/喚醒
```dart
// 每次 App 從背景回到前景時
firebaseService.logEvent(
  name: 'app_open',
  parameters: {
    'time_since_last_open': '3600', // 秒數
  },
);
```

#### 3. App 背景化/結束
```dart
// App 進入背景時
firebaseService.logEvent(
  name: 'app_background',
  parameters: {
    'session_duration': '300', // 秒數
  },
);
```

### B. 交通功能詳細統計

#### 公車功能
```dart
// 公車路線搜尋
FeatureAnalytics.trackSearch(
  searchType: 'bus_route',
  query: '307',
  resultCount: 5,
);

// 公車站點查看
FeatureAnalytics.trackFeatureUse(
  featureName: 'bus_stop_detail',
  featureType: 'bus',
  parameters: {
    'route_id': '12345',
    'stop_name': '台北車站',
  },
);

// 公車即時位置查看
FeatureAnalytics.trackFeatureUse(
  featureName: 'bus_realtime',
  featureType: 'bus',
  parameters: {
    'route_id': '12345',
  },
);

// 公車加入收藏
FeatureAnalytics.trackFeatureUse(
  featureName: 'bus_add_favorite',
  featureType: 'bus',
);
```

#### 台鐵功能
```dart
// 時刻表搜尋
FeatureAnalytics.trackSearch(
  searchType: 'tra_timetable',
  query: '台北-台中',
  resultCount: 25,
);

// 車站選擇
FeatureAnalytics.trackFeatureUse(
  featureName: 'select_station',
  featureType: 'tra',
  parameters: {
    'station_type': 'from',
    'station_name': '台北車站',
  },
);

// 時刻表篩選（車種）
FeatureAnalytics.trackFilter(
  filterType: 'train_type',
  filterValue: 'express',
);
```

#### 高鐵功能
```dart
// 高鐵時刻表搜尋
FeatureAnalytics.trackSearch(
  searchType: 'thsr_timetable',
  query: '台北-左營',
  resultCount: 12,
);

// 高鐵座位查詢
FeatureAnalytics.trackFeatureUse(
  featureName: 'thsr_seat_query',
  featureType: 'thsr',
  parameters: {
    'train_no': '123',
  },
);
```

#### YouBike 功能
```dart
// YouBike 站點搜尋
FeatureAnalytics.trackSearch(
  searchType: 'bike_station',
  query: '台北車站',
  resultCount: 8,
);

// YouBike 地圖查看
FeatureAnalytics.trackFeatureUse(
  featureName: 'bike_map_view',
  featureType: 'bike',
);

// YouBike 導航
FeatureAnalytics.trackFeatureUse(
  featureName: 'bike_navigation',
  featureType: 'bike',
  parameters: {
    'station_name': '捷運台北車站',
  },
);

// YouBike 站點加入收藏
FeatureAnalytics.trackFeatureUse(
  featureName: 'bike_add_favorite',
  featureType: 'bike',
);
```

### C. AI 規劃功能統計

```dart
// AI 規劃開始
FeatureAnalytics.trackFeatureUse(
  featureName: 'ai_plan_start',
  featureType: 'ai',
);

// AI 規劃完成（成功）
FeatureAnalytics.trackFeatureUse(
  featureName: 'ai_plan_complete',
  featureType: 'ai',
  parameters: {
    'duration_seconds': '15',
    'from_location': '台北市',
    'to_location': '台中市',
  },
);

// AI 規劃失敗
FeatureAnalytics.trackFeatureUse(
  featureName: 'ai_plan_failed',
  featureType: 'ai',
  parameters: {
    'error_type': 'timeout',
  },
);

// AI 重新規劃
FeatureAnalytics.trackFeatureUse(
  featureName: 'ai_plan_retry',
  featureType: 'ai',
);

// AI 結果分享
FeatureAnalytics.trackShare(
  contentType: 'ai_plan_result',
  contentId: 'plan_12345',
  method: 'clipboard', // 或 'social', 'email' 等
);
```

### D. 使用者行為統計

#### 1. 語言切換
```dart
// 在 SettingsScreen 中
FeatureAnalytics.trackFeatureUse(
  featureName: 'change_language',
  featureType: 'settings',
  parameters: {
    'from_language': 'zh',
    'to_language': 'en',
  },
);

// 設定使用者屬性
UserAnalytics.setLanguage('zh');
```

#### 2. 收藏功能
```dart
// 加入收藏
FeatureAnalytics.trackFeatureUse(
  featureName: 'add_to_favorites',
  featureType: 'user_action',
  parameters: {
    'item_type': 'bus_route',
    'item_id': '12345',
  },
);

// 移除收藏
FeatureAnalytics.trackFeatureUse(
  featureName: 'remove_from_favorites',
  featureType: 'user_action',
  parameters: {
    'item_type': 'bus_route',
    'item_id': '12345',
  },
);
```

#### 3. 搜尋歷史
```dart
// 清除搜尋歷史
FeatureAnalytics.trackFeatureUse(
  featureName: 'clear_search_history',
  featureType: 'user_action',
  parameters: {
    'item_count': '10',
  },
);
```

### E. 錯誤統計

```dart
// API 錯誤
FeatureAnalytics.trackError(
  errorType: 'api_error',
  errorMessage: 'TDX API timeout',
  screenName: 'BusScreen',
);

// 網路錯誤
FeatureAnalytics.trackError(
  errorType: 'network_error',
  errorMessage: 'No connection',
);

// 定位錯誤
FeatureAnalytics.trackError(
  errorType: 'location_error',
  errorMessage: 'Permission denied',
);
```

### F. 效能統計

```dart
// 頁面載入時間
FeatureAnalytics.trackFeatureUse(
  featureName: 'page_load_time',
  featureType: 'performance',
  parameters: {
    'screen_name': 'BusScreen',
    'load_time_ms': '500',
  },
);

// API 回應時間
FeatureAnalytics.trackFeatureUse(
  featureName: 'api_response_time',
  featureType: 'performance',
  parameters: {
    'api_name': 'bus_routes',
    'response_time_ms': '300',
  },
);
```

---

## 建議實作優先順序

### 第一階段（核心功能）
1. ✅ 頁面瀏覽追蹤
2. ✅ Tab 切換追蹤
3. 🔄 交通搜尋追蹤（公車、台鐵、高鐵、YouBike）
4. 🔄 時刻表查詢追蹤

### 第二階段（使用者行為）
5. 🔄 收藏功能追蹤
6. 🔄 搜尋歷史追蹤
7. 🔄 設定變更追蹤

### 第三階段（進階分析）
8. 🔄 AI 規劃追蹤
9. 🔄 錯誤追蹤
10. 🔄 效能追蹤

---

## 實作注意事項

### 1. 避免過度追蹤
- 每次使用者操作只追蹤一次
- 避免在迴圈中重複追蹤
- 設定最小追蹤間隔（例如同一按鈕 5 秒內不重複追蹤）

### 2. 參數命名規範
- 使用 snake_case
- 避免特殊字元
- 長度限制：事件名稱 40 字元，參數名稱 40 字元，參數值 100 字元

### 3. 隱私保護
- 不要追蹤個人識別資訊
- 不要追蹤精確位置（只追蹤城市級別）
- 提供使用者選擇退出選項

### 4. 測試驗證
- 使用 Firebase DebugView 即時檢視事件
- 確認事件在 Console 中正確顯示
- 驗證參數值是否符合預期
