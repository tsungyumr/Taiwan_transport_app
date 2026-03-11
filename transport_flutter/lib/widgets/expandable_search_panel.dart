// expandable_search_panel.dart
// 可展開/縮小的搜尋條件區域元件

import 'package:flutter/material.dart';
import '../ui_theme.dart';

/// 可展開/縮小的搜尋條件面板
class ExpandableSearchPanel extends StatefulWidget {
  final bool isExpanded;
  final VoidCallback onToggle;
  final Widget expandedContent;
  final String summaryText;
  final Color accentColor;
  final String title;

  const ExpandableSearchPanel({
    super.key,
    required this.isExpanded,
    required this.onToggle,
    required this.expandedContent,
    required this.summaryText,
    required this.accentColor,
    this.title = '搜尋條件',
  });

  @override
  State<ExpandableSearchPanel> createState() => _ExpandableSearchPanelState();
}

class _ExpandableSearchPanelState extends State<ExpandableSearchPanel>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _heightFactor;
  late Animation<double> _arrowRotation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: AppAnimations.normal,
      vsync: this,
    );
    _heightFactor = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _controller,
        curve: AppAnimations.curve,
      ),
    );
    _arrowRotation = Tween<double>(begin: 0, end: 0.5).animate(
      CurvedAnimation(
        parent: _controller,
        curve: AppAnimations.curve,
      ),
    );

    if (widget.isExpanded) {
      _controller.value = 1.0;
    }
  }

  @override
  void didUpdateWidget(ExpandableSearchPanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isExpanded != oldWidget.isExpanded) {
      if (widget.isExpanded) {
        _controller.forward();
      } else {
        _controller.reverse();
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      margin: const EdgeInsets.all(AppSpacing.md),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadius.medium),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 標題列（點擊可切換展開/縮小）
          InkWell(
            onTap: widget.onToggle,
            borderRadius: BorderRadius.vertical(
              top: const Radius.circular(AppRadius.medium),
              bottom: widget.isExpanded
                  ? const Radius.circular(0)
                  : const Radius.circular(AppRadius.medium),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md,
                vertical: AppSpacing.sm,
              ),
              child: Row(
                children: [
                  // 圖標
                  Container(
                    padding: const EdgeInsets.all(AppSpacing.sm),
                    decoration: BoxDecoration(
                      color: widget.accentColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(AppRadius.small),
                    ),
                    child: Icon(
                      Icons.search,
                      color: widget.accentColor,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  // 摘要文字
                  Expanded(
                    child: widget.isExpanded
                        ? Text(
                            widget.title,
                            style: AppTextStyles.titleMedium.copyWith(
                              color: AppColors.onSurface,
                            ),
                          )
                        : Text(
                            widget.summaryText,
                            style: AppTextStyles.bodyMedium.copyWith(
                              color: AppColors.onSurface,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                  ),
                  // 展開/縮小按鈕
                  RotationTransition(
                    turns: _arrowRotation,
                    child: IconButton(
                      icon: const Icon(Icons.expand_more),
                      color: widget.accentColor,
                      onPressed: widget.onToggle,
                    ),
                  ),
                ],
              ),
            ),
          ),
          // 展開內容
          ClipRect(
            child: AnimatedBuilder(
              animation: _controller,
              builder: (context, child) {
                return Align(
                  alignment: Alignment.topCenter,
                  heightFactor: _heightFactor.value,
                  child: child,
                );
              },
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  maxHeight: 400, // 限制最大高度
                ),
                child: SingleChildScrollView(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(
                      AppSpacing.md,
                      0,
                      AppSpacing.md,
                      AppSpacing.md,
                    ),
                    child: widget.expandedContent,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// 搜尋摘要卡片（縮小狀態）
class SearchSummaryCard extends StatelessWidget {
  final String fromStation;
  final String toStation;
  final String? date;
  final String? timeRange;
  final Color accentColor;
  final VoidCallback onTap;

  const SearchSummaryCard({
    super.key,
    required this.fromStation,
    required this.toStation,
    this.date,
    this.timeRange,
    required this.accentColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      margin: const EdgeInsets.all(AppSpacing.md),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadius.medium),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppRadius.medium),
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.md,
            vertical: AppSpacing.md,
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(AppSpacing.sm),
                decoration: BoxDecoration(
                  color: accentColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(AppRadius.small),
                ),
                child: Icon(
                  Icons.train,
                  color: accentColor,
                  size: 20,
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '$fromStation → $toStation',
                      style: AppTextStyles.titleMedium.copyWith(
                        color: AppColors.onSurface,
                      ),
                    ),
                    if (date != null || timeRange != null)
                      Text(
                        '${date ?? ''} ${timeRange ?? ''}'.trim(),
                        style: AppTextStyles.bodySmall.copyWith(
                          color: AppColors.onSurfaceLight,
                        ),
                      ),
                  ],
                ),
              ),
              Icon(
                Icons.expand_more,
                color: accentColor,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
