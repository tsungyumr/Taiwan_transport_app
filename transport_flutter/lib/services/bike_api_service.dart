// bike_api_service.dart
// UBike API 服務

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';
import '../models/bike_station.dart';

/// UBike API 服務類別
class BikeApiService {
  static const String _baseUrl = 'http://10.0.2.2:8001/api';

  /// 取得附近站點
  static Future<List<BikeStation>> getNearbyStations(
    double lat,
    double lon, {
    int radius = 1000,
    String city = 'Taipei',
  }) async {
    final uri = Uri.parse('$_baseUrl/bike/stations/nearby').replace(
      queryParameters: {
        'lat': lat.toString(),
        'lon': lon.toString(),
        'radius': radius.toString(),
        'city': city,
      },
    );

    try {
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        // 解析後端回傳格式: { "success": true, "data": [...], ... }
        if (json is Map<String, dynamic> && json['data'] is List) {
          final dataList = json['data'] as List;
          return dataList.map((item) => BikeStation.fromJson(item as Map<String, dynamic>)).toList();
        }
        return [];
      } else {
        throw Exception('取得站點失敗: ${response.statusCode}');
      }
    } catch (e) {
      // 開發時使用模擬資料
      print('API 錯誤，使用模擬資料: $e');
      return BikeStation.mockStations;
    }
  }

  /// 取得所有站點（支援多城市，預設同時取得 Taipei 和 NewTaipei）
  static Future<List<BikeStation>> getAllStations({List<String> cities = const ['Taipei', 'NewTaipei']}) async {
    final allStations = <BikeStation>[];
    String? errorMessage;

    // 並行取得所有指定城市的站點資料
    final futures = cities.map((city) async {
      try {
        final uri = Uri.parse('$_baseUrl/bike/stations').replace(
          queryParameters: {'city': city},
        );
        final response = await http.get(uri);

        if (response.statusCode == 200) {
          final json = jsonDecode(response.body);
          // 解析後端回傳格式: { "success": true, "data": [...], "total": ..., "city": ... }
          if (json is Map<String, dynamic> && json['data'] is List) {
            final dataList = json['data'] as List;
            return dataList.map((item) => BikeStation.fromJson(item as Map<String, dynamic>)).toList();
          }
        } else {
          print('取得 $city 站點失敗: ${response.statusCode}');
        }
      } catch (e) {
        print('取得 $city 站點錯誤: $e');
        errorMessage = e.toString();
      }
      return <BikeStation>[];
    });

    // 等待所有城市資料載入完成
    final results = await Future.wait(futures);
    for (final stations in results) {
      allStations.addAll(stations);
    }

    // 如果都沒有資料且發生錯誤，回傳模擬資料
    if (allStations.isEmpty && errorMessage != null) {
      print('所有城市 API 錯誤，使用模擬資料');
      return BikeStation.mockStations;
    }

    print('成功載入 ${allStations.length} 個站點');
    return allStations;
  }

  /// 搜尋地點（簡化版，使用預設地點）
  static Future<LatLng?> searchLocation(String keyword) async {
    // 預設地點對照表
    final locations = {
      '台北': LatLng(25.0330, 121.5654),
      '台北市': LatLng(25.0330, 121.5654),
      '台北101': LatLng(25.0330, 121.5654),
      '101': LatLng(25.0330, 121.5654),
      '市政府': LatLng(25.0412, 121.5654),
      '西門': LatLng(25.0420, 121.5080),
      '西門町': LatLng(25.0420, 121.5080),
      '台北車站': LatLng(25.0478, 121.5170),
      '車站': LatLng(25.0478, 121.5170),
      '中山': LatLng(25.0520, 121.5200),
      '大安': LatLng(25.0335, 121.5430),
      '信義': LatLng(25.0320, 121.5600),
      '大安森林公園': LatLng(25.0325, 121.5360),
      '中正紀念堂': LatLng(25.0350, 121.5200),
      '國父紀念館': LatLng(25.0401, 121.5600),
      '華山': LatLng(25.0440, 121.5290),
      '松山': LatLng(25.0500, 121.5700),
      '內湖': LatLng(25.0700, 121.5900),
      '南港': LatLng(25.0550, 121.6000),
      '文山': LatLng(25.0000, 121.5600),
      '新店': LatLng(24.9700, 121.5400),
    };

    // 關鍵字搜尋
    for (final entry in locations.entries) {
      if (keyword.contains(entry.key)) {
        return entry.value;
      }
    }

    // 如果沒有找到，返回 null
    return null;
  }

  /// 取得特定站點詳細資訊
  static Future<BikeStation?> getStationDetail(String stationId) async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/bike/station/$stationId'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return BikeStation.fromJson(data);
      }
      return null;
    } catch (e) {
      print('取得站點詳細資訊失敗: $e');
      return null;
    }
  }
}
