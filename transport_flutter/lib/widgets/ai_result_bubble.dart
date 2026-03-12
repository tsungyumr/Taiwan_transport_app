// ai_result_bubble.dart
// AI 規劃結果顯示氣泡對話框

import 'package:flutter/foundation.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import '../../ui_theme.dart';

/// AI 規劃結果氣泡對話框
/// 底部彈出的圓角氣泡，顯示 Gemini 回覆內容
class AIResultBubble extends StatelessWidget {
  final String result;
  final VoidCallback? onClose;
  final VoidCallback? onRetry;
  final bool isLoading;

  const AIResultBubble({
    super.key,
    required this.result,
    this.onClose,
    this.onRetry,
    this.isLoading = false,
  });

  /// 顯示結果氣泡的靜態方法
  static Future<void> show(
    BuildContext context, {
    required String result,
    VoidCallback? onRetry,
    bool isLoading = false,
  }) async {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      enableDrag: true,
      isDismissible: true,
      builder: (context) => AIResultBubble(
        result: result,
        onClose: () => Navigator.pop(context),
        onRetry: onRetry,
        isLoading: isLoading,
      ),
    );
  }

  /// 顯示載入中狀態
  static Future<void> showLoading(
    BuildContext context, {
    String message = 'AI 正在規劃路線...',
  }) async {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      enableDrag: false,
      isDismissible: false,
      builder: (context) => AIResultBubble(
        result: message,
        isLoading: true,
        onClose: () => Navigator.pop(context),
      ),
    );
  }

  /// 檢查結果是否為 HTML 格式
  bool _isHtmlContent(String content) {
    final trimmed = content.trim().toLowerCase();
    return trimmed.contains('<html') ||
           trimmed.contains('<!doctype html') ||
           trimmed.contains('<body') ||
           trimmed.contains('<div') ||
           trimmed.contains('<style');
  }

  /// 包裝 HTML 內容
  /// 如果內容已經是完整 HTML（包含 <html> 標籤），則直接返回
  /// 否則包裝成基本 HTML 結構
  String _wrapHtmlContent(String content) {
    final trimmed = content.trim();

    // 如果已經是完整 HTML，直接返回
    if (trimmed.toLowerCase().contains('<html')) {
      return trimmed;
    }

    // 包裝成基本 HTML 結構
    // AI 應該已經包含 viewport 設定，但這裡作為備援
    return '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=2.0, maximum-scale=3.0, user-scalable=yes">
    <title>交通規劃結果</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body {
            width: 100%;
            min-height: 100%;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
        }
        body {
            padding: 16px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
    </style>
</head>
<body>
    $trimmed
</body>
</html>''';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.8,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.vertical(
          top: Radius.circular(AppRadius.xl),
        ),
        boxShadow: [AppShadows.large],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 頂部拖曳指示器
          Container(
            margin: const EdgeInsets.only(top: AppSpacing.md),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.divider,
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // 標題列
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(AppSpacing.sm),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        AppColors.primary.withOpacity(0.2),
                        AppColors.secondary.withOpacity(0.1),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(AppRadius.small),
                  ),
                  child: isLoading
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                          ),
                        )
                      : const Icon(
                          Icons.smart_toy,
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
                        isLoading ? '規劃中...' : 'AI 規劃結果',
                        style: AppTextStyles.titleLarge.copyWith(
                          color: AppColors.onSurface,
                        ),
                      ),
                      if (!isLoading)
                        Text(
                          '由 Gemini AI 生成',
                          style: AppTextStyles.bodySmall,
                        ),
                    ],
                  ),
                ),
                if (!isLoading && onRetry != null)
                  TextButton.icon(
                    onPressed: onRetry,
                    icon: const Icon(Icons.refresh, size: 18),
                    label: const Text('重新規劃'),
                    style: TextButton.styleFrom(
                      foregroundColor: AppColors.primary,
                    ),
                  ),
                IconButton(
                  onPressed: onClose,
                  icon: const Icon(Icons.close, color: AppColors.onSurfaceLight),
                ),
              ],
            ),
          ),

          const Divider(height: 1),

          // 內容區域
          Expanded(
            child: isLoading
                ? _buildLoadingContent()
                : _buildResultContent(context),
          ),

          // 底部安全區域
          SizedBox(height: MediaQuery.of(context).padding.bottom),
        ],
      ),
    );
  }

  /// 構建載入中的內容
  Widget _buildLoadingContent() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AppColors.primary.withOpacity(0.1),
                    AppColors.secondary.withOpacity(0.05),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                shape: BoxShape.circle,
              ),
              child: const Center(
                child: SizedBox(
                  width: 50,
                  height: 50,
                  child: CircularProgressIndicator(
                    strokeWidth: 3,
                    valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                  ),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              result,
              style: AppTextStyles.titleMedium.copyWith(
                color: AppColors.onSurface,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              '這可能需要幾秒鐘',
              style: AppTextStyles.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  /// 構建結果內容
  Widget _buildResultContent(BuildContext context) {
    // 檢查是否為 HTML 內容
    if (_isHtmlContent(result)) {
      return _buildHtmlContent(context);
    }

    // 非 HTML 內容，使用原有文字顯示方式
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 結果內容（格式化顯示）
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(AppSpacing.lg),
            decoration: BoxDecoration(
              color: AppColors.background,
              borderRadius: BorderRadius.circular(AppRadius.medium),
              border: Border.all(
                color: AppColors.divider,
                width: 1,
              ),
            ),
            child: _buildFormattedResult(),
          ),

          const SizedBox(height: AppSpacing.lg),

          // 提示資訊
          _buildInfoNote(),
        ],
      ),
    );
  }

  /// 構建 HTML 內容顯示
  Widget _buildHtmlContent(BuildContext context) {
    final htmlContent = _wrapHtmlContent(result);

    return LayoutBuilder(
      builder: (context, constraints) {
        // 計算 WebView 高度：總高度減去提示訊息和安全區域的預估高度
        final bottomPadding = MediaQuery.of(context).padding.bottom;
        final webViewHeight = constraints.maxHeight - 80 - bottomPadding;

        return Column(
          children: [
            // WebView 區域
            SizedBox(
              height: webViewHeight > 100 ? webViewHeight : 200,
              child: Container(
                margin: const EdgeInsets.all(AppSpacing.lg),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(AppRadius.medium),
                  border: Border.all(
                    color: AppColors.divider,
                    width: 1,
                  ),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(AppRadius.medium),
                  child: InAppWebView(
                    initialData: InAppWebViewInitialData(
                      data: htmlContent,
                      mimeType: 'text/html',
                      encoding: 'utf-8',
                    ),
                    initialSettings: InAppWebViewSettings(
                      javaScriptEnabled: true,
                      transparentBackground: true,
                      supportZoom: true,
                      useWideViewPort: true,
                      loadWithOverviewMode: false,
                      verticalScrollBarEnabled: true,
                      horizontalScrollBarEnabled: false,
                      builtInZoomControls: true,
                      displayZoomControls: true,
                      initialScale: 0,
                      overScrollMode: OverScrollMode.ALWAYS,
                    ),
                    gestureRecognizers: <Factory<OneSequenceGestureRecognizer>>{
                      Factory<OneSequenceGestureRecognizer>(
                        () => EagerGestureRecognizer(),
                      ),
                    },
                  ),
                ),
              ),
            ),

            // 提示資訊
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: _buildInfoNote(),
            ),

            // 底部安全區域
            SizedBox(height: bottomPadding),
          ],
        );
      },
    );
  }

  /// 構建提示資訊
  Widget _buildInfoNote() {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.info.withOpacity(0.1),
        borderRadius: BorderRadius.circular(AppRadius.small),
        border: Border.all(
          color: AppColors.info.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.info_outline,
            size: 20,
            color: AppColors.info,
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(
              '以上資訊由 AI 生成，實際交通狀況可能有所不同，請以現場為準。',
              style: AppTextStyles.bodySmall.copyWith(
                color: AppColors.info,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 構建格式化的結果內容
  Widget _buildFormattedResult() {
    // 將結果文字轉換為更豐富的顯示
    final lines = result.split('\n');
    final widgets = <Widget>[];

    for (final line in lines) {
      final trimmedLine = line.trim();

      if (trimmedLine.isEmpty) {
        widgets.add(const SizedBox(height: AppSpacing.sm));
        continue;
      }

      // 檢查是否為標題行（數字開頭或特定格式）
      if (_isHeadingLine(trimmedLine)) {
        widgets.add(
          Padding(
            padding: const EdgeInsets.only(top: AppSpacing.md, bottom: AppSpacing.sm),
            child: Row(
              children: [
                Container(
                  width: 4,
                  height: 20,
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: Text(
                    trimmedLine,
                    style: AppTextStyles.titleMedium.copyWith(
                      color: AppColors.onSurface,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      }
      // 檢查是否為列表項目
      else if (_isListItem(trimmedLine)) {
        widgets.add(
          Padding(
            padding: const EdgeInsets.only(left: AppSpacing.md, bottom: AppSpacing.xs),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 6,
                  height: 6,
                  margin: const EdgeInsets.only(top: 8),
                  decoration: const BoxDecoration(
                    color: AppColors.primary,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: Text(
                    _cleanListItem(trimmedLine),
                    style: AppTextStyles.bodyLarge.copyWith(
                      color: AppColors.onSurface,
                      height: 1.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      }
      // 一般文字
      else {
        widgets.add(
          Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.xs),
            child: Text(
              trimmedLine,
              style: AppTextStyles.bodyLarge.copyWith(
                color: AppColors.onSurface,
                height: 1.6,
              ),
            ),
          ),
        );
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }

  /// 檢查是否為標題行
  bool _isHeadingLine(String line) {
    // 數字開頭的標題，如 "1."、"2."
    if (RegExp(r'^\d+\s*[.\)]\s*').hasMatch(line)) {
      return true;
    }
    // 特定關鍵詞開頭
    final headingKeywords = [
      '推薦',
      '方案',
      '路線',
      '時間',
      '費用',
      '注意',
      '建議',
      '備用',
    ];
    for (final keyword in headingKeywords) {
      if (line.startsWith(keyword)) {
        return true;
      }
    }
    return false;
  }

  /// 檢查是否為列表項目
  bool _isListItem(String line) {
    return line.startsWith('-') ||
        line.startsWith('•') ||
        line.startsWith('*');
  }

  /// 清理列表項目的標記符號
  String _cleanListItem(String line) {
    return line.replaceFirst(RegExp(r'^[-•*]\s*'), '');
  }
}

/// 簡化的 AI 結果氣泡按鈕
/// 用於在畫面中顯示 AI 結果的快速入口
class AIResultBubbleButton extends StatelessWidget {
  final VoidCallback onTap;
  final String? label;

  const AIResultBubbleButton({
    super.key,
    required this.onTap,
    this.label,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              AppColors.primary,
              AppColors.primaryDark,
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(AppRadius.full),
          boxShadow: [
            BoxShadow(
              color: AppColors.primary.withOpacity(0.4),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.smart_toy,
              size: 20,
              color: Colors.white,
            ),
            if (label != null) ...[
              const SizedBox(width: AppSpacing.xs),
              Text(
                label!,
                style: AppTextStyles.bodyMedium.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
