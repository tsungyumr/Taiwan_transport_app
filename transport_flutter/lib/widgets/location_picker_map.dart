// location_picker_map.dart
// 地圖選點對話框 - 讓用戶從地圖上選擇座標位置

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../ui_theme.dart';

/// 地圖選點對話框
/// 顯示地圖，讓用戶點擊選擇座標位置
class LocationPickerMap extends StatefulWidget {
  final LatLng? initialCenter;

  const LocationPickerMap({
    super.key,
    this.initialCenter,
  });

  /// 顯示地圖選點對話框
  static Future<LatLng?> show(
    BuildContext context, {
    LatLng? initialCenter,
  }) async {
    return showDialog<LatLng?>(
      context: context,
      barrierDismissible: false,
      builder: (context) => LocationPickerMap(
        initialCenter: initialCenter,
      ),
    );
  }

  @override
  State<LocationPickerMap> createState() => _LocationPickerMapState();
}

class _LocationPickerMapState extends State<LocationPickerMap> {
  LatLng? _selectedLocation;
  final MapController _mapController = MapController();

  @override
  Widget build(BuildContext context) {
    // 預設中心點（台北市中心）
    final centerPoint = widget.initialCenter ?? LatLng(25.0330, 121.5654);

    return Dialog(
      insetPadding: const EdgeInsets.all(16),
      child: Container(
        width: double.infinity,
        height: MediaQuery.of(context).size.height * 0.7,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(AppRadius.large),
        ),
        child: Column(
          children: [
            // 標題列
            Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(AppSpacing.sm),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(AppRadius.small),
                    ),
                    child: const Icon(
                      Icons.map,
                      color: AppColors.primary,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '選擇地點',
                          style: AppTextStyles.titleLarge.copyWith(
                            color: AppColors.onSurface,
                          ),
                        ),
                        Text(
                          '點擊地圖選擇位置',
                          style: AppTextStyles.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.pop(context, null),
                    icon: const Icon(Icons.close, color: AppColors.onSurfaceLight),
                  ),
                ],
              ),
            ),

            const Divider(height: 1),

            // 地圖區域
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.vertical(
                  bottom: Radius.circular(AppRadius.large),
                ),
                child: FlutterMap(
                  mapController: _mapController,
                  options: MapOptions(
                    initialCenter: centerPoint,
                    initialZoom: 15,
                    onTap: (tapPosition, latLng) {
                      setState(() {
                        _selectedLocation = latLng;
                      });
                    },
                  ),
                  children: [
                    // 底圖圖層
                    TileLayer(
                      urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                      userAgentPackageName: 'com.example.taiwan_transport',
                    ),
                    // 選擇點標記
                    if (_selectedLocation != null)
                      MarkerLayer(
                        markers: [
                          Marker(
                            point: _selectedLocation!,
                            width: 50,
                            height: 50,
                            child: Container(
                              decoration: BoxDecoration(
                                color: AppColors.primary.withOpacity(0.3),
                                shape: BoxShape.circle,
                              ),
                              child: Center(
                                child: Container(
                                  width: 20,
                                  height: 20,
                                  decoration: const BoxDecoration(
                                    color: AppColors.primary,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(
                                    Icons.location_on,
                                    color: Colors.white,
                                    size: 14,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                  ],
                ),
              ),
            ),

            // 底部資訊和按鈕
            Container(
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: const BorderRadius.vertical(
                  bottom: Radius.circular(AppRadius.large),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 4,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // 顯示選擇的座標
                  if (_selectedLocation != null)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(AppSpacing.sm),
                      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(AppRadius.small),
                        border: Border.all(
                          color: AppColors.primary.withOpacity(0.3),
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.location_on,
                            color: AppColors.primary,
                            size: 20,
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          Expanded(
                            child: Text(
                              '已選擇: ${_selectedLocation!.latitude.toStringAsFixed(4)}, ${_selectedLocation!.longitude.toStringAsFixed(4)}',
                              style: AppTextStyles.bodyMedium.copyWith(
                                color: AppColors.onSurface,
                              ),
                            ),
                          ),
                        ],
                      ),
                    )
                  else
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(AppSpacing.sm),
                      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(AppRadius.small),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.touch_app,
                            color: Colors.grey[600],
                            size: 20,
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          Expanded(
                            child: Text(
                              '點擊地圖選擇位置',
                              style: AppTextStyles.bodyMedium.copyWith(
                                color: Colors.grey[600],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                  // 按鈕列
                  Row(
                    children: [
                      // 取消按鈕
                      Expanded(
                        child: TextButton(
                          onPressed: () => Navigator.pop(context, null),
                          child: const Text('取消'),
                        ),
                      ),
                      const SizedBox(width: AppSpacing.sm),
                      // 確認按鈕
                      Expanded(
                        flex: 2,
                        child: ElevatedButton.icon(
                          onPressed: _selectedLocation != null
                              ? () => _showConfirmDialog()
                              : null,
                          icon: const Icon(Icons.check, size: 18),
                          label: const Text('確認選擇'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            disabledBackgroundColor: Colors.grey[300],
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(AppRadius.medium),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 顯示確認對話框
  void _showConfirmDialog() {
    if (_selectedLocation == null) return;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.large),
        ),
        title: Row(
          children: [
            Icon(Icons.check_circle, color: AppColors.primary),
            const SizedBox(width: AppSpacing.sm),
            const Text('確認選擇'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '確定要選擇這個座標嗎？',
              style: AppTextStyles.bodyLarge,
            ),
            const SizedBox(height: AppSpacing.md),
            Container(
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(AppRadius.small),
                border: Border.all(
                  color: AppColors.primary.withOpacity(0.3),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '緯度: ${_selectedLocation!.latitude.toStringAsFixed(6)}',
                    style: AppTextStyles.bodyMedium.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    '經度: ${_selectedLocation!.longitude.toStringAsFixed(6)}',
                    style: AppTextStyles.bodyMedium.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('重新選擇'),
          ),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.pop(context); // 關閉確認對話框
              Navigator.pop(context, _selectedLocation); // 關閉地圖對話框並返回結果
            },
            icon: const Icon(Icons.check, size: 18),
            label: const Text('確定'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}
