import 'package:json_annotation/json_annotation.dart';

part 'bus_route.g.dart';

@JsonSerializable()
class BusRoute {
  @JsonKey(name: 'route_id')
  final String routeId;
  @JsonKey(name: 'route_name')
  final String routeName;
  @JsonKey(name: 'departure_stop')
  final String departureStop;
  @JsonKey(name: 'arrival_stop')
  final String arrivalStop;
  @JsonKey(name: 'operator')
  final String operator;

  BusRoute({
    required this.routeId,
    required this.routeName,
    required this.departureStop,
    required this.arrivalStop,
    required this.operator,
  });

  factory BusRoute.fromJson(Map<String, dynamic> json) => _$BusRouteFromJson(json);
  Map<String, dynamic> toJson() => _$BusRouteToJson(this);
}

// 方向資訊模型
@JsonSerializable()
class DirectionInfo {
  @JsonKey(defaultValue: 0)
  final int direction; // 0=去程, 1=返程
  @JsonKey(name: 'direction_name', defaultValue: '去程')
  final String directionName; // "去程" 或 "返程"
  @JsonKey(defaultValue: '')
  final String departure; // 起點站
  @JsonKey(defaultValue: '')
  final String arrival; // 終點站
  // 雙向資訊供 Tab 顯示
  @JsonKey(defaultValue: null)
  final Map<String, dynamic>? go; // 去程資訊
  @JsonKey(defaultValue: null)
  final Map<String, dynamic>? back; // 返程資訊

  DirectionInfo({
    this.direction = 0,
    this.directionName = '去程',
    this.departure = '',
    this.arrival = '',
    this.go,
    this.back,
  });

  factory DirectionInfo.fromJson(Map<String, dynamic> json) => _$DirectionInfoFromJson(json);
  Map<String, dynamic> toJson() => _$DirectionInfoToJson(this);
}

@JsonSerializable()
class BusRouteData {
  final String route;
  @JsonKey(name: 'route_name', defaultValue: '')
  final String routeName;
  @JsonKey(fromJson: _directionFromJson)
  final DirectionInfo direction; // 方向資訊
  final List<BusStop> stops;
  final List<BusVehicle> buses;
  @JsonKey(fromJson: _parseDateTime, toJson: _dateTimeToJson)
  final DateTime? updated;

  BusRouteData({
    required this.route,
    this.routeName = '',
    required this.direction,
    required this.stops,
    required this.buses,
    this.updated,
  });

  factory BusRouteData.fromJson(Map<String, dynamic> json) => _$BusRouteDataFromJson(json);
  Map<String, dynamic> toJson() => _$BusRouteDataToJson(this);
}

// 處理 direction 可能為 null 的情況
DirectionInfo _directionFromJson(dynamic json) {
  if (json == null) {
    return DirectionInfo();
  }
  if (json is Map<String, dynamic>) {
    return DirectionInfo.fromJson(json);
  }
  return DirectionInfo();
}

DateTime? _parseDateTime(dynamic value) {
  if (value == null) return null;
  if (value is DateTime) return value;
  try {
    return DateTime.parse(value.toString());
  } catch (e) {
    return null;
  }
}

String? _dateTimeToJson(DateTime? value) {
  return value?.toIso8601String();
}

// 站點車輛資訊模型（顯示在特定站點的車輛）
@JsonSerializable()
class StopBusInfo {
  @JsonKey(name: 'plate_number', defaultValue: '')
  final String plateNumber; // 車牌號碼
  @JsonKey(name: 'bus_type', defaultValue: '')
  final String busType; // 車種
  @JsonKey(name: 'remaining_seats')
  final String? remainingSeats; // 剩餘座位數

  StopBusInfo({
    this.plateNumber = '',
    this.busType = '',
    this.remainingSeats,
  });

  factory StopBusInfo.fromJson(Map<String, dynamic> json) => _$StopBusInfoFromJson(json);
  Map<String, dynamic> toJson() => _$StopBusInfoToJson(this);
}

@JsonSerializable()
class BusStop {
  @JsonKey(defaultValue: 0)
  final int sequence; // 站序（從0開始）
  @JsonKey(defaultValue: '')
  final String name; // 站點名稱
  @JsonKey(defaultValue: '')
  final String eta; // 到站時間文字（如 "3 分鐘"、"進站中"、"未發車"）
  @JsonKey(defaultValue: 'normal')
  final String status; // 狀態代碼（not_started/arriving/near/normal）
  @JsonKey(defaultValue: [])
  final List<StopBusInfo> buses; // 在該站點的車輛列表
  @JsonKey(defaultValue: null)
  final double? latitude; // 緯度
  @JsonKey(defaultValue: null)
  final double? longitude; // 經度

  BusStop({
    this.sequence = 0,
    this.name = '',
    this.eta = '',
    this.status = 'normal',
    this.buses = const [],
    this.latitude,
    this.longitude,
  });

  factory BusStop.fromJson(Map<String, dynamic> json) => _$BusStopFromJson(json);
  Map<String, dynamic> toJson() => _$BusStopToJson(this);
}

@JsonSerializable()
class BusVehicle {
  @JsonKey(defaultValue: '')
  final String id; // 車輛唯一ID
  @JsonKey(name: 'plate_number', defaultValue: '')
  final String plateNumber; // 車牌號碼（如 EAL-3359）
  @JsonKey(name: 'bus_type', defaultValue: '')
  final String busType; // 車種（如 一般公車、低地板公車）
  @JsonKey(name: 'at_stop', defaultValue: 0)
  final int atStop; // 當前所在站點序號
  @JsonKey(name: 'eta_next', defaultValue: '')
  final String etaNext; // 到下一站時間
  @JsonKey(name: 'heading_to', defaultValue: 0)
  final int headingTo; // 正前往的站點序號
  @JsonKey(name: 'remaining_seats')
  final String? remainingSeats; // 剩餘座位數

  BusVehicle({
    this.id = '',
    this.plateNumber = '',
    this.busType = '',
    this.atStop = 0,
    this.etaNext = '',
    this.headingTo = 0,
    this.remainingSeats,
  });

  factory BusVehicle.fromJson(Map<String, dynamic> json) => _$BusVehicleFromJson(json);
  Map<String, dynamic> toJson() => _$BusVehicleToJson(this);
}
