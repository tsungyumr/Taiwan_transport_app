// station_detail_card.dart
// YouBike 站點底部詳情卡片

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/bike_station.dart';
import '../ui_theme.dart';
import '../l10n/app_localizations.dart';

/// YouBike 站點詳情卡片
class StationDetailCard extends StatelessWidget {
  final BikeStation station;
  final VoidCallback onClose;
  final VoidCallback? onRent;
  final VoidCallback? onReturn;

  const StationDetailCard({
    super.key,
    required this.station,
    required this.onClose,
    this.onRent,
    this.onReturn,
  });

  /// 開啟外部地圖導航
  Future<void> _openNavigation() async {
    final uri = Uri.parse(
      'https://www.google.com/maps/dir/?api=1&destination=${station.lat},${station.lng}&travelmode=walking',
    );
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.vertical(
          top: Radius.circular(AppRadius.large),
        ),
        boxShadow: const [AppShadows.large],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 拖曳指示條
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 12, bottom: 8),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.shade300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          // 標題列
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                // 狀態指示
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: station.statusColor,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                // 站點名稱
                Expanded(
                  child: Text(
                    station.name,
                    style: AppTextStyles.titleLarge.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                // 關閉按鈕
                IconButton(
                  onPressed: onClose,
                  icon: const Icon(Icons.close),
                  color: AppColors.onSurfaceLight,
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          // 地址
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                Icon(
                  Icons.location_on_outlined,
                  size: 16,
                  color: AppColors.onSurfaceLight,
                ),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    station.address,
                    style: AppTextStyles.bodySmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 4),
          // 更新時間
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                Icon(
                  Icons.access_time,
                  size: 14,
                  color: AppColors.onSurfaceLight,
                ),
                const SizedBox(width: 4),
                Text(
                  l10n.bikeUpdatedAt(_formatTime(station.updateTime, l10n)),
                  style: AppTextStyles.labelSmall.copyWith(
                    color: AppColors.onSurfaceLight,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // 統計資訊列
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                _StatItem(
                  icon: Icons.pedal_bike,
                  label: l10n.bikeAvailableBikes,
                  value: '${station.availableBikes}/${station.totalSlots}',
                  color: station.statusColor,
                ),
                const SizedBox(width: 24),
                _StatItem(
                  icon: Icons.local_parking,
                  label: l10n.bikeEmptySlots,
                  value: '${station.emptySlots}',
                  color: AppColors.info,
                ),
                if (station.distance != null) ...[
                  const SizedBox(width: 24),
                  _StatItem(
                    icon: Icons.navigation,
                    label: l10n.bikeDistance,
                    value: station.formattedDistance,
                    color: AppColors.primary,
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          // 操作按鈕列
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                Expanded(
                  child: _ActionButton(
                    icon: Icons.pedal_bike,
                    label: l10n.bikeRent,
                    onTap: onRent,
                    color: BikeColors.primary,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _ActionButton(
                    icon: Icons.local_parking,
                    label: l10n.bikeReturn,
                    onTap: onReturn,
                    color: AppColors.info,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _ActionButton(
                    icon: Icons.navigation,
                    label: l10n.bikeNavigate,
                    onTap: _openNavigation,
                    color: AppColors.success,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  String _formatTime(DateTime time, AppLocalizations l10n) {
    final now = DateTime.now();
    final diff = now.difference(time);

    if (diff.inMinutes < 1) {
      return l10n.bikeJustNow;
    } else if (diff.inMinutes < 60) {
      return l10n.bikeMinutesAgo(diff.inMinutes);
    } else if (diff.inHours < 24) {
      return l10n.bikeHoursAgo(diff.inHours);
    } else {
      return '${time.month}/${time.day} ${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
    }
  }
}

/// 統計項目
class _StatItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _StatItem({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(AppRadius.small),
          ),
          child: Icon(
            icon,
            size: 20,
            color: color,
          ),
        ),
        const SizedBox(width: 8),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: AppTextStyles.labelSmall.copyWith(
                color: AppColors.onSurfaceLight,
              ),
            ),
            Text(
              value,
              style: AppTextStyles.titleMedium.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

/// 操作按鈕
class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  final Color color;

  const _ActionButton({
    required this.icon,
    required this.label,
    this.onTap,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(AppRadius.medium),
          border: Border.all(
            color: color.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Column(
          children: [
            Icon(
              icon,
              size: 24,
              color: color,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: AppTextStyles.labelMedium.copyWith(
                color: color,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
