// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'bus_route.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BusRoute _$BusRouteFromJson(Map<String, dynamic> json) => BusRoute(
      routeId: json['route_id'] as String,
      routeName: json['route_name'] as String,
      departureStop: json['departure_stop'] as String,
      arrivalStop: json['arrival_stop'] as String,
      operator: json['operator'] as String,
    );

Map<String, dynamic> _$BusRouteToJson(BusRoute instance) => <String, dynamic>{
      'route_id': instance.routeId,
      'route_name': instance.routeName,
      'departure_stop': instance.departureStop,
      'arrival_stop': instance.arrivalStop,
      'operator': instance.operator,
    };

DirectionInfo _$DirectionInfoFromJson(Map<String, dynamic> json) =>
    DirectionInfo(
      direction: (json['direction'] as num?)?.toInt() ?? 0,
      directionName: json['direction_name'] as String? ?? '去程',
      departure: json['departure'] as String? ?? '',
      arrival: json['arrival'] as String? ?? '',
      go: json['go'] as Map<String, dynamic>?,
      back: json['back'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$DirectionInfoToJson(DirectionInfo instance) =>
    <String, dynamic>{
      'direction': instance.direction,
      'direction_name': instance.directionName,
      'departure': instance.departure,
      'arrival': instance.arrival,
      'go': instance.go,
      'back': instance.back,
    };

BusRouteData _$BusRouteDataFromJson(Map<String, dynamic> json) => BusRouteData(
      route: json['route'] as String,
      routeName: json['route_name'] as String? ?? '',
      direction: _directionFromJson(json['direction']),
      stops: (json['stops'] as List<dynamic>)
          .map((e) => BusStop.fromJson(e as Map<String, dynamic>))
          .toList(),
      buses: (json['buses'] as List<dynamic>)
          .map((e) => BusVehicle.fromJson(e as Map<String, dynamic>))
          .toList(),
      updated: _parseDateTime(json['updated']),
    );

Map<String, dynamic> _$BusRouteDataToJson(BusRouteData instance) =>
    <String, dynamic>{
      'route': instance.route,
      'route_name': instance.routeName,
      'direction': instance.direction,
      'stops': instance.stops,
      'buses': instance.buses,
      'updated': _dateTimeToJson(instance.updated),
    };

StopBusInfo _$StopBusInfoFromJson(Map<String, dynamic> json) => StopBusInfo(
      plateNumber: json['plate_number'] as String? ?? '',
      busType: json['bus_type'] as String? ?? '',
      remainingSeats: json['remaining_seats'] as String?,
    );

Map<String, dynamic> _$StopBusInfoToJson(StopBusInfo instance) =>
    <String, dynamic>{
      'plate_number': instance.plateNumber,
      'bus_type': instance.busType,
      'remaining_seats': instance.remainingSeats,
    };

BusStop _$BusStopFromJson(Map<String, dynamic> json) => BusStop(
      sequence: (json['sequence'] as num?)?.toInt() ?? 0,
      name: json['name'] as String? ?? '',
      eta: json['eta'] as String? ?? '',
      status: json['status'] as String? ?? 'normal',
      buses: (json['buses'] as List<dynamic>?)
              ?.map((e) => StopBusInfo.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$BusStopToJson(BusStop instance) => <String, dynamic>{
      'sequence': instance.sequence,
      'name': instance.name,
      'eta': instance.eta,
      'status': instance.status,
      'buses': instance.buses,
      'latitude': instance.latitude,
      'longitude': instance.longitude,
    };

BusVehicle _$BusVehicleFromJson(Map<String, dynamic> json) => BusVehicle(
      id: json['id'] as String? ?? '',
      plateNumber: json['plate_number'] as String? ?? '',
      busType: json['bus_type'] as String? ?? '',
      atStop: (json['at_stop'] as num?)?.toInt() ?? 0,
      etaNext: json['eta_next'] as String? ?? '',
      headingTo: (json['heading_to'] as num?)?.toInt() ?? 0,
      remainingSeats: json['remaining_seats'] as String?,
    );

Map<String, dynamic> _$BusVehicleToJson(BusVehicle instance) =>
    <String, dynamic>{
      'id': instance.id,
      'plate_number': instance.plateNumber,
      'bus_type': instance.busType,
      'at_stop': instance.atStop,
      'eta_next': instance.etaNext,
      'heading_to': instance.headingTo,
      'remaining_seats': instance.remainingSeats,
    };
