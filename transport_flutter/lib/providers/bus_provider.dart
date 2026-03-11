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