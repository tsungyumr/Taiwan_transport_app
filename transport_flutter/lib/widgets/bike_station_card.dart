// bike_station_card.dart
// UBike 站點卡片元件

import 'package:flutter/material.dart';
import '../models/bike_station.dart';
import '../ui_theme.dart';

/// UBike 站點卡片
class BikeStationCard extends StatelessWidget {
  final BikeStation station;
  final int viewCount;
  final VoidCallback? onTap;
  final VoidCallback? onNavigate;

  const BikeStationCard({
    super.key,
    required this.station,
    this.viewCount = 0,
    this.onTap,
    this.onNavigate,
  });

  /// 計算卡片高度（根據觀看次數）
  double get _cardHeight {
    // 基礎高度 100，每增加 1 次增加 8，最大 120
    final height = 100.0 + (viewCount * 8.0);
    return height.clamp(100.0, 120.0);
  }

  /// 計算卡片寬度比例（根據觀看次數）
  double get _cardWidthFactor {
    // 基礎寬度 0.95，每增加 1 次增加 0.02，最大 1.0
    final factor = 0.95 + (viewCount * 0.02);
    return factor.clamp(0.95, 1.0);
  }

  /// 計算透明度（根據觀看次數）
  double get _cardOpacity {
    // 基礎透明度 0.3，每增加 1 次增加 0.1，最大 1.0
    final opacity = 0.3 + (viewCount * 0.1);
    return opacity.clamp(0.3, 1.0);
  }

  /// 計算背景顏色
  Color get _cardColor {
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
    final cardColor = _cardColor;
    final widthFactor = _cardWidthFactor;
    final opacity = _cardOpacity;

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
            borderRadius: BorderRadius.circular(AppRadius.large),
            side: viewCount > 0
                ? BorderSide(
                    color: Colors.green.shade300.withOpacity(opacity),
                    width: 1 + (viewCount * 0.1).clamp(0, 2),
                  )
                : BorderSide.none,
          ),
          color: cardColor.withOpacity(opacity),
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(AppRadius.large),
            child: Container(
              height: _cardHeight,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  // 狀態指示圓點
                  _StatusDot(status: station.status, size: 16),
                  const SizedBox(width: 12),
                  // 站點資訊
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // 站點名稱
                        Text(
                          station.name,
                          style: TextStyle(
                            fontSize: 16 + (viewCount * 0.5).clamp(0, 4),
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
                        // 地址
                        Row(
                          children: [
                            Icon(
                              Icons.location_on_outlined,
                              size: 14,
                              color: AppColors.onSurfaceLight,
                            ),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                station.address,
                                style: TextStyle(
                                  fontSize: 12 + (viewCount * 0.3).clamp(0, 2),
                                  color: AppColors.onSurfaceLight,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        // 剩餘車輛
                        _BikeCountBadge(
                          count: station.availableBikes,
                          total: station.totalSlots,
                        ),
                      ],
                    ),
                  ),
                  // 距離和導航按鈕
                  Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (station.distance != null)
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(AppRadius.small),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.location_on,
                                size: 12,
                                color: AppColors.primary,
                              ),
                              const SizedBox(width: 2),
                              Text(
                                station.formattedDistance,
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500,
                                  color: AppColors.primaryDark,
                                ),
                              ),
                            ],
                          ),
                        ),
                      const SizedBox(height: 8),
                      // 觀看次數標示
                      if (viewCount > 0)
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
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
                              Icon(
                                Icons.visibility,
                                size: 12,
                                color: Colors.white,
                              ),
                              const SizedBox(width: 2),
                              Text(
                                '$viewCount',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(width: 8),
                  // 導航按鈕
                  _NavigateButton(onTap: onNavigate),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// 狀態指示圓點
class _StatusDot extends StatelessWidget {
  final BikeStatus status;
  final double size;

  const _StatusDot({
    required this.status,
    this.size = 16,
  });

  Color get _color {
    switch (status) {
      case BikeStatus.available:
        return BikeColors.available;
      case BikeStatus.limited:
        return BikeColors.limited;
      case BikeStatus.few:
        return BikeColors.few;
      case BikeStatus.empty:
        return BikeColors.empty;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: _color,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: _color.withOpacity(0.4),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
    );
  }
}

/// 剩餘車輛數標籤
class _BikeCountBadge extends StatelessWidget {
  final int count;
  final int total;

  const _BikeCountBadge({
    required this.count,
    required this.total,
  });

  Color get _color {
    if (count == 0) return BikeColors.empty;
    if (count < 5) return BikeColors.few;
    if (count < 10) return BikeColors.limited;
    return BikeColors.available;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(AppRadius.small),
        border: Border.all(
          color: _color.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.pedal_bike,
            size: 14,
            color: _color,
          ),
          const SizedBox(width: 4),
          Text(
            count == 0 ? '暫無車輛' : '剩餘 $count/$total 輛',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: _color,
            ),
          ),
        ],
      ),
    );
  }
}

/// 導航按鈕
class _NavigateButton extends StatelessWidget {
  final VoidCallback? onTap;

  const _NavigateButton({this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              AppColors.primary,
              AppColors.primary.withOpacity(0.8),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: AppColors.primary.withOpacity(0.3),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: const Icon(
          Icons.navigation,
          color: Colors.white,
          size: 20,
        ),
      ),
    );
  }
}

/// 站點統計列
class StationStatsBar extends StatelessWidget {
  final int stationCount;
  final VoidCallback? onRefresh;
  final DateTime? lastUpdateTime;

  const StationStatsBar({
    super.key,
    required this.stationCount,
    this.onRefresh,
    this.lastUpdateTime,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      color: AppColors.surface.withOpacity(0.5),
      child: Row(
        children: [
          Icon(
            Icons.location_on,
            size: 16,
            color: BikeColors.primary,
          ),
          const SizedBox(width: AppSpacing.xs),
          Text(
            '已記錄 $stationCount 個常用站點',
            style: AppTextStyles.labelSmall.copyWith(
              color: AppColors.onSurfaceLight,
            ),
          ),
          if (lastUpdateTime != null) ...[
            const Spacer(),
            Text(
              '更新於 ${_formatTime(lastUpdateTime!)}',
              style: AppTextStyles.labelSmall.copyWith(
                color: AppColors.onSurfaceLight,
                fontSize: 10,
              ),
            ),
            const SizedBox(width: AppSpacing.xs),
            if (onRefresh != null)
              GestureDetector(
                onTap: onRefresh,
                child: Icon(
                  Icons.refresh,
                  size: 14,
                  color: AppColors.primary,
                ),
              ),
          ],
        ],
      ),
    );
  }

  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final diff = now.difference(time);

    if (diff.inMinutes < 1) {
      return '剛剛';
    } else if (diff.inMinutes < 60) {
      return '${diff.inMinutes} 分鐘前';
    } else if (diff.inHours < 24) {
      return '${diff.inHours} 小時前';
    } else {
      return '${time.month}/${time.day} ${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
    }
  }
}

/// 站點空狀態卡片
class BikeEmptyStateCard extends StatelessWidget {
  final String? searchQuery;
  final VoidCallback? onClearSearch;
  final VoidCallback? onRetry;

  const BikeEmptyStateCard({
    super.key,
    this.searchQuery,
    this.onClearSearch,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    final isSearching = searchQuery != null && searchQuery!.isNotEmpty;

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: BikeColors.primary.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                isSearching ? Icons.search_off : Icons.pedal_bike,
                size: 40,
                color: BikeColors.primary,
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              isSearching ? '找不到站點' : '暫無站點資料',
              style: AppTextStyles.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              isSearching
                  ? '沒有符合 "$searchQuery" 的站點'
                  : '目前沒有可用的 UBike 站點資料',
              style: AppTextStyles.bodySmall,
              textAlign: TextAlign.center,
            ),
            if (isSearching && onClearSearch != null) ...[
              const SizedBox(height: AppSpacing.lg),
              ElevatedButton(
                onPressed: onClearSearch,
                child: const Text('清除搜尋'),
              ),
            ] else if (!isSearching && onRetry != null) ...[
              const SizedBox(height: AppSpacing.lg),
              ElevatedButton(
                onPressed: onRetry,
                child: const Text('重新載入'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
