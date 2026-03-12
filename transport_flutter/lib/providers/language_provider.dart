import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 支援的語系列表
enum AppLocale {
  zh,
  en,
}

/// 語系設定狀態
class LanguageState {
  final Locale locale;
  final bool isLoading;

  const LanguageState({
    required this.locale,
    this.isLoading = false,
  });

  LanguageState copyWith({
    Locale? locale,
    bool? isLoading,
  }) {
    return LanguageState(
      locale: locale ?? this.locale,
      isLoading: isLoading ?? this.isLoading,
    );
  }

  /// 取得當前語系的顯示名稱
  String getDisplayName(BuildContext context) {
    switch (locale.languageCode) {
      case 'zh':
        return '繁體中文';
      case 'en':
        return 'English';
      default:
        return 'English';
    }
  }

  /// 檢查是否為中文
  bool get isZh => locale.languageCode == 'zh';

  /// 檢查是否為英文
  bool get isEn => locale.languageCode == 'en';
}

/// 語系設定 Notifier
class LanguageNotifier extends StateNotifier<LanguageState> {
  static const String _prefsKey = 'app_locale';

  LanguageNotifier() : super(const LanguageState(locale: Locale('zh'))) {
    _loadSavedLocale();
  }

  /// 載入儲存的語系設定
  Future<void> _loadSavedLocale() async {
    state = state.copyWith(isLoading: true);
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedLocale = prefs.getString(_prefsKey);

      if (savedLocale != null) {
        state = LanguageState(
          locale: Locale(savedLocale),
          isLoading: false,
        );
      } else {
        // 沒有儲存的語系，使用系統語系
        final systemLocale = WidgetsBinding.instance.platformDispatcher.locale;
        final appLocale = _getSupportedLocale(systemLocale);
        state = LanguageState(
          locale: appLocale,
          isLoading: false,
        );
        // 儲存預設語系
        await prefs.setString(_prefsKey, appLocale.languageCode);
      }
    } catch (e) {
      // 載入失敗時使用預設語系（英文）
      state = const LanguageState(
        locale: Locale('en'),
        isLoading: false,
      );
    }
  }

  /// 根據系統語系取得支援的語系
  /// 如果系統語系不是支援的語系，預設使用英文
  Locale _getSupportedLocale(Locale systemLocale) {
    final languageCode = systemLocale.languageCode;

    // 檢查是否支援此語系
    switch (languageCode) {
      case 'zh':
        // 中文相關語系都使用繁體中文
        return const Locale('zh');
      case 'en':
        return const Locale('en');
      default:
        // 不支援的語系預設使用英文
        return const Locale('en');
    }
  }

  /// 設定語系
  Future<void> setLocale(AppLocale appLocale) async {
    state = state.copyWith(isLoading: true);

    try {
      final prefs = await SharedPreferences.getInstance();
      final locale = Locale(appLocale.name);

      await prefs.setString(_prefsKey, appLocale.name);

      state = LanguageState(
        locale: locale,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false);
    }
  }

  /// 切換語系
  Future<void> toggleLocale() async {
    if (state.isZh) {
      await setLocale(AppLocale.en);
    } else {
      await setLocale(AppLocale.zh);
    }
  }
}

/// 語系設定 Provider
final languageProvider = StateNotifierProvider<LanguageNotifier, LanguageState>(
  (ref) => LanguageNotifier(),
);
