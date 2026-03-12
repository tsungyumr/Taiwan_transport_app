import 'package:flutter/material.dart';
import '../main.dart';
import '../l10n/app_localizations.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../services/search_history_service.dart';
import '../widgets/animated_card.dart';
import '../widgets/loading_animations.dart';
import '../widgets/styled_inputs.dart';
import '../ui_theme.dart';
import 'bus_route_page.dart';

class BusScreen extends StatefulWidget {
  const BusScreen({super.key});

  @override
  State<BusScreen> createState() => _BusScreenState();
}

class _BusScreenState extends State<BusScreen> {
  final ApiService _apiService = ApiService();
  final BusSearchHistoryService _historyService = BusSearchHistoryService();
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  List<BusRoute> _allRoutes = []; // 所有路線
  List<BusRoute> _filteredRoutes = []; // 篩選後的路線
  List<BusSearchHistoryItem> _viewHistory = []; // 觀看歷史
  Map<String, int> _viewCounts = {}; // 路線ID -> 觀看次數
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadAllRoutes(); // 這會自動載入歷史並排序
  }

  /// 載入所有公車路線
  Future<void> _loadAllRoutes() async {
    setState(() => _isLoading = true);

    final routes = await _apiService.getBusRoutes();

    if (!mounted) return;

    setState(() {
      _allRoutes = routes;
      _filteredRoutes = routes;
      _isLoading = false;
    });

    // 載入觀看歷史後排序（讓常看的路線排在前面）
    await _loadViewHistory();
  }

  /// 載入觀看歷史
  Future<void> _loadViewHistory() async {
    final history = await _historyService.getSearchHistory();

    // 建立觀看次數對照表
    final viewCounts = <String, int>{};
    for (final item in history) {
      viewCounts[item.routeId] = item.searchCount;
    }

    if (!mounted) return;

    setState(() {
      _viewHistory = history;
      _viewCounts = viewCounts;
      // 根據觀看次數排序（常看的排在最前面）
      _sortRoutesByPopularity();
    });
  }

  /// 搜尋/篩選路線
  void _filterRoutes(String query) {
    setState(() {
      if (query.isEmpty) {
        _filteredRoutes = _allRoutes;
      } else {
        _filteredRoutes = _allRoutes.where((route) {
          return route.routeName.toLowerCase().contains(query.toLowerCase()) ||
                 route.departureStop.toLowerCase().contains(query.toLowerCase()) ||
                 route.arrivalStop.toLowerCase().contains(query.toLowerCase());
        }).toList();
      }
      // 根據觀看次數排序（熱門的在前）
      _sortRoutesByPopularity();
    });
  }

  /// 根據熱門程度排序路線
  void _sortRoutesByPopularity() {
    _filteredRoutes.sort((a, b) {
      final countA = _viewCounts[a.routeId] ?? 0;
      final countB = _viewCounts[b.routeId] ?? 0;
      // 先按觀看次數降序排序
      if (countA != countB) {
        return countB.compareTo(countA); // 次數高的在前
      }
      // 次數相同時，按路線名稱排序
      return a.routeName.compareTo(b.routeName);
    });
  }

  /// 選擇路線（點擊觀看）
  Future<void> _selectRoute(BusRoute route) async {
    // 記錄觀看歷史
    await _historyService.recordSearch(route);

    if (!mounted) return;

    // 導航到路線詳情頁
    await Navigator.push(
      context,
      SlidePageRoute(builder: (context) => BusRoutePage(route: route.routeName)),
    );

    // 返回後重新載入歷史並排序（讓常看的路線排在前面）
    if (mounted) {
      await _loadViewHistory();
    }
  }

  /// 清除所有觀看歷史
  Future<void> _clearAllHistory() async {
    final l10n = AppLocalizations.of(context)!;

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
            Text(l10n.busClearHistoryConfirmTitle),
          ],
        ),
        content: Text(l10n.busClearHistoryConfirmContent),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(l10n.commonCancel),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
            ),
            child: Text(l10n.commonClear),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _historyService.clearHistory();
      await _loadViewHistory();
      // 重新排序（恢復預設排序）
      setState(() {
        _sortRoutesByPopularity();
      });

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.check_circle, color: Colors.white),
              const SizedBox(width: AppSpacing.sm),
              Text(l10n.busHistoryCleared),
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

  /// 獲取路線的觀看次數
  int _getViewCount(String routeId) {
    return _viewCounts[routeId] ?? 0;
  }

  /// 計算卡片透明度（根據觀看次數）
  double _getCardOpacity(int viewCount) {
    // 基礎透明度 0.3，每增加 1 次增加 0.1，最大 1.0
    final opacity = 0.3 + (viewCount * 0.1);
    return opacity.clamp(0.3, 1.0);
  }

  /// 計算卡片高度（根據觀看次數）
  double _getCardHeight(int viewCount) {
    // 基礎高度 80，每增加 1 次增加 8，最大 120
    final height = 80.0 + (viewCount * 8.0);
    return height.clamp(80.0, 120.0);
  }

  /// 計算卡片寬度比例（根據觀看次數）
  double _getCardWidthFactor(int viewCount) {
    // 基礎寬度 0.95，每增加 1 次增加 0.02，最大 1.0
    final factor = 0.95 + (viewCount * 0.02);
    return factor.clamp(0.95, 1.0);
  }

  /// 計算背景顏色深淺（根據觀看次數）
  Color _getCardColor(int viewCount) {
    // 基礎顏色（淺綠色）到深色（深綠色）
    if (viewCount == 0) {
      return Colors.white;
    } else if (viewCount <= 2) {
      return Colors.green.shade50;
    } else if (viewCount <= 5) {
      return Colors.green.shade100;
    } else if (viewCount <= 10) {
      return Colors.green.shade200;
    } else {
      return Colors.green.shade300;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.busTitle),
        backgroundColor: TransportColors.bus,
        foregroundColor: Colors.white,
        elevation: 0,
        flexibleSpace: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                TransportColors.bus,
                TransportColors.bus.withOpacity(0.8),
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
              tooltip: l10n.busTooltipClearHistory,
              onPressed: _clearAllHistory,
            ),
        ],
      ),
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
              hintText: l10n.busSearchHint,
              onChanged: _filterRoutes,
              onClear: () {
                _searchController.clear();
                _filterRoutes('');
              },
              onSearch: () => _filterRoutes(_searchController.text),
            ),
          ),
          // 統計資訊
          if (_viewHistory.isNotEmpty)
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md,
                vertical: AppSpacing.sm,
              ),
              color: AppColors.surface.withOpacity(0.5),
              child: Row(
                children: [
                  Icon(
                    Icons.trending_up,
                    size: 16,
                    color: AppColors.primary,
                  ),
                  const SizedBox(width: AppSpacing.xs),
                  Text(
                    l10n.busViewCount(_viewHistory.length),
                    style: AppTextStyles.labelSmall.copyWith(
                      color: AppColors.onSurfaceLight,
                    ),
                  ),
                  const Spacer(),
                  Flexible(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.sm,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.green.shade100,
                        borderRadius: BorderRadius.circular(AppRadius.small),
                      ),
                      child: Text(
                        l10n.busColorIndicator,
                        style: AppTextStyles.labelSmall.copyWith(
                          color: Colors.green.shade800,
                          fontSize: 10,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          // 路線列表
          Expanded(
            child: _isLoading
                ? const SkeletonLoading(itemCount: 8)
                : _buildRoutesList(),
          ),
        ],
      ),
    );
  }

  /// 建立路線列表
  Widget _buildRoutesList() {
    final l10n = AppLocalizations.of(context)!;

    if (_filteredRoutes.isEmpty) {
      return EmptyStateCard(
        icon: Icons.directions_bus_outlined,
        title: l10n.busNoRoutesFound,
        subtitle: _searchController.text.isEmpty
            ? l10n.busNoRoutesEmpty
            : l10n.busNoRoutesSearch(_searchController.text),
        onAction: _searchController.text.isNotEmpty
            ? () {
                _searchController.clear();
                _filterRoutes('');
              }
            : _loadAllRoutes,
        actionLabel: _searchController.text.isNotEmpty ? l10n.busClearSearch : l10n.busReload,
      );
    }

    return RefreshIndicator(
      onRefresh: _loadAllRoutes,
      color: AppColors.primary,
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(AppSpacing.md),
        itemCount: _filteredRoutes.length,
        itemBuilder: (context, index) {
          final route = _filteredRoutes[index];
          final viewCount = _getViewCount(route.routeId);

          return FadeInAnimation(
            delay: Duration(milliseconds: (index % 10) * 30),
            child: _buildDynamicRouteCard(route, viewCount),
          );
        },
      ),
    );
  }

  /// 建立動態路線卡片（根據觀看次數調整樣式）
  Widget _buildDynamicRouteCard(BusRoute route, int viewCount) {
    final cardColor = _getCardColor(viewCount);
    final cardHeight = _getCardHeight(viewCount);
    final widthFactor = _getCardWidthFactor(viewCount);
    final opacity = _getCardOpacity(viewCount);

    // 計算字體大小（根據觀看次數）
    final titleFontSize = 16.0 + (viewCount * 0.5).clamp(0, 4);
    final subtitleFontSize = 12.0 + (viewCount * 0.3).clamp(0, 2);

    return Center(
      child: FractionallySizedBox(
        widthFactor: widthFactor,
        child: Card(
          margin: const EdgeInsets.symmetric(vertical: 6),
          elevation: viewCount > 0 ? 4 + (viewCount * 0.5).clamp(0, 6) : 2,
          shadowColor: viewCount > 0
              ? Colors.green.withOpacity(0.3)
              : Colors.black.withOpacity(0.1),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: viewCount > 0
                ? BorderSide(
                    color: Colors.green.shade300.withOpacity(opacity),
                    width: 1 + (viewCount * 0.1).clamp(0, 2),
                  )
                : BorderSide.none,
          ),
          color: cardColor.withOpacity(opacity),
          child: InkWell(
            onTap: () => _selectRoute(route),
            borderRadius: BorderRadius.circular(16),
            child: Container(
              height: cardHeight,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  // 路線號碼（圓形頭像）
                  Container(
                    width: (48 + (viewCount * 2).clamp(0, 12)).toDouble(),
                    height: (48 + (viewCount * 2).clamp(0, 12)).toDouble(),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: viewCount > 0
                            ? [
                                Colors.green.shade400,
                                Colors.green.shade600,
                              ]
                            : [
                                TransportColors.bus,
                                TransportColors.bus.withOpacity(0.8),
                              ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      shape: BoxShape.circle,
                      boxShadow: viewCount > 0
                          ? [
                              BoxShadow(
                                color: Colors.green.withOpacity(0.4),
                                blurRadius: 8,
                                offset: const Offset(0, 2),
                              ),
                            ]
                          : null,
                    ),
                    child: Center(
                      child: Text(
                        route.routeName.length > 4
                            ? route.routeName.substring(0, 4)
                            : route.routeName,
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 14 + (viewCount * 0.3).clamp(0, 4),
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  // 路線資訊
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          '${route.departureStop} → ${route.arrivalStop}',
                          style: TextStyle(
                            fontSize: titleFontSize,
                            fontWeight: viewCount > 0
                                ? FontWeight.bold
                                : FontWeight.w600,
                            color: viewCount > 5
                                ? Colors.green.shade900
                                : AppColors.onSurface,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          route.operator,
                          style: TextStyle(
                            fontSize: subtitleFontSize,
                            color: AppColors.onSurfaceLight,
                          ),
                        ),
                      ],
                    ),
                  ),
                  // 觀看次數標示
                  if (viewCount > 0)
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [
                            Colors.amber.shade300,
                            Colors.amber.shade500,
                          ],
                        ),
                        borderRadius: BorderRadius.circular(12),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.amber.withOpacity(0.3),
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.visibility,
                            size: 14,
                            color: Colors.white,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '$viewCount',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                  // 箭頭圖標
                  const SizedBox(width: 8),
                  Icon(
                    Icons.chevron_right,
                    color: viewCount > 0
                        ? Colors.green.shade700
                        : AppColors.onSurfaceLight,
                    size: 24 + (viewCount * 0.5).clamp(0, 8),
                  ),
                ],
              ),
            ),
          ),
        ),
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
