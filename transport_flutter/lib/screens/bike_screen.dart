// bike_screen.dart
// YouBike 腳踏車主頁面

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import '../l10n/app_localizations.dart';
import '../models/bike_station.dart';
import '../services/bike_api_service.dart';
import '../ui_theme.dart';
import '../widgets/bike_station_card.dart';
import '../widgets/loading_animations.dart';
import '../widgets/styled_inputs.dart';
import 'bike_map_screen.dart';

class BikeScreen extends StatefulWidget {
  final bool showAppBar;

  const BikeScreen({super.key, this.showAppBar = true});

  @override
  State<BikeScreen> createState() => _BikeScreenState();
}

class _BikeScreenState extends State<BikeScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  List<BikeStation> _allStations = []; // 所有站點
  List<BikeStation> _filteredStations = []; // 篩選後的站點（顯示用）
  bool _isLoading = false;
  DateTime? _lastUpdateTime;

  // 站點統計資訊
  int _totalStationCount = 0;
  final List<String> _cities = ['Taipei', 'NewTaipei'];

  // GPS 位置
  Position? _currentPosition;
  bool _isLocationLoading = false;
  String? _locationError;

  bool _isInitialized = false;

  @override
  void initState() {
    super.initState();
    // 不再這裡初始化，改到 didChangeDependencies
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // 在 didChangeDependencies 中初始化，確保 Localizations 可用
    if (!_isInitialized) {
      _isInitialized = true;
      _initializeScreen();
    }
  }

  /// 初始化畫面：先取得 GPS 位置，再載入站點
  Future<void> _initializeScreen() async {
    await _getCurrentLocation();
    await _loadStations();
  }

  /// 取得當前 GPS 位置
  Future<void> _getCurrentLocation() async {
    final l10n = AppLocalizations.of(context)!;
    setState(() => _isLocationLoading = true);

    try {
      // 檢查位置服務是否啟用
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        setState(() {
          _locationError = l10n.bikeGpsDisabled;
          _isLocationLoading = false;
        });
        return;
      }

      // 檢查權限
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          setState(() {
            _locationError = l10n.bikePermissionDenied;
            _isLocationLoading = false;
          });
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        setState(() {
          _locationError = l10n.bikePermissionDeniedForever;
          _isLocationLoading = false;
        });
        return;
      }

      // 取得當前位置
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      setState(() {
        _currentPosition = position;
        _locationError = null;
        _isLocationLoading = false;
      });

      print('取得 GPS 位置: ${position.latitude}, ${position.longitude}');
    } catch (e) {
      setState(() {
        _locationError = '${l10n.bikeLocationFailed}: $e';
        _isLocationLoading = false;
      });
      print('取得 GPS 位置失敗: $e');
    }
  }

  /// 計算兩點間的距離（公里）
  double _calculateDistance(
      double lat1, double lon1, double lat2, double lon2) {
    const Distance distance = Distance();
    return distance.as(
      LengthUnit.Kilometer,
      LatLng(lat1, lon1),
      LatLng(lat2, lon2),
    );
  }

  /// 根據距離排序並只顯示最近的 N 個站點
  void _sortStationsByDistance({int limit = 5}) {
    if (_currentPosition == null) return;

    // 計算每個站點與當前位置的距離
    final stationsWithDistance = _allStations.map((station) {
      final dist = _calculateDistance(
        _currentPosition!.latitude,
        _currentPosition!.longitude,
        station.lat,
        station.lng,
      );
      return station.copyWithDistance(dist);
    }).toList();

    // 按距離排序（近的在前）
    stationsWithDistance.sort((a, b) {
      final distA = a.distance ?? double.infinity;
      final distB = b.distance ?? double.infinity;
      return distA.compareTo(distB);
    });

    // 只取前 N 個
    setState(() {
      _filteredStations = stationsWithDistance.take(limit).toList();
    });
  }

  /// 載入所有 YouBike 站點
  Future<void> _loadStations() async {
    final l10n = AppLocalizations.of(context)!;
    setState(() => _isLoading = true);

    try {
      // 呼叫真實 API 取得站點資料
      final stations = await BikeApiService.getAllStations();

      if (!mounted) return;

      setState(() {
        _allStations = stations;
        _totalStationCount = stations.length;
        _isLoading = false;
        _lastUpdateTime = DateTime.now();
      });

      // 如果有 GPS 位置，自動顯示最近的 5 個站點
      if (_currentPosition != null) {
        _sortStationsByDistance(limit: 5);
      } else {
        // 沒有 GPS 時顯示所有站點
        setState(() {
          _filteredStations = stations;
        });
      }
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _isLoading = false;
      });

      // 顯示錯誤提示
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${l10n.bikeLoadFailed}: $e'),
          backgroundColor: Colors.red,
          behavior: SnackBarBehavior.floating,
          action: SnackBarAction(
            label: l10n.bikeRetry,
            onPressed: _loadStations,
          ),
        ),
      );
    }
  }

  /// 搜尋/篩選站點
  void _filterStations(String query) {
    setState(() {
      if (query.isEmpty) {
        // 搜尋框清空時，恢復顯示最近的 5 個站點
        if (_currentPosition != null) {
          _sortStationsByDistance(limit: 5);
        } else {
          _filteredStations = _allStations;
        }
      } else {
        // 有搜尋關鍵字時，顯示所有符合的站點
        _filteredStations = _allStations.where((station) {
          return station.name.toLowerCase().contains(query.toLowerCase()) ||
              station.address.toLowerCase().contains(query.toLowerCase());
        }).toList();
        // 按距離排序（如果有的話）
        if (_currentPosition != null) {
          _filteredStations.sort((a, b) {
            final distA = a.distance ?? double.infinity;
            final distB = b.distance ?? double.infinity;
            return distA.compareTo(distB);
          });
        }
      }
    });
  }

  /// 根據熱門程度排序站點（已棄用，改為按距離排序）
  void _sortStationsByPopularity() {
    // 現在主要按距離排序
    if (_currentPosition != null) {
      _sortStationsByDistance(limit: 5);
    }
  }

  /// 選擇站點（點擊觀看）
  Future<void> _selectStation(BikeStation station) async {
    final l10n = AppLocalizations.of(context)!;
    if (!mounted) return;

    // 關閉任何已開啟的 bottom sheet（切換站點時）
    _closeBottomSheet();

    // 顯示站點詳情（暫時用 SnackBar，未來可導航到詳情頁）
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(Icons.pedal_bike, color: station.statusColor),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Text(
                '${station.name} - ${station.statusText}',
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
            ),
          ],
        ),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.small),
        ),
        duration: const Duration(seconds: 2),
        action: SnackBarAction(
          label: l10n.bikeNavigate,
          onPressed: () => _openNavigation(station),
        ),
      ),
    );
  }

  /// 開啟導航
  Future<void> _openNavigation(BikeStation station) async {
    if (!mounted) return;

    if (!mounted) return;

    // 顯示導航選項
    Navigator.of(context).push(MaterialPageRoute(
      builder: (context) => BikeMapScreen(initialStation: station),
    ));
  }

  /// 關閉 Bottom Sheet
  void _closeBottomSheet() {
    if (mounted) {
      ScaffoldMessenger.of(context).clearSnackBars();
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: widget.showAppBar
          ? AppBar(
              title: Text(l10n.bikeTitle),
              backgroundColor: BikeColors.primary,
              foregroundColor: Colors.white,
              elevation: 0,
              flexibleSpace: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      BikeColors.primary,
                      BikeColors.primaryLight,
                    ],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
              ),
            )
          : null,
      body: InkWell(
        onTap: () {
          _closeBottomSheet();
        },
        child: Column(
          children: [
            // 搜尋欄與位置資訊
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
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 搜尋欄
                  SearchTextField(
                    controller: _searchController,
                    hintText: l10n.bikeSearchHint,
                    onChanged: _filterStations,
                    onClear: () {
                      _searchController.clear();
                      _filterStations('');
                    },
                    onSearch: () => _filterStations(_searchController.text),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  // 位置資訊列
                  _buildLocationInfo(),
                ],
              ),
            ),
            // 統計資訊列
            if (_totalStationCount > 0)
              StationStatsBar(
                totalStations: _totalStationCount,
                cities: _cities,
                lastUpdateTime: _lastUpdateTime,
                onRefresh: _initializeScreen,
              ),
            // 站點列表
            Expanded(
              child: _isLoading
                  ? const SkeletonLoading(itemCount: 8)
                  : _buildStationsList(),
            ),
          ],
        ),
      ),
      floatingActionButton: IconButton(
          color: Colors.red,
          iconSize: 32,
          onPressed: () {
            Navigator.of(context).push(MaterialPageRoute(
              builder: (context) => const BikeMapScreen(),
            ));
          },
          icon: const Icon(Icons.map)),
    );
  }

  /// 建立位置資訊顯示
  Widget _buildLocationInfo() {
    final l10n = AppLocalizations.of(context)!;

    if (_isLocationLoading) {
      return Row(
        children: [
          const SizedBox(
            width: 12,
            height: 12,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: BikeColors.primary,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            l10n.bikeGettingLocation,
            style: AppTextStyles.labelSmall.copyWith(
              color: AppColors.onSurfaceLight,
            ),
          ),
        ],
      );
    }

    if (_locationError != null) {
      return Row(
        children: [
          const Icon(
            Icons.location_off,
            size: 14,
            color: AppColors.error,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _locationError!,
              style: AppTextStyles.labelSmall.copyWith(
                color: AppColors.error,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          TextButton(
            onPressed: _getCurrentLocation,
            child: Text(l10n.bikeRetry),
          ),
        ],
      );
    }

    if (_currentPosition != null) {
      return Row(
        children: [
          const Icon(
            Icons.location_on,
            size: 14,
            color: BikeColors.primary,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _searchController.text.isEmpty
                  ? l10n.bikeShowNearby
                  : l10n.bikeShowSearchResults,
              style: AppTextStyles.labelSmall.copyWith(
                color: AppColors.onSurfaceLight,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          TextButton(
            onPressed: _getCurrentLocation,
            child: Text(l10n.bikeUpdateLocation),
          ),
        ],
      );
    }

    return Row(
      children: [
        const Icon(
          Icons.location_off,
          size: 14,
          color: AppColors.onSurfaceLight,
        ),
        const SizedBox(width: 8),
        Text(
          l10n.bikeLocationFailed,
          style: AppTextStyles.labelSmall.copyWith(
            color: AppColors.onSurfaceLight,
          ),
        ),
      ],
    );
  }

  /// 建立站點列表
  Widget _buildStationsList() {
    if (_filteredStations.isEmpty) {
      return BikeEmptyStateCard(
        searchQuery: _searchController.text.isNotEmpty
            ? _searchController.text
            : (_locationError != null && _allStations.isEmpty
                ? 'location_error'
                : null),
        onClearSearch: _searchController.text.isNotEmpty
            ? () {
                _searchController.clear();
                _filterStations('');
              }
            : null,
        onRetry: _searchController.text.isEmpty && _locationError != null
            ? _getCurrentLocation
            : (_searchController.text.isEmpty ? _loadStations : null),
      );
    }

    return RefreshIndicator(
      onRefresh: _initializeScreen,
      color: BikeColors.primary,
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(AppSpacing.md),
        itemCount: _filteredStations.length,
        itemBuilder: (context, index) {
          final station = _filteredStations[index];

          return FadeInAnimation(
            delay: Duration(milliseconds: (index % 10) * 30),
            child: BikeStationCard(
              station: station,
              onTap: () => _selectStation(station),
              onNavigate: () => _openNavigation(station),
            ),
          );
        },
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}
