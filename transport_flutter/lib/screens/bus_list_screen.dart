import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/bus_route.dart';
import '../providers/bus_provider.dart';
import '../widgets/animated_card.dart';
import '../widgets/loading_animations.dart';
import '../widgets/styled_inputs.dart';
import '../ui_theme.dart';
import 'bus_route_page.dart';

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
            return const Center(
              child: PulseLoading(color: TransportColors.bus),
            );
          }
          if (provider.error != null) {
            return Center(
              child: EmptyStateCard(
                icon: Icons.error_outline,
                title: '載入失敗',
                subtitle: provider.error,
                onAction: () => provider.loadRoutes(),
                actionLabel: '重試',
              ),
            );
          }
          return Column(
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
                  hintText: '搜尋路線（名稱、起迄站）',
                  onChanged: (value) {
                    if (value.isEmpty) {
                      provider.clearSearch();
                    } else {
                      provider.loadRoutes(query: value);
                    }
                  },
                  onClear: () => provider.clearSearch(),
                  onSearch: () {},
                ),
              ),

              // 結果統計
              if (provider.searchQuery.isNotEmpty)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.md,
                    vertical: AppSpacing.sm,
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.search,
                        size: 14,
                        color: AppColors.onSurfaceLight,
                      ),
                      const SizedBox(width: AppSpacing.xs),
                      Text(
                        '找到 ${provider.routes.length} 條路線',
                        style: AppTextStyles.labelMedium,
                      ),
                    ],
                  ),
                ),

              // 路線列表
              Expanded(
                child: provider.routes.isEmpty
                    ? EmptyStateCard(
                        icon: Icons.search_off,
                        title: '沒有找到路線',
                        subtitle: '請嘗試其他關鍵字搜尋',
                      )
                    : RefreshIndicator(
                        onRefresh: () =>
                            provider.loadRoutes(query: provider.searchQuery),
                        color: TransportColors.bus,
                        child: ListView.builder(
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.all(AppSpacing.md),
                          itemCount: provider.routes.length,
                          itemBuilder: (context, index) {
                            final route = provider.routes[index];
                            return FadeInAnimation(
                              delay: Duration(milliseconds: index * 30),
                              child: BusRouteCard(
                                routeName: route.routeName,
                                fromStop: route.departureStop,
                                toStop: route.arrivalStop,
                                operator: route.operator,
                                onTap: () => Navigator.push(
                                  context,
                                  SlidePageRoute(
                                    builder: (ctx) => BusRoutePage(
                                        route: route.routeId),
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
