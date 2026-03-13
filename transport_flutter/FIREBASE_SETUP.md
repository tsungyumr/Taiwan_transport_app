# Firebase 整合使用說明

這份文件說明如何在台灣交通時刻表 App 中使用 Firebase Crashlytics 和 Analytics。

## 已完成設定

### 1. pubspec.yaml
已添加以下 Firebase 依賴：
- `firebase_core: ^3.12.0` - Firebase 核心
- `firebase_crashlytics: ^4.3.4` - 崩潰報告
- `firebase_analytics: ^11.4.3` - 分析追蹤

### 2. Android 設定
- `android/build.gradle` - 已添加 Firebase 插件
- `android/app/build.gradle` - 已應用 Firebase 插件
- `android/app/google-services.json` - 需要填入您的 Firebase 設定

### 3. iOS 設定
- `ios/Runner/GoogleService-Info.plist` - 需要填入您的 Firebase 設定

### 4. Dart 程式碼
- `lib/services/firebase_service.dart` - Firebase 服務類別
- `lib/firebase_options.dart` - Firebase 設定選項
- `lib/main.dart` - 已更新為初始化 Firebase

## 後續步驟

### 1. 設定 Firebase 專案

1. 前往 [Firebase Console](https://console.firebase.google.com/)
2. 建立新專案或選擇現有專案
3. 添加 Android 應用程式：
   - 套件名稱：`com.zaizaicat.transportapp`
   - 下載 `google-services.json` 並替換 `android/app/google-services.json`
4. 添加 iOS 應用程式：
   - Bundle ID：`com.zaizaicat.transportapp`
   - 下載 `GoogleService-Info.plist` 並替換 `ios/Runner/GoogleService-Info.plist`

### 2. 產生 Firebase 設定檔案

執行 FlutterFire CLI：

```bash
# 安裝 FlutterFire CLI
dart pub global activate flutterfire_cli

# 產生設定檔案
flutterfire configure --project=YOUR_FIREBASE_PROJECT_ID
```

這會自動產生 `lib/firebase_options.dart` 檔案。

### 3. 安裝依賴

```bash
cd transport_flutter
flutter pub get
```

## 使用範例

### 在畫面中追蹤頁面瀏覽

```dart
import 'package:flutter/material.dart';
import 'services/firebase_service.dart';

class MyScreen extends StatefulWidget {
  @override
  void initState() {
    super.initState();
    // 追蹤頁面瀏覽
    firebaseService.setCurrentScreen(screenName: 'MyScreen');
  }
  // ...
}
```

### 記錄自訂事件

```dart
// 追蹤交通搜尋
firebaseService.logTransportSearch(
  transportType: 'railway',
  fromStation: '台北',
  toStation: '台中',
);

// 追蹤路線查詢
firebaseService.logRouteQuery(
  routeName: '307',
  city: 'Taipei',
);

// 追蹤一般事件
firebaseService.logEvent(
  eventName: 'button_click',
  parameters: {'button_name': 'search'},
);
```

### 記錄錯誤

```dart
try {
  // 某些可能失敗的操作
  await fetchData();
} catch (e, stack) {
  // 記錄到 Crashlytics
  await firebaseService.recordError(
    e,
    stack,
    reason: '資料載入失敗',
  );
  // 同時記錄到 Analytics
  firebaseService.logAppError(
    errorType: 'network_error',
    errorMessage: e.toString(),
  );
}
```

### 設定使用者識別

```dart
// 登入後設定使用者 ID
await firebaseService.setUserIdentifier('user_12345');

// 設定自訂鍵值
await firebaseService.setCustomKey('user_type', 'premium');
```

## Crashlytics 功能

### 自動錯誤收集
- Flutter 框架錯誤會自動記錄
- 非同步錯誤會自動記錄
- 在正式環境中自動啟用，開發環境中停用

### 測試崩潰
```dart
// 測試崩潰（僅用於開發）
firebaseService.testCrash();

// 測試非同步崩潰
firebaseService.testAsyncCrash();
```

## Analytics 事件

### 預定義事件
- `transport_search` - 交通搜尋
- `route_query` - 路線查詢
- `app_error` - 應用程式錯誤

### 自訂事件
```dart
firebaseService.logEvent(
  eventName: 'custom_event',
  parameters: {
    'param1': 'value1',
    'param2': 123,
  },
);
```

事件命名規則：
- 只能包含字母、數字和下劃線
- 必須以字母開頭
- 最多 40 個字元
- 不允許前導空白或預留名稱

## 查看數據

### Crashlytics 數據
- 前往 Firebase Console → Crashlytics
- 查看崩潰報告、錯誤趨勢
- 檢視堆疊追蹤和裝置資訊

### Analytics 數據
- 前往 Firebase Console → Analytics
- 查看即時數據、使用者行為
- 建立自訂報表

## 注意事項

1. **開發 vs 正式環境**：
   - 開發環境中 Crashlytics 不會自動收集錯誤
   - Analytics 在所有環境中都會收集

2. **網路連線**：
   - Firebase 需要網路連線才能上傳數據
   - 離線時數據會在本地佇列，連線後上傳

3. **隱私合規**：
   - 確保遵守 GDPR、CCPA 等隱私法規
   - 提供使用者選擇退出追蹤的選項

## 疑難排解

### Firebase 初始化失敗
- 檢查 `google-services.json` / `GoogleService-Info.plist` 是否正確放置
- 確認套件名稱/Bundle ID 與 Firebase 專案設定相符
- 查看 Logcat/Xcode 控制台錯誤訊息

### 看不到 Analytics 數據
- Analytics 數據可能有數小時延遲
- 使用「即時」標籤查看最近活動
- 確認事件名稱符合命名規則

### Crashlytics 不顯示崩潰
- 首次設定後可能需要強制停止並重新啟動應用
- 測試時使用 `testCrash()` 方法
- 檢查是否為 debug 模式（debug 模式下不自動收集）
