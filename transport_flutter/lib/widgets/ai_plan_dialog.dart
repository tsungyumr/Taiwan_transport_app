// ai_plan_dialog.dart
// AI 規劃輸入對話框元件

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import '../../ui_theme.dart';
import '../../widgets/styled_inputs.dart';
import 'location_picker_map.dart';

/// AI 規劃輸入對話框
/// 顯示出發地、目的地輸入框及 GPS 抓取功能
class AIPlanDialog extends StatefulWidget {
  final Function(String fromLocation, String toLocation) onSubmit;

  const AIPlanDialog({
    super.key,
    required this.onSubmit,
  });

  /// 顯示對話框的靜態方法
  static Future<void> show(BuildContext context, {
    required Function(String fromLocation, String toLocation) onSubmit,
  }) async {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => AIPlanDialog(
        onSubmit: onSubmit,
      ),
    );
  }

  @override
  State<AIPlanDialog> createState() => _AIPlanDialogState();
}

class _AIPlanDialogState extends State<AIPlanDialog> {
  final TextEditingController _fromController = TextEditingController();
  final TextEditingController _toController = TextEditingController();
  bool _isLoading = false;
  String? _gpsError;

  @override
  void initState() {
    super.initState();
    // 確保輸入框在每次開啟時都是空的
    _fromController.text = '';
    _toController.text = '';
  }

  @override
  void dispose() {
    _fromController.dispose();
    _toController.dispose();
    super.dispose();
  }

  /// 構建地圖選點按鈕
  Widget _buildMapPickerButton({required Function(double lat, double lng) onSelected}) {
    return GestureDetector(
      onTap: () async {
        final currentContext = context;
        // 取得目前 GPS 位置作為地圖中心點
        Position? currentPosition;
        try {
          bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
          if (serviceEnabled) {
            LocationPermission permission = await Geolocator.checkPermission();
            if (permission == LocationPermission.whileInUse ||
                permission == LocationPermission.always) {
              currentPosition = await Geolocator.getCurrentPosition(
                desiredAccuracy: LocationAccuracy.high,
              );
            }
          }
        } catch (e) {
          debugPrint('取得目前位置失敗: $e');
        }

        // 顯示地圖選點對話框
        final result = await LocationPickerMap.show(
          currentContext,
          initialCenter: currentPosition != null
              ? LatLng(currentPosition.latitude, currentPosition.longitude)
              : null,
        );

        // 如果用戶選擇了座標
        if (result != null && mounted) {
          setState(() {
            onSelected(result.latitude, result.longitude);
          });
        }
      },
      child: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: AppColors.secondary.withOpacity(0.1),
          borderRadius: BorderRadius.circular(AppRadius.medium),
          border: Border.all(
            color: AppColors.secondary.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: const Icon(
          Icons.map,
          color: AppColors.secondary,
        ),
      ),
    );
  }

  /// 抓取 GPS 位置
  Future<void> _fetchGPSLocation() async {
    setState(() {
      _isLoading = true;
      _gpsError = null;
    });

    try {
      // 檢查定位服務是否啟用
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        setState(() {
          _gpsError = '請先開啟定位服務';
          _isLoading = false;
        });
        return;
      }

      // 檢查權限
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          setState(() {
            _gpsError = '需要定位權限才能使用此功能';
            _isLoading = false;
          });
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        setState(() {
          _gpsError = '定位權限已被永久拒絕，請在設定中開啟';
          _isLoading = false;
        });
        return;
      }

      // 取得當前位置
      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      // 將座標格式化為地址字串（簡化版）
      String locationText = '${position.latitude.toStringAsFixed(4)}, ${position.longitude.toStringAsFixed(4)}';

      setState(() {
        _fromController.text = locationText;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _gpsError = '無法取得位置：$e';
        _isLoading = false;
      });
    }
  }

  /// 提交表單
  void _submit() {
    final fromLocation = _fromController.text.trim();
    final toLocation = _toController.text.trim();

    if (fromLocation.isEmpty || toLocation.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('請填寫出發地和目的地'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    Navigator.pop(context);
    widget.onSubmit(fromLocation, toLocation);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(AppRadius.xl),
        ),
        boxShadow: [AppShadows.large],
      ),
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom + AppSpacing.lg,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 頂部拖曳指示器
          Container(
            margin: const EdgeInsets.only(top: AppSpacing.md),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.divider,
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // 標題列
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(AppSpacing.sm),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(AppRadius.small),
                  ),
                  child: const Icon(
                    Icons.smart_toy,
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
                        'AI 交通規劃',
                        style: AppTextStyles.titleLarge.copyWith(
                          color: AppColors.onSurface,
                        ),
                      ),
                      Text(
                        '讓 Gemini AI 幫您規劃最佳路線',
                        style: AppTextStyles.bodySmall,
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close, color: AppColors.onSurfaceLight),
                ),
              ],
            ),
          ),

          const Divider(height: 1),

          // 輸入表單
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              children: [
                // 出發地輸入框
                Row(
                  children: [
                    Expanded(
                      child: StyledTextField(
                        controller: _fromController,
                        labelText: '出發地',
                        hintText: '輸入出發地點或抓取 GPS',
                        prefixIcon: Icons.location_on,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    // 地圖選點按鈕
                    _buildMapPickerButton(
                      onSelected: (lat, lng) {
                        setState(() {
                          _fromController.text = '${lat.toStringAsFixed(4)}, ${lng.toStringAsFixed(4)}';
                        });
                      },
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    // GPS 按鈕
                    _isLoading
                        ? Container(
                            width: 48,
                            height: 48,
                            decoration: BoxDecoration(
                              color: AppColors.primary.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(AppRadius.medium),
                            ),
                            child: const Center(
                              child: SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                                ),
                              ),
                            ),
                          )
                        : GestureDetector(
                            onTap: _fetchGPSLocation,
                            child: Container(
                              width: 48,
                              height: 48,
                              decoration: BoxDecoration(
                                color: AppColors.primary.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(AppRadius.medium),
                              ),
                              child: const Icon(
                                Icons.gps_fixed,
                                color: AppColors.primary,
                              ),
                            ),
                          ),
                  ],
                ),

                // GPS 錯誤提示
                if (_gpsError != null)
                  Padding(
                    padding: const EdgeInsets.only(top: AppSpacing.sm),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.error_outline,
                          size: 16,
                          color: AppColors.error,
                        ),
                        const SizedBox(width: AppSpacing.xs),
                        Expanded(
                          child: Text(
                            _gpsError!,
                            style: AppTextStyles.bodySmall.copyWith(
                              color: AppColors.error,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                const SizedBox(height: AppSpacing.md),

                // 目的地輸入框
                Row(
                  children: [
                    Expanded(
                      child: StyledTextField(
                        controller: _toController,
                        labelText: '目的地',
                        hintText: '輸入目的地或抓取GPS',
                        prefixIcon: Icons.flag,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    // 地圖選點按鈕
                    _buildMapPickerButton(
                      onSelected: (lat, lng) {
                        setState(() {
                          _toController.text = '${lat.toStringAsFixed(4)}, ${lng.toStringAsFixed(4)}';
                        });
                      },
                    ),
                  ],
                ),

                const SizedBox(height: AppSpacing.lg),

                // 提交按鈕
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton.icon(
                    onPressed: _submit,
                    icon: const Icon(Icons.auto_fix_high),
                    label: const Text(
                      '開始規劃',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      elevation: 2,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(AppRadius.medium),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// AI 規劃載入遮罩
/// 顯示在 AI 處理中的全螢幕載入畫面
class AIPlanLoadingOverlay extends StatelessWidget {
  final String message;

  const AIPlanLoadingOverlay({
    super.key,
    this.message = 'Gemini AI 正在規劃您的路線...',
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black.withOpacity(0.5),
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(AppSpacing.lg),
          padding: const EdgeInsets.all(AppSpacing.xl),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(AppRadius.large),
            boxShadow: [AppShadows.large],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // AI 動畫圖標
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      AppColors.primary.withOpacity(0.2),
                      AppColors.secondary.withOpacity(0.1),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  shape: BoxShape.circle,
                ),
                child: const Center(
                  child: Icon(
                    Icons.smart_toy,
                    size: 40,
                    color: AppColors.primary,
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.lg),
              // 載入動畫
              const SizedBox(
                width: 40,
                height: 40,
                child: CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                ),
              ),
              const SizedBox(height: AppSpacing.lg),
              // 提示文字
              Text(
                message,
                style: AppTextStyles.titleMedium.copyWith(
                  color: AppColors.onSurface,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.sm),
              Text(
                '這可能需要幾秒鐘',
                style: AppTextStyles.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
