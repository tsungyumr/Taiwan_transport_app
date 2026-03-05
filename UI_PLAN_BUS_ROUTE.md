# 台灣公車路線頁面 UI 規劃文件 - 藍15 等路線

## 專案位置
`/root/.openclaw/workspace-developer/taiwan-transport-app/transport_flutter/`

## 需求總結
- **單頁列表式**：垂直列表顯示所有站點
- **站點資訊**：
  - 站名
  - 狀態：`公車已離開` / `X分後到達` / `即將進站`
- **公車圖示**：
  - 多輛公車位置標示（列表中內嵌）
  - 即時位置：目前在第X站 / 前往第Y站
  - ETA (預計到達時間)
- **即時更新**：每30秒輪詢API

## 1. Wireframe 文字描述 + ASCII Art

### 描述
- **頂部**：路線標題 + 多輛公車即時摘要（水平滾動或卡片）
- **主體**：垂直ListView，每個站點為卡片式ListTile
  - 左側：站名 + 序號
  - 右側：狀態文字 + 顏色（綠=即將進站, 黃=等待, 灰=已離開）
  - 疊加：如果公車在此站或前往此站，顯示🚌圖示 + 動畫
- **底部**：最後更新時間 + 重新整理按鈕
- **滾動**：自動捲動到最近公車位置

### ASCII Art
```
┌─────────────────────────────────────┐
│ 🔄 藍15 公車路線 (台北 -> 板橋)     │
│ 🚌 bus1 @站3 →站4 (2min)  🚌 bus2 @站8│
└─────────────────────────────────────┘
│
│ ┌─────────────────────────────┐     🚌←目前公車
│ │ 01. 台北火車站              │
│ │   公車已離開                │
│ └─────────────────────────────┘
│
│ ┌─────────────────────────────┐
│ │ 02. 忠孝東路                │
│ │   即將進站 (1min)            │
│ └─────────────────────────────┘
│
│ ┌─────────────────────────────┐
│ │ 03. 民生西路                │
│ │   5分後到達                 │
│ └─────────────────────────────┘
│ ⋮ ⋮ ⋮ (共25站)
│
│ 🚌 bus1 即將抵達 → 前往站04
│
└─────────────────────────────────────┘
  最後更新: 2026-02-28 10:54  🔄重新整理
```

## 2. Flutter 畫面結構 (Widget 樹)

```
BusRoutePage (StatelessWidget, ConsumerWidget if Riverpod)
├── Scaffold
    ├── AppBar
    │   ├── title: '藍15 公車路線'
    │   └── actions: [RefreshButton]
    ├── body: Column
    │   ├── BusSummaryRow (Row with Chips for each bus)
    │   ├── Expanded: ListView.builder
    │   │   └── itemBuilder: StopListTile (for each stop)
    │   │       ├── Stack (for bus overlay)
    │   │       │   ├── Container (stop card)
    │   │       │   │   ├── Row
    │   │       │   │   │   ├── Column: stop index + name
    │   │       │   │   │   └── Column: status + ETA
    │   │       │   └── if bus here: Positioned 🚌 icon with pulse animation
    │   └── Container: last update + refresh
    └── floatingActionButton: Scroll to current bus
```

## 3. API 整合 - 新增端點 `/api/bus/{route}`

### 資料結構 (JSON)
```json
{
  "route": "藍15",
  "stops": [
    {"name": "台北火車站", "eta": "已離開"},
    {"name": "忠孝東路", "eta": "1min"},
    {"name": "民生西路", "eta": "5min"}
  ],
  "buses": [
    {"id": "bus1", "at_stop": 3, "eta_next": "2min", "heading_to": 4},
    {"id": "bus2", "at_stop": 8, "eta_next": "10min", "heading_to": 9}
  ]
}
```

### Backend 修改 (main.py 新增)
```python
from typing import Dict, Any
import random
from datetime import datetime

@app.get("/api/bus/{route}", response_model=Dict[str, Any])
async def get_bus_route_info(route: str):
    \"\"\"公車路線即時資料 (藍15 等)\"\"\"
    # Mock stops for 藍15 (real: from TaipeiBusScraper)
    stops = [
        {'name': f'站{i+1}: 站名{i+1}', 'eta': random.choice(['已離開', '即將進站', f'{random.randint(1,30)}min'])}
        for i in range(25)
    ]
    buses = [
        {'id': f'bus{j}', 'at_stop': random.randint(1, 25), 'eta_next': f'{random.randint(1,15)}min', 'heading_to': random.randint(1,26)}
        for j in range(1,4)
    ]
    return {
        'route': route,
        'stops': stops,
        'buses': buses,
        'updated': datetime.now().isoformat()
    }
```
- **新增位置**：在 TaipeiBusScraper 後，API 端點區塊。
- **真實整合**：未來連結 5284 API 或 PTX Open Data。

## 4. 實作代碼草稿 (lib/screens/bus_route_page.dart)

```dart
// 已寫入檔案: lib/screens/bus_route_page.dart
// 見下方工具呼叫結果
```

## 5. 狀態管理：使用 Provider (已存在於 pubspec.yaml)

### BusRouteNotifier (ChangeNotifier)
- 屬性：BusRouteData? data, DateTime? lastUpdated, String error
- 方法：fetchData(route), startPolling(), dispose()
- 每30秒自動輪詢 `/api/bus/{route}`

### 使用
```dart
Provider.of<BusRouteNotifier>(context, listen: true).data?.stops
ChangeNotifierProvider(create: (_) => BusRouteNotifier('藍15')..fetchData('藍15'))
```

### Models (lib/models/bus_route.dart)
```dart
class BusRouteData {
  final String route;
  final List<BusStop> stops;
  final List<BusVehicle> buses;
  final DateTime updated;
  // constructors, fromJson
}

class BusStop { String name; String eta; }
class BusVehicle { String id; int at_stop; String eta_next; int heading_to; }
```

## 實作檔案
- ✅ `lib/models/bus_route.dart`
- ✅ `lib/services/bus_api_service.dart` (HTTP client)
- ✅ `lib/screens/bus_route_page.dart`
- ✅ Backend: `/api/bus/{route}` endpoint 代碼草稿 (請手動新增至 main.py)
- 🔄 **下一步**：在 main.dart 加入導航 `Navigator.push(MaterialPageRoute(builder: (_) => BusRoutePage(route: '藍15')));`
- 🔄 執行 `flutter pub get` 後 `flutter run`

## 截圖概念
(未來 Canvas 或實際跑起來後產生)

**完成！** 此文件為完整規劃，可直接實作。
