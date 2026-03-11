// station_marker.dart
// UBike 站點地圖標記元件

import 'package:flutter/material.dart';
import '../models/bike_station.dart';
import '../ui_theme.dart';

/// UBike 站點地圖標記
class StationMarker extends StatelessWidget {
  final BikeStation station;
  final VoidCallback onTap;

  const StationMarker({
    super.key,
    required this.station,
    required this.onTap,
  });

  /// 取得狀態顏色
  Color get _statusColor {
    switch (station.status) {
      case BikeStatus.available:
        return Colors.green.shade500;
      case BikeStatus.limited:
        return Colors.amber.shade500;
      case BikeStatus.few:
        return Colors.red.shade500;
      case BikeStatus.empty:
        return Colors.grey.shade500;
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Stack(children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: _statusColor,
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 2),
            boxShadow: const [AppShadows.small],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.pedal_bike,
                size: 16,
                color: Colors.white,
              ),
              Text(
                '${station.availableBikes}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
        if (station.matchSearch)
          Container(
            margin: const EdgeInsets.only(top: 13, left: 32),
            child: const Icon(
              Icons.star_border,
              size: 35,
              color: Colors.cyanAccent,
            ),
          ),
      ]),
    );
  }
}

/// 用戶位置標記
class UserLocationMarker extends StatelessWidget {
  const UserLocationMarker({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 24,
      height: 24,
      decoration: BoxDecoration(
        color: Colors.blue.shade500,
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 3),
        boxShadow: const [
          BoxShadow(
            color: Color(0x1A000000),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
    );
  }
}

/// 定位按鈕
class LocationButton extends StatelessWidget {
  final VoidCallback onPressed;

  const LocationButton({
    super.key,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton.small(
      onPressed: onPressed,
      backgroundColor: Colors.white,
      foregroundColor: AppColors.primary,
      elevation: 4,
      child: const Icon(Icons.my_location),
    );
  }
}

/// 重新整理按鈕
class RefreshButton extends StatelessWidget {
  final VoidCallback onPressed;
  final bool isLoading;

  const RefreshButton({
    super.key,
    required this.onPressed,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton.small(
      onPressed: isLoading ? null : onPressed,
      backgroundColor: Colors.white,
      foregroundColor: AppColors.primary,
      elevation: 4,
      child: isLoading
          ? const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
              ),
            )
          : const Icon(Icons.refresh),
    );
  }
}
