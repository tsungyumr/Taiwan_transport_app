// bike_search_history_service.dart
// YouBike 站點搜尋歷史服務

import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/bike_station.dart';

/// YouBike 站點觀看歷史項目
class BikeSearchHistoryItem {
  final String stationId;
  final String name;
  final String address;
  final double lat;
  final double lng;
  final int searchCount; // 觀看次數
  final DateTime lastViewedAt; // 最後觀看時間

  BikeSearchHistoryItem({
    required this.stationId,
    required this.name,
    required this.address,
    required this.lat,
    required this.lng,
    this.searchCount = 1,
    required this.lastViewedAt,
  });

  /// 從 BikeStation 建立歷史記錄
  factory BikeSearchHistoryItem.fromBikeStation(BikeStation station) {
    return BikeSearchHistoryItem(
      stationId: station.stationId,
      name: station.name,
      address: station.address,
      lat: station.lat,
      lng: station.lng,
      searchCount: 1,
      lastViewedAt: DateTime.now(),
    );
  }

  /// 增加觀看次數
  BikeSearchHistoryItem incrementCount() {
    return BikeSearchHistoryItem(
      stationId: stationId,
      name: name,
      address: address,
      lat: lat,
      lng: lng,
      searchCount: searchCount + 1,
      lastViewedAt: DateTime.now(),
    );
  }

  /// 轉換為 JSON
  Map<String, dynamic> toJson() {
    return {
      'station_id': stationId,
      'name': name,
      'address': address,
      'lat': lat,
      'lng': lng,
      'search_count': searchCount,
      'last_viewed_at': lastViewedAt.toIso8601String(),
    };
  }

  /// 從 JSON 解析
  factory BikeSearchHistoryItem.fromJson(Map<String, dynamic> json) {
    return BikeSearchHistoryItem(
      stationId: json['station_id'] ?? '',
      name: json['name'] ?? '',
      address: json['address'] ?? '',
      lat: (json['lat'] ?? 0).toDouble(),
      lng: (json['lng'] ?? 0).toDouble(),
      searchCount: json['search_count'] ?? 1,
      lastViewedAt: DateTime.tryParse(json['last_viewed_at'] ?? '') ?? DateTime.now(),
    );
  }
}

/// YouBike 站點搜尋歷史服務
class BikeSearchHistoryService {
  static const String _storageKey = 'bike_search_history';
  static const int _maxHistoryItems = 50; // 最多保存的歷史記錄數

  /// 獲取所有觀看歷史
  Future<List<BikeSearchHistoryItem>> getSearchHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final String? jsonString = prefs.getString(_storageKey);

    if (jsonString == null || jsonString.isEmpty) {
      return [];
    }

    try {
      final List<dynamic> jsonList = jsonDecode(jsonString);
      return jsonList
          .map((json) => BikeSearchHistoryItem.fromJson(json))
          .toList();
    } catch (e) {
      // 解析失敗時回傳空列表
      return [];
    }
  }

  /// 記錄一次站點觀看
  Future<void> recordView(BikeStation station) async {
    final history = await getSearchHistory();

    // 檢查是否已存在
    final existingIndex = history.indexWhere((item) => item.stationId == station.stationId);

    if (existingIndex >= 0) {
      // 已存在，增加次數並更新時間
      history[existingIndex] = history[existingIndex].incrementCount();
    } else {
      // 新增記錄
      history.add(BikeSearchHistoryItem.fromBikeStation(station));
    }

    await _saveHistory(history);
  }

  /// 獲取排序後的觀看歷史（按觀看頻率和時間）
  Future<List<BikeSearchHistoryItem>> getSortedHistory() async {
    final history = await getSearchHistory();

    // 排序規則：
    // 1. 觀看次數越高越前面
    // 2. 相同次數時，最近觀看的越前面
    history.sort((a, b) {
      if (a.searchCount != b.searchCount) {
        return b.searchCount.compareTo(a.searchCount); // 降序
      }
      return b.lastViewedAt.compareTo(a.lastViewedAt); // 時間降序
    });

    return history;
  }

  /// 獲取常用站點（觀看次數最多的前 N 個）
  Future<List<BikeSearchHistoryItem>> getPopularStations({int limit = 10}) async {
    final sortedHistory = await getSortedHistory();
    return sortedHistory.take(limit).toList();
  }

  /// 獲取最近觀看（按時間排序）
  Future<List<BikeSearchHistoryItem>> getRecentViews({int limit = 10}) async {
    final history = await getSearchHistory();

    // 按時間降序排序
    history.sort((a, b) => b.lastViewedAt.compareTo(a.lastViewedAt));

    return history.take(limit).toList();
  }

  /// 清除所有觀看歷史
  Future<void> clearHistory() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
  }

  /// 刪除單筆歷史記錄
  Future<void> removeHistoryItem(String stationId) async {
    final history = await getSearchHistory();
    history.removeWhere((item) => item.stationId == stationId);
    await _saveHistory(history);
  }

  /// 獲取特定站點的觀看次數
  Future<int> getViewCount(String stationId) async {
    final history = await getSearchHistory();
    final item = history.firstWhere(
      (item) => item.stationId == stationId,
      orElse: () => BikeSearchHistoryItem(
        stationId: stationId,
        name: '',
        address: '',
        lat: 0,
        lng: 0,
        searchCount: 0,
        lastViewedAt: DateTime.now(),
      ),
    );
    return item.searchCount;
  }

  /// 保存歷史記錄到本地儲存
  Future<void> _saveHistory(List<BikeSearchHistoryItem> history) async {
    final prefs = await SharedPreferences.getInstance();

    // 限制保存數量
    if (history.length > _maxHistoryItems) {
      // 按觀看次數和時間排序，只保留前 N 個
      history.sort((a, b) {
        if (a.searchCount != b.searchCount) {
          return b.searchCount.compareTo(a.searchCount);
        }
        return b.lastViewedAt.compareTo(a.lastViewedAt);
      });
      history.removeRange(_maxHistoryItems, history.length);
    }

    final jsonList = history.map((item) => item.toJson()).toList();
    final jsonString = jsonEncode(jsonList);
    await prefs.setString(_storageKey, jsonString);
  }
}
