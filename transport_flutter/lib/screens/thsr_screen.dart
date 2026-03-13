import 'package:flutter/material.dart';
import '../main.dart';
import '../l10n/app_localizations.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/animated_card.dart';
import '../widgets/expandable_search_panel.dart';
import '../widgets/loading_animations.dart';
import '../widgets/styled_inputs.dart';
import '../widgets/analytics_widgets.dart';
import '../ui_theme.dart';

class THSRScreen extends StatefulWidget {
  final bool showAppBar;
  final bool isActive;

  const THSRScreen({
    super.key,
    this.showAppBar = true,
    this.isActive = true,
  });

  @override
  State<THSRScreen> createState() => _THSRScreenState();
}

class _THSRScreenState extends State<THSRScreen> {
  final ApiService _apiService = ApiService();

  List<TrainStation> _stations = [];
  List<THSRTrainEntry> _timetable = [];
  bool _isLoading = false;

  String? _selectedFromStationCode;
  String? _selectedFromStationName;
  String? _selectedToStationCode;
  String? _selectedToStationName;
  DateTime? _selectedDate;

  // 時間選擇模式
  int _timeModeIndex = 0; // 0 = 當天, 1 = 自訂時間

  // 起訖時間
  TimeOfDay? _startTime;
  TimeOfDay? _endTime;

  // 搜尋條件區域展開狀態
  bool _isSearchPanelExpanded = true;

  // 追蹤語言變化
  String? _currentLang;
  bool _isInitialized = false;

  @override
  void initState() {
    super.initState();
    // 初始化時間
    _startTime = TimeOfDay.now();
    _endTime = const TimeOfDay(hour: 23, minute: 59);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final lang = Localizations.localeOf(context).languageCode;

    // 首次初始化
    if (!_isInitialized) {
      _isInitialized = true;
      _currentLang = lang;
      // 只有在活躍狀態時才載入資料
      if (widget.isActive) {
        _loadStations();
      }
      return;
    }

    // 語言變化時重新加載站點
    if (_currentLang != lang) {
      _currentLang = lang;
      _loadStations();
    }
  }

  @override
  void didUpdateWidget(covariant THSRScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    // 當從非活躍變成活躍時，且資料還沒載入，則載入資料
    if (!oldWidget.isActive && widget.isActive && _stations.isEmpty && !_isLoading) {
      _loadStations();
    }
  }

  // 格式化時間為字串 (HH:mm)
  String _formatTime(TimeOfDay? time) {
    if (time == null) return '--:--';
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }

  // 取得時間範圍字串用於 API
  String? _getTimeRangeForApi() {
    if (_timeModeIndex == 0) {
      // 當天模式：使用目前時間作為起始時間，結束時間不傳
      final now = TimeOfDay.now();
      return _formatTime(now);
    }
    // 自訂時間模式
    if (_startTime == null) return null;
    return _formatTime(_startTime);
  }

  // 取得搜尋摘要文字
  String _getSearchSummary() {
    final l10n = AppLocalizations.of(context)!;
    final fromStation = _selectedFromStationName ?? l10n.railwaySelectFromStation;
    final toStation = _selectedToStationName ?? l10n.railwaySelectToStation;
    final date = _selectedDate != null
        ? '${_selectedDate!.year}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}'
        : l10n.commonToday;
    final timeRange = _timeModeIndex == 1 && (_startTime != null || _endTime != null)
        ? '${_formatTime(_startTime)} - ${_formatTime(_endTime)}'
        : l10n.railwayAllDay;
    return '$fromStation → $toStation | $date | $timeRange';
  }

  Future<void> _loadStations({String? langOverride}) async {
    setState(() => _isLoading = true);
    final lang = langOverride ?? Localizations.localeOf(context).languageCode;
    final stations = await _apiService.getTHSRStations(lang: lang);
    if (!mounted) return;
    setState(() {
      _stations = stations;
      _isLoading = false;
    });
  }

  Future<void> _searchTimetable() async {
    final l10n = AppLocalizations.of(context)!;

    if (_selectedFromStationName == null || _selectedToStationName == null) {
      _showErrorSnackBar(l10n.thsrSelectStationsError);
      return;
    }

    setState(() => _isLoading = true);

    // 準備時間參數
    final String? timeParam = _getTimeRangeForApi();
    final String? endTimeParam =
        (_timeModeIndex == 1 && _endTime != null) ? _formatTime(_endTime) : null;

    // 取得當前語言
    final locale = Localizations.localeOf(context);
    final lang = locale.languageCode;

    // TDX API 使用站名（如「台北」）查詢時刻表
    final timetable = await _apiService.getTHSRTimetable(
      fromStation: _selectedFromStationName!,
      toStation: _selectedToStationName!,
      date: _selectedDate?.toIso8601String().split('T')[0],
      time: timeParam,
      endTime: endTimeParam,
      lang: lang,
    );

    if (!mounted) return;
    setState(() {
      _timetable = timetable;
      _isLoading = false;
      // 搜尋後自動縮小搜尋條件區域
      _isSearchPanelExpanded = false;
    });

    // 追蹤搜尋事件
    FeatureAnalytics.trackSearch(
      searchType: 'thsr_timetable',
      query: '$_selectedFromStationName-$_selectedToStationName',
      resultCount: timetable.length,
    );
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.error_outline, color: Colors.white),
            const SizedBox(width: AppSpacing.sm),
            Text(message),
          ],
        ),
        backgroundColor: AppColors.error,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.small),
        ),
      ),
    );
  }

  Future<void> _selectStartTime() async {
    final time = await showTimePicker(
      context: context,
      initialTime: _startTime ?? TimeOfDay.now(),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: Theme.of(context).colorScheme.copyWith(
              primary: TransportColors.railway,
            ),
          ),
          child: child!,
        );
      },
    );
    if (time != null) {
      setState(() => _startTime = time);
    }
  }

  Future<void> _selectEndTime() async {
    final time = await showTimePicker(
      context: context,
      initialTime: _endTime ??
          (_startTime != null
              ? TimeOfDay(
              hour: (_startTime!.hour + 3) % 24, minute: _startTime!.minute)
              : const TimeOfDay(hour: 23, minute: 59)),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: Theme.of(context).colorScheme.copyWith(
              primary: TransportColors.railway,
            ),
          ),
          child: child!,
        );
      },
    );
    if (time != null) {
      setState(() => _endTime = time);
    }
  }

  void _toggleSearchPanel() {
    setState(() {
      _isSearchPanelExpanded = !_isSearchPanelExpanded;
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: widget.showAppBar
          ? AppBar(
              title: Text(l10n.thsrTitle),
              backgroundColor: TransportColors.thsr,
              foregroundColor: Colors.white,
              elevation: 0,
              flexibleSpace: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      TransportColors.thsr,
                      TransportColors.thsr.withOpacity(0.8),
                    ],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
              ),
            )
          : null,
      body: _isLoading && _stations.isEmpty
          ? const Center(
              child: PulseLoading(color: TransportColors.thsr),
            )
          : Column(
              children: [
                // 可展開/縮小的搜尋條件區域
                ExpandableSearchPanel(
                  isExpanded: _isSearchPanelExpanded,
                  onToggle: _toggleSearchPanel,
                  summaryText: _getSearchSummary(),
                  accentColor: TransportColors.thsr,
                  title: l10n.railwaySearchConditions,
                  expandedContent: _buildSearchForm(),
                ),

                // 結果統計
                if (_timetable.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                    child: Row(
                      children: [
                        const Icon(Icons.speed, size: 16, color: AppColors.onSurfaceLight),
                        const SizedBox(width: AppSpacing.xs),
                        Text(
                          l10n.thsrTrainsFound(_timetable.length),
                          style: AppTextStyles.labelMedium.copyWith(
                            color: AppColors.onSurfaceLight,
                          ),
                        ),
                      ],
                    ),
                  ),

                // 時刻表列表
                Expanded(
                  child: _timetable.isEmpty
                      ? _isLoading
                          ? const Center(child: PulseLoading(color: TransportColors.thsr))
                          : EmptyStateCard(
                              icon: Icons.speed_outlined,
                              title: l10n.thsrEmptyTitle,
                              subtitle: l10n.thsrEmptySubtitle,
                            )
                      : ListView.builder(
                          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                          itemCount: _timetable.length,
                          itemBuilder: (context, index) {
                            final train = _timetable[index];
                            return TimetableCard(
                              trainNo: train.trainNo,
                              fromStation: train.departureStation,
                              toStation: train.arrivalStation,
                              departureTime: train.departureTime,
                              arrivalTime: train.arrivalTime,
                              duration: train.duration,
                              accentColor: TransportColors.thsr,
                              trainType: 'HSR ',
                              extras: [
                                Row(
                                  children: [
                                    _buildSeatIndicator(
                                      icon: Icons.business,
                                      label: l10n.thsrSeatBusiness,
                                      available: train.businessSeatAvailable,
                                    ),
                                    const SizedBox(width: AppSpacing.md),
                                    _buildSeatIndicator(
                                      icon: Icons.event_seat,
                                      label: l10n.thsrSeatStandard,
                                      available: train.standardSeatAvailable,
                                    ),
                                    const SizedBox(width: AppSpacing.md),
                                    _buildSeatIndicator(
                                      icon: Icons.chair,
                                      label: l10n.thsrSeatFree,
                                      available: train.freeSeatAvailable,
                                    ),
                                  ],
                                ),
                              ],
                            );
                          },
                        ),
                ),
              ],
            ),
    );
  }

  Widget _buildSearchForm() {
    final l10n = AppLocalizations.of(context)!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // 出發站選擇
        StyledDropdown<String>(
          value: _stations.isEmpty ? null : _selectedFromStationCode,
          labelText: l10n.railwayFromStation,
          prefixIcon: Icons.train,
          items: _stations
              .map((station) => DropdownMenuItem(
                    value: station.stationCode,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(station.stationName),
                        if (station.coordinatesText.isNotEmpty)
                          Text(
                            station.coordinatesText,
                            style: const TextStyle(
                              fontSize: 11,
                              color: Colors.grey,
                            ),
                          ),
                      ],
                    ),
                  ))
              .toList(),
          selectedItemBuilder: (context) => _stations
              .map((station) => Text(station.stationName))
              .toList(),
          onChanged: (value) {
            if (value != null) {
              final selectedStation = _stations.firstWhere(
                (s) => s.stationCode == value,
                orElse: () => _stations.first,
              );
              setState(() {
                _selectedFromStationCode = value;
                _selectedFromStationName = selectedStation.stationName;
              });

              // 追蹤出發站選擇
              FeatureAnalytics.trackFeatureUse(
                featureName: 'select_thsr_station',
                featureType: 'thsr',
                parameters: {
                  'station_type': 'from',
                  'station_name': selectedStation.stationName,
                },
              );
            }
          },
        ),
        const SizedBox(height: AppSpacing.md),

        // 抵達站選擇
        StyledDropdown<String>(
          value: _stations.isEmpty ? null : _selectedToStationCode,
          labelText: l10n.railwayToStation,
          prefixIcon: Icons.location_on,
          items: _stations
              .map((station) => DropdownMenuItem(
                    value: station.stationCode,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(station.stationName),
                        if (station.coordinatesText.isNotEmpty)
                          Text(
                            station.coordinatesText,
                            style: const TextStyle(
                              fontSize: 11,
                              color: Colors.grey,
                            ),
                          ),
                      ],
                    ),
                  ))
              .toList(),
          selectedItemBuilder: (context) => _stations
              .map((station) => Text(station.stationName))
              .toList(),
          onChanged: (value) {
            if (value != null) {
              final selectedStation = _stations.firstWhere(
                (s) => s.stationCode == value,
                orElse: () => _stations.first,
              );
              setState(() {
                _selectedToStationCode = value;
                _selectedToStationName = selectedStation.stationName;
              });

              // 追蹤抵達站選擇
              FeatureAnalytics.trackFeatureUse(
                featureName: 'select_thsr_station',
                featureType: 'thsr',
                parameters: {
                  'station_type': 'to',
                  'station_name': selectedStation.stationName,
                },
              );
            }
          },
        ),
        const SizedBox(height: AppSpacing.md),

        // 時間模式選擇 - 使用 SegmentedControl
        SegmentedControl(
          options: [l10n.railwayToday, l10n.railwayCustomTime],
          selectedIndex: _timeModeIndex,
          onChanged: (index) {
            setState(() {
              _timeModeIndex = index;
              if (index == 0) {
                _startTime = TimeOfDay.now();
                _endTime = const TimeOfDay(hour: 23, minute: 59);
              }
            });
          },
        ),
        const SizedBox(height: AppSpacing.md),

        // 日期選擇
        DatePickerButton(
          selectedDate: _selectedDate,
          label: l10n.railwayDepartureDate,
          onTap: () async {
            final date = await showDatePicker(
              context: context,
              initialDate: _selectedDate ?? DateTime.now(),
              firstDate: DateTime.now(),
              lastDate: DateTime.now().add(const Duration(days: 30)),
              locale: Localizations.localeOf(context),
              builder: (context, child) {
                return Theme(
                  data: Theme.of(context).copyWith(
                    colorScheme: Theme.of(context).colorScheme.copyWith(
                      primary: TransportColors.thsr,
                    ),
                  ),
                  child: child!,
                );
              },
            );
            if (date != null) {
              setState(() => _selectedDate = date);
            }
          },
        ),
        const SizedBox(height: AppSpacing.md),

        // 自訂時間模式下顯示起訖時間選擇器
        if (_timeModeIndex == 1)
          AnimatedCard(
            elevation: 1,
            color: TransportColors.railway.withValues(alpha: 0.05),
            padding: const EdgeInsets.all(AppSpacing.sm),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.access_time,
                        color: TransportColors.railway, size: 16),
                    const SizedBox(width: AppSpacing.xs),
                    Text(
                      l10n.railwayTimeRange,
                      style: AppTextStyles.labelMedium.copyWith(
                        color: TransportColors.railway,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.sm),
                Row(
                  children: [
                    // 起始時間
                    Expanded(
                      child: TimePickerButton(
                        selectedTime: _startTime,
                        label: l10n.railwayStart,
                        onTap: _selectStartTime,
                      ),
                    ),
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: AppSpacing.sm),
                      child: Icon(Icons.arrow_forward,
                          color: AppColors.onSurfaceLight, size: 16),
                    ),
                    // 結束時間
                    Expanded(
                      child: TimePickerButton(
                        selectedTime: _endTime,
                        label: l10n.railwayEnd,
                        onTap: _selectEndTime,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

        if (_timeModeIndex == 1) const SizedBox(height: AppSpacing.md),

        // 查詢按鈕
        SizedBox(
          height: 50,
          child: ElevatedButton.icon(
            onPressed: _searchTimetable,
            style: ElevatedButton.styleFrom(
              backgroundColor: TransportColors.thsr,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppRadius.medium),
              ),
            ),
            icon: const Icon(Icons.search),
            label: Text(
              l10n.thsrSearchButton,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSeatIndicator({
    required IconData icon,
    required String label,
    required bool available,
  }) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          icon,
          size: 16,
          color: available ? AppColors.success : AppColors.onSurfaceLight,
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: AppTextStyles.labelSmall.copyWith(
            color: available ? AppColors.success : AppColors.onSurfaceLight,
          ),
        ),
      ],
    );
  }
}
