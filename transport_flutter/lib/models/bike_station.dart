// bike_station.dart
// YouBike 站點資料模型

import 'package:flutter/material.dart';

/// YouBike 站點狀態
enum BikeStatus {
  available,  // 充足 (> 10)
  limited,    // 中等 (5-10)
  few,        // 少量 (1-4)
  empty,      // 無車 (0)
}

/// YouBike 站點資料模型
class BikeStation {
  final String stationId;      // 站點ID
  final String name;           // 站點名稱
  final String address;        // 地址
  final double lat;            // 緯度
  final double lng;            // 經度
  final int totalSlots;        // 總停車位
  final int availableBikes;    // 剩餘車輛
  final int emptySlots;        // 空位數
  final DateTime updateTime;   // 更新時間
  final double? distance;      // 與用戶距離（公里）
  bool matchSearch = false;       // 是否正在被搜尋

  BikeStation({
    required this.stationId,
    required this.name,
    required this.address,
    required this.lat,
    required this.lng,
    required this.totalSlots,
    required this.availableBikes,
    required this.emptySlots,
    required this.updateTime,
    this.distance,
  });

  /// 計算站點狀態
  BikeStatus get status {
    if (availableBikes == 0) return BikeStatus.empty;
    if (availableBikes < 5) return BikeStatus.few;
    if (availableBikes < 10) return BikeStatus.limited;
    return BikeStatus.available;
  }

  /// 取得狀態顏色
  Color get statusColor {
    switch (status) {
      case BikeStatus.available:
        return const Color(0xFF4CAF50); // 綠色
      case BikeStatus.limited:
        return const Color(0xFFFFC107); // 黃色
      case BikeStatus.few:
        return const Color(0xFFF44336); // 紅色
      case BikeStatus.empty:
        return const Color(0xFF9E9E9E); // 灰色
    }
  }

  /// 取得狀態文字
  String get statusText {
    switch (status) {
      case BikeStatus.available:
        return '充足';
      case BikeStatus.limited:
        return '中等';
      case BikeStatus.few:
        return '少量';
      case BikeStatus.empty:
        return '無車';
    }
  }

  /// 格式化距離顯示
  String get formattedDistance {
    if (distance == null) return '';
    if (distance! < 1) {
      return '${(distance! * 1000).toInt()}m';
    } else {
      return '${distance!.toStringAsFixed(1)}km';
    }
  }

  /// 複製並更新距離
  BikeStation copyWithDistance(double? newDistance) {
    return BikeStation(
      stationId: stationId,
      name: name,
      address: address,
      lat: lat,
      lng: lng,
      totalSlots: totalSlots,
      availableBikes: availableBikes,
      emptySlots: emptySlots,
      updateTime: updateTime,
      distance: newDistance,
    );
  }

  /// 從 JSON 解析（支援後端 API 回傳格式）
  factory BikeStation.fromJson(Map<String, dynamic> json) {
    // 處理後端 API 回傳格式
    // 後端欄位: station_uid, station_id, name, latitude, longitude, capacity,
    //          available_rent_bikes, available_return_bikes, service_status
    return BikeStation(
      stationId: json['station_uid'] ?? json['station_id'] ?? '',
      name: json['name'] ?? '',
      address: json['address'] ?? '',
      lat: (json['latitude'] ?? json['lat'] ?? 0).toDouble(),
      lng: (json['longitude'] ?? json['lng'] ?? 0).toDouble(),
      totalSlots: json['capacity'] ?? json['total_slots'] ?? 0,
      availableBikes: json['available_rent_bikes'] ?? json['available_bikes'] ?? 0,
      emptySlots: json['available_return_bikes'] ?? json['empty_slots'] ?? 0,
      updateTime: DateTime.tryParse(json['availability_update_time'] ?? json['station_update_time'] ?? json['update_time'] ?? '') ?? DateTime.now(),
      distance: json['distance']?.toDouble(),
    );
  }

  /// 轉換為 JSON
  Map<String, dynamic> toJson() {
    return {
      'station_id': stationId,
      'name': name,
      'address': address,
      'lat': lat,
      'lng': lng,
      'total_slots': totalSlots,
      'available_bikes': availableBikes,
      'empty_slots': emptySlots,
      'update_time': updateTime.toIso8601String(),
      'distance': distance,
    };
  }

  /// 模擬資料 - 用於開發測試
  static List<BikeStation> get mockStations {
    return [
      BikeStation(
        stationId: '500101001',
        name: '市政府站',
        address: '臺北市信義區市府路1號',
        lat: 25.0412,
        lng: 121.5654,
        totalSlots: 30,
        availableBikes: 15,
        emptySlots: 15,
        updateTime: DateTime.now(),
        distance: 0.5,
      ),
      BikeStation(
        stationId: '500101002',
        name: '台北101/世貿站',
        address: '臺北市信義區信義路五段7號',
        lat: 25.0330,
        lng: 121.5654,
        totalSlots: 25,
        availableBikes: 8,
        emptySlots: 17,
        updateTime: DateTime.now(),
        distance: 0.8,
      ),
      BikeStation(
        stationId: '500101003',
        name: '國父紀念館站',
        address: '臺北市信義區仁愛路四段505號',
        lat: 25.0401,
        lng: 121.5600,
        totalSlots: 20,
        availableBikes: 2,
        emptySlots: 18,
        updateTime: DateTime.now(),
        distance: 1.2,
      ),
      BikeStation(
        stationId: '500101004',
        name: '大安森林公園站',
        address: '臺北市大安區新生南路二段1號',
        lat: 25.0325,
        lng: 121.5360,
        totalSlots: 35,
        availableBikes: 0,
        emptySlots: 35,
        updateTime: DateTime.now(),
        distance: 2.1,
      ),
      BikeStation(
        stationId: '500101005',
        name: '捷運忠孝復興站',
        address: '臺北市大安區忠孝東路三段',
        lat: 25.0416,
        lng: 121.5440,
        totalSlots: 28,
        availableBikes: 12,
        emptySlots: 16,
        updateTime: DateTime.now(),
        distance: 0.6,
      ),
      BikeStation(
        stationId: '500101006',
        name: '捷運忠孝敦化站',
        address: '臺北市大安區忠孝東路四段',
        lat: 25.0415,
        lng: 121.5510,
        totalSlots: 22,
        availableBikes: 18,
        emptySlots: 4,
        updateTime: DateTime.now(),
        distance: 0.3,
      ),
      BikeStation(
        stationId: '500101007',
        name: '華山文創園區',
        address: '臺北市中正區八德路一段1號',
        lat: 25.0440,
        lng: 121.5290,
        totalSlots: 40,
        availableBikes: 25,
        emptySlots: 15,
        updateTime: DateTime.now(),
        distance: 1.5,
      ),
      BikeStation(
        stationId: '500101008',
        name: '捷運西門站',
        address: '臺北市萬華區西門路',
        lat: 25.0420,
        lng: 121.5080,
        totalSlots: 32,
        availableBikes: 6,
        emptySlots: 26,
        updateTime: DateTime.now(),
        distance: 2.5,
      ),
    ];
  }
}
