import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/bus_provider.dart';
import 'bus_route_screen.dart';

class BusListScreen extends StatefulWidget {
  const BusListScreen({super.key});

  @override
  State<BusListScreen> createState() => _BusListScreenState();
}

class _BusListScreenState extends State<BusListScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<BusListProvider>(context, listen: false).loadRoutes();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('新北市公車路線'),
        actions: [
          // 清除搜尋按鈕
          Consumer<BusListProvider>(
            builder: (context, provider, child) {
              if (provider.searchQuery.isNotEmpty) {
                return IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    _searchController.clear();
                    provider.clearSearch();
                  },
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
      body: Consumer<BusListProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (provider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('錯誤：${provider.error}'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.loadRoutes(),
                    child: const Text('重試'),
                  ),
                ],
              ),
            );
          }
          return Column(
            children: [
              // 搜尋欄
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    labelText: '搜尋路線（名稱、起迄站）',
                    hintText: '例如：935、板橋、台北',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: () {
                              _searchController.clear();
                              provider.clearSearch();
                            },
                          )
                        : null,
                    border: const OutlineInputBorder(),
                  ),
                  onChanged: (value) {
                    if (value.isEmpty) {
                      provider.clearSearch();
                    } else {
                      provider.loadRoutes(query: value);
                    }
                  },
                ),
              ),

              // 結果統計
              if (provider.searchQuery.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      '找到 ${provider.routes.length} 條路線',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ),

              // 路線列表
              Expanded(
                child: provider.routes.isEmpty
                    ? const Center(
                        child: Text('沒有找到路線'),
                      )
                    : RefreshIndicator(
                        onRefresh: () => provider.loadRoutes(query: provider.searchQuery),
                        child: ListView.builder(
                          physics: const AlwaysScrollableScrollPhysics(),
                          itemCount: provider.routes.length,
                          itemBuilder: (context, index) {
                          final route = provider.routes[index];
                          return Card(
                            margin: const EdgeInsets.symmetric(
                              horizontal: 16.0,
                              vertical: 4.0,
                            ),
                            child: ListTile(
                              leading: CircleAvatar(
                                child: Text(
                                  route.routeName.length > 3
                                      ? route.routeName.substring(0, 3)
                                      : route.routeName,
                                  style: const TextStyle(fontSize: 12),
                                ),
                              ),
                              title: Text(
                                route.routeName,
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('${route.departureStop} → ${route.arrivalStop}'),
                                  if (route.operator.isNotEmpty)
                                    Text(
                                      route.operator,
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: Colors.grey[600],
                                      ),
                                    ),
                                ],
                              ),
                              isThreeLine: route.operator.isNotEmpty,
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () => Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (ctx) => ChangeNotifierProvider(
                                    create: (_) => BusRouteProvider(route.routeId)
                                      ..startPolling(),
                                    child: BusRouteScreen(route: route.routeId),
                                  ),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
              ),
            ],
          );
        },
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
}