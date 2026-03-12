// ai_planning_service.dart
// AI 規劃服務 - 整合後端 API 取得附近站點資訊

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/material.dart';
import '../services/gemini_webview_service.dart';

/// 附近站點資訊模型
class NearbyStations {
  final List<StationInfo> busStops;
  final List<StationInfo> railwayStations;
  final List<StationInfo> thsrStations;
  final List<StationInfo> bikeStations;

  NearbyStations({
    required this.busStops,
    required this.railwayStations,
    required this.thsrStations,
    required this.bikeStations,
  });

  /// 檢查是否有任何站點資訊
  bool get hasAnyStations {
    return busStops.isNotEmpty ||
        railwayStations.isNotEmpty ||
        thsrStations.isNotEmpty ||
        bikeStations.isNotEmpty;
  }
}

/// 站點基本資訊
class StationInfo {
  final String id;
  final String name;
  final double? latitude;
  final double? longitude;
  final double? distance; // 與查詢點的距離（公里）
  final String? extraInfo; // 額外資訊（如公車路線、剩餘腳踏車數等）

  StationInfo({
    required this.id,
    required this.name,
    this.latitude,
    this.longitude,
    this.distance,
    this.extraInfo,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'latitude': latitude,
      'longitude': longitude,
      'distance': distance,
      'extraInfo': extraInfo,
    };
  }
}

/// AI 規劃服務
/// 負責呼叫後端 API 取得附近站點並生成完整 Prompt
class AIPlanningService {
  static const String _baseUrl = 'http://10.0.2.2:8001/api';

  final http.Client _client = http.Client();

  /// 解析座標字串
  /// 支援格式："25.0330, 121.5654" 或 "台北車站"
  static Map<String, double>? parseCoordinates(String location) {
    // 嘗試解析 "lat, lng" 格式
    final coordPattern = RegExp(r'([\d.]+)\s*,\s*([\d.]+)');
    final match = coordPattern.firstMatch(location);

    if (match != null) {
      final lat = double.tryParse(match.group(1) ?? '');
      final lng = double.tryParse(match.group(2) ?? '');
      if (lat != null && lng != null) {
        return {'lat': lat, 'lng': lng};
      }
    }
    return null;
  }

  /// 取得附近所有站點資訊
  /// [location] 可以是座標 "25.0330, 121.5654" 或地名
  Future<NearbyStations> getNearbyStations(String location) async {
    debugPrint('正在取得附近站點: $location');

    // 解析座標
    final coords = parseCoordinates(location);

    try {
      // 並行取得所有類型的站點
      final results = await Future.wait([
        _getNearbyBusStops(location, coords),
        _getNearbyRailwayStations(location, coords),
        _getNearbyTHSRStations(location, coords),
        _getNearbyBikeStations(location, coords),
      ]);

      return NearbyStations(
        busStops: results[0],
        railwayStations: results[1],
        thsrStations: results[2],
        bikeStations: results[3],
      );
    } catch (e) {
      debugPrint('取得附近站點失敗: $e');
      // 返回空結果，讓 AI 只根據地名規劃
      return NearbyStations(
        busStops: [],
        railwayStations: [],
        thsrStations: [],
        bikeStations: [],
      );
    }
  }

  /// 取得附近公車站點
  Future<List<StationInfo>> _getNearbyBusStops(
    String location,
    Map<String, double>? coords,
  ) async {
    try {
      // 如果有座標，使用附近站點 API
      if (coords != null) {
        final uri = Uri.parse('$_baseUrl/bus/stops/nearby').replace(
          queryParameters: {
            'lat': coords['lat'].toString(),
            'lon': coords['lng'].toString(),
            'radius': '1000', // 1公里範圍
          },
        );

        final response = await _client.get(uri);
        if (response.statusCode == 200) {
          final data = json.decode(response.body);
          return _parseBusStops(data);
        }
      }

      // 否則取得所有路線（簡化處理）
      final response = await _client.get(Uri.parse('$_baseUrl/bus/routes'));
      if (response.statusCode == 200) {
        final List<dynamic> routes = json.decode(response.body);
        // 取前 10 條路線作為參考
        return routes.take(10).map((route) => StationInfo(
          id: route['route_id'] ?? '',
          name: route['route_name'] ?? '',
          extraInfo: '${route['departure_stop'] ?? ''} - ${route['arrival_stop'] ?? ''}',
        )).toList();
      }
    } catch (e) {
      debugPrint('取得公車站點失敗: $e');
    }
    return [];
  }

  /// 取得附近台鐵站點
  Future<List<StationInfo>> _getNearbyRailwayStations(
    String location,
    Map<String, double>? coords,
  ) async {
    try {
      // 取得所有台鐵站點
      final response = await _client.get(Uri.parse('$_baseUrl/railway/stations'));
      if (response.statusCode == 200) {
        final List<dynamic> stations = json.decode(response.body);

        // 如果有座標，計算距離並排序
        if (coords != null) {
          final stationList = stations.map((s) {
            final lat = (s['latitude'] as num?)?.toDouble();
            final lng = (s['longitude'] as num?)?.toDouble();
            final distance = lat != null && lng != null
                ? _calculateDistance(coords['lat']!, coords['lng']!, lat, lng)
                : null;

            return StationInfo(
              id: s['station_code'] ?? s['code'] ?? '',
              name: s['station_name'] ?? s['name'] ?? '',
              latitude: lat,
              longitude: lng,
              distance: distance,
            );
          }).toList();

          // 按距離排序，取最近的 5 個
          stationList.sort((a, b) {
            if (a.distance == null) return 1;
            if (b.distance == null) return -1;
            return a.distance!.compareTo(b.distance!);
          });

          return stationList.where((s) => s.distance != null && s.distance! < 10).take(5).toList();
        }

        // 如果沒有座標，返回主要站點
        return stations
            .where((s) {
              final name = s['station_name'] ?? s['name'] ?? '';
              return name.contains('台北') ||
                  name.contains('台中') ||
                  name.contains('高雄') ||
                  name.contains('板橋') ||
                  name.contains('南港');
            })
            .take(5)
            .map((s) => StationInfo(
              id: s['station_code'] ?? s['code'] ?? '',
              name: s['station_name'] ?? s['name'] ?? '',
            ))
            .toList();
      }
    } catch (e) {
      debugPrint('取得台鐵站點失敗: $e');
    }
    return [];
  }

  /// 取得附近高鐵站點
  Future<List<StationInfo>> _getNearbyTHSRStations(
    String location,
    Map<String, double>? coords,
  ) async {
    try {
      final response = await _client.get(Uri.parse('$_baseUrl/thsr/stations'));
      if (response.statusCode == 200) {
        final List<dynamic> stations = json.decode(response.body);

        // 如果有座標，計算距離並排序
        if (coords != null) {
          final stationList = stations.map((s) {
            final lat = (s['latitude'] as num?)?.toDouble();
            final lng = (s['longitude'] as num?)?.toDouble();
            final distance = lat != null && lng != null
                ? _calculateDistance(coords['lat']!, coords['lng']!, lat, lng)
                : null;

            return StationInfo(
              id: s['station_code'] ?? s['code'] ?? '',
              name: s['station_name'] ?? s['name'] ?? '',
              latitude: lat,
              longitude: lng,
              distance: distance,
            );
          }).toList();

          // 按距離排序，取最近的 3 個
          stationList.sort((a, b) {
            if (a.distance == null) return 1;
            if (b.distance == null) return -1;
            return a.distance!.compareTo(b.distance!);
          });

          return stationList.where((s) => s.distance != null && s.distance! < 20).take(3).toList();
        }

        // 如果沒有座標，返回所有高鐵站（只有 12 個）
        return stations
            .map((s) => StationInfo(
              id: s['station_code'] ?? s['code'] ?? '',
              name: s['station_name'] ?? s['name'] ?? '',
            ))
            .toList();
      }
    } catch (e) {
      debugPrint('取得高鐵站點失敗: $e');
    }
    return [];
  }

  /// 取得附近腳踏車站點
  Future<List<StationInfo>> _getNearbyBikeStations(
    String location,
    Map<String, double>? coords,
  ) async {
    try {
      if (coords != null) {
        final uri = Uri.parse('$_baseUrl/bike/stations/nearby').replace(
          queryParameters: {
            'lat': coords['lat'].toString(),
            'lon': coords['lng'].toString(),
            'radius': '1000', // 1公里範圍
            'city': 'Taipei',
            'limit': '10',
          },
        );

        final response = await _client.get(uri);
        if (response.statusCode == 200) {
          final data = json.decode(response.body);
          if (data is Map<String, dynamic> && data['data'] is List) {
            final List<dynamic> stations = data['data'];
            return stations.map((s) => StationInfo(
              id: s['station_uid'] ?? s['station_id'] ?? '',
              name: s['name'] ?? '',
              latitude: (s['latitude'] ?? s['lat'])?.toDouble(),
              longitude: (s['longitude'] ?? s['lng'])?.toDouble(),
              distance: (s['distance'] as num?)?.toDouble(),
              extraInfo: '可借 ${s['available_rent_bikes'] ?? s['available_bikes'] ?? '?'} 輛',
            )).toList();
          }
        }
      }
    } catch (e) {
      debugPrint('取得腳踏車站點失敗: $e');
    }
    return [];
  }

  /// 解析公車站點資料
  /// 新的 API 回傳格式包含 route_id, route_name, departure, destination
  List<StationInfo> _parseBusStops(dynamic data) {
    if (data is Map<String, dynamic> && data['stops'] is List) {
      final stops = data['stops'] as List;
      return stops.take(10).map((stop) => StationInfo(
        id: stop['stop_id'] ?? stop['id'] ?? '',
        name: stop['name'] ?? stop['stop_name'] ?? '',
        latitude: (stop['latitude'] ?? stop['lat'])?.toDouble(),
        longitude: (stop['longitude'] ?? stop['lng'])?.toDouble(),
        distance: (stop['distance'] as num?)?.toDouble(),
        // 包含路線資訊在 extraInfo 中
        extraInfo: '${stop['route_name'] ?? ''} (${stop['departure'] ?? ''} - ${stop['destination'] ?? ''})',
      )).toList();
    }
    // 相容舊格式
    if (data is List) {
      return data.take(5).map((stop) => StationInfo(
        id: stop['stop_id'] ?? stop['id'] ?? '',
        name: stop['stop_name'] ?? stop['name'] ?? '',
        latitude: (stop['latitude'] ?? stop['lat'])?.toDouble(),
        longitude: (stop['longitude'] ?? stop['lng'])?.toDouble(),
        distance: (stop['distance'] as num?)?.toDouble(),
      )).toList();
    }
    return [];
  }

  /// 計算兩點間的距離（使用 Haversine 公式）
  double _calculateDistance(double lat1, double lng1, double lat2, double lng2) {
    const earthRadius = 6371; // 地球半徑（公里）

    final dLat = _degreesToRadians(lat2 - lat1);
    final dLng = _degreesToRadians(lng2 - lng1);

    final a =
        (dLat / 2).sin() * (dLat / 2).sin() +
        _degreesToRadians(lat1).cos() *
            _degreesToRadians(lat2).cos() *
            (dLng / 2).sin() *
            (dLng / 2).sin();

    final c = 2 * a.sqrt().asin();

    return earthRadius * c;
  }

  double _degreesToRadians(double degrees) {
    return degrees * 3.141592653589793 / 180;
  }

  /// 從公車站點的 extraInfo 中提取路線名稱
  /// extraInfo 格式: "路線名稱 (起點 - 終點)"
  String? _extractRouteName(String? extraInfo) {
    if (extraInfo == null || extraInfo.isEmpty) return null;
    // 提取括號前的路線名稱
    final match = RegExp(r'^(.+?)\s*\(').firstMatch(extraInfo);
    return match?.group(1)?.trim() ?? extraInfo;
  }

  /// 找出出發地和目的地都有的公車路線
  List<String?> _findCommonBusRoutes(
    List<StationInfo> fromBusStops,
    List<StationInfo> toBusStops,
  ) {
    // 提取出發地的所有路線名稱
    final fromRoutes = fromBusStops
        .map((stop) => _extractRouteName(stop.extraInfo))
        .where((route) => route != null && route.isNotEmpty)
        .toSet();

    // 提取目的地的所有路線名稱
    final toRoutes = toBusStops
        .map((stop) => _extractRouteName(stop.extraInfo))
        .where((route) => route != null && route.isNotEmpty)
        .toSet();

    // 找出交集
    final commonRoutes = fromRoutes.intersection(toRoutes).toList();
    return commonRoutes;
  }

  /// 生成完整的 AI 規劃 Prompt
  String generateEnhancedPrompt({
    required String fromLocation,
    required String toLocation,
    required NearbyStations fromStations,
    required NearbyStations toStations,
    String language = 'zh', // 新增語言參數，預設繁體中文
  }) {
    final buffer = StringBuffer();

    // 根據語言決定回覆語言要求
    final languageInstruction = language == 'en'
        ? '請用「英文」回答我。'
        : '請用「繁體中文」回答我。';

    buffer.writeln('請幫我規劃從「$fromLocation」到「$toLocation」的最佳大眾交通工具搭乘方案。');
    buffer.writeln();

    // 出發地附近站點
    if (fromStations.hasAnyStations) {
      buffer.writeln('【出發地附近交通資訊】');

      if (fromStations.busStops.isNotEmpty) {
        // 收集所有公車路線號碼
        final fromRoutes = fromStations.busStops
            .map((stop) => _extractRouteName(stop.extraInfo))
            .where((route) => route != null && route.isNotEmpty)
            .toSet()
            .toList();

        if (fromRoutes.isNotEmpty) {
          buffer.writeln('🚌 可搭乘公車：${fromRoutes.join('、')}');
          buffer.writeln();
        }

        buffer.writeln('附近公車站點：');
        for (final stop in fromStations.busStops.take(5)) {
          final distanceStr = stop.distance != null ? ' (${stop.distance!.toStringAsFixed(0)}m)' : '';
          buffer.writeln('- ${stop.name}$distanceStr');
        }
      }

      if (fromStations.railwayStations.isNotEmpty) {
        buffer.writeln('台鐵：');
        for (final station in fromStations.railwayStations.take(3)) {
          buffer.writeln('- ${station.name}${station.distance != null ? ' (${station.distance!.toStringAsFixed(1)}km)' : ''}');
        }
      }

      if (fromStations.thsrStations.isNotEmpty) {
        buffer.writeln('高鐵：');
        for (final station in fromStations.thsrStations.take(2)) {
          buffer.writeln('- ${station.name}${station.distance != null ? ' (${station.distance!.toStringAsFixed(1)}km)' : ''}');
        }
      }

      if (fromStations.bikeStations.isNotEmpty) {
        buffer.writeln('🚲 YouBike 租借站：');
        for (final station in fromStations.bikeStations.take(5)) {
          final distanceStr = station.distance != null ? ' (${station.distance!.toStringAsFixed(0)}m)' : '';
          final bikeInfo = station.extraInfo != null && station.extraInfo!.isNotEmpty
              ? ' - ${station.extraInfo}'
              : '';
          buffer.writeln('- ${station.name}$distanceStr$bikeInfo');
        }
      }

      buffer.writeln();
    }

    // 目的地附近站點
    if (toStations.hasAnyStations) {
      buffer.writeln('【目的地附近交通資訊】');

      if (toStations.busStops.isNotEmpty) {
        // 收集所有公車路線號碼
        final toRoutes = toStations.busStops
            .map((stop) => _extractRouteName(stop.extraInfo))
            .where((route) => route != null && route.isNotEmpty)
            .toSet()
            .toList();

        if (toRoutes.isNotEmpty) {
          buffer.writeln('🚌 可搭乘公車：${toRoutes.join('、')}');
          buffer.writeln();
        }

        buffer.writeln('附近公車站點：');
        for (final stop in toStations.busStops.take(5)) {
          final distanceStr = stop.distance != null ? ' (${stop.distance!.toStringAsFixed(0)}m)' : '';
          buffer.writeln('- ${stop.name}$distanceStr');
        }
      }

      if (toStations.railwayStations.isNotEmpty) {
        buffer.writeln('台鐵：');
        for (final station in toStations.railwayStations.take(3)) {
          buffer.writeln('- ${station.name}${station.distance != null ? ' (${station.distance!.toStringAsFixed(1)}km)' : ''}');
        }
      }

      if (toStations.thsrStations.isNotEmpty) {
        buffer.writeln('高鐵：');
        for (final station in toStations.thsrStations.take(2)) {
          buffer.writeln('- ${station.name}${station.distance != null ? ' (${station.distance!.toStringAsFixed(1)}km)' : ''}');
        }
      }

      if (toStations.bikeStations.isNotEmpty) {
        buffer.writeln('🚲 YouBike 租借站：');
        for (final station in toStations.bikeStations.take(5)) {
          final distanceStr = station.distance != null ? ' (${station.distance!.toStringAsFixed(0)}m)' : '';
          final bikeInfo = station.extraInfo != null && station.extraInfo!.isNotEmpty
              ? ' - ${station.extraInfo}'
              : '';
          buffer.writeln('- ${station.name}$distanceStr$bikeInfo');
        }
      }

      buffer.writeln();
    }

    buffer.writeln('請根據以上資訊，提供以下內容：');
    buffer.writeln('1. 列出所有可行的交通方式組合（請列出 3-4 個不同方案），評估時請同時考量捷運(MRT)路線：');
    buffer.writeln('   - 第一個方案請標示「(推薦)」，這是最佳/最快速的方案');
    buffer.writeln('   - 其他方案依便利性或時間排序');
    buffer.writeln('   - 每個方案請包含：預估總時間、預估費用、詳細轉乘步驟');
    buffer.writeln('   - 規劃時請考慮：公車、台鐵、高鐵、捷運(MRT)、YouBike 等各種組合');
    buffer.writeln('   - 如果出發地或目的地附近有捷運站，請優先考慮捷運方案');
    buffer.writeln('   - 最後一個方案請加上「(健身方案)」：建議騎腳踏車前往，並列出出發地附近所有可租借的YouBike站點（含可借車輛數），以及目的地附近可還車的站點，開玩笑地描述這是最健康環保的方式');
    buffer.writeln('2. 備用方案（如果主要方案不可行時的替代選擇）');
    buffer.writeln('3. 注意事項（如尖峰時段建議、步行距離、轉乘提醒、捷運班次等）');
    buffer.writeln();
    buffer.writeln('=== 回覆格式要求 ===');
    buffer.writeln(languageInstruction);
    buffer.writeln('請使用 RWD HTML5 語法格式回覆，內容需包含在 <html><body>...</body></html> 中。');
    buffer.writeln('CSS 可以使用，但必須是 inline style（直接寫在 HTML 標籤的 style 屬性中）。');
    buffer.writeln('禁止包含外部 CSS 檔案（<link rel="stylesheet">）。');
    buffer.writeln('禁止包含外部 JavaScript 檔案（<script src="...">）。');
    buffer.writeln('禁止使用任何會發出網路外連hyperlink功能語法。');
    buffer.writeln('');
    buffer.writeln('【重要 HTML 規範 - 必須遵守】');
    buffer.writeln('1. 必須在 <head> 中加入：<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=false">');
    //buffer.writeln('   - 使用 initial-scale=2.0 讓內容預設放大 2 倍');
    //buffer.writeln('   - 允許用戶縮放調整大小');
    //buffer.writeln('');
    buffer.writeln('2. 內容區域必須可以垂直滾動：');
    buffer.writeln('   - body 元素添加 style="overflow-y: scroll; -webkit-overflow-scrolling: touch;"');
    buffer.writeln('   - 確保內容超過螢幕高度時可以滑動');
    buffer.writeln('');
    buffer.writeln('3. HTML 結構建議：');
    buffer.writeln('   - 使用 <h1>, <h2>, <h3> 區分標題層級');
    buffer.writeln('   - 使用 <ul> 和 <li> 顯示列表資訊');
    buffer.writeln('   - 使用 <strong> 標示重要資訊');
    buffer.writeln('==================');

    return buffer.toString();
  }

  /// 執行完整的 AI 規劃流程
  Future<String> performAIPlanning({
    required String fromLocation,
    required String toLocation,
    Function(String status)? onStatusUpdate, // 新增狀態回調
    String language = 'zh', // 新增語言參數
    BuildContext? context, // 新增 context 參數
  }) async {
    // 1. 取得附近站點資訊
    debugPrint('開始取得附近站點資訊...');
    onStatusUpdate?.call('正在取得出發地附近站點...');
    final fromStations = await getNearbyStations(fromLocation);

    onStatusUpdate?.call('正在取得目的地附近站點...');
    final toStations = await getNearbyStations(toLocation);

    // 2. 生成增強版 Prompt
    onStatusUpdate?.call('正在生成規劃請求...');
    final prompt = generateEnhancedPrompt(
      fromLocation: fromLocation,
      toLocation: toLocation,
      fromStations: fromStations,
      toStations: toStations,
      language: language,
    );

    debugPrint('生成的 Prompt:');
    debugPrint(prompt);

    // 3. 重新初始化 WebView 並發送到 Gemini
    onStatusUpdate?.call('正在初始化 Gemini AI...');
    final geminiService = GeminiWebViewService();

    // 重新載入 WebView，確保每次規劃都是全新的對話
    await geminiService.reset();

    onStatusUpdate?.call('正在詢問 Gemini AI...');
    // 傳遞 context 參數，讓 WebView 可以在需要時顯示登入介面
    final response = await geminiService.sendPrompt(prompt, context: context);

    return response;
  }
}

/// 擴展方法：計算數字的平方根
extension MathExtension on double {
  double sqrt() {
    if (this <= 0) return 0;
    double x = this;
    double y = 1;
    double e = 0.000001;
    while (x - y > e) {
      x = (x + y) / 2;
      y = this / x;
    }
    return x;
  }

  double sin() {
    // 簡化的 sin 計算（使用泰勒級數）
    double x = this;
    double result = x;
    double term = x;
    int n = 1;
    for (int i = 1; i < 10; i++) {
      n += 2;
      term = -term * x * x / (n * (n - 1));
      result += term;
    }
    return result;
  }

  double cos() {
    // 簡化的 cos 計算
    double x = this;
    double result = 1;
    double term = 1;
    int n = 0;
    for (int i = 1; i < 10; i++) {
      n += 2;
      term = -term * x * x / (n * (n - 1));
      result += term;
    }
    return result;
  }

  double asin() {
    // 簡化的 asin 計算
    double x = this.clamp(-1, 1);
    double result = x;
    double term = x;
    for (int i = 1; i < 10; i++) {
      term = term * x * x * (2 * i - 1) * (2 * i - 1) / ((2 * i) * (2 * i + 1));
      result += term;
    }
    return result;
  }

  double clamp(double min, double max) {
    if (this < min) return min;
    if (this > max) return max;
    return this;
  }
}
