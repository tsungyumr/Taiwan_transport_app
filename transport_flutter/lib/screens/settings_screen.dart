import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../l10n/app_localizations.dart';
import '../providers/language_provider.dart';
import '../widgets/analytics_widgets.dart';
import '../ui_theme.dart';

/// 設定頁面
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final languageState = ref.watch(languageProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.commonSettings),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        flexibleSpace: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                AppColors.primary,
                AppColors.primary.withOpacity(0.8),
              ],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          // 語言設定卡片
          _buildLanguageCard(context, ref, l10n, languageState),

          const SizedBox(height: AppSpacing.lg),

          // App 資訊
          _buildAppInfoCard(context, l10n),
        ],
      ),
    );
  }

  /// 建立語言設定卡片
  Widget _buildLanguageCard(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    LanguageState languageState,
  ) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadius.large),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 標題列
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(AppSpacing.sm),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(AppRadius.medium),
                  ),
                  child: Icon(
                    Icons.language,
                    color: AppColors.primary,
                    size: 24,
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        l10n.commonLanguage,
                        style: AppTextStyles.titleMedium.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        l10n.languageSubtitle,
                        style: AppTextStyles.labelMedium.copyWith(
                          color: AppColors.onSurfaceLight,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: AppSpacing.lg),

            // 語言選項
            _buildLanguageOption(
              context,
              ref,
              l10n,
              title: '繁體中文',
              subtitle: 'Traditional Chinese',
              locale: AppLocale.zh,
              isSelected: languageState.isZh,
              flag: '🇹🇼',
            ),

            const SizedBox(height: AppSpacing.sm),

            _buildLanguageOption(
              context,
              ref,
              l10n,
              title: 'English',
              subtitle: 'English (US)',
              locale: AppLocale.en,
              isSelected: languageState.isEn,
              flag: '🇺🇸',
            ),
          ],
        ),
      ),
    );
  }

  /// 建立語言選項
  Widget _buildLanguageOption(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n, {
    required String title,
    required String subtitle,
    required AppLocale locale,
    required bool isSelected,
    required String flag,
  }) {
    return InkWell(
      onTap: () async {
        // 追蹤語言切換
        final oldLocale = ref.read(languageProvider);
        final toLanguageCode = locale == AppLocale.zh ? 'zh' : 'en';
        FeatureAnalytics.trackFeatureUse(
          featureName: 'change_language',
          featureType: 'settings',
          parameters: {
            'from': oldLocale.locale.languageCode,
            'to': toLanguageCode,
          },
        );
        UserAnalytics.setLanguage(toLanguageCode);

        await ref.read(languageProvider.notifier).setLocale(locale);
      },
      borderRadius: BorderRadius.circular(AppRadius.medium),
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.md,
        ),
        decoration: BoxDecoration(
          color: isSelected
              ? AppColors.primary.withOpacity(0.1)
              : AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.medium),
          border: Border.all(
            color: isSelected ? AppColors.primary : AppColors.divider,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            // 國旗
            Text(
              flag,
              style: const TextStyle(fontSize: 24),
            ),
            const SizedBox(width: AppSpacing.md),

            // 語言名稱
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: AppTextStyles.bodyLarge.copyWith(
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                      color: isSelected ? AppColors.primary : AppColors.onSurface,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: AppTextStyles.labelMedium.copyWith(
                      color: AppColors.onSurfaceLight,
                    ),
                  ),
                ],
              ),
            ),

            // 選中標記
            if (isSelected)
              Container(
                padding: const EdgeInsets.all(AppSpacing.xs),
                decoration: const BoxDecoration(
                  color: AppColors.primary,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.check,
                  color: Colors.white,
                  size: 16,
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// 建立 App 資訊卡片
  Widget _buildAppInfoCard(BuildContext context, AppLocalizations l10n) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadius.large),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.appInfoTitle,
              style: AppTextStyles.titleMedium.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // App 名稱
            _buildInfoRow(
              icon: Icons.app_shortcut,
              label: l10n.appInfoName,
              value: l10n.appTitle,
            ),

            const Divider(height: AppSpacing.lg),

            // 版本
            _buildInfoRow(
              icon: Icons.info_outline,
              label: l10n.appInfoVersion,
              value: '1.0.0',
            ),

            const Divider(height: AppSpacing.lg),

            // 資料來源
            _buildInfoRow(
              icon: Icons.data_usage,
              label: l10n.appInfoDataSource,
              value: l10n.appInfoDataSourceValue,
            ),
          ],
        ),
      ),
    );
  }

  /// 建立資訊行
  Widget _buildInfoRow({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Row(
      children: [
        Icon(
          icon,
          size: 20,
          color: AppColors.onSurfaceLight,
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: AppTextStyles.labelMedium.copyWith(
                  color: AppColors.onSurfaceLight,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: AppTextStyles.bodyMedium,
              ),
            ],
          ),
        ),
      ],
    );
  }
}
