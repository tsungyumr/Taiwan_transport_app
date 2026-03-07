import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/bus_route.dart';
import '../services/bus_api_service.dart';

class BusListProvider extends ChangeNotifier {
  List<BusRoute> _routes = [];
  List<dynamic> _searchResults = []; // 搜尋結果（包含更多欄位）
  String _searchQuery = '';
  bool _isLoading = false;
  String? _error;
  bool _isSearchMode = false; // 是否為搜尋模式

  List<BusRoute> get routes => _routes;
  List<dynamic> get searchResults => _searchResults;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isSearchMode => _isSearchMode;

  Future<void> loadRoutes({String? query}) async {
    _isLoading = true;
    _error = null;
    _searchQuery = query ?? '';
    notifyListeners();

    try {
      if (_searchQuery.isEmpty) {
        // 無搜尋關鍵字，取得所有路線
        _isSearchMode = false;
        _routes = await BusApiService.fetchBusRoutes(routeName: null);
      } else {
        // 有搜尋關鍵字，使用搜尋 API
        _isSearchMode = true;
        _searchResults = await BusApiService.searchBusRoutes(_searchQuery);

        // 同時也取得基本路線列表（相容舊版）
        _routes = await BusApiService.fetchBusRoutes(routeName: _searchQuery);
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 清除搜尋
  void clearSearch() {
    _searchQuery = '';
    _searchResults = [];
    _isSearchMode = false;
    loadRoutes();
  }
}

class BusRouteProvider extends ChangeNotifier {
  BusRouteData? _data;
  BusRouteData? _goData;      // 去程資料
  BusRouteData? _backData;    // 返程資料
  DateTime? _lastUpdated;
  bool _isLoading = false;
  String? _error;
  Timer? _timer;
  final String route;
  int _currentDirection = 0;  // 當前方向：0=去程, 1=返程

  BusRouteData? get data => _data;
  BusRouteData? get goData => _goData;
  BusRouteData? get backData => _backData;
  DateTime? get lastUpdated => _lastUpdated;
  bool get isLoading => _isLoading;
  String? get error => _error;
  int get currentDirection => _currentDirection;

  BusRouteProvider(this.route) {
    loadData(direction: 0);
  }

  /// 切換方向
  Future<void> switchDirection(int direction) async {
    if (_currentDirection == direction) return;

    _currentDirection = direction;

    // 檢查是否已有該方向的資料
    if (direction == 0 && _goData != null) {
      _data = _goData;
      notifyListeners();
      return;
    } else if (direction == 1 && _backData != null) {
      _data = _backData;
      notifyListeners();
      return;
    }

    // 沒有資料則重新載入
    await loadData(direction: direction);
  }

  Future<void> loadData({int direction = 0, bool forceRefresh = false}) async {
    print('【BusRouteProvider】開始載入資料，路線: $route, 方向: $direction, 強制重新整理: $forceRefresh');
    _isLoading = true;
    _error = null;
    _currentDirection = direction;
    notifyListeners();

    try {
      print('【BusRouteProvider】呼叫 API...');
      _data = await BusApiService.fetchBusRouteData(route, direction: direction, forceRefresh: forceRefresh);
      _lastUpdated = DateTime.now();

      // 儲存到對應的方向資料
      if (direction == 0) {
        _goData = _data;
      } else {
        _backData = _data;
      }

      print('【BusRouteProvider】資料載入成功，站數: ${_data?.stops.length ?? 0}');

      // 除錯：印出前幾個站點的名稱
      if (_data?.stops != null && _data!.stops.isNotEmpty) {
        print('【BusRouteProvider】前3個站點名稱:');
        for (int i = 0; i < _data!.stops.length && i < 3; i++) {
          print('  站點 $i: ${_data!.stops[i].name}');
        }
      }
    } catch (e) {
      _error = e.toString();
      print('【BusRouteProvider】載入失敗: $_error');
    } finally {
      _isLoading = false;
      print('【BusRouteProvider】通知 UI 更新狀態，isLoading: $_isLoading, error: $_error');
      notifyListeners();
    }
  }

  void startPolling() {
    stopPolling();
    loadData(direction: _currentDirection);
    _timer = Timer.periodic(const Duration(seconds: 30), (timer) => loadData(direction: _currentDirection));
  }

  void stopPolling() {
    _timer?.cancel();
    _timer = null;
  }

  @override
  void dispose() {
    stopPolling();
    super.dispose();
  }
}