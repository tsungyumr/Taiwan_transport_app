import 'package:flutter/material.dart';
import 'ui_theme.dart';
import 'screens/main_tab_screen.dart';

void main() {
  runApp(const TaiwanTransportApp());
}

// 交通工具代表色 - 與黃色主題協調
class TransportColors {
  static const Color bus = Color(0xFF8BC34A);          // 公車：草綠色（與黃色協調）
  static const Color railway = Color(0xFFFFA726);      // 火車：暖橘色（與黃色協調）
  static const Color thsr = Color(0xFFFF7043);         // 高鐵：珊瑚橘（與黃色協調）
  static const Color bike = Color(0xFF2E7D32);           // 腳踏車：環保綠色
}

class TaiwanTransportApp extends StatelessWidget {
  const TaiwanTransportApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '交通萬事通',
      theme: AppTheme.lightTheme,
      home: const MainTabScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
