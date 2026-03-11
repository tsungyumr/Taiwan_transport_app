import 'package:flutter/material.dart';
import '../ui_theme.dart';
import '../main.dart';
import '../models/models.dart';
import '../services/search_history_service.dart';

/// 最近搜尋區塊元件
class RecentSearchesSection extends StatelessWidget {
  final List<BusSearchHistoryItem> recentSearches;
  final Function(BusRoute) onRouteSelected;
  final VoidCallback onClearAll;
  final Function(String) onRemoveItem;

  const RecentSearchesSection({
    super.key,
    required this.recentSearches,
    required this.onRouteSelected,
    required this.onClearAll,
    required this.onRemoveItem,
  });

  @override
  Widget build(BuildContext context) {
    if (recentSearches.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 標題列
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(Icons.history, size: 20, color: Colors.grey[600]),
                  const SizedBox(width: 8),
                  const Text(
                    '最近搜尋',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              TextButton.icon(
                onPressed: onClearAll,
                icon: const Icon(Icons.delete_outline, size: 18),
                label: const Text('清除全部'),
                style: TextButton.styleFrom(
                  foregroundColor: Colors.grey[600],
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                ),
              ),
            ],
          ),
        ),
        // 最近搜尋列表
        SizedBox(
          height: 50,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            itemCount: recentSearches.length,
            itemBuilder: (context, index) {
              final item = recentSearches[index];
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: GestureDetector(
                  onTap: () => onRouteSelected(item.toBusRoute()),
                  child: Chip(
                    avatar: const Icon(
                      Icons.directions_bus,
                      size: 18,
                      color: TransportColors.bus,
                    ),
                    label: Text(item.routeName),
                    deleteIcon: const Icon(Icons.close, size: 18),
                    onDeleted: () => onRemoveItem(item.routeId),
                    backgroundColor: Colors.grey[100],
                    side: BorderSide.none,
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

/// 熱門路線區塊元件
class PopularRoutesSection extends StatelessWidget {
  final List<BusSearchHistoryItem> popularRoutes;
  final Function(BusRoute) onRouteSelected;

  const PopularRoutesSection({
    super.key,
    required this.popularRoutes,
    required this.onRouteSelected,
  });

  @override
  Widget build(BuildContext context) {
    if (popularRoutes.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 標題列
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
          child: Row(
            children: [
              Icon(Icons.local_fire_department, size: 20, color: TransportColors.thsr),
              const SizedBox(width: 8),
              const Text(
                '熱門路線',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
        // 熱門路線列表
        ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: popularRoutes.length,
          itemBuilder: (context, index) {
            final item = popularRoutes[index];
            return ListTile(
              leading: CircleAvatar(
                backgroundColor: _getRankColor(index),
                child: Text(
                  '${index + 1}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              title: Text(item.routeName),
              subtitle: Text('${item.departureStop} → ${item.arrivalStop}'),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.search, size: 16, color: Colors.grey[400]),
                  const SizedBox(width: 4),
                  Text(
                    '${item.searchCount}',
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
              onTap: () => onRouteSelected(item.toBusRoute()),
            );
          },
        ),
      ],
    );
  }

  Color _getRankColor(int index) {
    switch (index) {
      case 0:
        return AppColors.secondary; // 第一名琥珀金色
      case 1:
        return Colors.grey[400]!; // 第二名銀色
      case 2:
        return Colors.brown[300]!; // 第三名銅色
      default:
        return AppColors.primary; // 其他使用主色黃色
    }
  }
}

/// 搜尋歷史為空時的提示元件
class EmptySearchHistory extends StatelessWidget {
  const EmptySearchHistory({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.search,
            size: 64,
            color: Colors.grey[300],
          ),
          const SizedBox(height: 16),
          Text(
            '開始搜尋公車路線',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '搜尋過的路線會顯示在這裡',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[400],
            ),
          ),
        ],
      ),
    );
  }
}
