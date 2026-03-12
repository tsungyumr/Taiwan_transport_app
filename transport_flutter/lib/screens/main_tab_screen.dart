import 'package:flutter/material.dart';
import 'package:motion_tab_bar/MotionTabBar.dart';
import 'package:motion_tab_bar/MotionTabBarController.dart';
import 'package:flutter_speed_dial/flutter_speed_dial.dart';
import '../main.dart';
import '../widgets/animated_card.dart';
import '../widgets/loading_animations.dart';
import '../widgets/ai_plan_dialog.dart';
import '../widgets/ai_result_bubble.dart';
import '../services/gemini_webview_service.dart';
import '../services/ai_planning_service.dart';
import '../ui_theme.dart';
import 'bus_screen.dart';
import 'railway_screen.dart';
import 'thsr_screen.dart';
import 'bike_screen.dart';

// 公車 Tab 內容 - 顯示大台北公車入口卡片
class BusTabContent extends StatelessWidget {
  const BusTabContent({super.key});

  @override
  Widget build(BuildContext context) {
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
                title: '大台北公車',
                subtitle: '查詢台北市、新北市公車路線',
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
    // 根據當前選中的 tab 決定主題色
    final selectedColor = _tabColors[_motionTabBarController?.index ?? 0];

    return Scaffold(
      appBar: AppBar(
        title: const Text('交通萬事通'),
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
      ),
      bottomNavigationBar: Container(
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
          initialSelectedTab: "公車",
          useSafeArea: true,
          labels: const ["公車", "火車", "高鐵", "腳踏車"],
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
            setState(() {
              _motionTabBarController!.index = value;
            });
          },
        ),
      ),
      body: TabBarView(
        controller: _motionTabBarController,
        physics: const NeverScrollableScrollPhysics(), // 禁用滑動切換，避免與列表衝突
        children: const [
          // 公車 tab 內容
          BusTabContent(),
          // 火車 tab 內容
          RailwayTabView(),
          // 高鐵 tab 內容
          THSRTabView(),
          // 腳踏車 tab 內容
          BikeTabView(),
        ],
      ),
      // 全局浮動操作按鈕選單
      floatingActionButton: _buildSpeedDial(),
    );
  }

  // 建立 SpeedDial 浮動選單
  Widget _buildSpeedDial() {
    return SpeedDial(
      // 主按鈕圖標
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
          label: 'AI最佳搭乘規劃',
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
          label: '遊戲空間',
          labelStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
          labelBackgroundColor: Colors.white,
          onTap: () => _onGameSpaceTap(),
        ),
      ],
    );
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

  // 清除 AI 緩存並顯示輸入對話框
  void _clearAICacheAndShowDialog() {
    // 先關閉當前的結果畫面
    Navigator.pop(context);

    setState(() {
      _cachedAIResult = null;
      _cachedFromLocation = null;
      _cachedToLocation = null;
    });

    // 顯示輸入對話框
    _showAIPlanDialog();
  }

  // 開始 AI 規劃
  Future<void> _startAIPlanning(String fromLocation, String toLocation) async {
    if (_isPlanning) return;

    setState(() {
      _isPlanning = true;
    });

    // 保存查詢地點
    _cachedFromLocation = fromLocation;
    _cachedToLocation = toLocation;

    // 顯示載入中的氣泡
    AIResultBubble.showLoading(context, message: '正在分析附近交通站點...');

    try {
      // 使用 AI 規劃服務執行完整流程
      // 1. 取得附近站點 2. 生成 Prompt 3. 發送到 Gemini
      final response = await _aiPlanningService.performAIPlanning(
        fromLocation: fromLocation,
        toLocation: toLocation,
      );

      // 緩存結果
      _cachedAIResult = response;

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

      // 關閉載入對話框
      if (mounted) {
        Navigator.pop(context);

        // 顯示錯誤結果
        AIResultBubble.show(
          context,
          result: '規劃失敗：$e\n\n請檢查網路連線或稍後再試。',
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
    // 顯示即將推出的提示
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('遊戲空間即將推出！'),
        duration: Duration(seconds: 2),
        backgroundColor: AppColors.secondary,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(AppRadius.medium)),
        ),
      ),
    );
  }
}

// 火車 Tab 視圖 - 直接使用 RailwayScreen 的內容（隱藏 AppBar）
class RailwayTabView extends StatelessWidget {
  const RailwayTabView({super.key});

  @override
  Widget build(BuildContext context) {
    // 直接使用 RailwayScreen，隱藏其 AppBar
    return const RailwayScreen(showAppBar: false);
  }
}

// 高鐵 Tab 視圖 - 直接使用 THSRScreen 的內容（隱藏 AppBar）
class THSRTabView extends StatelessWidget {
  const THSRTabView({super.key});

  @override
  Widget build(BuildContext context) {
    // 使用 THSRScreen，隱藏其 AppBar
    return const THSRScreen(showAppBar: false);
  }
}

// 腳踏車 Tab 視圖 - 直接使用 BikeScreen 的內容（隱藏 AppBar）
class BikeTabView extends StatelessWidget {
  const BikeTabView({super.key});

  @override
  Widget build(BuildContext context) {
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
                title: 'UBike腳踏車',
                subtitle: '查詢台北市、新北市UBike腳踏車',
                icon: Icons.directions_bike,
                color: TransportColors.bike,
                onTap: () => Navigator.push(
                  context,
                  SlidePageRoute(
                      builder: (_) => const BikeScreen(showAppBar: true)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
