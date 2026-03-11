import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';

/// 公車搜尋歷史記錄項目
class BusSearchHistoryItem {
  final String routeId;
  final String routeName;
  final String departureStop;
  final String arrivalStop;
  final String operator;
  final int searchCount; // 搜尋次數
  final DateTime lastSearchedAt; // 最後搜尋時間

  BusSearchHistoryItem({
    required this.routeId,
    required this.routeName,
    required this.departureStop,
    required this.arrivalStop,
    required this.operator,
    this.searchCount = 1,
    required this.lastSearchedAt,
  });

  /// 從 BusRoute 建立歷史記錄
  factory BusSearchHistoryItem.fromBusRoute(BusRoute route) {
    return BusSearchHistoryItem(
      routeId: route.routeId,
      routeName: route.routeName,
      departureStop: route.departureStop,
      arrivalStop: route.arrivalStop,
      operator: route.operator,
      searchCount: 1,
      lastSearchedAt: DateTime.now(),
    );
  }

  /// 增加搜尋次數
  BusSearchHistoryItem incrementCount() {
    return BusSearchHistoryItem(
      routeId: routeId,
      routeName: routeName,
      departureStop: departureStop,
      arrivalStop: arrivalStop,
      operator: operator,
      searchCount: searchCount + 1,
      lastSearchedAt: DateTime.now(),
    );
  }

  /// 轉換為 JSON
  Map<String, dynamic> toJson() {
    return {
      'route_id': routeId,
      'route_name': routeName,
      'departure_stop': departureStop,
      'arrival_stop': arrivalStop,
      'operator': operator,
      'search_count': searchCount,
      'last_searched_at': lastSearchedAt.toIso8601String(),
    };
  }

  /// 從 JSON 解析
  factory BusSearchHistoryItem.fromJson(Map<String, dynamic> json) {
    return BusSearchHistoryItem(
      routeId: json['route_id'] ?? '',
      routeName: json['route_name'] ?? '',
      departureStop: json['departure_stop'] ?? '',
      arrivalStop: json['arrival_stop'] ?? '',
      operator: json['operator'] ?? '',
      searchCount: json['search_count'] ?? 1,
      lastSearchedAt: DateTime.tryParse(json['last_searched_at'] ?? '') ?? DateTime.now(),
    );
  }

  /// 轉換為 BusRoute
  BusRoute toBusRoute() {
    return BusRoute(
      routeId: routeId,
      routeName: routeName,
      departureStop: departureStop,
      arrivalStop: arrivalStop,
      operator: operator,
    );
  }
}

/// 公車搜尋歷史服務
class BusSearchHistoryService {
  static const String _storageKey = 'bus_search_history';
  static const int _maxHistoryItems = 50; // 最多保存的歷史記錄數

  /// 獲取所有搜尋歷史
  Future<List<BusSearchHistoryItem>> getSearchHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final String? jsonString = prefs.getString(_storageKey);

    if (jsonString == null || jsonString.isEmpty) {
      return [];
    }

    try {
      final List<dynamic> jsonList = jsonDecode(jsonString);
      return jsonList
          .map((json) => BusSearchHistoryItem.fromJson(json))
          .toList();
    } catch (e) {
      // 解析失敗時回傳空列表
      return [];
    }
  }

  /// 記錄一次搜尋
  Future<void> recordSearch(BusRoute route) async {
    final history = await getSearchHistory();

    // 檢查是否已存在
    final existingIndex = history.indexWhere((item) => item.routeId == route.routeId);

    if (existingIndex >= 0) {
      // 已存在，增加次數並更新時間
      history[existingIndex] = history[existingIndex].incrementCount();
    } else {
      // 新增記錄
      history.add(BusSearchHistoryItem.fromBusRoute(route));
    }

    await _saveHistory(history);
  }

  /// 獲取排序後的搜尋歷史（按搜尋頻率和時間）
  Future<List<BusSearchHistoryItem>> getSortedHistory() async {
    final history = await getSearchHistory();

    // 排序規則：
    // 1. 搜尋次數越高越前面
    // 2. 相同次數時，最近搜尋的越前面
    history.sort((a, b) {
      if (a.searchCount != b.searchCount) {
        return b.searchCount.compareTo(a.searchCount); // 降序
      }
      return b.lastSearchedAt.compareTo(a.lastSearchedAt); // 時間降序
    });

    return history;
  }

  /// 獲取熱門路線（搜尋次數最多的前 N 個）
  Future<List<BusSearchHistoryItem>> getPopularRoutes({int limit = 10}) async {
    final sortedHistory = await getSortedHistory();
    return sortedHistory.take(limit).toList();
  }

  /// 獲取最近搜尋（按時間排序）
  Future<List<BusSearchHistoryItem>> getRecentSearches({int limit = 10}) async {
    final history = await getSearchHistory();

    // 按時間降序排序
    history.sort((a, b) => b.lastSearchedAt.compareTo(a.lastSearchedAt));

    return history.take(limit).toList();
  }

  /// 清除所有搜尋歷史
  Future<void> clearHistory() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
  }

  /// 刪除單筆歷史記錄
  Future<void> removeHistoryItem(String routeId) async {
    final history = await getSearchHistory();
    history.removeWhere((item) => item.routeId == routeId);
    await _saveHistory(history);
  }

  /// 保存歷史記錄到本地儲存
  Future<void> _saveHistory(List<BusSearchHistoryItem> history) async {
    final prefs = await SharedPreferences.getInstance();

    // 限制保存數量
    if (history.length > _maxHistoryItems) {
      // 按搜尋次數和時間排序，只保留前 N 個
      history.sort((a, b) {
        if (a.searchCount != b.searchCount) {
          return b.searchCount.compareTo(a.searchCount);
        }
        return b.lastSearchedAt.compareTo(a.lastSearchedAt);
      });
      history.removeRange(_maxHistoryItems, history.length);
    }

    final jsonList = history.map((item) => item.toJson()).toList();
    final jsonString = jsonEncode(jsonList);
    await prefs.setString(_storageKey, jsonString);
  }
}
