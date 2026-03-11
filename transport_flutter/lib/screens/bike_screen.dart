// bike_screen.dart
// UBike 腳踏車主頁面

import 'package:flutter/material.dart';
import '../models/bike_station.dart';
import '../services/bike_search_history_service.dart';
import '../ui_theme.dart';
import '../widgets/bike_station_card.dart';
import '../widgets/loading_animations.dart';
import '../widgets/styled_inputs.dart';

class BikeScreen extends StatefulWidget {
  final bool showAppBar;

  const BikeScreen({super.key, this.showAppBar = true});

  @override
  State<BikeScreen> createState() => _BikeScreenState();
}

class _BikeScreenState extends State<BikeScreen> {
  final BikeSearchHistoryService _historyService = BikeSearchHistoryService();
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  List<BikeStation> _allStations = []; // 所有站點
  List<BikeStation> _filteredStations = []; // 篩選後的站點
  List<BikeSearchHistoryItem> _viewHistory = []; // 觀看歷史
  Map<String, int> _viewCounts = {}; // 站點ID -> 觀看次數
  bool _isLoading = false;
  DateTime? _lastUpdateTime;

  @override
  void initState() {
    super.initState();
    _loadStations(); // 這會自動載入歷史並排序
  }

  /// 載入所有 UBike 站點
  Future<void> _loadStations() async {
    setState(() => _isLoading = true);

    // 使用模擬資料（未來可替換為真實 API）
    final stations = BikeStation.mockStations;

    // 模擬載入延遲
    await Future.delayed(const Duration(milliseconds: 500));

    if (!mounted) return;

    setState(() {
      _allStations = stations;
      _filteredStations = stations;
      _isLoading = false;
      _lastUpdateTime = DateTime.now();
    });

    // 載入觀看歷史後排序（讓常看的站點排在前面）
    await _loadViewHistory();
  }

  /// 載入觀看歷史
  Future<void> _loadViewHistory() async {
    final history = await _historyService.getSearchHistory();

    // 建立觀看次數對照表
    final viewCounts = <String, int>{};
    for (final item in history) {
      viewCounts[item.stationId] = item.searchCount;
    }

    if (!mounted) return;

    setState(() {
      _viewHistory = history;
      _viewCounts = viewCounts;
      // 根據觀看次數排序（常看的排在最前面）
      _sortStationsByPopularity();
    });
  }

  /// 搜尋/篩選站點
  void _filterStations(String query) {
    setState(() {
      if (query.isEmpty) {
        _filteredStations = _allStations;
      } else {
        _filteredStations = _allStations.where((station) {
          return station.name.toLowerCase().contains(query.toLowerCase()) ||
                 station.address.toLowerCase().contains(query.toLowerCase());
        }).toList();
      }
      // 根據觀看次數排序（熱門的在前）
      _sortStationsByPopularity();
    });
  }

  /// 根據熱門程度排序站點
  void _sortStationsByPopularity() {
    _filteredStations.sort((a, b) {
      final countA = _viewCounts[a.stationId] ?? 0;
      final countB = _viewCounts[b.stationId] ?? 0;
      // 先按觀看次數降序排序
      if (countA != countB) {
        return countB.compareTo(countA); // 次數高的在前
      }
      // 次數相同時，按距離排序（近的在前）
      final distA = a.distance ?? double.infinity;
      final distB = b.distance ?? double.infinity;
      return distA.compareTo(distB);
    });
  }

  /// 選擇站點（點擊觀看）
  Future<void> _selectStation(BikeStation station) async {
    // 記錄觀看歷史
    await _historyService.recordView(station);

    if (!mounted) return;

    // 顯示站點詳情（暫時用 SnackBar，未來可導航到詳情頁）
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(Icons.pedal_bike, color: station.statusColor),
            const SizedBox(width: AppSpacing.sm),
            Text('${station.name} - ${station.statusText}'),
          ],
        ),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.small),
        ),
        duration: const Duration(seconds: 2),
        action: SnackBarAction(
          label: '導航',
          onPressed: () => _openNavigation(station),
        ),
      ),
    );

    // 重新載入歷史並排序
    if (mounted) {
      await _loadViewHistory();
    }
  }

  /// 開啟導航
  Future<void> _openNavigation(BikeStation station) async {
    // 記錄觀看歷史
    await _historyService.recordView(station);

    if (!mounted) return;

    // 顯示導航選項
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '導航到 ${station.name}',
              style: AppTextStyles.titleLarge,
            ),
            const SizedBox(height: AppSpacing.md),
            ListTile(
              leading: const Icon(Icons.map, color: Colors.blue),
              title: const Text('Google Maps'),
              subtitle: const Text('使用 Google Maps 導航'),
              onTap: () {
                Navigator.pop(context);
                _launchGoogleMaps(station);
              },
            ),
            ListTile(
              leading: const Icon(Icons.apple, color: Colors.black),
              title: const Text('Apple Maps'),
              subtitle: const Text('使用 Apple Maps 導航 (iOS)'),
              onTap: () {
                Navigator.pop(context);
                _launchAppleMaps(station);
              },
            ),
          ],
        ),
      ),
    );
  }

  /// 啟動 Google Maps
  void _launchGoogleMaps(BikeStation station) {
    // 實際應用中需要使用 url_launcher
    // final url = 'https://www.google.com/maps/dir/?api=1&destination=${station.lat},${station.lng}&travelmode=walking';
    // launchUrl(Uri.parse(url));
    debugPrint('導航到 ${station.name}: ${station.lat}, ${station.lng}');
  }

  /// 啟動 Apple Maps
  void _launchAppleMaps(BikeStation station) {
    // 實際應用中需要使用 url_launcher
    // final url = 'http://maps.apple.com/?daddr=${station.lat},${station.lng}&dirflg=w';
    // launchUrl(Uri.parse(url));
    debugPrint('導航到 ${station.name}: ${station.lat}, ${station.lng}');
  }

  /// 清除所有觀看歷史
  Future<void> _clearAllHistory() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.large),
        ),
        title: Row(
          children: [
            Icon(Icons.delete_outline, color: AppColors.error),
            const SizedBox(width: AppSpacing.sm),
            const Text('清除觀看歷史'),
          ],
        ),
        content: const Text('確定要清除所有站點觀看記錄嗎？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
            ),
            child: const Text('清除'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _historyService.clearHistory();
      await _loadViewHistory();
      // 重新排序（恢復預設排序）
      setState(() {
        _sortStationsByPopularity();
      });

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.check_circle, color: Colors.white),
              const SizedBox(width: AppSpacing.sm),
              const Text('觀看歷史已清除'),
            ],
          ),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.small),
          ),
          duration: const Duration(seconds: 2),
        ),
      );
    }
  }

  /// 獲取站點的觀看次數
  int _getViewCount(String stationId) {
    return _viewCounts[stationId] ?? 0;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: widget.showAppBar
          ? AppBar(
              title: const Text('UBike 腳踏車'),
              backgroundColor: BikeColors.primary,
              foregroundColor: Colors.white,
              elevation: 0,
              flexibleSpace: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      BikeColors.primary,
                      BikeColors.primaryLight,
                    ],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
              ),
              actions: [
                // 清除歷史按鈕
                if (_viewHistory.isNotEmpty)
                  IconButton(
                    icon: const Icon(Icons.delete_outline),
                    tooltip: '清除觀看歷史',
                    onPressed: _clearAllHistory,
                  ),
              ],
            )
          : null,
      body: Column(
        children: [
          // 搜尋欄
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: AppColors.surface,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: SearchTextField(
              controller: _searchController,
              hintText: '搜尋站點或地點...',
              onChanged: _filterStations,
              onClear: () {
                _searchController.clear();
                _filterStations('');
              },
              onSearch: () => _filterStations(_searchController.text),
            ),
          ),
          // 統計資訊列
          if (_viewHistory.isNotEmpty)
            StationStatsBar(
              stationCount: _viewHistory.length,
              lastUpdateTime: _lastUpdateTime,
              onRefresh: _loadStations,
            ),
          // 站點列表
          Expanded(
            child: _isLoading
                ? const SkeletonLoading(itemCount: 8)
                : _buildStationsList(),
          ),
        ],
      ),
    );
  }

  /// 建立站點列表
  Widget _buildStationsList() {
    if (_filteredStations.isEmpty) {
      return BikeEmptyStateCard(
        searchQuery: _searchController.text,
        onClearSearch: _searchController.text.isNotEmpty
            ? () {
                _searchController.clear();
                _filterStations('');
              }
            : null,
        onRetry: _searchController.text.isEmpty ? _loadStations : null,
      );
    }

    return RefreshIndicator(
      onRefresh: _loadStations,
      color: BikeColors.primary,
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(AppSpacing.md),
        itemCount: _filteredStations.length,
        itemBuilder: (context, index) {
          final station = _filteredStations[index];
          final viewCount = _getViewCount(station.stationId);

          return FadeInAnimation(
            delay: Duration(milliseconds: (index % 10) * 30),
            child: BikeStationCard(
              station: station,
              viewCount: viewCount,
              onTap: () => _selectStation(station),
              onNavigate: () => _openNavigation(station),
            ),
          );
        },
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}
