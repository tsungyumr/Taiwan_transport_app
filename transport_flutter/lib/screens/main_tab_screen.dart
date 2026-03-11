import 'package:flutter/material.dart';
import 'package:motion_tab_bar/MotionTabBar.dart';
import 'package:motion_tab_bar/MotionTabBarController.dart';
import '../main.dart';
import '../widgets/animated_card.dart';
import '../widgets/loading_animations.dart';
import '../ui_theme.dart';
import 'bike_map_screen.dart';
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
    //return const BikeMapScreen();
    //return const BikeScreen(showAppBar: false);
  }
}
