import 'dart:math';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/bus_route.dart';
import '../providers/bus_provider.dart';

class BusRouteScreen extends StatefulWidget {
  final String route;
  const BusRouteScreen({super.key, required this.route});

  @override
  State<BusRouteScreen> createState() => _BusRouteScreenState();
}

class _BusRouteScreenState extends State<BusRouteScreen> with SingleTickerProviderStateMixin {
  late ScrollController _scrollController;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController();
    _pulseController = AnimationController(
      duration: const Duration(seconds: 1),
      vsync: this,
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.3).animate(_pulseController);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  // 根據狀態取得對應顏色
  Color _getStatusColor(String status) {
    switch (status) {
      case 'arriving':
        return Colors.green; // 進站中 - 綠色
      case 'near':
        return Colors.orange; // 即將進站 - 橘色
      case 'not_started':
        return Colors.grey; // 未發車 - 灰色
      default:
        return Colors.blue; // 正常 - 藍色
    }
  }

  // 取得狀態文字顯示
  String _getStatusText(String status) {
    switch (status) {
      case 'arriving':
        return '進站中';
      case 'near':
        return '即將進站';
      case 'not_started':
        return '未發車';
      default:
        return '正常';
    }
  }

  // 找到最近有公車的站點索引
  int _getNearestBusIndex(BusRouteData? data) {
    if (data?.buses.isEmpty ?? true) return 0;
    return data!.buses.map((b) => b.atStop).reduce(min);
  }

  // 捲動到最近有公車的站點
  void _scrollToBus() {
    final data = Provider.of<BusRouteProvider>(context, listen: false).data;
    if (data != null && data.buses.isNotEmpty) {
      final index = _getNearestBusIndex(data) - 1;
      if (index >= 0 && index < data.stops.length) {
        _scrollController.animateTo(
          index * 100.0, // 調整高度以適應新的卡片設計
          duration: const Duration(milliseconds: 500),
          curve: Curves.easeInOut,
        );
      }
    }
  }

  // 檢查指定站點是否有公車（從 stop.buses 或 data.buses 中查找）
  List<dynamic> _getBusesAtStop(BusRouteData? data, int stopIndex) {
    if (data == null) return [];

    final stop = data.stops[stopIndex - 1]; // stopIndex 是 1-based

    // 優先使用 stop.buses（從 HTML 直接解析的車輛資訊）
    if (stop.buses.isNotEmpty) {
      return stop.buses;
    }

    // 如果 stop.buses 為空，從 data.buses 中查找匹配 atStop 的車輛
    if (data.buses.isNotEmpty) {
      return data.buses.where((bus) => bus.atStop == stopIndex).toList();
    }

    return [];
  }

  // 判斷是否為起點站或終點站
  bool _isEndpoint(BusStop stop, int index, int totalStops) {
    return index == 0 || index == totalStops - 1;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.route} 公車路線'),
        actions: [
          Consumer<BusRouteProvider>(
            builder: (context, provider, _) => IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: provider.isLoading ? null : () => provider.loadData(direction: provider.currentDirection, forceRefresh: true),
            ),
          ),
        ],
      ),
      body: Consumer<BusRouteProvider>(
        builder: (context, provider, child) {
          // 取得方向名稱（使用資料或預設值）
          String goDirectionName = '往 終點站';
          String backDirectionName = '往 起點站';

          final data = provider.data;
          if (data != null) {
            if (data.direction.go != null) {
              goDirectionName = data.direction.go!['direction_name'] ?? '往 終點站';
            }
            if (data.direction.back != null) {
              backDirectionName = data.direction.back!['direction_name'] ?? '往 起點站';
            }
          }

          return Column(
            children: [
              // ===== 方向切換按鈕區（總是顯示） =====
              Container(
                padding: const EdgeInsets.all(12.0),
                color: Colors.blue[700],
                child: Row(
                  children: [
                    // 去程按鈕
                    Expanded(
                      flex: 2,
                      child: ElevatedButton.icon(
                        onPressed: provider.isLoading || provider.currentDirection == 0
                            ? null
                            : () => provider.switchDirection(0),
                        icon: const Icon(Icons.arrow_forward),
                        label: Text(goDirectionName),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: provider.currentDirection == 0
                              ? Colors.white
                              : Colors.blue[500],
                          foregroundColor: provider.currentDirection == 0
                              ? Colors.blue[700]
                              : Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    // 返程按鈕
                    Expanded(
                      flex: 2,
                      child: ElevatedButton.icon(
                        onPressed: provider.isLoading || provider.currentDirection == 1
                            ? null
                            : () => provider.switchDirection(1),
                        icon: const Icon(Icons.arrow_back),
                        label: Text(backDirectionName),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: provider.currentDirection == 1
                              ? Colors.white
                              : Colors.blue[500],
                          foregroundColor: provider.currentDirection == 1
                              ? Colors.blue[700]
                              : Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // ===== 載入中狀態 =====
              if (provider.isLoading)
                Expanded(
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const CircularProgressIndicator(),
                        const SizedBox(height: 16),
                        const Text('正在載入公車資料...'),
                        const SizedBox(height: 8),
                        Text(
                          '後端爬蟲需要時間，請稍候',
                          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ),
                )

              // ===== 錯誤狀態 =====
              else if (provider.error != null)
                Expanded(
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.error_outline, color: Colors.red, size: 48),
                          const SizedBox(height: 16),
                          Text(
                            '載入失敗',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            provider.error!,
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.grey[600]),
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton.icon(
                            onPressed: () => provider.loadData(direction: provider.currentDirection, forceRefresh: true),
                            icon: const Icon(Icons.refresh),
                            label: const Text('重新嘗試'),
                          ),
                        ],
                      ),
                    ),
                  ),
                )

              // ===== 無資料狀態 =====
              else if (data == null)
                const Expanded(
                  child: Center(child: Text('無資料')),
                )

              // ===== 正常顯示路線內容 =====
              else
                Expanded(
                  flex: 8,
                  child: _buildRouteContent(context, provider, data),
                ),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _scrollToBus,
        icon: const Icon(Icons.navigation),
        label: const Text('定位公車'),
        backgroundColor: Colors.orange,
      ),
    );
  }

  // 構建路線內容
  Widget _buildRouteContent(BuildContext context, BusRouteProvider provider, BusRouteData data) {
    final directionName = data.direction.directionName;
    final departure = data.direction.departure;
    final arrival = data.direction.arrival;

    return Column(
      children: [
        // 路線資訊標題區
        Container(
          padding: const EdgeInsets.all(12.0),
          color: Colors.blue[50],
          child: Column(
            children: [
              // 路線名稱和方向
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.blue,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      directionName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    data.routeName,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              // 起訖站資訊
              if (departure.isNotEmpty || arrival.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 4.0),
                  child: Text(
                    '$departure → $arrival',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[700],
                    ),
                  ),
                ),
              const SizedBox(height: 8),
              // 行駛中公車摘要
              if (data.buses.isNotEmpty)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.orange[50],
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.orange[200]!),
                  ),
                  child: Text(
                    '路上共有 ${data.buses.length} 輛公車行駛中',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.orange[800],
                    ),
                  ),
                ),
            ],
          ),
        ),

        // 站點列表（支持下拉重新整理）
        Expanded(
          child: RefreshIndicator(
            onRefresh: () => provider.loadData(direction: provider.currentDirection, forceRefresh: true),
            child: ListView.builder(
              physics: const AlwaysScrollableScrollPhysics(),
              controller: _scrollController,
              itemCount: data.stops.length,
              itemBuilder: (context, index) {
              final stop = data.stops[index];
              final stopIndex = index + 1;
              final busesAtStop = _getBusesAtStop(data, stopIndex);
              final hasBus = busesAtStop.isNotEmpty;

              return Container(
                margin: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 4.0),
                child: IntrinsicHeight(
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // 左側：站序和連接線
                      SizedBox(
                        width: 50,
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            // 連接線（除了第一站和最後站）
                            if (index > 0)
                              Positioned(
                                top: 0,
                                bottom: 20,
                                child: Container(width: 2, color: Colors.grey[300]),
                              ),
                            if (index < data.stops.length - 1)
                              Positioned(
                                top: 20,
                                bottom: 0,
                                child: Container(width: 2, color: Colors.grey[300]),
                              ),
                            // 站序圓圈
                            Container(
                              width: 36,
                              height: 36,
                              decoration: BoxDecoration(
                                color: hasBus ? Colors.orange : Colors.blue,
                                shape: BoxShape.circle,
                                border: Border.all(color: Colors.white, width: 2),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.1),
                                    blurRadius: 4,
                                    offset: const Offset(0, 2),
                                  ),
                                ],
                              ),
                              child: Center(
                                child: hasBus
                                    ? AnimatedBuilder(
                                        animation: _pulseAnimation,
                                        builder: (context, child) => Transform.scale(
                                          scale: _pulseAnimation.value,
                                          child: const Icon(
                                            Icons.directions_bus,
                                            size: 18,
                                            color: Colors.white,
                                          ),
                                        ),
                                      )
                                    : Text(
                                        '$stopIndex',
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontWeight: FontWeight.bold,
                                          fontSize: 14,
                                        ),
                                      ),
                              ),
                            ),
                          ],
                        ),
                      ),

                      // 右側：站點資訊卡片
                      Expanded(
                        child: Card(
                          elevation: hasBus ? 4 : 1,
                          margin: const EdgeInsets.only(left: 8),
                          color: hasBus ? Colors.orange[50] : Colors.white,
                          child: Padding(
                            padding: const EdgeInsets.all(12.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                // 站名和ETA
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Expanded(
                                      child: Text(
                                        stop.name,
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: _getStatusColor(stop.status).withOpacity(0.1),
                                        borderRadius: BorderRadius.circular(12),
                                        border: Border.all(
                                          color: _getStatusColor(stop.status).withOpacity(0.3),
                                        ),
                                      ),
                                      child: Text(
                                        stop.eta,
                                        style: TextStyle(
                                          color: _getStatusColor(stop.status),
                                          fontWeight: FontWeight.bold,
                                          fontSize: 13,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),

                                // 狀態標籤
                                if (stop.status != 'normal')
                                  Padding(
                                    padding: const EdgeInsets.only(top: 4.0),
                                    child: Text(
                                      _getStatusText(stop.status),
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: _getStatusColor(stop.status),
                                      ),
                                    ),
                                  ),

                                // 在該站的公車資訊
                                if (hasBus)
                                  Padding(
                                    padding: const EdgeInsets.only(top: 8.0),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: busesAtStop.map((bus) {
                                        // 處理兩種類型：StopBusInfo 或 BusVehicle
                                        final plateNumber = bus is StopBusInfo
                                            ? bus.plateNumber
                                            : (bus as BusVehicle).plateNumber;
                                        final busType = bus is StopBusInfo
                                            ? bus.busType
                                            : (bus as BusVehicle).busType;
                                        final remainingSeats = bus is StopBusInfo
                                            ? bus.remainingSeats
                                            : (bus as BusVehicle).remainingSeats;

                                        return Container(
                                          margin: const EdgeInsets.only(top: 4),
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(
                                            color: Colors.orange[100],
                                            borderRadius: BorderRadius.circular(6),
                                          ),
                                          child: Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              const Icon(
                                                Icons.directions_bus,
                                                size: 16,
                                                color: Colors.orange,
                                              ),
                                              const SizedBox(width: 4),
                                              Text(
                                                plateNumber.isNotEmpty
                                                    ? plateNumber
                                                    : '公車',
                                                style: const TextStyle(
                                                  fontSize: 13,
                                                  fontWeight: FontWeight.w500,
                                                  color: Colors.orange,
                                                ),
                                              ),
                                              if (busType.isNotEmpty)
                                                Text(
                                                  ' · $busType',
                                                  style: TextStyle(
                                                    fontSize: 12,
                                                    color: Colors.orange[700],
                                                  ),
                                                ),
                                              if (remainingSeats != null && remainingSeats.toString().isNotEmpty)
                                                Text(
                                                  ' · ${remainingSeats}座',
                                                  style: TextStyle(
                                                    fontSize: 12,
                                                    color: Colors.orange[700],
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
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        ),

        // 底部資訊列
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
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
          child: SafeArea(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '最後更新',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                    Text(
                      provider.lastUpdated?.toString().substring(11, 16) ?? '--:--',
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                ElevatedButton.icon(
                  onPressed: () => provider.loadData(direction: provider.currentDirection, forceRefresh: true),
                  icon: const Icon(Icons.refresh, size: 18),
                  label: const Text('重新整理'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
