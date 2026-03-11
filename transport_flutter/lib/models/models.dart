// 公車路線模型
class BusRoute {
  final String routeId;
  final String routeName;
  final String departureStop;
  final String arrivalStop;
  final String operator;

  BusRoute({
    required this.routeId,
    required this.routeName,
    required this.departureStop,
    required this.arrivalStop,
    required this.operator,
  });

  factory BusRoute.fromJson(Map<String, dynamic> json) {
    return BusRoute(
      routeId: json['route_id'] ?? '',
      routeName: json['route_name'] ?? '',
      departureStop: json['departure_stop'] ?? '',
      arrivalStop: json['arrival_stop'] ?? '',
      operator: json['operator'] ?? '',
    );
  }
}

// 公車時刻表項目
class BusTimeEntry {
  final String stopName;
  final String arrivalTime;
  final String routeName;

  BusTimeEntry({
    required this.stopName,
    required this.arrivalTime,
    required this.routeName,
  });

  factory BusTimeEntry.fromJson(Map<String, dynamic> json) {
    return BusTimeEntry(
      stopName: json['stop_name'] ?? '',
      arrivalTime: json['arrival_time'] ?? '',
      routeName: json['route_name'] ?? '',
    );
  }
}

// 火車站模型
class TrainStation {
  final String stationCode;
  final String stationName;
  final String stationNameEn;
  final double? latitude;
  final double? longitude;
  final String? city;

  TrainStation({
    required this.stationCode,
    required this.stationName,
    required this.stationNameEn,
    this.latitude,
    this.longitude,
    this.city,
  });

  factory TrainStation.fromJson(Map<String, dynamic> json) {
    return TrainStation(
      stationCode: json['station_code'] ?? json['code'] ?? '',
      stationName: json['station_name'] ?? json['name'] ?? '',
      stationNameEn: json['station_name_en'] ?? json['name'] ?? '',
      latitude: json['latitude'] != null ? (json['latitude'] as num).toDouble() : null,
      longitude: json['longitude'] != null ? (json['longitude'] as num).toDouble() : null,
      city: json['city'] as String?,
    );
  }

  // 取得座標顯示文字
  String get coordinatesText {
    if (latitude != null && longitude != null) {
      return '(${latitude!.toStringAsFixed(4)}, ${longitude!.toStringAsFixed(4)})';
    }
    return '';
  }
}

// 台鐵時刻表項目
class TrainTimeEntry {
  final String trainNo;
  final String trainType;
  final String departureStation;
  final String arrivalStation;
  final String departureTime;
  final String arrivalTime;
  final String duration;
  final bool transferable;

  TrainTimeEntry({
    required this.trainNo,
    required this.trainType,
    required this.departureStation,
    required this.arrivalStation,
    required this.departureTime,
    required this.arrivalTime,
    required this.duration,
    required this.transferable,
  });

  factory TrainTimeEntry.fromJson(Map<String, dynamic> json) {
    return TrainTimeEntry(
      trainNo: json['train_no'] ?? '',
      trainType: json['train_type'] ?? '',
      departureStation: json['departure_station'] ?? '',
      arrivalStation: json['arrival_station'] ?? '',
      departureTime: json['departure_time'] ?? '',
      arrivalTime: json['arrival_time'] ?? '',
      duration: json['duration'] ?? '',
      transferable: json['transferable'] ?? true,
    );
  }
}

// 高鐵時刻表項目
class THSRTrainEntry {
  final String trainNo;
  final String departureStation;
  final String arrivalStation;
  final String departureTime;
  final String arrivalTime;
  final String duration;
  final bool businessSeatAvailable;
  final bool standardSeatAvailable;
  final bool freeSeatAvailable;

  THSRTrainEntry({
    required this.trainNo,
    required this.departureStation,
    required this.arrivalStation,
    required this.departureTime,
    required this.arrivalTime,
    required this.duration,
    required this.businessSeatAvailable,
    required this.standardSeatAvailable,
    required this.freeSeatAvailable,
  });

  factory THSRTrainEntry.fromJson(Map<String, dynamic> json) {
    return THSRTrainEntry(
      trainNo: json['train_no'] ?? '',
      departureStation: json['departure_station'] ?? '',
      arrivalStation: json['arrival_station'] ?? '',
      departureTime: json['departure_time'] ?? '',
      arrivalTime: json['arrival_time'] ?? '',
      duration: json['duration'] ?? '',
      businessSeatAvailable: json['business_seat_available'] ?? false,
      standardSeatAvailable: json['standard_seat_available'] ?? false,
      freeSeatAvailable: json['free_seat_available'] ?? false,
    );
  }
}
