import 'package:flutter/material.dart';
import 'package:motion_tab_bar/MotionTabBar.dart';
import 'package:motion_tab_bar/MotionTabBarController.dart';
import 'package:flutter_speed_dial/flutter_speed_dial.dart';
import '../main.dart';
import '../l10n/app_localizations.dart';
import '../widgets/animated_card.dart';
import '../widgets/loading_animations.dart';
import '../widgets/ai_plan_dialog.dart';
import '../widgets/ai_result_bubble.dart';
import '../widgets/analytics_widgets.dart';
import '../services/gemini_webview_service.dart';
import '../services/ai_planning_service.dart';
import '../ui_theme.dart';
import 'bus_screen.dart';
import 'railway_screen.dart';
import 'thsr_screen.dart';
import 'bike_screen.dart';
import 'settings_screen.dart';

// 公車 Tab 內容 - 顯示大台北公車入口卡片
class BusTabContent extends StatelessWidget {
  const BusTabContent({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 20),
            // 交通工具選擇卡片
            FadeInAnimation(
              delay: const Duration(milliseconds: 100),
              child: TransportCard(
                title: l10n.busTitle,
                subtitle: l10n.busSubtitle,
                icon: Icons.directions_bus,
                color: TransportColors.bus,
                onTap: () => Navigator.push(
                  context,
                  SlidePageRoute(builder: (_) => const BusScreen()),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class MainTabScreen extends StatefulWidget {
  const MainTabScreen({super.key});

  @override
  State<MainTabScreen> createState() => _MainTabScreenState();
}

class _MainTabScreenState extends State<MainTabScreen>
    with TickerProviderStateMixin {
  MotionTabBarController? _motionTabBarController;

  // Gemini WebView 服務
  final GeminiWebViewService _geminiService = GeminiWebViewService();
  // AI 規劃服務
  final AIPlanningService _aiPlanningService = AIPlanningService();
  bool _isPlanning = false;

  // 緩存上次 AI 規劃結果
  String? _cachedAIResult;
  String? _cachedFromLocation;
  String? _cachedToLocation;

  // 定義每個 tab 的主題色 - 使用黃色系內的協調色
  final List<Color> _tabColors = [
    TransportColors.bus, // 公車：草綠色（與黃色協調）
    TransportColors.railway, // 火車：暖橘色（與黃色協調）
    TransportColors.thsr, // 高鐵：珊瑚橘（與黃色協調）
    const Color(0xFF2E7D32), // 腳踏車：環保綠色
  ];

  @override
  void initState() {
    super.initState();
    _motionTabBarController = MotionTabBarController(
      initialIndex: 0,
      length: 4,
      vsync: this,
    );
  }

  @override
  void dispose() {
    _motionTabBarController?.dispose();
    _geminiService.dispose();
    super.dispose();
  }

  // 切換到指定 tab 的方法，供子元件呼叫
  void switchToTab(int index) {
    if (index >= 0 && index < 4) {
      setState(() {
        _motionTabBarController!.index = index;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    // 根據當前選中的 tab 決定主題色
    final selectedColor = _tabColors[_motionTabBarController?.index ?? 0];

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.appTitle),
        centerTitle: true,
        backgroundColor: selectedColor,
        foregroundColor: Colors.white,
        elevation: 0,
        // 添加漸層效果
        flexibleSpace: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                selectedColor,
                selectedColor.withOpacity(0.8),
              ],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
        ),
        actions: [
          // 設定按鈕
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: l10n.commonSettings,
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const SettingsScreen(),
                ),
              );
            },
          ),
        ],
      ),
      bottomNavigationBar: Container(
        key: ValueKey(
            'motion_tab_bar_${Localizations.localeOf(context).languageCode}'),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 8,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: MotionTabBar(
          controller: _motionTabBarController,
          initialSelectedTab: l10n.tabBus,
          useSafeArea: true,
          labels: [l10n.tabBus, l10n.tabRailway, l10n.tabThsr, l10n.tabBike],
          icons: const [
            Icons.directions_bus,
            Icons.train,
            Icons.speed,
            Icons.directions_bike,
          ],
          badges: const [null, null, null, null],
          tabSize: 50,
          tabBarHeight: 60,
          textStyle: const TextStyle(
            fontSize: 12,
            color: Colors.black87,
            fontWeight: FontWeight.w600,
          ),
          tabIconColor: Colors.grey[600],
          tabIconSize: 28.0,
          tabIconSelectedSize: 26.0,
          tabSelectedColor: selectedColor,
          tabIconSelectedColor: Colors.white,
          tabBarColor: Colors.white,
          onTabItemSelected: (int value) {
            // 追蹤 Tab 切換
            final tabNames = [l10n.tabBus, l10n.tabRailway, l10n.tabThsr, l10n.tabBike];
            FeatureAnalytics.trackFeatureUse(
              featureName: 'tab_switch',
              featureType: 'navigation',
              parameters: {
                'tab_name': tabNames[value],
                'tab_index': value,
              },
            );

            setState(() {
              _motionTabBarController!.index = value;
            });
          },
        ),
      ),
      body: TabBarView(
        controller: _motionTabBarController,
        physics: const NeverScrollableScrollPhysics(), // 禁用滑動切換，避免與列表衝突
        children: [
          // 公車 tab 內容
          const BusTabContent(),
          // 火車 tab 內容 - 傳入目前選中的 tab 索引
          RailwayTabView(
            isActive: _motionTabBarController?.index == 1,
          ),
          // 高鐵 tab 內容 - 傳入目前選中的 tab 索引
          THSRTabView(
            isActive: _motionTabBarController?.index == 2,
          ),
          // 腳踏車 tab 內容
          const BikeTabView(),
        ],
      ),
      // 全局浮動操作按鈕選單
      floatingActionButton: _buildSpeedDial(),
    );
  }

  // 建立 SpeedDial 浮動選單
  Widget _buildSpeedDial() {
    final l10n = AppLocalizations.of(context)!;

    return Container(
        margin: const EdgeInsets.only(bottom: 14),
        child: SpeedDial(
          // Hero tag 避免衝突
          heroTag: 'mainSpeedDial',
          // 主按圖標
          icon: Icons.menu,
          activeIcon: Icons.close,
          // 使用黃色主題色
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          activeBackgroundColor: AppColors.primaryDark,
          activeForegroundColor: Colors.white,
          // 動畫設定
          animationDuration: AppAnimations.normal,
          animationCurve: AppAnimations.curve,
          // 展開方向
          direction: SpeedDialDirection.up,
          // 遮罩效果
          renderOverlay: true,
          overlayColor: Colors.black,
          overlayOpacity: 0.5,
          // 是否可見
          visible: true,
          // 關閉選單時的行為
          closeManually: false,
          // 子選單項目
          children: [
            // AI最佳搭乘規劃
            SpeedDialChild(
              child: const Icon(Icons.auto_fix_high, color: Colors.white),
              backgroundColor: AppColors.railway,
              label: l10n.aiPlanTitle,
              labelStyle: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
              labelBackgroundColor: Colors.white,
              onTap: () => _onAIFeatureTap(),
            ),
            // 遊戲空間
            SpeedDialChild(
              child: const Icon(Icons.sports_esports, color: Colors.white),
              backgroundColor: AppColors.secondary,
              label: l10n.gameSpaceTitle,
              labelStyle: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
              labelBackgroundColor: Colors.white,
              onTap: () => _onGameSpaceTap(),
            ),
          ],
        ));
  }

  // AI最佳搭乘規劃功能
  void _onAIFeatureTap() async {
    // 如果有緩存的結果，直接顯示上次結果
    if (_cachedAIResult != null &&
        _cachedFromLocation != null &&
        _cachedToLocation != null) {
      AIResultBubble.show(
        context,
        result: _cachedAIResult!,
        onRetry: () {
          // 清除緩存並重新顯示輸入對話框
          _clearAICacheAndShowDialog();
        },
      );
      return;
    }

    // 沒有緩存，顯示輸入對話框
    _showAIPlanDialog();
  }

  // 顯示 AI 規劃輸入對話框
  void _showAIPlanDialog() {
    AIPlanDialog.show(
      context,
      onSubmit: (fromLocation, toLocation) {
        _startAIPlanning(fromLocation, toLocation);
      },
    );
  }

  // 清除 AI 緩存並顯示輸入對話框（保留地點作為預設值，讓用戶可以修改後重新規劃）
  void _clearAICacheAndShowDialog() {
    // 追蹤 AI 重新規劃
    FeatureAnalytics.trackFeatureUse(
      featureName: 'ai_plan_retry',
      featureType: 'ai',
    );

    // 先關閉當前的結果畫面
    Navigator.pop(context);

    // 只清除結果緩存，保留地點供對話框預設
    setState(() {
      _cachedAIResult = null;
    });

    // 顯示輸入對話框，傳入現有地點作為預設
    AIPlanDialog.show(
      context,
      initialFromLocation: _cachedFromLocation,
      initialToLocation: _cachedToLocation,
      onSubmit: (newFromLocation, newToLocation) {
        _startAIPlanning(newFromLocation, newToLocation);
      },
    );
  }

  // 開始 AI 規劃
  Future<void> _startAIPlanning(String fromLocation, String toLocation) async {
    final l10n = AppLocalizations.of(context)!;
    // 取得當前語言設定
    final currentLocale = Localizations.localeOf(context);
    final languageCode = currentLocale.languageCode; // 'zh' 或 'en'

    if (_isPlanning) return;

    // 追蹤 AI 規劃開始
    FeatureAnalytics.trackFeatureUse(
      featureName: 'ai_plan_start',
      featureType: 'ai',
      parameters: {
        'language': languageCode,
      },
    );

    setState(() {
      _isPlanning = true;
    });

    // 保存查詢地點
    _cachedFromLocation = fromLocation;
    _cachedToLocation = toLocation;

    // 顯示載入中的氣泡
    AIResultBubble.showLoading(context, message: l10n.aiPlanAnalyzing);

    try {
      // 使用 AI 規劃服務執行完整流程
      // 1. 取得附近站點 2. 生成 Prompt 3. 發送到 Gemini
      final response = await _aiPlanningService.performAIPlanning(
        fromLocation: fromLocation,
        toLocation: toLocation,
        language: languageCode,
        context: context, // 傳遞 context 參數，讓 WebView 可以在需要時顯示登入介面
      );

      // 緩存結果
      _cachedAIResult = response;

      // 追蹤 AI 規劃成功
      FeatureAnalytics.trackFeatureUse(
        featureName: 'ai_plan_complete',
        featureType: 'ai',
        parameters: {
          'language': languageCode,
        },
      );

      // 關閉載入對話框
      if (mounted) {
        Navigator.pop(context);

        // 顯示結果
        AIResultBubble.show(
          context,
          result: response,
          onRetry: () {
            // 清除緩存並重新顯示輸入對話框
            _clearAICacheAndShowDialog();
          },
        );
      }
    } catch (e) {
      // 清除緩存（因為規劃失敗）
      _cachedAIResult = null;

      // 追蹤 AI 規劃失敗
      FeatureAnalytics.trackFeatureUse(
        featureName: 'ai_plan_failed',
        featureType: 'ai',
        parameters: {
          'error_type': e.toString(),
          'language': languageCode,
        },
      );

      // 關閉載入對話框
      if (mounted) {
        Navigator.pop(context);

        // 顯示錯誤結果
        AIResultBubble.show(
          context,
          result: l10n.aiPlanErrorMessage(e.toString()),
          onRetry: () {
            // 清除緩存並重新顯示輸入對話框
            _clearAICacheAndShowDialog();
          },
        );
      }
    } finally {
      setState(() {
        _isPlanning = false;
      });
    }
  }

  // 遊戲空間功能
  void _onGameSpaceTap() {
    final l10n = AppLocalizations.of(context)!;

    // 追蹤遊戲空間點擊
    FeatureAnalytics.trackFeatureUse(
      featureName: 'game_space_click',
      featureType: 'game',
    );

    // 顯示即將推出的提示
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(l10n.gameSpaceComingSoon),
        duration: const Duration(seconds: 2),
        backgroundColor: AppColors.secondary,
        behavior: SnackBarBehavior.floating,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(AppRadius.medium)),
        ),
      ),
    );
  }
}

// 火車 Tab 視圖 - 直接使用 RailwayScreen 的內容（隱藏 AppBar）
class RailwayTabView extends StatelessWidget {
  final bool isActive;

  const RailwayTabView({
    super.key,
    required this.isActive,
  });

  @override
  Widget build(BuildContext context) {
    // 傳入 isActive 控制何時載入資料
    return RailwayScreen(
      showAppBar: false,
      isActive: isActive,
    );
  }
}

// 高鐵 Tab 視圖 - 直接使用 THSRScreen 的內容（隱藏 AppBar）
class THSRTabView extends StatelessWidget {
  final bool isActive;

  const THSRTabView({
    super.key,
    required this.isActive,
  });

  @override
  Widget build(BuildContext context) {
    // 使用 THSRScreen，隱藏其 AppBar，傳入 isActive
    return THSRScreen(
      showAppBar: false,
      isActive: isActive,
    );
  }
}

// 腳踏車 Tab 視圖 - 直接使用 BikeScreen 的內容（隱藏 AppBar）
class BikeTabView extends StatelessWidget {
  const BikeTabView({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    // 使用 BikeScreen，隱藏其 AppBar
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 20),
            // 交通工具選擇卡片
            FadeInAnimation(
              delay: const Duration(milliseconds: 100),
              child: TransportCard(
                title: l10n.bikeTitle,
                subtitle: l10n.bikeSubtitle,
                icon: Icons.directions_bike,
                color: TransportColors.bike,
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const BikeScreen(showAppBar: true),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
