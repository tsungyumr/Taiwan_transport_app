// splash_screen.dart
// 自定義歡迎畫面組件

import 'package:flutter/material.dart';
import '../widgets/loading_animations.dart';
import 'main_tab_screen.dart';

/// 自定義歡迎畫面
///
/// 顯示 Logo 並播放淡入淡出動畫：
/// - 淡入：1秒 (opacity 0 → 1)
/// - 停留：3秒 (保持 opacity 1)
/// - 淡出：1秒 (opacity 1 → 0)
/// 總時長：5秒
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _opacityAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 5),
      vsync: this,
    );

    // 三階段動畫：淡入 → 停留 → 淡出
    // 使用 TweenSequence 來組合多個動畫階段
    _opacityAnimation = TweenSequence<double>([
      // 淡入階段：0.0 → 1.0，佔總時長的 1/5 (1秒)
      TweenSequenceItem(
        tween: Tween(begin: 0.0, end: 1.0),
        weight: 1,
      ),
      // 停留階段：保持 1.0，佔總時長的 3/5 (3秒)
      TweenSequenceItem(
        tween: ConstantTween(1.0),
        weight: 3,
      ),
      // 淡出階段：1.0 → 0.0，佔總時長的 1/5 (1秒)
      TweenSequenceItem(
        tween: Tween(begin: 1.0, end: 0.0),
        weight: 1,
      ),
    ]).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    // 監聽動畫狀態，完成後切換到主介面
    _controller.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        _navigateToMainScreen();
      }
    });

    // 開始播放動畫
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  /// 切換到主介面
  void _navigateToMainScreen() {
    Navigator.of(context).pushReplacement(
      SlidePageRoute(builder: (_) => const MainTabScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Opacity(
            opacity: _opacityAnimation.value,
            child: Center(
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  maxWidth: MediaQuery.of(context).size.width * 0.5,
                  maxHeight: 200,
                ),
                child: Image.asset(
                  'assets/images/logo.png',
                  fit: BoxFit.contain,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
