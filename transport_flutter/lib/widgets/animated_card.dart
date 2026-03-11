// animated_card.dart
// 美化動畫卡片元件

import 'package:flutter/material.dart';
import '../ui_theme.dart';

/// 動畫卡片 - 帶有陰影、圓角和觸碰反饋
class AnimatedCard extends StatefulWidget {
  final Widget child;
  final VoidCallback? onTap;
  final double elevation;
  final Color? color;
  final EdgeInsetsGeometry padding;
  final EdgeInsetsGeometry margin;
  final BorderRadius? borderRadius;
  final Duration animationDuration;

  const AnimatedCard({
    super.key,
    required this.child,
    this.onTap,
    this.elevation = 2,
    this.color,
    this.padding = const EdgeInsets.all(AppSpacing.md),
    this.margin = const EdgeInsets.symmetric(
      horizontal: AppSpacing.md,
      vertical: AppSpacing.sm,
    ),
    this.borderRadius,
    this.animationDuration = AppAnimations.normal,
  });

  @override
  State<AnimatedCard> createState() => _AnimatedCardState();
}

class _AnimatedCardState extends State<AnimatedCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: AppAnimations.fast,
      vsync: this,
    );
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.98,
    ).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
    }

  void _onTapDown(TapDownDetails details) {
    _controller.forward();
  }

  void _onTapUp(TapUpDetails details) {
    _controller.reverse();
  }

  void _onTapCancel() {
    _controller.reverse();
  }

  @override
  Widget build(BuildContext context) {
    final borderRadius = widget.borderRadius ??
        BorderRadius.circular(AppRadius.medium);

    return AnimatedBuilder(
      animation: _scaleAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _scaleAnimation.value,
          child: Container(
            margin: widget.margin,
            decoration: BoxDecoration(
              color: widget.color ?? AppColors.surface,
              borderRadius: borderRadius,
              boxShadow: [
                BoxShadow(
                  color: const Color(0x26000000),
                  blurRadius: widget.elevation * 4,
                  offset: Offset(0, widget.elevation * 2),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: borderRadius,
              child: Material(
                color: Colors.transparent,
                child: widget.onTap != null
                    ? InkWell(
                        onTap: widget.onTap,
                        onTapDown: _onTapDown,
                        onTapUp: _onTapUp,
                        onTapCancel: _onTapCancel,
                        child: Padding(
                          padding: widget.padding,
                          child: widget.child,
                        ),
                      )
                    : Padding(
                        padding: widget.padding,
                        child: widget.child,
                      ),
              ),
            ),
          ),
        );
      },
    );
  }
}

/// 交通工具卡片 - 首頁使用的選擇卡片
class TransportCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  final double? height;

  const TransportCard({
    super.key,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.onTap,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedCard(
      onTap: onTap,
      elevation: 3,
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Row(
        children: [
          // 圖標容器
          Hero(
            tag: 'transport_icon_$title',
            child: Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    color.withOpacity(0.2),
                    color.withOpacity(0.1),
                  ],
                ),
                borderRadius: BorderRadius.circular(AppRadius.medium),
              ),
              child: Icon(icon, size: 32, color: color),
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          // 文字內容
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: AppTextStyles.titleLarge.copyWith(
                    color: AppColors.onSurface,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  subtitle,
                  style: AppTextStyles.bodySmall,
                ),
              ],
            ),
          ),
          // 箭頭
          Icon(
            Icons.arrow_forward_ios,
            size: 16,
            color: color.withOpacity(0.6),
          ),
        ],
      ),
    );
  }
}

/// 時間表項目卡片 - 用於顯示火車/高鐵時刻
class TimetableCard extends StatelessWidget {
  final String trainNo;
  final String fromStation;
  final String toStation;
  final String departureTime;
  final String arrivalTime;
  final String duration;
  final Color accentColor;
  final String? trainType;
  final Widget? trailing;
  final List<Widget>? extras;

  const TimetableCard({
    super.key,
    required this.trainNo,
    required this.fromStation,
    required this.toStation,
    required this.departureTime,
    required this.arrivalTime,
    required this.duration,
    required this.accentColor,
    this.trainType,
    this.trailing,
    this.extras,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedCard(
      elevation: 2,
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 頂部資訊列
          Row(
            children: [
              // 車次標籤
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.sm,
                  vertical: AppSpacing.xs,
                ),
                decoration: BoxDecoration(
                  color: accentColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppRadius.small),
                ),
                child: Text(
                  trainType != null ? '$trainType $trainNo' : '車次 $trainNo',
                  style: AppTextStyles.labelLarge.copyWith(color: accentColor),
                ),
              ),
              const Spacer(),
              if (trailing != null) trailing!,
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          // 時間顯示
          Row(
            children: [
              // 出發時間
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      departureTime,
                      style: AppTextStyles.headlineSmall.copyWith(
                        color: accentColor,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      fromStation,
                      style: AppTextStyles.bodySmall,
                    ),
                  ],
                ),
              ),
              // 箭頭和時間
              Expanded(
                flex: 2,
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: accentColor.withOpacity(0.5),
                            shape: BoxShape.circle,
                          ),
                        ),
                        Expanded(
                          child: Container(
                            height: 2,
                            margin: const EdgeInsets.symmetric(
                              horizontal: AppSpacing.xs,
                            ),
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                colors: [
                                  accentColor.withOpacity(0.5),
                                  accentColor.withOpacity(0.3),
                                ],
                              ),
                            ),
                          ),
                        ),
                        Icon(Icons.arrow_forward, size: 16, color: accentColor),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.sm,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.background,
                        borderRadius: BorderRadius.circular(AppRadius.full),
                      ),
                      child: Text(
                        duration,
                        style: AppTextStyles.labelSmall,
                      ),
                    ),
                  ],
                ),
              ),
              // 抵達時間
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      arrivalTime,
                      style: AppTextStyles.headlineSmall.copyWith(
                        color: AppColors.onSurface,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      toStation,
                      style: AppTextStyles.bodySmall,
                      textAlign: TextAlign.right,
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (extras != null && extras!.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.md),
            const Divider(height: 1),
            const SizedBox(height: AppSpacing.sm),
            ...extras!,
          ],
        ],
      ),
    );
  }
}

/// 公車路線卡片
class BusRouteCard extends StatelessWidget {
  final String routeName;
  final String fromStop;
  final String toStop;
  final String operator;
  final VoidCallback onTap;

  const BusRouteCard({
    super.key,
    required this.routeName,
    required this.fromStop,
    required this.toStop,
    required this.operator,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedCard(
      onTap: onTap,
      elevation: 2,
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Row(
        children: [
          // 路線編號圓形
          Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [AppColors.bus, AppColors.bus.withOpacity(0.7)],
              ),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                routeName.length > 3 ? routeName.substring(0, 3) : routeName,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          // 路線資訊
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  routeName,
                  style: AppTextStyles.titleMedium,
                ),
                const SizedBox(height: AppSpacing.xs),
                Row(
                  children: [
                    Icon(Icons.location_on_outlined,
                        size: 14, color: AppColors.onSurfaceLight),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        '$fromStop → $toStop',
                        style: AppTextStyles.bodySmall,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          // 營運商標籤
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.sm,
              vertical: AppSpacing.xs,
            ),
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(AppRadius.full),
            ),
            child: Text(
              operator,
              style: AppTextStyles.labelSmall.copyWith(
                color: AppColors.primaryDark,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// 公車站點卡片
class BusStopCard extends StatelessWidget {
  final String stopName;
  final String eta;
  final int? busCount;
  final bool isActive;
  final VoidCallback? onTap;

  const BusStopCard({
    super.key,
    required this.stopName,
    required this.eta,
    this.busCount,
    this.isActive = false,
    this.onTap,
  });

  Color get _etaColor {
    if (eta == '即將進站') return AppColors.success;
    if (eta.contains('分') || eta.contains('min')) {
      final minutes = int.tryParse(eta.replaceAll(RegExp(r'[^0-9]'), ''));
      if (minutes != null && minutes < 5) return AppColors.warning;
    }
    return AppColors.onSurfaceLight;
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedCard(
      onTap: onTap,
      elevation: isActive ? 3 : 1,
      color: isActive ? AppColors.primary.withOpacity(0.05) : null,
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Row(
        children: [
          // 站點編號指示器
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: isActive ? AppColors.primary : AppColors.divider,
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Icon(
                Icons.location_on,
                size: 18,
                color: isActive ? Colors.white : AppColors.onSurfaceLight,
              ),
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          // 站名
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  stopName,
                  style: AppTextStyles.titleSmall.copyWith(
                    color: isActive ? AppColors.primaryDark : AppColors.onSurface,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  eta,
                  style: AppTextStyles.bodySmall.copyWith(
                    color: _etaColor,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          // 公車數量指示
          if (busCount != null && busCount! > 0)
            Container(
              padding: const EdgeInsets.all(AppSpacing.sm),
              decoration: BoxDecoration(
                color: AppColors.bus.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Badge(
                label: Text('$busCount'),
                child: const Icon(
                  Icons.directions_bus,
                  size: 20,
                  color: AppColors.bus,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// 資訊統計卡片
class StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;
  final VoidCallback? onTap;

  const StatCard({
    super.key,
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedCard(
      onTap: onTap,
      elevation: 2,
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.sm),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(AppRadius.small),
            ),
            child: Icon(icon, size: 24, color: color),
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            value,
            style: AppTextStyles.headlineSmall.copyWith(
              color: AppColors.onSurface,
            ),
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            title,
            style: AppTextStyles.bodySmall,
          ),
        ],
      ),
    );
  }
}

/// 載入骨架屏
class SkeletonCard extends StatelessWidget {
  final double height;
  final EdgeInsetsGeometry margin;

  const SkeletonCard({
    super.key,
    this.height = 80,
    this.margin = const EdgeInsets.symmetric(
      horizontal: AppSpacing.md,
      vertical: AppSpacing.sm,
    ),
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      margin: margin,
      decoration: BoxDecoration(
        color: AppColors.divider,
        borderRadius: BorderRadius.circular(AppRadius.medium),
      ),
    );
  }
}

/// 空狀態卡片
class EmptyStateCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final VoidCallback? onAction;
  final String? actionLabel;

  const EmptyStateCard({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    this.onAction,
    this.actionLabel,
  });

  @override
  Widget build(BuildContext context) {
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
                color: AppColors.primary.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                icon,
                size: 40,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              title,
              style: AppTextStyles.headlineSmall,
              textAlign: TextAlign.center,
            ),
            if (subtitle != null) ...[
              const SizedBox(height: AppSpacing.sm),
              Text(
                subtitle!,
                style: AppTextStyles.bodySmall,
                textAlign: TextAlign.center,
              ),
            ],
            if (onAction != null && actionLabel != null) ...[
              const SizedBox(height: AppSpacing.lg),
              ElevatedButton(
                onPressed: onAction,
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
