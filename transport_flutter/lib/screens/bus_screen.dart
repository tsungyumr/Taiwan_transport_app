import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import 'bus_route_page.dart';

class BusScreen extends StatefulWidget {
  const BusScreen({super.key});

  @override
  State<BusScreen> createState() => _BusScreenState();
}

class _BusScreenState extends State<BusScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _searchController = TextEditingController();
  
  List<BusRoute> _routes = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _searchRoutes();
  }

  Future<void> _searchRoutes() async {
    // 檢查 widget 是否仍在樹中，避免 dispose 後調用 setState
    if (!mounted) return;

    setState(() => _isLoading = true);

    final routes = await _apiService.getBusRoutes(
      routeName: _searchController.text.isEmpty ? null : _searchController.text,
    );

    // 再次檢查 mounted，因為異步操作後 widget 可能已被銷毀
    if (!mounted) return;

    setState(() {
      _routes = routes;
      _isLoading = false;
    });
  }

  void _selectRoute(BusRoute route) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => BusRoutePage(route: route.routeName),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('大台北公車'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: '輸入公車路線名稱',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    _searchController.clear();
                    _searchRoutes();
                  },
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
                fillColor: Colors.grey[100],
              ),
              onSubmitted: (_) => _searchRoutes(),
            ),
          ),
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _routes.isEmpty
                      ? const Center(child: Text('請輸入公車路線名稱搜尋'))
                      : ListView.builder(
                          itemCount: _routes.length,
                          itemBuilder: (context, index) {
                            final route = _routes[index];
                            return ListTile(
                              leading: const CircleAvatar(
                                backgroundColor: Colors.green,
                                child: Icon(Icons.directions_bus, color: Colors.white),
                              ),
                              title: Text(route.routeName),
                              subtitle: Text('${route.departureStop} → ${route.arrivalStop}'),
                              trailing: Text(route.operator),
                              onTap: () => _selectRoute(route),
                            );
                          },
                        ),
            ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
}
