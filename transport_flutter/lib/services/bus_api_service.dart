import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/bus_route.dart';

class BusApiService {
  //static const String _baseUrl = 'http://zaizaicat.com:8000/api';
  static const String _baseUrl = 'http://10.0.2.2:8001/api';

  // 設定較長的 timeout，因為後端爬蟲需要時間
  static const Duration _timeout = Duration(seconds: 60);

  static Future<List<BusRoute>> fetchBusRoutes({String? routeName}) async {
    try {
      // 建構 URI 並添加 query parameters
      final uri = Uri.parse('$_baseUrl/bus/routes').replace(
        queryParameters: routeName != null && routeName.isNotEmpty ? {'route_name': routeName} : {},
      );

      print('【BusApiService】===========================');
      print('【BusApiService】正在請求路線列表');
      print('【BusApiService】搜尋關鍵字: ${routeName ?? "(無)"}');
      print('【BusApiService】完整 URL: $uri');
      print('【BusApiService】===========================');

      final response = await http.get(uri).timeout(_timeout);

      print('【BusApiService】收到回應');
      print('【BusApiService】狀態碼: ${response.statusCode}');
      print('【BusApiService】內容長度: ${response.body.length}');

      if (response.statusCode == 200) {
        print('【BusApiService】開始解析 JSON...');
        final List<dynamic> data = json.decode(response.body);
        print('【BusApiService】✅ 成功解析 ${data.length} 條路線');
        return data.map((json) => BusRoute.fromJson(json)).toList();
      } else {
        print('【BusApiService】❌ 請求失敗！');
        print('【BusApiService】狀態碼: ${response.statusCode}');
        print('【BusApiService】原因: ${response.reasonPhrase}');
        print('【BusApiService】回應內容: ${response.body.substring(0, response.body.length > 500 ? 500 : response.body.length)}');
        throw Exception('Failed to load routes: ${response.statusCode} - ${response.reasonPhrase}');
      }
    } on SocketException catch (e) {
      print('【BusApiService】❌ 網路連接錯誤！');
      print('【BusApiService】錯誤訊息: $e');
      print('【BusApiService】請檢查：');
      print('  1. 後端服務是否運行在 http://10.0.2.2:8001');
      print('  2. Android 模擬器是否可以訪問主機');
      throw Exception('網路連接錯誤，請檢查後端服務是否運行');
    } on FormatException catch (e) {
      print('【BusApiService】❌ JSON 解析錯誤！');
      print('【BusApiService】錯誤訊息: $e');
      throw Exception('資料格式錯誤: $e');
    } on TimeoutException catch (e) {
      print('【BusApiService】❌ 請求超時！');
      print('【BusApiService】後端爬蟲需要較長時間，請稍後重試');
      throw Exception('請求超時，後端爬蟲需要較長時間');
    } catch (e) {
      print('【BusApiService】❌ 未知錯誤！');
      print('【BusApiService】錯誤類型: ${e.runtimeType}');
      print('【BusApiService】錯誤訊息: $e');
      throw Exception('載入路線失敗: $e');
    }
  }

  static Future<BusRouteData> fetchBusRouteData(String route, {int direction = 0, bool forceRefresh = false}) async {
    try {
      // 建立 query parameters
      final queryParams = <String, String>{
        'direction': direction.toString(),
      };

      // 如果是強制重新整理，添加時間戳參數來繞過快取
      if (forceRefresh) {
        queryParams['_t'] = DateTime.now().millisecondsSinceEpoch.toString();
      }

      // 使用 Uri 建構式來正確編碼 URL 路徑，並加入 direction 參數
      final uri = Uri(
        scheme: 'http',
        host: '10.0.2.2',
        port: 8001,
        path: '/api/bus/${Uri.encodeComponent(route)}',
        queryParameters: queryParams,
      );

      print('【BusApiService】===========================');
      print('【BusApiService】正在請求路線資料');
      print('【BusApiService】路線名稱: $route');
      print('【BusApiService】方向: $direction');
      print('【BusApiService】完整 URL: $uri');
      print('【BusApiService】===========================');

      final response = await http.get(uri).timeout(_timeout);

      print('【BusApiService】收到回應');
      print('【BusApiService】狀態碼: ${response.statusCode}');
      print('【BusApiService】內容長度: ${response.body.length}');

      if (response.statusCode == 200) {
        print('【BusApiService】開始解析 JSON...');
        final data = json.decode(response.body);
        print('【BusApiService】JSON 解析成功');
        print('【BusApiService】路線: ${data['route']}');
        print('【BusApiService】站數: ${data['stops']?.length ?? 0}');
        print('【BusApiService】車輛數: ${data['buses']?.length ?? 0}');

        // 除錯：印出前幾個站點的詳細資訊
        if (data['stops'] != null && data['stops'] is List) {
          final stops = data['stops'] as List;
          print('【BusApiService】前3個站點資料:');
          for (int i = 0; i < stops.length && i < 3; i++) {
            final stop = stops[i];
            print('  站點 $i: name=${stop['name']}, sequence=${stop['sequence']}, eta=${stop['eta']}');
          }
        }

        return BusRouteData.fromJson(data);
      } else {
        print('【BusApiService】❌ 請求失敗！');
        print('【BusApiService】狀態碼: ${response.statusCode}');
        print('【BusApiService】原因: ${response.reasonPhrase}');
        print('【BusApiService】回應內容: ${response.body.substring(0, response.body.length > 500 ? 500 : response.body.length)}');
        throw Exception('Failed to load route data for $route: ${response.statusCode} - ${response.reasonPhrase}');
      }
    } on SocketException catch (e) {
      print('【BusApiService】❌ 網路連接錯誤！');
      print('【BusApiService】錯誤訊息: $e');
      print('【BusApiService】請檢查：');
      print('  1. 後端服務是否運行在 http://10.0.2.2:8001');
      print('  2. Android 模擬器是否可以訪問主機');
      throw Exception('網路連接錯誤，請檢查後端服務是否運行');
    } on FormatException catch (e) {
      print('【BusApiService】❌ JSON 解析錯誤！');
      print('【BusApiService】錯誤訊息: $e');
      throw Exception('資料格式錯誤: $e');
    } on TimeoutException catch (e) {
      print('【BusApiService】❌ 請求超時！');
      print('【BusApiService】後端爬蟲需要較長時間，請稍後重試');
      throw Exception('請求超時，後端爬蟲需要較長時間');
    } catch (e) {
      print('【BusApiService】❌ 未知錯誤！');
      print('【BusApiService】錯誤類型: ${e.runtimeType}');
      print('【BusApiService】錯誤訊息: $e');
      throw Exception('載入路線資料失敗: $e');
    }
  }

  /// 搜尋新北市公車路線
  ///
  /// [keyword] 搜尋關鍵字（路線名稱、起迄站）
  /// [limit] 回傳數量上限，預設 20
  static Future<List<dynamic>> searchBusRoutes(String keyword, {int limit = 20}) async {
    try {
      final uri = Uri(
        scheme: 'http',
        host: '10.0.2.2',
        port: 8001,
        path: '/api/bus/routes/search',
        queryParameters: {
          'keyword': keyword,
          'limit': limit.toString(),
        },
      );

      print('【BusApiService】===========================');
      print('【BusApiService】正在搜尋路線');
      print('【BusApiService】關鍵字: $keyword');
      print('【BusApiService】完整 URL: $uri');
      print('【BusApiService】===========================');

      final response = await http.get(uri).timeout(_timeout);

      print('【BusApiService】收到回應');
      print('【BusApiService】狀態碼: ${response.statusCode}');

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        print('【BusApiService】✅ 成功找到 ${data.length} 條路線');
        return data;
      } else {
        print('【BusApiService】❌ 搜尋失敗！');
        print('【BusApiService】錯誤: ${response.body}');
        throw Exception('搜尋路線失敗: ${response.statusCode}');
      }
    } on SocketException catch (e) {
      print('【BusApiService】❌ 網路連接錯誤！');
      throw Exception('網路連接錯誤，請檢查後端服務是否運行');
    } on FormatException catch (e) {
      print('【BusApiService】❌ JSON 解析錯誤！');
      throw Exception('資料格式錯誤: $e');
    } catch (e) {
      print('【BusApiService】❌ 搜尋失敗: $e');
      throw Exception('搜尋路線失敗: $e');
    }
  }
}