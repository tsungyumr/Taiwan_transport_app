import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:taiwan_transport_app/config.dart';
import '../models/models.dart';

class ApiService {
  final http.Client _client = http.Client();

  // ----- 公車 API -----

  Future<List<BusRoute>> getBusRoutes({String? routeName}) async {
    try {
      final queryParams = routeName != null ? {'route_name': routeName} : null;
      final response = await _client.get(
        Uri.parse('${AppConfig.baseUrl}${AppConfig.getBusRoutesApi}').replace(queryParameters: queryParams),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => BusRoute.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      if (kDebugMode) {
        print('Error fetching bus routes: $e');
      }
      return [];
    }
  }

  Future<List<BusTimeEntry>> getBusTimetable(String routeId) async {
    try {
      final response = await _client.get(
        Uri.parse('${AppConfig.baseUrl}${AppConfig.getBusTimetableApi}$routeId'),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => BusTimeEntry.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      if (kDebugMode) {
        print('Error fetching bus timetable: $e');
      }
      return [];
    }
  }

  // ----- 台鐵 API -----

  Future<List<TrainStation>> getRailwayStations({String? lang}) async {
    try {
      final queryParams = lang != null ? {'lang': lang} : null;
      final response = await _client.get(
        Uri.parse('${AppConfig.baseUrl}${AppConfig.getRailwayStationsApi}').replace(queryParameters: queryParams),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => TrainStation.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      if (kDebugMode) {
        print('Error fetching railway stations: $e');
      }
      return [];
    }
  }

  Future<List<TrainTimeEntry>> getRailwayTimetable({
    required String fromStation,
    required String toStation,
    String? date,
    String? time,
    String? lang,
  }) async {
    try {
      final queryParams = <String, String>{
        'from_station': fromStation,
        'to_station': toStation,
      };

      if (date != null) queryParams['date'] = date;
      if (time != null) queryParams['time'] = time;
      if (lang != null) queryParams['lang'] = lang;

      final response = await _client.get(
        Uri.parse('${AppConfig.baseUrl}${AppConfig.getRailwayTimetableApi}').replace(queryParameters: queryParams),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => TrainTimeEntry.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      if (kDebugMode) {
        print('Error fetching railway timetable: $e');
      }
      return [];
    }
  }

  // ----- 高鐵 API -----

  Future<List<TrainStation>> getTHSRStations({String? lang}) async {
    try {
      final queryParams = lang != null ? {'lang': lang} : null;
      final response = await _client.get(
        Uri.parse('${AppConfig.baseUrl}${AppConfig.getTHSRStationsApi}').replace(queryParameters: queryParams),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => TrainStation.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      if (kDebugMode) {
        print('Error fetching THSR stations: $e');
      }
      return [];
    }
  }

  Future<List<THSRTrainEntry>> getTHSRTimetable({
    required String fromStation,
    required String toStation,
    String? date,
    String? time,
    String? endTime,
    String? lang,
  }) async {
    try {
      final queryParams = <String, String>{
        'from_station': fromStation,
        'to_station': toStation,
      };

      if (date != null) queryParams['date'] = date;
      if (time != null) queryParams['time'] = time;
      if (endTime != null) queryParams['end_time'] = endTime;
      if (lang != null) queryParams['lang'] = lang;

      final response = await _client.get(
        Uri.parse('${AppConfig.baseUrl}${AppConfig.getTHSRTimetableApi}').replace(queryParameters: queryParams),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => THSRTrainEntry.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      if (kDebugMode) {
        print('Error fetching THSR timetable: $e');
      }
      return [];
    }
  }
}
