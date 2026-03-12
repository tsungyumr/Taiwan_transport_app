import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'l10n/app_localizations.dart';
import 'providers/language_provider.dart';
import 'screens/main_tab_screen.dart';
import 'ui_theme.dart';

void main() {
  runApp(
    const ProviderScope(
      child: TaiwanTransportApp(),
    ),
  );
}

// 交通工具代表色 - 與黃色主題協調
class TransportColors {
  static const Color bus = Color(0xFF8BC34A);          // 公車：草綠色（與黃色協調）
  static const Color railway = Color(0xFFFFA726);      // 火車：暖橘色（與黃色協調）
  static const Color thsr = Color(0xFFFF7043);         // 高鐵：珊瑚橘（與黃色協調）
  static const Color bike = Color(0xFF2E7D32);           // 腳踏車：環保綠色
}

class TaiwanTransportApp extends ConsumerWidget {
  const TaiwanTransportApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final languageState = ref.watch(languageProvider);

    return MaterialApp(
      title: 'Transport Guide',
      theme: AppTheme.lightTheme,
      debugShowCheckedModeBanner: false,

      // 語系設定
      locale: languageState.locale,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      localeResolutionCallback: (locale, supportedLocales) {
        // 如果系統語系是支援的語系，就使用它
        for (var supportedLocale in supportedLocales) {
          if (supportedLocale.languageCode == locale?.languageCode) {
            return supportedLocale;
          }
        }
        // 不支援的語系預設使用英文
        return const Locale('en');
      },

      home: const MainTabScreen(),
    );
  }
}
