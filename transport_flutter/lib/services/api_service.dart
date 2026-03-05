import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';

class ApiService {
  // 修改為你的後端伺服器地址
  // 如果後端在手機上運行，需要使用實際 IP 位址
  // 例如: http://192.168.1.x:8000/api
  //static const String baseUrl = 'http://zaizaicat.com:8000/api'; // Android 模擬器專用
  static const String baseUrl = 'http://10.0.2.2:8001/api'; // iOS 模擬器/本地端

  final http.Client _client = http.Client();

  // ----- 公車 API -----

  Future<List<BusRoute>> getBusRoutes({String? routeName}) async {
    try {
      final queryParams = routeName != null ? {'route_name': routeName} : null;
      final response = await _client.get(
        Uri.parse('$baseUrl/bus/routes').replace(queryParameters: queryParams),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => BusRoute.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('Error fetching bus routes: $e');
      return [];
    }
  }

  Future<List<BusTimeEntry>> getBusTimetable(String routeId) async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl/bus/timetable/$routeId'),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => BusTimeEntry.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('Error fetching bus timetable: $e');
      return [];
    }
  }

  // ----- 台鐵 API -----

  Future<List<TrainStation>> getRailwayStations() async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl/railway/stations'),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => TrainStation.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('Error fetching railway stations: $e');
      return [];
    }
  }

  Future<List<TrainTimeEntry>> getRailwayTimetable({
    required String fromStation,
    required String toStation,
    String? date,
    String? time,
  }) async {
    try {
      final queryParams = <String, String>{
        'from_station': fromStation,
        'to_station': toStation,
      };
      
      if (date != null) queryParams['date'] = date;
      if (time != null) queryParams['time'] = time;
      
      final response = await _client.get(
        Uri.parse('$baseUrl/railway/timetable').replace(queryParameters: queryParams),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => TrainTimeEntry.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('Error fetching railway timetable: $e');
      return [];
    }
  }

  // ----- 高鐵 API -----

  Future<List<TrainStation>> getTHSRStations() async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl/thsr/stations'),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => TrainStation.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('Error fetching THSR stations: $e');
      return [];
    }
  }

  Future<List<THSRTrainEntry>> getTHSRTimetable({
    required String fromStation,
    required String toStation,
    String? date,
  }) async {
    try {
      final queryParams = <String, String>{
        'from_station': fromStation,
        'to_station': toStation,
      };
      
      if (date != null) queryParams['date'] = date;
      
      final response = await _client.get(
        Uri.parse('$baseUrl/thsr/timetable').replace(queryParameters: queryParams),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => THSRTrainEntry.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('Error fetching THSR timetable: $e');
      return [];
    }
  }
}
