import 'dart:async';
import 'dart:developer';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../firebase_options.dart';

/// Firebase 服務類別
/// 負責初始化 Firebase 並提供 Crashlytics 和 Analytics 功能
class FirebaseService {
  static final FirebaseService _instance = FirebaseService._internal();
  static FirebaseService get instance => _instance;

  FirebaseAnalytics? _analytics;
  FirebaseCrashlytics? _crashlytics;

  bool _initialized = false;
  bool get isInitialized => _initialized;

  FirebaseService._internal();

  /// 初始化 Firebase
  /// 在 main() 函數中呼叫，需要在 runApp() 之前
  Future<void> initialize() async {
    if (_initialized) return;

    try {
      // 初始化 Firebase Core，使用平台特定的設定
      await Firebase.initializeApp(
        options: DefaultFirebaseOptions.currentPlatform,
      );

      _analytics = FirebaseAnalytics.instance;
      _crashlytics = FirebaseCrashlytics.instance;

      // 設定 Crashlytics
      await _setupCrashlytics();

      _initialized = true;
      log('Firebase 初始化成功', name: 'FirebaseService');
    } catch (e, stack) {
      log('Firebase 初始化失敗: $e', name: 'FirebaseService', error: e, stackTrace: stack);
      // 初始化失敗不應該阻止應用啟動
    }
  }

  /// 設定 Crashlytics
  Future<void> _setupCrashlytics() async {
    if (_crashlytics == null) return;

    // 在正式環境中啟用自動錯誤收集
    await _crashlytics!.setCrashlyticsCollectionEnabled(!kDebugMode);

    // 設定 Flutter 框架錯誤處理器
    FlutterError.onError = (errorDetails) {
      // 將 Flutter 錯誤記錄到 Crashlytics
      _crashlytics?.recordFlutterFatalError(errorDetails);
    };

    // 處理非同步錯誤
    PlatformDispatcher.instance.onError = (error, stack) {
      _crashlytics?.recordError(error, stack, fatal: true);
      return true;
    };

    log('Crashlytics 設定完成', name: 'FirebaseService');
  }

  /// 記錄自訂錯誤到 Crashlytics
  /// [error] - 錯誤物件
  /// [stack] - 堆疊追蹤
  /// [reason] - 錯誤原因說明
  /// [fatal] - 是否為致命錯誤
  Future<void> recordError(
    dynamic error,
    StackTrace? stack, {
    String? reason,
    bool fatal = false,
  }) async {
    if (_crashlytics == null || !_initialized) return;

    try {
      await _crashlytics!.recordError(
        error,
        stack,
        reason: reason,
        fatal: fatal,
      );
    } catch (e) {
      log('記錄錯誤失敗: $e', name: 'FirebaseService');
    }
  }

  /// 設定使用者識別碼
  /// 用於在 Crashlytics 中識別特定使用者的錯誤
  Future<void> setUserIdentifier(String userId) async {
    if (_crashlytics == null || !_initialized) return;

    try {
      await _crashlytics!.setUserIdentifier(userId);
    } catch (e) {
      log('設定使用者識別碼失敗: $e', name: 'FirebaseService');
    }
  }

  /// 設定自訂鍵值對到 Crashlytics
  /// 這些資料會隨著錯誤報告一起發送
  Future<void> setCustomKey(String key, String value) async {
    if (_crashlytics == null || !_initialized) return;

    try {
      await _crashlytics!.setCustomKey(key, value);
    } catch (e) {
      log('設定自訂鍵值失敗: $e', name: 'FirebaseService');
    }
  }

  /// 記錄自訂訊息到 Crashlytics
  Future<void> logMessage(String message) async {
    if (_crashlytics == null || !_initialized) return;

    try {
      await _crashlytics!.log(message);
    } catch (e) {
      log('記錄訊息失敗: $e', name: 'FirebaseService');
    }
  }

  /// 追蹤 Analytics 事件
  /// [eventName] - 事件名稱（必須符合 Firebase 命名規則）
  /// [parameters] - 事件參數（可選）
  Future<void> logEvent({
    required String eventName,
    Map<String, Object>? parameters,
  }) async {
    if (_analytics == null || !_initialized) return;

    try {
      await _analytics!.logEvent(
        name: eventName,
        parameters: parameters,
      );
    } catch (e) {
      log('追蹤事件失敗: $e', name: 'FirebaseService');
    }
  }

  /// 設定目前頁面名稱（用於追蹤頁面瀏覽）
  Future<void> setCurrentScreen({
    required String screenName,
    String? screenClass,
  }) async {
    if (_analytics == null || !_initialized) return;

    try {
      await _analytics!.logScreenView(
        screenName: screenName,
        screenClass: screenClass,
      );
    } catch (e) {
      log('設定目前頁面失敗: $e', name: 'FirebaseService');
    }
  }

  /// 設定使用者屬性
  Future<void> setUserProperty({
    required String name,
    required String? value,
  }) async {
    if (_analytics == null || !_initialized) return;

    try {
      await _analytics!.setUserProperty(name: name, value: value);
    } catch (e) {
      log('設定使用者屬性失敗: $e', name: 'FirebaseService');
    }
  }

  /// 追蹤交通方式搜尋事件
  void logTransportSearch({
    required String transportType,
    required String fromStation,
    required String toStation,
  }) {
    logEvent(
      eventName: 'transport_search',
      parameters: {
        'transport_type': transportType,
        'from_station': fromStation,
        'to_station': toStation,
      },
    );
  }

  /// 追蹤路線查詢事件
  void logRouteQuery({
    required String routeName,
    required String city,
  }) {
    logEvent(
      eventName: 'route_query',
      parameters: {
        'route_name': routeName,
        'city': city,
      },
    );
  }

  /// 追蹤錯誤事件
  void logAppError({
    required String errorType,
    required String errorMessage,
  }) {
    logEvent(
      eventName: 'app_error',
      parameters: {
        'error_type': errorType,
        'error_message': errorMessage,
      },
    );
  }

  /// 測試崩潰（僅用於開發測試）
  /// 呼叫此函數會觸發一個測試崩潰
  void testCrash() {
    _crashlytics?.crash();
  }

  /// 測試非同步崩潰
  void testAsyncCrash() {
    _crashlytics?.log('Testing async crash');
    throw Exception('這是一個測試錯誤');
  }
}

/// 全域 FirebaseService 實例
final firebaseService = FirebaseService.instance;
