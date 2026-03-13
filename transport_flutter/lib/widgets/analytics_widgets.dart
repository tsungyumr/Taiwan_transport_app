import 'package:flutter/material.dart';
import '../services/firebase_service.dart';

/// 自動追蹤 Analytics 頁面瀏覽的 Mixin
/// 使用方式：
/// ```dart
/// class MyScreen extends StatefulWidget with AnalyticsScreenTracking {
///   @override
///   String get screenName => 'MyScreen';
///   // ...
/// }
/// ```
mixin AnalyticsScreenTracking<T extends StatefulWidget> on State<T> {
  /// 頁面名稱，用於 Analytics 追蹤
  String get screenName;

  /// 頁面類別（可選）
  String? get screenClass => null;

  DateTime? _screenEnterTime;

  @override
  void initState() {
    super.initState();
    _screenEnterTime = DateTime.now();
    // 頁面初始化時追蹤頁面瀏覽
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _trackScreenView();
    });
  }

  @override
  void dispose() {
    // 追蹤頁面停留時間
    if (_screenEnterTime != null) {
      final duration = DateTime.now().difference(_screenEnterTime!);
      firebaseService.logEvent(
        eventName: 'screen_time',
        parameters: {
          'screen_name': screenName,
          'duration_seconds': duration.inSeconds,
        },
      );
    }
    super.dispose();
  }

  void _trackScreenView() {
    firebaseService.setCurrentScreen(
      screenName: screenName,
      screenClass: screenClass ?? screenName,
    );
    // 同時記錄頁面瀏覽事件
    firebaseService.logEvent(
      eventName: 'screen_view',
      parameters: {
        'screen_name': screenName,
        'screen_class': screenClass ?? screenName,
      },
    );
  }
}

/// 自動追蹤頁面瀏覽的 StatefulWidget 基類
abstract class AnalyticsTrackedScreen extends StatefulWidget {
  final String screenName;
  final String? screenClass;

  const AnalyticsTrackedScreen({
    super.key,
    required this.screenName,
    this.screenClass,
  });
}

/// AnalyticsTrackedScreen 的基礎 State 類別
abstract class AnalyticsTrackedScreenState<T extends AnalyticsTrackedScreen>
    extends State<T> with AnalyticsScreenTracking {
  @override
  String get screenName => widget.screenName;

  @override
  String? get screenClass => widget.screenClass;
}

/// 帶有 Analytics 追蹤的 TabBar
class AnalyticsTabBar extends StatelessWidget {
  final TabController controller;
  final List<String> tabNames;
  final List<Widget> tabs;
  final Color? indicatorColor;
  final Color? labelColor;
  final Color? unselectedLabelColor;

  const AnalyticsTabBar({
    super.key,
    required this.controller,
    required this.tabNames,
    required this.tabs,
    this.indicatorColor,
    this.labelColor,
    this.unselectedLabelColor,
  });

  @override
  Widget build(BuildContext context) {
    return TabBar(
      controller: controller,
      indicatorColor: indicatorColor,
      labelColor: labelColor,
      unselectedLabelColor: unselectedLabelColor,
      onTap: (index) {
        // 追蹤 tab 點擊
        firebaseService.logEvent(
          eventName: 'tab_click',
          parameters: {
            'tab_name': tabNames[index],
            'tab_index': index,
            'total_tabs': tabNames.length,
          },
        );
      },
      tabs: tabs,
    );
  }
}

/// 帶有 Analytics 追蹤的 TabBarView
class AnalyticsTabBarView extends StatefulWidget {
  final TabController controller;
  final List<String> tabNames;
  final List<Widget> children;

  const AnalyticsTabBarView({
    super.key,
    required this.controller,
    required this.tabNames,
    required this.children,
  });

  @override
  State<AnalyticsTabBarView> createState() => _AnalyticsTabBarViewState();
}

class _AnalyticsTabBarViewState extends State<AnalyticsTabBarView> {
  int _previousIndex = 0;
  DateTime? _tabEnterTime;

  @override
  void initState() {
    super.initState();
    _tabEnterTime = DateTime.now();
    widget.controller.addListener(_onTabChanged);
  }

  void _onTabChanged() {
    if (widget.controller.index != _previousIndex) {
      // 追蹤上一個 tab 的停留時間
      if (_tabEnterTime != null) {
        final duration = DateTime.now().difference(_tabEnterTime!);
        firebaseService.logEvent(
          eventName: 'tab_duration',
          parameters: {
            'tab_name': widget.tabNames[_previousIndex],
            'tab_index': _previousIndex,
            'duration_seconds': duration.inSeconds,
          },
        );
      }

      _previousIndex = widget.controller.index;
      _tabEnterTime = DateTime.now();

      // 追蹤 tab 切換
      firebaseService.logEvent(
        eventName: 'tab_switch',
        parameters: {
          'tab_name': widget.tabNames[widget.controller.index],
          'tab_index': widget.controller.index,
          'total_tabs': widget.tabNames.length,
        },
      );
    }
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onTabChanged);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return TabBarView(
      controller: widget.controller,
      children: widget.children,
    );
  }
}

/// 帶有 Analytics 追蹤的按鈕
class AnalyticsButton extends StatelessWidget {
  final String buttonId;
  final String buttonName;
  final String? category;
  final VoidCallback? onPressed;
  final Widget child;
  final ButtonStyle? style;

  const AnalyticsButton({
    super.key,
    required this.buttonId,
    required this.buttonName,
    this.category,
    required this.onPressed,
    required this.child,
    this.style,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      style: style,
      onPressed: () {
        // 追蹤按鈕點擊
        firebaseService.logEvent(
          eventName: 'button_click',
          parameters: {
            'button_id': buttonId,
            'button_name': buttonName,
            'category': category ?? 'general',
          },
        );
        onPressed?.call();
      },
      child: child,
    );
  }
}

/// 帶有 Analytics 追蹤的 IconButton
class AnalyticsIconButton extends StatelessWidget {
  final String buttonId;
  final String buttonName;
  final String? category;
  final VoidCallback? onPressed;
  final Widget icon;

  const AnalyticsIconButton({
    super.key,
    required this.buttonId,
    required this.buttonName,
    this.category,
    required this.onPressed,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return IconButton(
      onPressed: () {
        firebaseService.logEvent(
          eventName: 'icon_button_click',
          parameters: {
            'button_id': buttonId,
            'button_name': buttonName,
            'category': category ?? 'general',
          },
        );
        onPressed?.call();
      },
      icon: icon,
    );
  }
}

/// 帶有 Analytics 追蹤的 ListTile
class AnalyticsListTile extends StatelessWidget {
  final String tileId;
  final String tileName;
  final String? category;
  final VoidCallback? onTap;
  final Widget? leading;
  final Widget? title;
  final Widget? subtitle;
  final Widget? trailing;

  const AnalyticsListTile({
    super.key,
    required this.tileId,
    required this.tileName,
    this.category,
    this.onTap,
    this.leading,
    this.title,
    this.subtitle,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: leading,
      title: title,
      subtitle: subtitle,
      trailing: trailing,
      onTap: () {
        firebaseService.logEvent(
          eventName: 'list_tile_tap',
          parameters: {
            'tile_id': tileId,
            'tile_name': tileName,
            'category': category ?? 'general',
          },
        );
        onTap?.call();
      },
    );
  }
}

/// 帶有 Analytics 追蹤的 InkWell
class AnalyticsInkWell extends StatelessWidget {
  final String actionId;
  final String actionName;
  final String? category;
  final VoidCallback? onTap;
  final Widget child;

  const AnalyticsInkWell({
    super.key,
    required this.actionId,
    required this.actionName,
    this.category,
    required this.onTap,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () {
        firebaseService.logEvent(
          eventName: 'tap_action',
          parameters: {
            'action_id': actionId,
            'action_name': actionName,
            'category': category ?? 'general',
          },
        );
        onTap?.call();
      },
      child: child,
    );
  }
}

/// 帶有 Analytics 追蹤的文字輸入框
class AnalyticsTextField extends StatefulWidget {
  final String fieldId;
  final String fieldName;
  final TextEditingController? controller;
  final String? hintText;
  final ValueChanged<String>? onSubmitted;
  final ValueChanged<String>? onChanged;

  const AnalyticsTextField({
    super.key,
    required this.fieldId,
    required this.fieldName,
    this.controller,
    this.hintText,
    this.onSubmitted,
    this.onChanged,
  });

  @override
  State<AnalyticsTextField> createState() => _AnalyticsTextFieldState();
}

class _AnalyticsTextFieldState extends State<AnalyticsTextField> {
  DateTime? _focusTime;

  @override
  Widget build(BuildContext context) {
    return Focus(
      onFocusChange: (hasFocus) {
        if (hasFocus) {
          _focusTime = DateTime.now();
          firebaseService.logEvent(
            eventName: 'text_field_focus',
            parameters: {
              'field_id': widget.fieldId,
              'field_name': widget.fieldName,
            },
          );
        } else {
          if (_focusTime != null) {
            final duration = DateTime.now().difference(_focusTime!);
            firebaseService.logEvent(
              eventName: 'text_field_interaction',
              parameters: {
                'field_id': widget.fieldId,
                'field_name': widget.fieldName,
                'duration_seconds': duration.inSeconds,
              },
            );
          }
        }
      },
      child: TextField(
        controller: widget.controller,
        decoration: InputDecoration(
          hintText: widget.hintText,
        ),
        onChanged: widget.onChanged,
        onSubmitted: (value) {
          if (value.isNotEmpty) {
            firebaseService.logEvent(
              eventName: 'search_submit',
              parameters: {
                'field_id': widget.fieldId,
                'field_name': widget.fieldName,
                'query_length': value.length,
              },
            );
          }
          widget.onSubmitted?.call(value);
        },
      ),
    );
  }
}

/// 功能使用追蹤工具類別
class FeatureAnalytics {
  /// 追蹤功能使用
  static void trackFeatureUse({
    required String featureName,
    required String featureType,
    Map<String, dynamic>? parameters,
  }) {
    final baseParams = {
      'feature_name': featureName,
      'feature_type': featureType,
    };

    if (parameters != null) {
      baseParams.addAll(parameters.map((key, value) =>
        MapEntry(key, value.toString())));
    }

    firebaseService.logEvent(
      eventName: 'feature_use',
      parameters: baseParams,
    );
  }

  /// 追蹤搜尋功能
  static void trackSearch({
    required String searchType,
    required String query,
    int? resultCount,
  }) {
    firebaseService.logEvent(
      eventName: 'search',
      parameters: {
        'search_type': searchType,
        'query_length': query.length,
        'has_results': resultCount != null && resultCount > 0,
        if (resultCount != null) 'result_count': resultCount,
      },
    );
  }

  /// 追蹤篩選功能
  static void trackFilter({
    required String filterType,
    required String filterValue,
  }) {
    firebaseService.logEvent(
      eventName: 'filter_use',
      parameters: {
        'filter_type': filterType,
        'filter_value': filterValue,
      },
    );
  }

  /// 追蹤分享功能
  static void trackShare({
    required String contentType,
    required String contentId,
    String? method,
  }) {
    firebaseService.logEvent(
      eventName: 'share',
      parameters: {
        'content_type': contentType,
        'content_id': contentId,
        'method': method ?? 'unknown',
      },
    );
  }

  /// 追蹤導航功能
  static void trackNavigation({
    required String fromScreen,
    required String toScreen,
    String? navigationType,
  }) {
    firebaseService.logEvent(
      eventName: 'navigation',
      parameters: {
        'from_screen': fromScreen,
        'to_screen': toScreen,
        'navigation_type': navigationType ?? 'tap',
      },
    );
  }

  /// 追蹤錯誤
  static void trackError({
    required String errorType,
    required String errorMessage,
    String? screenName,
  }) {
    firebaseService.logEvent(
      eventName: 'app_error',
      parameters: {
        'error_type': errorType,
        'error_message': errorMessage,
        if (screenName != null) 'screen_name': screenName,
      },
    );
  }
}

/// 使用者屬性設定工具類別
class UserAnalytics {
  /// 設定使用者偏好語言
  static Future<void> setLanguage(String languageCode) async {
    await firebaseService.setUserProperty(
      name: 'preferred_language',
      value: languageCode,
    );
  }

  /// 設定常用交通方式
  static Future<void> setPreferredTransport(String transportType) async {
    await firebaseService.setUserProperty(
      name: 'preferred_transport',
      value: transportType,
    );
  }

  /// 設定使用者地區
  static Future<void> setUserRegion(String region) async {
    await firebaseService.setUserProperty(
      name: 'user_region',
      value: region,
    );
  }
}
