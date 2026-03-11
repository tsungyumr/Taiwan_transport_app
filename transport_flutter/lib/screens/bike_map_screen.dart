// bike_map_screen.dart
// UBike 地圖頁面

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import '../models/bike_station.dart';
import '../services/bike_api_service.dart';
import '../ui_theme.dart';
import '../widgets/station_marker.dart';
import '../widgets/station_detail_card.dart';

/// UBike 地圖頁面
class BikeMapScreen extends StatefulWidget {
  final BikeStation? initialStation;

  const BikeMapScreen({
    super.key,
    this.initialStation,
  });

  @override
  State<BikeMapScreen> createState() => _BikeMapScreenState();
}

class _BikeMapScreenState extends State<BikeMapScreen> {
  final MapController _mapController = MapController();
  final TextEditingController _searchController = TextEditingController();

  List<BikeStation> _stations = [];
  BikeStation? _selectedStation;
  LatLng? _userLocation;
  bool _isLoading = false;
  bool _isSearching = false;

  @override
  void initState() {
    super.initState();
    _initializeMap();
  }

  @override
  void dispose() {
    _mapController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  /// 初始化地圖
  Future<void> _initializeMap() async {
    setState(() => _isLoading = true);

    try {
      // 如果有初始站點，先定位到該站點
      if (widget.initialStation != null) {
        _userLocation = LatLng(
          widget.initialStation!.lat,
          widget.initialStation!.lng,
        );
      } else {
        // 否則取得用戶位置
        _userLocation = await _getCurrentLocation();
      }

      // 載入站點資料
      await _loadStations();
    } finally {
      setState(() => _isLoading = false);
    }
  }

  /// 取得當前位置
  Future<LatLng?> _getCurrentLocation() async {
    try {
      // 檢查定位服務
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        // 定位服務未開啟，使用預設位置（台北市中心）
        return const LatLng(25.0330, 121.5654);
      }

      // 檢查權限
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          // 權限被拒絕，使用預設位置
          return const LatLng(25.0330, 121.5654);
        }
      }

      if (permission == LocationPermission.deniedForever) {
        // 權限永久被拒絕，使用預設位置
        return const LatLng(25.0330, 121.5654);
      }

      // 取得位置
      Position position = await Geolocator.getCurrentPosition();
      return LatLng(position.latitude, position.longitude);
    } catch (e) {
      print('取得位置失敗: $e');
      // 使用預設位置
      return const LatLng(25.0330, 121.5654);
    }
  }

  /// 載入站點資料
  Future<void> _loadStations() async {
    try {
      final stations = await BikeApiService.getAllStations();
      setState(() {
        _stations = stations;
      });
    } catch (e) {
      print('載入站點失敗: $e');
    }
  }

  /// 移動到用戶位置
  Future<void> _moveToUserLocation() async {
    final location = await _getCurrentLocation();
    if (location != null) {
      setState(() => _userLocation = location);
      _mapController.move(location, 16);
    }
  }

  /// 搜尋地點
  Future<void> _searchLocation() async {
    final keyword = _searchController.text.trim();
    if (keyword.isEmpty) return;

    setState(() => _isSearching = true);

    try {
      final location = await BikeApiService.searchLocation(keyword);
      if (location != null) {
        _mapController.move(location, 16);
        setState(() => _userLocation = location);
      } else {
        // 顯示搜尋失敗提示
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('找不到 "$keyword" 的位置'),
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } finally {
      setState(() => _isSearching = false);
    }
  }

  /// 選擇站點
  void _selectStation(BikeStation station) {
    setState(() => _selectedStation = station);
    _mapController.move(
      LatLng(station.lat, station.lng),
      _mapController.camera.zoom,
    );
  }

  /// 關閉站點詳情
  void _closeStationDetail() {
    setState(() => _selectedStation = null);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('地圖'),
        backgroundColor: BikeColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Stack(
        children: [
          // 地圖
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _userLocation ?? const LatLng(25.0330, 121.5654),
              initialZoom: 14,
              minZoom: 10,
              maxZoom: 18,
              onTap: (_, __) => _closeStationDetail(),
            ),
            children: [
              // OpenStreetMap 底圖
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.example.transport_flutter',
              ),
              // 站點標記圖層
              MarkerLayer(
                markers: _stations.map((station) {
                  return Marker(
                    width: 48,
                    height: 48,
                    point: LatLng(station.lat, station.lng),
                    child: StationMarker(
                      station: station,
                      onTap: () => _selectStation(station),
                    ),
                  );
                }).toList(),
              ),
              // 用戶位置標記
              if (_userLocation != null)
                MarkerLayer(
                  markers: [
                    Marker(
                      width: 24,
                      height: 24,
                      point: _userLocation!,
                      child: const UserLocationMarker(),
                    ),
                  ],
                ),
            ],
          ),
          // 搜尋欄
          Positioned(
            top: 16,
            left: 16,
            right: 16,
            child: _SearchBar(
              controller: _searchController,
              onSearch: _searchLocation,
              isLoading: _isSearching,
            ),
          ),
          // 控制按鈕
          Positioned(
            right: 16,
            bottom: _selectedStation != null ? 280 : 32,
            child: Column(
              children: [
                RefreshButton(
                  onPressed: _loadStations,
                  isLoading: _isLoading,
                ),
                const SizedBox(height: 8),
                LocationButton(
                  onPressed: _moveToUserLocation,
                ),
              ],
            ),
          ),
          // 載入中指示器
          if (_isLoading)
            const Center(
              child: CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(BikeColors.primary),
              ),
            ),
          // 底部站點詳情卡片
          if (_selectedStation != null)
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: StationDetailCard(
                station: _selectedStation!,
                onClose: _closeStationDetail,
                onRent: () {
                  // 租借按鈕動作
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('請使用 YouBike App 掃碼租借'),
                      duration: Duration(seconds: 2),
                    ),
                  );
                },
                onReturn: () {
                  // 還車按鈕動作
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('請將腳踏車歸還至停車柱'),
                      duration: Duration(seconds: 2),
                    ),
                  );
                },
              ),
            ),
        ],
      ),
    );
  }
}

/// 搜尋欄
class _SearchBar extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSearch;
  final bool isLoading;

  const _SearchBar({
    required this.controller,
    required this.onSearch,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(AppRadius.medium),
        boxShadow: const [AppShadows.medium],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              decoration: InputDecoration(
                hintText: '搜尋地點...',
                hintStyle: TextStyle(
                  color: AppColors.onSurfaceLight.withOpacity(0.5),
                ),
                border: InputBorder.none,
                contentPadding: EdgeInsets.zero,
                isDense: true,
              ),
              style: const TextStyle(fontSize: 16),
              onSubmitted: (_) => onSearch(),
            ),
          ),
          if (isLoading)
            SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
              ),
            )
          else
            Row(
              children: [
                IconButton(
                  onPressed: onSearch,
                  icon: const Icon(Icons.search),
                  color: AppColors.primary,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: () {
                    controller.clear();
                  },
                  icon: const Icon(Icons.clear),
                  color: AppColors.onSurfaceLight,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
        ],
      ),
    );
  }
}
