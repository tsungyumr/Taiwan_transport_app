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

  @override
  void initState() {
    super.initState();
    // 頁面初始化時追蹤頁面瀏覽
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _trackScreenView();
    });
  }

  void _trackScreenView() {
    firebaseService.setCurrentScreen(
      screenName: screenName,
      screenClass: screenClass ?? screenName,
    );
  }
}

/// 自動追蹤頁面瀏覽的 StatefulWidget 基類
/// 子類只需要設定 [screenName] 屬性
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

/// 簡單的 Analytics 按鈕包裝器
/// 自動追蹤按鈕點擊事件
class AnalyticsButton extends StatelessWidget {
  final String buttonName;
  final VoidCallback? onPressed;
  final Widget child;
  final ButtonStyle? style;

  const AnalyticsButton({
    super.key,
    required this.buttonName,
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
          parameters: {'button_name': buttonName},
        );
        onPressed?.call();
      },
      child: child,
    );
  }
}

/// 帶有 Analytics 追蹤的 InkWell
class AnalyticsInkWell extends StatelessWidget {
  final String actionName;
  final VoidCallback? onTap;
  final Widget child;

  const AnalyticsInkWell({
    super.key,
    required this.actionName,
    required this.onTap,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () {
        firebaseService.logEvent(
          eventName: 'tap_action',
          parameters: {'action_name': actionName},
        );
        onTap?.call();
      },
      child: child,
    );
  }
}

/// 帶有 Analytics 追蹤的 ListTile
class AnalyticsListTile extends StatelessWidget {
  final String tileName;
  final VoidCallback? onTap;
  final Widget? leading;
  final Widget? title;
  final Widget? subtitle;
  final Widget? trailing;

  const AnalyticsListTile({
    super.key,
    required this.tileName,
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
          parameters: {'tile_name': tileName},
        );
        onTap?.call();
      },
    );
  }
}

/// 帶有 Analytics 追蹤的 TabBarView
/// 自動追蹤分頁切換
class AnalyticsTabController extends StatefulWidget {
  final int length;
  final List<String> tabNames;
  final List<Widget> tabs;
  final List<Widget> tabViews;
  final TabController? controller;

  const AnalyticsTabController({
    super.key,
    required this.length,
    required this.tabNames,
    required this.tabs,
    required this.tabViews,
    this.controller,
  });

  @override
  State<AnalyticsTabController> createState() => _AnalyticsTabControllerState();
}

class _AnalyticsTabControllerState extends State<AnalyticsTabController>
    with TickerProviderStateMixin {
  late TabController _tabController;
  int _previousIndex = 0;

  @override
  void initState() {
    super.initState();
    _tabController = widget.controller ??
        TabController(length: widget.length, vsync: this);
    _tabController.addListener(_onTabChanged);
  }

  void _onTabChanged() {
    if (_tabController.index != _previousIndex) {
      _previousIndex = _tabController.index;
      final tabName = widget.tabNames[_tabController.index];
      firebaseService.logEvent(
        eventName: 'tab_switch',
        parameters: {
          'tab_name': tabName,
          'tab_index': _tabController.index,
        },
      );
    }
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    if (widget.controller == null) {
      _tabController.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        TabBar(
          controller: _tabController,
          tabs: widget.tabs,
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: widget.tabViews,
          ),
        ),
      ],
    );
  }
}

/// 使用範例：
/// ```dart
/// class MyScreen extends StatefulWidget with AnalyticsScreenTracking {
///   const MyScreen({super.key});
///
///   @override
///   String get screenName => 'MyScreen';
///
///   @override
///   State<MyScreen> createState() => _MyScreenState();
/// }
///
/// class _MyScreenState extends State<MyScreen> {
///   @override
///   Widget build(BuildContext context) {
///     return Scaffold(
///       appBar: AppBar(title: const Text('我的頁面')),
///       body: Column(
///         children: [
///           AnalyticsButton(
///             buttonName: 'search_button',
///             onPressed: () {
///               // 執行搜尋
///             },
///             child: const Text('搜尋'),
///           ),
///           AnalyticsListTile(
///             tileName: 'settings_tile',
///             title: const Text('設定'),
///             onTap: () {
///               // 開啟設定頁面
///             },
///           ),
///         ],
///       ),
///     );
///   }
/// }
/// ```
