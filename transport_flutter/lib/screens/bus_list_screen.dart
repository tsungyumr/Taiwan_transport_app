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
      appBar: AppBar(title: const Text('公車路線')),
      body: Consumer<BusListProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (provider.error != null) {
            return Center(child: Text('錯誤：${provider.error}'));
          }
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: TextField(
                  controller: _searchController,
                  decoration: const InputDecoration(
                    labelText: '搜尋路線',
                    prefixIcon: Icon(Icons.search),
                    border: OutlineInputBorder(),
                  ),
                  onChanged: (value) => provider.loadRoutes(query: value),
                ),
              ),
              Expanded(
                child: ListView.builder(
                  itemCount: provider.routes.length,
                  itemBuilder: (context, index) {
                    final route = provider.routes[index];
                    return ListTile(
                      title: Text(route.routeName),
                      subtitle: Text('\${route.departureStop} → \${route.arrivalStop}'),
                      trailing: Text(route.operator),
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (ctx) => ChangeNotifierProvider(
                            create: (_) => BusRouteProvider(route.routeName)..startPolling(),
                            child: BusRouteScreen(route: route.routeName),
                          ),
                        ),
                      ),
                    );
                  },
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