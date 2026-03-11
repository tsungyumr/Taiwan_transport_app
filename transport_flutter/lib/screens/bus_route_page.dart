import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/bus_route.dart';
import '../services/bus_api_service.dart';
import '../widgets/animated_card.dart';
import '../widgets/loading_animations.dart';
import '../widgets/bus_route_timeline.dart';
import '../ui_theme.dart';

class BusRouteNotifier extends ChangeNotifier {
  BusRouteData? data;
  DateTime? lastUpdated;
  String? error;
  Timer? _timer;
  final BusApiService _api = BusApiService();
  final String route;
  bool _isDisposed = false;
  int _currentDirection = 0; // 當前方向：0=去程, 1=返程

  BusRouteNotifier(this.route) {
    fetchData();
    startPolling();
  }

  int get currentDirection => _currentDirection;

  // 切換方向
  Future<void> switchDirection(int direction) async {
    if (_currentDirection == direction) return;
    _currentDirection = direction;
    await fetchData();
  }

  // 安全的通知方法，避免在 dispose 後呼叫
  void _safeNotifyListeners() {
    if (!_isDisposed) {
      notifyListeners();
    }
  }

  Future<void> fetchData() async {
    try {
      data = await BusApiService.fetchBusRouteData(route,
          direction: _currentDirection);
      // 檢查 await 後是否已被 dispose
      if (_isDisposed) return;
      lastUpdated = DateTime.now();
      error = null;
      _safeNotifyListeners();
    } catch (e) {
      // 檢查 catch 後是否已被 dispose
      if (_isDisposed) return;
      error = e.toString();
      _safeNotifyListeners();
    }
  }

  void startPolling() {
    _timer =
        Timer.periodic(const Duration(seconds: 30), (timer) => fetchData());
  }

  @override
  void dispose() {
    _isDisposed = true;
    _timer?.cancel();
    super.dispose();
  }
}

class BusRoutePage extends StatelessWidget {
  final String route;
  const BusRoutePage({super.key, required this.route});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => BusRouteNotifier(route),
      child: Scaffold(
        appBar: AppBar(
          title: Text('$route 公車路線'),
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
        ),
        body: Consumer<BusRouteNotifier>(
          builder: (context, notifier, child) {
            // 取得方向名稱（使用資料或預設值）
            String goDirectionName = '往 終點站';
            String backDirectionName = '往 起點站';

            if (notifier.data != null) {
              final data = notifier.data!;
              if (data.direction.go != null) {
                goDirectionName =
                    data.direction.go!['direction_name'] ?? '往 終點站';
              }
              if (data.direction.back != null) {
                backDirectionName =
                    data.direction.back!['direction_name'] ?? '往 起點站';
              }
            }

            return Column(
              children: [
                // ===== 方向切換按鈕區 =====
                Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: TransportColors.bus,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      // 去程按鈕
                      Expanded(
                        child: AnimatedScaleButton(
                          onTap: notifier.data == null ||
                                  notifier.currentDirection == 0
                              ? () {}
                              : () => notifier.switchDirection(0),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: notifier.currentDirection == 0
                                  ? Colors.white
                                  : TransportColors.bus.withOpacity(0.7),
                              borderRadius:
                                  BorderRadius.circular(AppRadius.medium),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.arrow_forward,
                                  size: 18,
                                  color: notifier.currentDirection == 0
                                      ? TransportColors.bus
                                      : Colors.white,
                                ),
                                const SizedBox(width: AppSpacing.sm),
                                Text(
                                  goDirectionName,
                                  style: TextStyle(
                                    color: notifier.currentDirection == 0
                                        ? TransportColors.bus
                                        : Colors.white,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      // 返程按鈕
                      Expanded(
                        child: AnimatedScaleButton(
                          onTap: notifier.data == null ||
                                  notifier.currentDirection == 1
                              ? () {}
                              : () => notifier.switchDirection(1),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: notifier.currentDirection == 1
                                  ? Colors.white
                                  : TransportColors.bus.withOpacity(0.7),
                              borderRadius:
                                  BorderRadius.circular(AppRadius.medium),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.arrow_back,
                                  size: 18,
                                  color: notifier.currentDirection == 1
                                      ? TransportColors.bus
                                      : Colors.white,
                                ),
                                const SizedBox(width: AppSpacing.sm),
                                Text(
                                  backDirectionName,
                                  style: TextStyle(
                                    color: notifier.currentDirection == 1
                                        ? TransportColors.bus
                                        : Colors.white,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // 載入中
                if (notifier.data == null)
                  const Expanded(
                    child: Center(
                      child: PulseLoading(color: TransportColors.bus),
                    ),
                  )
                // 錯誤
                else if (notifier.error != null)
                  Expanded(
                    child: Center(
                      child: EmptyStateCard(
                        icon: Icons.error_outline,
                        title: '載入失敗',
                        subtitle: notifier.error,
                        onAction: () => notifier.fetchData(),
                        actionLabel: '重試',
                      ),
                    ),
                  )
                // 正常顯示內容
                else
                  Expanded(
                    child: _buildRouteContent(context, notifier),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildRouteContent(BuildContext context, BusRouteNotifier notifier) {
    final data = notifier.data!;
    return Column(
      children: [
        // Bus Summary - 運行中公車
        if (data.buses.isNotEmpty)
          Container(
            padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
            decoration: BoxDecoration(
              color: AppColors.background,
              border: Border(
                bottom: BorderSide(color: AppColors.divider),
              ),
            ),
            child: SizedBox(
              height: 48,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                itemCount: data.buses.length,
                itemBuilder: (ctx, i) {
                  final bus = data.buses[i];
                  return Container(
                    margin: const EdgeInsets.only(right: 8),
                    child: AnimatedCard(
                      elevation: 1,
                      margin: EdgeInsets.zero,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 6,
                      ),
                      child: IntrinsicHeight(
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.directions_bus,
                              size: 12,
                              color: TransportColors.bus,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '${bus.id}',
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        // 站點列表
        Expanded(
          child: RefreshIndicator(
            onRefresh: () => notifier.fetchData(),
            color: TransportColors.bus,
            child: ListView.builder(
              padding: const EdgeInsets.all(AppSpacing.md),
              itemCount: data.stops.length,
              itemBuilder: (ctx, i) {
                final stop = data.stops[i];
                final busesHere = data.buses
                    .where((b) =>
                        b.atStop == i + 1 || b.headingTo == i + 1)
                    .toList();
                return FadeInAnimation(
                  delay: Duration(milliseconds: min(i * 10, 200)),
                  child: BusStopListTile(
                    stop: stop,
                    index: i + 1,
                    totalStops: data.stops.length,
                    buses: busesHere,
                    isFirst: i == 0,
                    isLast: i == data.stops.length - 1,
                  ),
                );
              },
            ),
          ),
        ),
        // Footer
        Container(
          padding: const EdgeInsets.all(AppSpacing.md),
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 4,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(
                    Icons.access_time,
                    size: 14,
                    color: AppColors.onSurfaceLight,
                  ),
                  const SizedBox(width: AppSpacing.xs),
                  Text(
                    '最後更新: ${notifier.lastUpdated?.toString().substring(11, 16) ?? '--:--'}',
                    style: AppTextStyles.labelSmall,
                  ),
                ],
              ),
              AnimatedScaleButton(
                onTap: () => notifier.fetchData(),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.md,
                    vertical: AppSpacing.sm,
                  ),
                  decoration: BoxDecoration(
                    color: TransportColors.bus.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(AppRadius.medium),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.refresh,
                        size: 16,
                        color: TransportColors.bus,
                      ),
                      const SizedBox(width: AppSpacing.xs),
                      Text(
                        '重新整理',
                        style: AppTextStyles.labelMedium.copyWith(
                          color: TransportColors.bus,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class BusStopListTile extends StatelessWidget {
  final BusStop stop;
  final int index;
  final int totalStops;
  final List<BusVehicle> buses;
  final bool isFirst;
  final bool isLast;

  const BusStopListTile({
    super.key,
    required this.stop,
    required this.index,
    required this.totalStops,
    required this.buses,
    this.isFirst = false,
    this.isLast = false,
  });

  Color get _etaColor {
    if (stop.eta == '即將進站') return AppColors.success;
    if (stop.eta.contains('分') || stop.eta.contains('min')) {
      final minutes = int.tryParse(stop.eta.replaceAll(RegExp(r'[^0-9]'), ''));
      if (minutes != null && minutes < 5) return AppColors.warning;
    }
    return AppColors.onSurfaceLight;
  }

  bool get _isActive => stop.eta == '即將進站' ||
      (stop.eta.contains('分') &&
          int.tryParse(stop.eta.replaceAll(RegExp(r'[^0-9]'), '')) != null &&
          int.tryParse(stop.eta.replaceAll(RegExp(r'[^0-9]'), ''))! < 5);

  // 分離在站點上的公車和在路上（headingTo）的公車
  ({List<BusVehicle> atStop, List<BusVehicle> onRoute}) _separateBuses() {
    final atStop = <BusVehicle>[];
    final onRoute = <BusVehicle>[];

    for (final bus in buses) {
      if (bus.atStop == index) {
        atStop.add(bus);
      } else if (bus.headingTo == index + 1) {
        onRoute.add(bus);
      }
    }

    return (atStop: atStop, onRoute: onRoute);
  }

  @override
  Widget build(BuildContext context) {
    final separated = _separateBuses();
    final hasBusAtStop = separated.atStop.isNotEmpty;
    final hasBusOnRoute = separated.onRoute.isNotEmpty;

    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 左側：時間軸（包含路線和公車位置）
            SizedBox(
              width: 60,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // 上行連接線（從上一站到本站）
                  if (!isFirst)
                    Positioned(
                      top: 0,
                      bottom: 32,
                      child: Container(
                        width: 3,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [
                              _getGradientColor(index - 2),
                              _getGradientColor(index - 1),
                            ],
                          ),
                          borderRadius: BorderRadius.circular(1.5),
                        ),
                      ),
                    ),

                  // 下行連接線（從本站到下一站）- 純線條，無公車
                  if (!isLast)
                    Positioned(
                      top: 32,
                      bottom: 0,
                      child: Container(
                        width: 3,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [
                              _getGradientColor(index - 1),
                              _getGradientColor(index),
                            ],
                          ),
                          borderRadius: BorderRadius.circular(1.5),
                        ),
                      ),
                    ),

                  // 站點標記
                  _buildStopIndicator(hasBusAtStop),

                  // 在站點上的公車
                  if (hasBusAtStop) _buildBusesAtStop(separated.atStop),
                ],
              ),
            ),

            const SizedBox(width: AppSpacing.md),

            // 右側：站點資訊（簡潔設計，無Card）
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: BoxDecoration(
                  color: hasBusAtStop ? TransportColors.bus.withOpacity(0.05) : Colors.white,
                  borderRadius: BorderRadius.circular(AppRadius.medium),
                  border: Border.all(
                    color: hasBusAtStop
                        ? TransportColors.bus.withOpacity(0.3)
                        : AppColors.divider,
                    width: 1,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // 站名和ETA
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            stop.name,
                            style: AppTextStyles.titleSmall.copyWith(
                              color: hasBusAtStop
                                  ? TransportColors.bus
                                  : AppColors.onSurface,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: AppSpacing.sm,
                            vertical: AppSpacing.xs,
                          ),
                          decoration: BoxDecoration(
                            color: _etaColor.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(AppRadius.full),
                            border: Border.all(
                              color: _etaColor.withOpacity(0.3),
                            ),
                          ),
                          child: Text(
                            stop.eta,
                            style: AppTextStyles.labelMedium.copyWith(
                              color: _etaColor,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),

                    // 站點經緯度座標
                    Builder(builder: (context) {
                      print('【UI】站點 ${stop.name} lat=${stop.latitude} lon=${stop.longitude}');
                      if (stop.latitude != null && stop.longitude != null) {
                        return Padding(
                          padding: const EdgeInsets.only(top: AppSpacing.xs),
                          child: Row(
                            children: [
                              Icon(
                                Icons.location_on,
                                size: 12,
                                color: AppColors.onSurfaceLight,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                '${stop.latitude!.toStringAsFixed(5)}, ${stop.longitude!.toStringAsFixed(5)}',
                                style: AppTextStyles.bodySmall.copyWith(
                                  color: AppColors.onSurfaceLight,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        );
                      }
                      return const SizedBox.shrink();
                    }),

                    // 在站公車資訊（使用 Wrap 並排）
                    if (hasBusAtStop)
                      Padding(
                        padding: const EdgeInsets.only(top: AppSpacing.sm),
                        child: Wrap(
                          spacing: AppSpacing.xs,
                          runSpacing: AppSpacing.xs,
                          children: separated.atStop.map((bus) {
                            return Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: AppSpacing.sm,
                                vertical: AppSpacing.xs,
                              ),
                              decoration: BoxDecoration(
                                color: TransportColors.bus.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(AppRadius.small),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(
                                    Icons.directions_bus,
                                    size: 14,
                                    color: TransportColors.bus,
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    bus.plateNumber.isNotEmpty ? bus.plateNumber : '公車',
                                    style: AppTextStyles.labelMedium.copyWith(
                                      color: TransportColors.bus,
                                    ),
                                  ),
                                  if (bus.busType.isNotEmpty)
                                    Text(
                                      ' · ${bus.busType}',
                                      style: AppTextStyles.bodySmall.copyWith(
                                        color: TransportColors.bus.withOpacity(0.8),
                                      ),
                                    ),
                                ],
                              ),
                            );
                          }).toList(),
                        ),
                      ),

                    // 路上公車（headingTo）- 顯示在站牌之間行進中
                    if (hasBusOnRoute)
                      Padding(
                        padding: const EdgeInsets.only(top: AppSpacing.sm),
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: AppSpacing.md,
                            vertical: AppSpacing.sm,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.secondary.withOpacity(0.08),
                            borderRadius: BorderRadius.circular(AppRadius.medium),
                            border: Border.all(
                              color: AppColors.secondary.withOpacity(0.3),
                              width: 1,
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                Icons.arrow_forward,
                                size: 14,
                                color: AppColors.secondary,
                              ),
                              const SizedBox(width: AppSpacing.xs),
                              Text(
                                '前往下一站',
                                style: AppTextStyles.labelSmall.copyWith(
                                  color: AppColors.secondary,
                                ),
                              ),
                              const SizedBox(width: AppSpacing.sm),
                              Expanded(
                                child: Wrap(
                                  spacing: AppSpacing.xs,
                                  runSpacing: AppSpacing.xs,
                                  children: separated.onRoute.map((bus) {
                                    return Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: AppSpacing.sm,
                                        vertical: 4,
                                      ),
                                      decoration: BoxDecoration(
                                        color: AppColors.secondary.withOpacity(0.15),
                                        borderRadius: BorderRadius.circular(AppRadius.small),
                                      ),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Icon(
                                            Icons.directions_bus,
                                            size: 12,
                                            color: AppColors.secondary,
                                          ),
                                          const SizedBox(width: 4),
                                          Text(
                                            bus.plateNumber.isNotEmpty ? bus.plateNumber : '公車',
                                            style: AppTextStyles.labelSmall.copyWith(
                                              color: AppColors.secondary,
                                              fontWeight: FontWeight.w500,
                                            ),
                                          ),
                                        ],
                                      ),
                                    );
                                  }).toList(),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // 根據索引計算漸層顏色
  Color _getGradientColor(int index) {
    final progress = (index + 1) / totalStops;
    return Color.lerp(
      TransportColors.bus.withAlpha(102),
      TransportColors.bus.withAlpha(230),
      progress,
    )!;
  }

  // 站點標記
  Widget _buildStopIndicator(bool hasBus) {
    if (isFirst) {
      return _buildStartStopIndicator(hasBus);
    } else if (isLast) {
      return _buildEndStopIndicator(hasBus);
    }
    return _buildRegularStopIndicator(hasBus);
  }

  // 起點站標記
  Widget _buildStartStopIndicator(bool hasBus) {
    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        color: hasBus ? TransportColors.bus : Colors.white,
        shape: BoxShape.circle,
        border: Border.all(
          color: TransportColors.bus,
          width: 3,
        ),
        boxShadow: const [AppShadows.small],
      ),
      child: Center(
        child: hasBus
            ? const Icon(
                Icons.directions_bus,
                size: 18,
                color: Colors.white,
              )
            : const Icon(
                Icons.flag,
                size: 16,
                color: TransportColors.bus,
              ),
      ),
    );
  }

  // 終點站標記
  Widget _buildEndStopIndicator(bool hasBus) {
    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        color: hasBus ? TransportColors.bus : Colors.white,
        shape: BoxShape.circle,
        border: Border.all(
          color: TransportColors.bus,
          width: 3,
        ),
        boxShadow: const [AppShadows.small],
      ),
      child: Center(
        child: hasBus
            ? const Icon(
                Icons.directions_bus,
                size: 18,
                color: Colors.white,
              )
            : const Icon(
                Icons.flag_outlined,
                size: 16,
                color: TransportColors.bus,
              ),
      ),
    );
  }

  // 一般站點標記
  Widget _buildRegularStopIndicator(bool hasBus) {
    return Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        color: hasBus ? TransportColors.bus : Colors.white,
        shape: BoxShape.circle,
        border: Border.all(
          color: hasBus ? TransportColors.bus : AppColors.divider,
          width: 2,
        ),
        boxShadow: const [AppShadows.small],
      ),
      child: Center(
        child: hasBus
            ? const Icon(
                Icons.directions_bus,
                size: 16,
                color: Colors.white,
              )
            : Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: AppColors.divider,
                  shape: BoxShape.circle,
                ),
              ),
      ),
    );
  }

  // 在站點上的公車（多台並排）
  Widget _buildBusesAtStop(List<BusVehicle> busesAtStop) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.9),
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Center(
        child: busesAtStop.length == 1
            ? Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: TransportColors.bus,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 2),
                  boxShadow: [
                    BoxShadow(
                      color: TransportColors.bus.withOpacity(0.4),
                      blurRadius: 6,
                      spreadRadius: 1,
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.directions_bus,
                  size: 16,
                  color: Colors.white,
                ),
              )
            : Row(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ...busesAtStop.take(2).map((bus) {
                    return Container(
                      width: 20,
                      height: 20,
                      margin: const EdgeInsets.symmetric(horizontal: 1),
                      decoration: BoxDecoration(
                        color: TransportColors.bus,
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white, width: 1.5),
                        boxShadow: [
                          BoxShadow(
                            color: TransportColors.bus.withOpacity(0.4),
                            blurRadius: 4,
                            spreadRadius: 1,
                          ),
                        ],
                      ),
                      child: const Center(
                        child: Icon(
                          Icons.directions_bus,
                          size: 10,
                          color: Colors.white,
                        ),
                      ),
                    );
                  }),
                  if (busesAtStop.length > 2)
                    Container(
                      width: 18,
                      height: 18,
                      margin: const EdgeInsets.only(left: 1),
                      decoration: BoxDecoration(
                        color: Colors.grey[600],
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white, width: 1.5),
                      ),
                      child: Center(
                        child: Text(
                          '+${busesAtStop.length - 2}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 7,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
      ),
    );
  }
}
