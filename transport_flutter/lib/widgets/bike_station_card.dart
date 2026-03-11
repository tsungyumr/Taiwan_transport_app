// bike_station_card.dart
// UBike 站點卡片元件

import 'package:flutter/material.dart';
import '../models/bike_station.dart';
import '../ui_theme.dart';

/// UBike 站點卡片
class BikeStationCard extends StatelessWidget {
  final BikeStation station;
  final VoidCallback? onTap;
  final VoidCallback? onNavigate;

  const BikeStationCard({
    super.key,
    required this.station,
    this.onTap,
    this.onNavigate,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: FractionallySizedBox(
        widthFactor: 0.95,
        child: Card(
          margin: const EdgeInsets.symmetric(vertical: 6),
          elevation: 2,
          shadowColor: Colors.black.withOpacity(0.1),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.large),
          ),
          color: Colors.white,
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(AppRadius.large),
            child: Container(
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
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // 站點名稱
                        Text(
                          station.name,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        // 地址
                        Text(
                          station.address,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 8),
                        // 車輛資訊
                        Row(
                          children: [
                            // 可借車輛
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: station.statusColor.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                '可借 ${station.availableBikes}/${station.totalSlots}',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: station.statusColor,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            // 距離（如果有）
                            if (station.distance != null)
                              Text(
                                station.formattedDistance,
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[600],
                                ),
                              ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  // 導航按鈕
                  if (onNavigate != null)
                    IconButton(
                      icon: const Icon(Icons.navigation, color: BikeColors.primary),
                      onPressed: onNavigate,
                    ),
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

/// 站點統計列
class StationStatsBar extends StatelessWidget {
  final int stationCount;
  final int? totalStations;
  final List<String>? cities;
  final VoidCallback? onRefresh;
  final DateTime? lastUpdateTime;

  const StationStatsBar({
    super.key,
    this.stationCount = 0,
    this.totalStations,
    this.cities,
    this.onRefresh,
    this.lastUpdateTime,
  });

  @override
  Widget build(BuildContext context) {
    // 城市代碼轉中文
    final cityNameMap = {
      'Taipei': '台北市',
      'NewTaipei': '新北市',
      'Taichung': '台中市',
      'Tainan': '台南市',
      'Kaohsiung': '高雄市',
      'Taoyuan': '桃園市',
    };
    final cityText = cities != null && cities!.isNotEmpty
        ? cities!.map((c) => cityNameMap[c] ?? c).join('、')
        : '';

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
          Expanded(
            child: Text(
              totalStations != null
                  ? '共 $totalStations 個站點 ($cityText)'
                  : '已記錄 $stationCount 個常用站點',
              style: AppTextStyles.labelSmall.copyWith(
                color: AppColors.onSurfaceLight,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (lastUpdateTime != null) ...[
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
    final isLocationError = searchQuery == 'location_error';

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
                isLocationError
                    ? Icons.location_off
                    : (isSearching ? Icons.search_off : Icons.pedal_bike),
                size: 40,
                color: isLocationError ? AppColors.error : BikeColors.primary,
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              isLocationError
                  ? '無法取得位置'
                  : (isSearching ? '找不到站點' : '暫無站點資料'),
              style: AppTextStyles.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              isLocationError
                  ? '請確認 GPS 已開啟並允許位置權限'
                  : (isSearching
                      ? '沒有符合 "$searchQuery" 的站點'
                      : '目前沒有可用的 UBike 站點資料'),
              style: AppTextStyles.bodySmall,
              textAlign: TextAlign.center,
            ),
            if ((isSearching) && onClearSearch != null) ...[
              const SizedBox(height: AppSpacing.lg),
              ElevatedButton(
                onPressed: onClearSearch,
                child: const Text('清除搜尋'),
              ),
            ] else if (isLocationError && onRetry != null) ...[
              const SizedBox(height: AppSpacing.lg),
              ElevatedButton(
                onPressed: onRetry,
                child: const Text('重試取得位置'),
              ),
            ] else if (!isSearching && !isLocationError && onRetry != null) ...[
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
