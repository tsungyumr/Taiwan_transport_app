// bike_map_screen.dart
// UBike 地圖頁面

import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import '../models/bike_station.dart';
import '../services/bike_api_service.dart';
import '../ui_theme.dart';
import '../l10n/app_localizations.dart';
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
      _userLocation = await _getCurrentLocation();

      if (widget.initialStation != null) {
        setState(() => _selectStation(widget.initialStation!));
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
      _mapController.move(location, 25);
    }
  }

  LatLng getCenterCoordinate(List<LatLng> coords) {
    if (coords.isEmpty) return LatLng(0, 0);
    if (coords.length == 1) return coords.first;

    double x = 0;
    double y = 0;
    double z = 0;

    for (var coord in coords) {
      // 將角度轉換為弧度
      double lat = coord.latitude * pi / 180;
      double lon = coord.longitude * pi / 180;

      // 轉換為 3D 笛卡兒座標
      x += cos(lat) * cos(lon);
      y += cos(lat) * sin(lon);
      z += sin(lat);
    }

    // 計算平均值
    int total = coords.length;
    x /= total;
    y /= total;
    z /= total;

    // 將平均後的笛卡兒座標轉回經緯度
    double centralLon = atan2(y, x);
    double centralHyp = sqrt(x * x + y * y);
    double centralLat = atan2(z, centralHyp);

    // 轉回角度並回傳
    return LatLng(centralLat * 180 / pi, centralLon * 180 / pi);
  }

  /// 搜尋地點
  Future<void> _searchLocation() async {
    final keyword = _searchController.text.trim();
    if (keyword.isEmpty) {
      setState(() {
        for (var station in _stations) {
          station.matchSearch = false;
        }
      });
      return;
    }

    setState(() => _isSearching = true);

    try {
      _closeStationDetail();

      final l10n = AppLocalizations.of(context)!;
      bool find = false;
      List<LatLng> coords = [];

      setState(() {
        for (var station in _stations) {
          if (station.name.contains(keyword)) {
            station.matchSearch = true;
            coords.add(LatLng(station.lat, station.lng));
            find = true;
          } else {
            station.matchSearch = false;
          }
        }
      });

      if (!find) {
        // 顯示搜尋失敗提示
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l10n.bikeLocationNotFound(keyword)),
            duration: const Duration(seconds: 2),
          ),
        );
      } else {
        LatLng center = getCenterCoordinate(coords);
        _mapController.move(LatLng(center.latitude, center.longitude), 16);
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
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.bikeMapTitle),
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
              initialCenter: _userLocation ??
                  (widget.initialStation != null
                      ? LatLng(widget.initialStation!.lat, widget.initialStation!.lng)
                      : const LatLng(25.0478, 121.5170)), // 台北車站預設位置
              initialZoom: 16,
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
              hintText: l10n.bikeMapSearchHint,
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
                    SnackBar(
                      content: Text(l10n.bikeScanToRent),
                      duration: const Duration(seconds: 2),
                    ),
                  );
                },
                onReturn: () {
                  // 還車按鈕動作
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(l10n.bikeReturnToPillar),
                      duration: const Duration(seconds: 2),
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
  final String hintText;

  const _SearchBar({
    required this.controller,
    required this.onSearch,
    this.isLoading = false,
    required this.hintText,
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
                hintText: hintText,
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
            const SizedBox(
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
