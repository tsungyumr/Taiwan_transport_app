// ui_theme.dart
// 統一的 UI 主題與元件樣式

import 'package:flutter/material.dart';

/// App 主色調 - 黃色系
class AppColors {
  // 主要黃色調
  static const Color primary = Color(0xFFFFB800);      // 主要黃色
  static const Color primaryLight = Color(0xFFFFD54F); // 淺黃色
  static const Color primaryDark = Color(0xFFFF8F00);  // 深黃色

  // 輔助色
  static const Color secondary = Color(0xFFFF6D00);    // 橘黃色
  static const Color accent = Color(0xFFFFAB00);       // 金黃色

  // 功能色
  static const Color success = Color(0xFF4CAF50);      // 綠色
  static const Color warning = Color(0xFFFF9800);      // 警告橘
  static const Color error = Color(0xFFE53935);        // 錯誤紅
  static const Color info = Color(0xFF2196F3);         // 資訊藍

  // 中性色
  static const Color background = Color(0xFFFAFAFA);   // 背景淺灰
  static const Color surface = Colors.white;           // 卡片表面
  static const Color onSurface = Color(0xFF212121);    // 深色文字
  static const Color onSurfaceLight = Color(0xFF757575); // 淺色文字
  static const Color onBackground = Color(0xFF212121); // 背景上的文字
  static const Color onSurfaceVariant = Color(0xFF757575); // 表面變體文字
  static const Color onPrimary = Colors.white;         // 主色上的文字
  static const Color divider = Color(0xFFEEEEEE);      // 分隔線

  // 交通工具特定色
  static const Color bus = Color(0xFF4CAF50);          // 公車綠
  static const Color railway = Color(0xFFFF6D00);      // 台鐵橘
  static const Color thsr = Color(0xFFE53935);         // 高鐵紅
  static const Color bike = Color(0xFF2E7D32);         // YouBike 環保綠
}

/// YouBike 專屬顏色
class BikeColors {
  // 主要環保綠色
  static const Color primary = Color(0xFF2E7D32);      // 深綠色
  static const Color primaryLight = Color(0xFF4CAF50); // 亮綠色
  static const Color primaryDark = Color(0xFF1B5E20);  // 墨綠色

  // 狀態顏色
  static const Color available = Color(0xFF4CAF50);    // 綠色 - 充足
  static const Color limited = Color(0xFFFFC107);      // 黃色 - 中等
  static const Color few = Color(0xFFF44336);          // 紅色 - 少量
  static const Color empty = Color(0xFF9E9E9E);        // 灰色 - 無車

  // 輔助色
  static const Color accent = Color(0xFF81C784);       // 淺綠色
  static const Color background = Color(0xFFE8F5E9);   // 極淺綠背景
}

/// 統一的陰影樣式
class AppShadows {
  // 小陰影 - 用於按鈕、小卡片
  static const BoxShadow small = BoxShadow(
    color: Color(0x1A000000),
    blurRadius: 4,
    offset: Offset(0, 2),
  );

  // 中陰影 - 用於卡片
  static const BoxShadow medium = BoxShadow(
    color: Color(0x26000000),
    blurRadius: 8,
    offset: Offset(0, 4),
  );

  // 大陰影 - 用於底部導航、對話框
  static const BoxShadow large = BoxShadow(
    color: Color(0x33000000),
    blurRadius: 16,
    offset: Offset(0, 8),
  );

  // 內陰影效果（用於輸入框）
  static const BoxShadow inner = BoxShadow(
    color: Color(0x0D000000),
    blurRadius: 4,
    offset: Offset(0, 2),
    spreadRadius: -2,
  );
}

/// 圓角半徑
class AppRadius {
  static const double small = 8.0;
  static const double medium = 12.0;
  static const double large = 16.0;
  static const double xl = 24.0;
  static const double full = 999.0; // 完全圓角
}

/// 間距
class AppSpacing {
  static const double xs = 4.0;
  static const double sm = 8.0;
  static const double md = 16.0;
  static const double lg = 24.0;
  static const double xl = 32.0;
}

/// 動畫持續時間
class AppAnimations {
  static const Duration fast = Duration(milliseconds: 150);
  static const Duration normal = Duration(milliseconds: 300);
  static const Duration slow = Duration(milliseconds: 500);

  // 標準曲線
  static const Curve curve = Curves.easeInOutCubic;
  static const Curve bounce = Curves.elasticOut;
  static const Curve decelerate = Curves.decelerate;
}

/// 統一的 AppTheme
class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: const ColorScheme(
        brightness: Brightness.light,
        primary: AppColors.primary,
        onPrimary: Colors.white,
        primaryContainer: AppColors.primaryLight,
        onPrimaryContainer: AppColors.primaryDark,
        secondary: AppColors.secondary,
        onSecondary: Colors.white,
        secondaryContainer: Color(0xFFFFE0B2),
        onSecondaryContainer: AppColors.secondary,
        surface: AppColors.surface,
        onSurface: AppColors.onSurface,
        error: AppColors.error,
        onError: Colors.white,
        surfaceContainerHighest: AppColors.background,
        onSurfaceVariant: AppColors.onSurfaceLight,
        outline: AppColors.divider,
      ),
      scaffoldBackgroundColor: AppColors.background,

      // AppBar 主題
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        elevation: 0,
        scrolledUnderElevation: 2,
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        titleTextStyle: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),

      // 卡片主題
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.medium),
        ),
        color: AppColors.surface,
        shadowColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
      ),

      // 輸入框主題
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.md,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.medium),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.medium),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.medium),
          borderSide: const BorderSide(color: AppColors.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.medium),
          borderSide: const BorderSide(color: AppColors.error, width: 1),
        ),
        prefixIconColor: AppColors.onSurfaceLight,
        suffixIconColor: AppColors.onSurfaceLight,
      ),

      // 按鈕主題
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 2,
          shadowColor: const Color(0x40000000),
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.lg,
            vertical: AppSpacing.md,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.medium),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.primaryDark,
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.md,
            vertical: AppSpacing.sm,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.small),
          ),
        ),
      ),

      // 列表主題
      listTileTheme: const ListTileThemeData(
        contentPadding: EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(AppRadius.small)),
        ),
      ),

      // 底部導航主題
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: Colors.white,
        elevation: 8,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.onSurfaceLight,
        type: BottomNavigationBarType.fixed,
      ),

      // 浮動按鈕主題
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.full),
        ),
      ),

      // 分隔線主題
      dividerTheme: const DividerThemeData(
        color: AppColors.divider,
        thickness: 1,
        space: AppSpacing.md,
      ),

      // Chip 主題
      chipTheme: ChipThemeData(
        backgroundColor: AppColors.background,
        disabledColor: AppColors.divider,
        selectedColor: AppColors.primary.withOpacity(0.2),
        secondarySelectedColor: AppColors.primary,
        labelStyle: const TextStyle(fontSize: 14),
        secondaryLabelStyle: const TextStyle(
          fontSize: 14,
          color: AppColors.primaryDark,
        ),
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.xs,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.full),
        ),
      ),
    );
  }
}

/// 動畫頁面轉換
class AppPageTransitions {
  // 從右滑入
  static Route<T> slideFromRight<T>({
    required WidgetBuilder builder,
    RouteSettings? settings,
  }) {
    return PageRouteBuilder<T>(
      settings: settings,
      pageBuilder: (context, animation, secondaryAnimation) => builder(context),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        const begin = Offset(1.0, 0.0);
        const end = Offset.zero;
        const curve = Curves.easeInOutCubic;

        var tween = Tween(begin: begin, end: end).chain(
          CurveTween(curve: curve),
        );

        return SlideTransition(
          position: animation.drive(tween),
          child: FadeTransition(
            opacity: animation,
            child: child,
          ),
        );
      },
      transitionDuration: AppAnimations.normal,
    );
  }

  // 淡入淡出
  static Route<T> fade<T>({
    required WidgetBuilder builder,
    RouteSettings? settings,
  }) {
    return PageRouteBuilder<T>(
      settings: settings,
      pageBuilder: (context, animation, secondaryAnimation) => builder(context),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return FadeTransition(
          opacity: animation,
          child: child,
        );
      },
      transitionDuration: AppAnimations.normal,
    );
  }

  // 縮放進入
  static Route<T> scale<T>({
    required WidgetBuilder builder,
    RouteSettings? settings,
  }) {
    return PageRouteBuilder<T>(
      settings: settings,
      pageBuilder: (context, animation, secondaryAnimation) => builder(context),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return ScaleTransition(
          scale: animation.drive(
            Tween(begin: 0.8, end: 1.0).chain(
              CurveTween(curve: Curves.easeOutCubic),
            ),
          ),
          child: FadeTransition(
            opacity: animation,
            child: child,
          ),
        );
      },
      transitionDuration: AppAnimations.normal,
    );
  }
}

/// 裝飾盒樣式
class AppDecorations {
  // 卡片陰影盒
  static BoxDecoration card({Color? color}) {
    return BoxDecoration(
      color: color ?? AppColors.surface,
      borderRadius: BorderRadius.circular(AppRadius.medium),
      boxShadow: const [AppShadows.medium],
    );
  }

  // 卡片陰影盒（小）
  static BoxDecoration cardSmall({Color? color}) {
    return BoxDecoration(
      color: color ?? AppColors.surface,
      borderRadius: BorderRadius.circular(AppRadius.small),
      boxShadow: const [AppShadows.small],
    );
  }

  // 主要顏色卡片
  static BoxDecoration primaryCard = BoxDecoration(
    color: AppColors.primary,
    borderRadius: BorderRadius.circular(AppRadius.medium),
    boxShadow: const [AppShadows.medium],
  );

  // 輸入框樣式
  static BoxDecoration input = BoxDecoration(
    color: Colors.white,
    borderRadius: BorderRadius.circular(AppRadius.medium),
    boxShadow: const [AppShadows.small],
  );

  // 圓形圖標背景
  static BoxDecoration circleIcon(Color color) {
    return BoxDecoration(
      color: color.withOpacity(0.1),
      shape: BoxShape.circle,
    );
  }

  // 圓角圖標背景
  static BoxDecoration roundedIcon(Color color, {double radius = AppRadius.small}) {
    return BoxDecoration(
      color: color.withOpacity(0.1),
      borderRadius: BorderRadius.circular(radius),
    );
  }
}

/// 文字樣式
class AppTextStyles {
  // 標題
  static const TextStyle headlineLarge = TextStyle(
    fontSize: 28,
    fontWeight: FontWeight.bold,
    color: AppColors.onSurface,
  );

  static const TextStyle headlineMedium = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
    color: AppColors.onSurface,
  );

  static const TextStyle headlineSmall = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w600,
    color: AppColors.onSurface,
  );

  // 內文
  static const TextStyle titleLarge = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w600,
    color: AppColors.onSurface,
  );

  static const TextStyle titleMedium = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w600,
    color: AppColors.onSurface,
  );

  static const TextStyle titleSmall = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w500,
    color: AppColors.onSurface,
  );

  static const TextStyle bodyLarge = TextStyle(
    fontSize: 16,
    color: AppColors.onSurface,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontSize: 14,
    color: AppColors.onSurface,
  );

  static const TextStyle bodySmall = TextStyle(
    fontSize: 12,
    color: AppColors.onSurfaceLight,
  );

  // 標籤
  static const TextStyle labelLarge = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w600,
    color: AppColors.primary,
  );

  static const TextStyle labelMedium = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w500,
    color: AppColors.onSurfaceLight,
  );

  static const TextStyle labelSmall = TextStyle(
    fontSize: 10,
    fontWeight: FontWeight.w500,
    color: AppColors.onSurfaceLight,
  );
}
