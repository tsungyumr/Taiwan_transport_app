import 'dart:async';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/bus_route.dart';
import '../services/bus_api_service.dart';

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
      data = await BusApiService.fetchBusRouteData(route, direction: _currentDirection);
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
    _timer = Timer.periodic(const Duration(seconds: 30), (timer) => fetchData());
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
        appBar: AppBar(title: Text('$route 公車路線')),
        body: Consumer<BusRouteNotifier>(
          builder: (context, notifier, child) {
            // 取得方向名稱（使用資料或預設值）
            String goDirectionName = '往 終點站';
            String backDirectionName = '往 起點站';

            if (notifier.data != null) {
              final data = notifier.data!;
              if (data.direction.go != null) {
                goDirectionName = data.direction.go!['direction_name'] ?? '往 終點站';
              }
              if (data.direction.back != null) {
                backDirectionName = data.direction.back!['direction_name'] ?? '往 起點站';
              }
            }

            return Column(
              children: [
                // ===== 方向切換按鈕區 =====
                Container(
                  padding: const EdgeInsets.all(12.0),
                  color: Colors.blue[700],
                  child: Row(
                    children: [
                      // 去程按鈕
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: notifier.data == null || notifier.currentDirection == 0
                              ? null
                              : () => notifier.switchDirection(0),
                          icon: const Icon(Icons.arrow_forward),
                          label: Text(goDirectionName),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: notifier.currentDirection == 0
                                ? Colors.white
                                : Colors.blue[500],
                            foregroundColor: notifier.currentDirection == 0
                                ? Colors.blue[700]
                                : Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      // 返程按鈕
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: notifier.data == null || notifier.currentDirection == 1
                              ? null
                              : () => notifier.switchDirection(1),
                          icon: const Icon(Icons.arrow_back),
                          label: Text(backDirectionName),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: notifier.currentDirection == 1
                                ? Colors.white
                                : Colors.blue[500],
                            foregroundColor: notifier.currentDirection == 1
                                ? Colors.blue[700]
                                : Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // 載入中
                if (notifier.data == null)
                  const Expanded(
                    child: Center(child: CircularProgressIndicator()),
                  )
                // 錯誤
                else if (notifier.error != null)
                  Expanded(
                    child: Center(child: Text('錯誤: ${notifier.error}')),
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
        // Bus Summary
        Container(
          height: 60,
          padding: const EdgeInsets.all(8),
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            itemCount: data.buses.length,
            itemBuilder: (ctx, i) {
              final bus = data.buses[i];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: Text('${bus.id} @站${bus.atStop} →${bus.headingTo} (${bus.etaNext})'),
                ),
              );
            },
          ),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: data.stops.length,
            itemBuilder: (ctx, i) {
              final stop = data.stops[i];
              final busesHere = data.buses.where((b) => b.atStop == i + 1 || b.headingTo == i + 1).toList();
              return StopListTile(stop: stop, index: i + 1, buses: busesHere);
            },
          ),
        ),
        // Footer
        Padding(
          padding: const EdgeInsets.all(8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('最後更新: ${notifier.lastUpdated?.toString().substring(11, 16) ?? ''}'),
              ElevatedButton(
                onPressed: () => notifier.fetchData(),
                child: const Text('🔄 重新整理'),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class StopListTile extends StatelessWidget {
  final BusStop stop;
  final int index;
  final List<BusVehicle> buses;

  const StopListTile({super.key, required this.stop, required this.index, required this.buses});

  @override
  Widget build(BuildContext context) {
    Color statusColor = Colors.grey;
    if (stop.eta == '即將進站') statusColor = Colors.green;
    else if (stop.eta.contains('min') && int.tryParse(stop.eta.split('min')[0])! < 5) statusColor = Colors.orange;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Stack(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('$index. ${stop.name}', style: Theme.of(context).textTheme.titleMedium),
                    Text(stop.eta, style: TextStyle(color: statusColor, fontWeight: FontWeight.bold)),
                  ],
                ),
              ],
            ),
          ),
          if (buses.isNotEmpty)
            Positioned(
              top: 8,
              right: 8,
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(color: Colors.blue, shape: BoxShape.circle),
                child: const Icon(Icons.directions_bus, color: Colors.white, size: 24),
              ),
            ),
        ],
      ),
    );
  }
}
