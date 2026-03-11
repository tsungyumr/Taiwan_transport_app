import 'package:flutter/material.dart';
import '../main.dart';
import '../models/bus_route.dart';
import '../ui_theme.dart';

/// 公車路線時間軸元件
///
/// 功能：
/// - 顯示站牌之間的漸層連接線（從淺到深，表示行進方向）
/// - 顯示站點標記（起點、終點、一般站點）
/// - 支援顯示站點上的公車（通過 hasBus 參數）
///
/// 漸層效果說明：
/// - 起點站：淺綠色（40% 透明度）
/// - 終點站：深綠色（90% 透明度）
/// - 中間站：根據位置計算漸層色
class BusRouteTimeline extends StatelessWidget {
  final int currentIndex;
  final int totalStops;
  final bool isFirst;
  final bool isLast;
  final bool hasBus;

  const BusRouteTimeline({
    super.key,
    required this.currentIndex,
    required this.totalStops,
    required this.isFirst,
    required this.isLast,
    required this.hasBus,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 50,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // 上行連接線（從上一站到本站）
          if (!isFirst) _buildUpperConnector(),

          // 下行連接線（從本站到下一站）
          if (!isLast) _buildLowerConnector(),

          // 站點標記
          _buildStopIndicator(),
        ],
      ),
    );
  }

  /// 上行連接線（漸層效果）
  Widget _buildUpperConnector() {
    return Positioned(
      top: 0,
      bottom: 28, // 調整以對齊圓圈中心
      child: Container(
        width: 4,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              _getGradientColor(currentIndex - 1),
              _getGradientColor(currentIndex),
            ],
          ),
          borderRadius: BorderRadius.circular(2),
        ),
      ),
    );
  }

  /// 下行連接線（漸層效果）
  Widget _buildLowerConnector() {
    return Positioned(
      top: 28,
      bottom: 0,
      child: Container(
        width: 4,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              _getGradientColor(currentIndex),
              _getGradientColor(currentIndex + 1),
            ],
          ),
          borderRadius: BorderRadius.circular(2),
        ),
      ),
    );
  }

  /// 根據索引計算漸層顏色（從淺綠到深綠）
  Color _getGradientColor(int index) {
    final progress = index / (totalStops - 1);
    // 從淺綠色（起點）到深綠色（終點）
    return Color.lerp(
      TransportColors.bus.withAlpha(102), // 0.4 opacity - 起點淺色
      TransportColors.bus.withAlpha(230), // 0.9 opacity - 終點深色
      progress,
    )!;
  }

  /// 站點標記
  Widget _buildStopIndicator() {
    if (isFirst) {
      return _StartStopIndicator(hasBus: hasBus);
    } else if (isLast) {
      return _EndStopIndicator(hasBus: hasBus);
    }
    return _RegularStopIndicator(hasBus: hasBus);
  }
}

/// 起點站標記
class _StartStopIndicator extends StatelessWidget {
  final bool hasBus;

  const _StartStopIndicator({required this.hasBus});

  @override
  Widget build(BuildContext context) {
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
}

/// 終點站標記
class _EndStopIndicator extends StatelessWidget {
  final bool hasBus;

  const _EndStopIndicator({required this.hasBus});

  @override
  Widget build(BuildContext context) {
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
}

/// 一般站點標記
class _RegularStopIndicator extends StatelessWidget {
  final bool hasBus;

  const _RegularStopIndicator({required this.hasBus});

  @override
  Widget build(BuildContext context) {
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
}

/// 公車路線進度指示器
/// 顯示整體路線的進度視覺化（用於頂部或底部）
class RouteProgressIndicator extends StatelessWidget {
  final int currentStopIndex;
  final int totalStops;
  final List<int> busPositions;

  const RouteProgressIndicator({
    super.key,
    required this.currentStopIndex,
    required this.totalStops,
    required this.busPositions,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 8,
      decoration: BoxDecoration(
        color: AppColors.divider,
        borderRadius: BorderRadius.circular(4),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          return Stack(
            children: [
              // 背景漸層條
              Container(
                width: constraints.maxWidth,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      TransportColors.bus.withAlpha(51), // 0.2
                      TransportColors.bus.withAlpha(153), // 0.6
                    ],
                  ),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
              // 公車位置標記
              ...busPositions.map((position) {
                final progress = position / totalStops;
                return Positioned(
                  left: constraints.maxWidth * progress - 6,
                  top: -2,
                  child: Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      color: TransportColors.bus,
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 2),
                      boxShadow: const [AppShadows.small],
                    ),
                  ),
                );
              }),
            ],
          );
        },
      ),
    );
  }
}

/// 使用 CustomPainter 繪製虛線路線（進階選項）
/// 提供更細緻的視覺控制
class DashedRouteLinePainter extends CustomPainter {
  final Color color;
  final double dashHeight;
  final double dashSpace;
  final double strokeWidth;

  DashedRouteLinePainter({
    required this.color,
    this.dashHeight = 8.0,
    this.dashSpace = 4.0,
    this.strokeWidth = 3.0,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    var startY = 0.0;
    final centerX = size.width / 2;

    while (startY < size.height) {
      canvas.drawLine(
        Offset(centerX, startY),
        Offset(centerX, startY + dashHeight),
        paint,
      );
      startY += dashHeight + dashSpace;
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// 虛線路線元件（使用 CustomPainter）
class DashedRouteLine extends StatelessWidget {
  final Color color;
  final double? height;

  const DashedRouteLine({
    super.key,
    required this.color,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 4,
      height: height,
      child: CustomPaint(
        painter: DashedRouteLinePainter(color: color),
      ),
    );
  }
}

/// 公車路線時間軸元件（整合公車動態位置顯示）
///
/// 功能：
/// - 顯示站牌之間的漸層連接線（從淺到深，表示行進方向）
/// - 顯示站點標記（起點、終點、一般站點）
/// - 顯示公車位置：
///   - atStop > 0：公車顯示在站牌圓圈內
///   - headingTo > 0：公車顯示在 (headingTo-1) 和 headingTo 之間的路線上
///
/// 使用場景：需要顯示公車即時位置時使用此元件
class BusRouteTimelineWithVehicles extends StatelessWidget {
  final int currentIndex;
  final int totalStops;
  final bool isFirst;
  final bool isLast;
  final bool hasBus;
  final List<BusVehicle> busesAtStop;
  final List<BusVehicle> busesBetweenStops;

  const BusRouteTimelineWithVehicles({
    super.key,
    required this.currentIndex,
    required this.totalStops,
    required this.isFirst,
    required this.isLast,
    required this.hasBus,
    this.busesAtStop = const [],
    this.busesBetweenStops = const [],
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 60,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // 上行連接線（從上一站到本站）
          if (!isFirst) _buildUpperConnector(),

          // 下行連接線（從本站到下一站）- 包含路徑上的公車
          if (!isLast) _buildLowerConnector(),

          // 站點標記
          _buildStopIndicator(),

          // 公車在站點上（atStop 狀態）
          if (busesAtStop.isNotEmpty) _buildBusesAtStop(),
        ],
      ),
    );
  }

  /// 上行連接線（簡潔路線設計）
  Widget _buildUpperConnector() {
    return Positioned(
      top: 0,
      bottom: 32,
      child: Column(
        children: [
          // 主路線線條
          Container(
            width: 3,
            height: double.infinity,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  _getGradientColor(currentIndex - 1),
                  _getGradientColor(currentIndex),
                ],
              ),
              borderRadius: BorderRadius.circular(1.5),
            ),
          ),
        ],
      ),
    );
  }

  /// 下行連接線（簡潔路線設計，包含公車行進路徑）
  Widget _buildLowerConnector() {
    return Positioned(
      top: 32,
      bottom: 0,
      left: 0,
      right: 0,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // 主路線線條
          Container(
            width: 3,
            height: double.infinity,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  _getGradientColor(currentIndex),
                  _getGradientColor(currentIndex + 1),
                ],
              ),
              borderRadius: BorderRadius.circular(1.5),
            ),
          ),
          // 公車在路徑上（headingTo 狀態）
          if (busesBetweenStops.isNotEmpty)
            Positioned(
              top: 8,
              child: _buildBusesOnRoute(),
            ),
        ],
      ),
    );
  }

  /// 顯示在路徑上的公車（多台並排）
  Widget _buildBusesOnRoute() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.secondary.withOpacity(0.3),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: busesBetweenStops.map((bus) {
          return Container(
            width: 26,
            height: 26,
            margin: const EdgeInsets.symmetric(horizontal: 2),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  AppColors.secondary,
                  AppColors.secondary.withOpacity(0.8),
                ],
              ),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2),
              boxShadow: [
                BoxShadow(
                  color: AppColors.secondary.withOpacity(0.4),
                  blurRadius: 4,
                  spreadRadius: 1,
                ),
              ],
            ),
            child: const Center(
              child: Icon(
                Icons.directions_bus,
                size: 12,
                color: Colors.white,
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  /// 根據索引計算漸層顏色（從淺綠到深綠）
  Color _getGradientColor(int index) {
    final progress = index / (totalStops - 1);
    return Color.lerp(
      TransportColors.bus.withAlpha(102), // 0.4 opacity - 起點淺色
      TransportColors.bus.withAlpha(230), // 0.9 opacity - 終點深色
      progress,
    )!;
  }

  /// 站點標記
  Widget _buildStopIndicator() {
    if (isFirst) {
      return _StartStopIndicator(hasBus: hasBus);
    } else if (isLast) {
      return _EndStopIndicator(hasBus: hasBus);
    }
    return _RegularStopIndicator(hasBus: hasBus);
  }

  /// 顯示在站點上的公車（atStop 狀態）
  /// 公車 Icon 疊加在站牌圓圈上，多台並排顯示
  Widget _buildBusesAtStop() {
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
                  ...busesAtStop.take(3).map((bus) {
                    return Container(
                      width: 22,
                      height: 22,
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
                  if (busesAtStop.length > 3)
                    Container(
                      width: 20,
                      height: 20,
                      margin: const EdgeInsets.only(left: 2),
                      decoration: BoxDecoration(
                        color: Colors.grey[600],
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white, width: 1.5),
                      ),
                      child: Center(
                        child: Text(
                          '+${busesAtStop.length - 3}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 8,
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

/// 公車位置計算輔助類
///
/// 用於計算每個站點應該顯示的公車位置
class BusPositionCalculator {
  /// 計算每個站點應該顯示的公車
  ///
  /// 回傳格式：
  /// - key: 站點索引 (0-based)
  /// - value: (busesAtStop, busesBetweenStops)
  ///   - busesAtStop: 在該站點上的公車 (atStop > 0)
  ///   - busesBetweenStops: 在該站到下一站之間的公車 (headingTo == 站點索引+1)
  static Map<int, ({List<BusVehicle> atStop, List<BusVehicle> betweenStops})>
      calculateBusPositions(List<BusStop> stops, List<BusVehicle> buses) {
    final result =
        <int, ({List<BusVehicle> atStop, List<BusVehicle> betweenStops})>{};

    // 初始化每個站點
    for (int i = 0; i < stops.length; i++) {
      result[i] = (atStop: <BusVehicle>[], betweenStops: <BusVehicle>[]);
    }

    // 分配公車到對應位置
    for (final bus in buses) {
      // atStop > 0：公車在站點上
      if (bus.atStop > 0) {
        final stopIndex = bus.atStop - 1; // 轉換為 0-based 索引
        if (stopIndex >= 0 && stopIndex < stops.length) {
          result[stopIndex] = (
            atStop: [...result[stopIndex]!.atStop, bus],
            betweenStops: result[stopIndex]!.betweenStops,
          );
        }
      }
      // headingTo > 0：公車正在前往某站（在站間）
      else if (bus.headingTo > 0) {
        // headingTo 是 1-based，表示前往的站點
        // 公車在 (headingTo - 1) 和 headingTo 之間
        final fromStopIndex = bus.headingTo - 2; // 從上一站出發
        if (fromStopIndex >= 0 && fromStopIndex < stops.length) {
          result[fromStopIndex] = (
            atStop: result[fromStopIndex]!.atStop,
            betweenStops: [...result[fromStopIndex]!.betweenStops, bus],
          );
        }
      }
    }

    return result;
  }

  /// 檢查是否有公車在指定站點或站間
  static bool hasAnyBus(
    int stopIndex,
    Map<int, ({List<BusVehicle> atStop, List<BusVehicle> betweenStops})> positions,
  ) {
    final position = positions[stopIndex];
    if (position == null) return false;
    return position.atStop.isNotEmpty || position.betweenStops.isNotEmpty;
  }
}
