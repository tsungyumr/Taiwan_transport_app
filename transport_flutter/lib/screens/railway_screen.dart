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

// 台鐵車種定義
enum TrainType {
  all,
  express,
  chuKuang,
  local,
  localFast,
  taroko,
  puyuma;

  String getDisplayName(AppLocalizations l10n) {
    switch (this) {
      case TrainType.all:
        return l10n.railwayTrainTypeAll;
      case TrainType.express:
        return l10n.railwayTrainTypeExpress;
      case TrainType.chuKuang:
        return l10n.railwayTrainTypeChuKuang;
      case TrainType.local:
        return l10n.railwayTrainTypeLocal;
      case TrainType.localFast:
        return l10n.railwayTrainTypeLocalFast;
      case TrainType.taroko:
        return l10n.railwayTrainTypeTaroko;
      case TrainType.puyuma:
        return l10n.railwayTrainTypePuyuma;
    }
  }

  String get searchKeyword {
    switch (this) {
      case TrainType.all:
        return '';
      case TrainType.express:
        return '自強';
      case TrainType.chuKuang:
        return '莒光';
      case TrainType.local:
        return '區間';
      case TrainType.localFast:
        return '區快';
      case TrainType.taroko:
        return '太魯閣';
      case TrainType.puyuma:
        return '普悠瑪';
    }
  }
}

class RailwayScreen extends StatefulWidget {
  final bool showAppBar;
  final bool isActive;

  const RailwayScreen({
    super.key,
    this.showAppBar = true,
    this.isActive = true,
  });

  @override
  State<RailwayScreen> createState() => _RailwayScreenState();
}

class _RailwayScreenState extends State<RailwayScreen> {
  final ApiService _apiService = ApiService();

  List<TrainStation> _stations = [];
  List<TrainTimeEntry> _timetable = [];
  List<TrainTimeEntry> _filteredTimetable = [];
  bool _isLoading = false;

  String? _selectedFromStationCode;
  String? _selectedFromStationName;
  String? _selectedToStationCode;
  String? _selectedToStationName;
  DateTime? _selectedDate;

  // 縣市篩選
  String? _selectedFromCity;
  String? _selectedToCity;

  // 時間選擇模式
  int _timeModeIndex = 0; // 0 = 當天, 1 = 自訂時間

  // 起訖時間
  TimeOfDay? _startTime;
  TimeOfDay? _endTime;

  // 搜尋條件區域展開狀態
  bool _isSearchPanelExpanded = true;

  // 車種篩選
  TrainType _selectedTrainType = TrainType.all;

  // 追蹤語言變化
  String? _currentLang;
  bool _isInitialized = false;

  // 取得所有縣市列表
  List<String> get _cities {
    final cities = _stations
        .where((s) => s.city != null && s.city!.isNotEmpty)
        .map((s) => s.city!)
        .toSet()
        .toList();
    cities.sort();
    return cities;
  }

  // 根據縣市取得站點列表
  List<TrainStation> _getStationsByCity(String? city) {
    if (city == null || city.isEmpty) {
      return _stations;
    }
    return _stations.where((s) => s.city == city).toList();
  }

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
  void didUpdateWidget(covariant RailwayScreen oldWidget) {
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
      return _formatTime(TimeOfDay.now());
    }
    // 自訂時間模式
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
    final stations = await _apiService.getRailwayStations(lang: lang);
    if (!mounted) return;
    setState(() {
      _stations = stations;
      _isLoading = false;
    });
  }

  Future<void> _searchTimetable() async {
    final l10n = AppLocalizations.of(context)!;

    if (_selectedFromStationName == null || _selectedToStationName == null) {
      _showErrorSnackBar(l10n.railwaySelectStationsError);
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
    final timetable = await _apiService.getRailwayTimetable(
      fromStation: _selectedFromStationName!,
      toStation: _selectedToStationName!,
      date: _selectedDate?.toIso8601String().split('T')[0],
      time: timeParam,
      lang: lang,
    );

    if (!mounted) return;
    setState(() {
      _timetable = timetable;
      _applyAllFilters(endTimeParam);
      _isLoading = false;
      // 搜尋後自動縮小搜尋條件區域
      _isSearchPanelExpanded = false;
    });

    // 追蹤搜尋事件
    FeatureAnalytics.trackSearch(
      searchType: 'tra_timetable',
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

  // 同時應用時間範圍和車種篩選
  void _applyAllFilters(String? endTimeParam) {
    _filteredTimetable = _timetable.where((entry) {
      // 車種篩選
      bool matchesTrainType = _selectedTrainType == TrainType.all ||
          entry.trainType.contains(_selectedTrainType.searchKeyword);

      // 時間範圍篩選（在前端本地處理）
      bool matchesTimeRange = true;
      if (_timeModeIndex == 1 && (_startTime != null || _endTime != null)) {
        final entryTime = _parseTime(entry.departureTime);
        if (entryTime != null) {
          if (_startTime != null) {
            final startMinutes = _startTime!.hour * 60 + _startTime!.minute;
            if (entryTime < startMinutes) matchesTimeRange = false;
          }
          if (_endTime != null && matchesTimeRange) {
            final endMinutes = _endTime!.hour * 60 + _endTime!.minute;
            if (entryTime > endMinutes) matchesTimeRange = false;
          }
        }
      }

      return matchesTrainType && matchesTimeRange;
    }).toList();
  }

  // 解析時間字串為分鐘數
  int? _parseTime(String timeStr) {
    try {
      final parts = timeStr.split(':');
      if (parts.length >= 2) {
        final hour = int.parse(parts[0]);
        final minute = int.parse(parts[1]);
        return hour * 60 + minute;
      }
    } catch (e) {
      // 解析時間失敗
    }
    return null;
  }

  void _applyTrainTypeFilter() {
    _applyAllFilters(null);
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
              title: Text(l10n.railwayTitle),
              backgroundColor: TransportColors.railway,
              foregroundColor: Colors.white,
              elevation: 0,
              flexibleSpace: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      TransportColors.railway,
                      TransportColors.railway.withOpacity(0.8),
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
              child: PulseLoading(color: TransportColors.railway),
            )
          : SafeArea(
              child: Column(
                children: [
                  // 可展開/縮小的搜尋條件區域
                  ExpandableSearchPanel(
                    isExpanded: _isSearchPanelExpanded,
                    onToggle: _toggleSearchPanel,
                    summaryText: _getSearchSummary(),
                    accentColor: TransportColors.railway,
                    title: l10n.railwaySearchConditions,
                    expandedContent: _buildSearchForm(),
                  ),

                  // 結果統計
                  if (_filteredTimetable.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(
                        left: AppSpacing.md,
                        right: AppSpacing.md,
                        bottom: AppSpacing.xs,
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.train, size: 16, color: AppColors.onSurfaceLight),
                          const SizedBox(width: AppSpacing.xs),
                          Text(
                            l10n.railwayTrainsFound(_filteredTimetable.length),
                            style: AppTextStyles.labelMedium.copyWith(
                              color: AppColors.onSurfaceLight,
                            ),
                          ),
                        ],
                      ),
                    ),

                  // 時刻表列表
                  Expanded(
                    child: _filteredTimetable.isEmpty
                      ? _isLoading
                          ? const Center(child: PulseLoading(color: TransportColors.railway))
                          : EmptyStateCard(
                              icon: Icons.train_outlined,
                              title: l10n.railwayEmptyTitle,
                              subtitle: l10n.railwayEmptySubtitle,
                            )
                      : ListView.builder(
                          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                          itemCount: _filteredTimetable.length,
                          itemBuilder: (context, index) {
                            final train = _filteredTimetable[index];
                            return TimetableCard(
                              trainNo: train.trainNo,
                              fromStation: train.departureStation,
                              toStation: train.arrivalStation,
                              departureTime: train.departureTime,
                              arrivalTime: train.arrivalTime,
                              duration: train.duration,
                              accentColor: _getTrainTypeColor(train.trainType),
                              trainType: train.trainType,
                              trailing: Icon(
                                train.transferable ? Icons.swap_horiz : Icons.block,
                                color: train.transferable ? AppColors.success : AppColors.onSurfaceLight,
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
    );
  }

  Widget _buildSearchForm() {
    final l10n = AppLocalizations.of(context)!;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
        // 出發縣市選擇
        StyledDropdown<String>(
          value: _selectedFromCity,
          labelText: l10n.railwayFromCity,
          prefixIcon: Icons.location_city,
          items: [
            DropdownMenuItem(
              value: null,
              child: Text(l10n.railwayAllCities),
            ),
            ..._cities.map((city) => DropdownMenuItem(
                  value: city,
                  child: Text(city),
                )),
          ],
          selectedItemBuilder: (context) => [
            Text(l10n.railwayAllCities),
            ..._cities.map((city) => Text(city)),
          ],
          onChanged: (value) {
            setState(() {
              _selectedFromCity = value;
              // 清除已選擇的站點
              _selectedFromStationCode = null;
              _selectedFromStationName = null;
            });
          },
        ),
        const SizedBox(height: AppSpacing.xs),

        // 出發站選擇
        StyledDropdown<String>(
          value: _getStationsByCity(_selectedFromCity).isEmpty
              ? null
              : _selectedFromStationCode,
          labelText: l10n.railwayFromStation,
          prefixIcon: Icons.train,
          items: _getStationsByCity(_selectedFromCity)
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
          selectedItemBuilder: (context) => _getStationsByCity(_selectedFromCity)
              .map((station) => Text(station.stationName))
              .toList(),
          onChanged: (value) {
            if (value != null) {
              final selectedStation = _getStationsByCity(_selectedFromCity)
                  .firstWhere(
                    (s) => s.stationCode == value,
                    orElse: () => _getStationsByCity(_selectedFromCity).first,
                  );
              setState(() {
                _selectedFromStationCode = value;
                _selectedFromStationName = selectedStation.stationName;
              });

              // 追蹤出發站選擇
              FeatureAnalytics.trackFeatureUse(
                featureName: 'select_tra_station',
                featureType: 'railway',
                parameters: {
                  'station_type': 'from',
                  'station_name': selectedStation.stationName,
                },
              );
            }
          },
        ),
        const SizedBox(height: AppSpacing.xs),

        // 抵達縣市選擇
        StyledDropdown<String>(
          value: _selectedToCity,
          labelText: l10n.railwayToCity,
          prefixIcon: Icons.location_city,
          items: [
            DropdownMenuItem(
              value: null,
              child: Text(l10n.railwayAllCities),
            ),
            ..._cities.map((city) => DropdownMenuItem(
                  value: city,
                  child: Text(city),
                )),
          ],
          selectedItemBuilder: (context) => [
            Text(l10n.railwayAllCities),
            ..._cities.map((city) => Text(city)),
          ],
          onChanged: (value) {
            setState(() {
              _selectedToCity = value;
              // 清除已選擇的站點
              _selectedToStationCode = null;
              _selectedToStationName = null;
            });
          },
        ),
        const SizedBox(height: AppSpacing.xs),

        // 抵達站選擇
        StyledDropdown<String>(
          value: _getStationsByCity(_selectedToCity).isEmpty
              ? null
              : _selectedToStationCode,
          labelText: l10n.railwayToStation,
          prefixIcon: Icons.location_on,
          items: _getStationsByCity(_selectedToCity)
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
          selectedItemBuilder: (context) => _getStationsByCity(_selectedToCity)
              .map((station) => Text(station.stationName))
              .toList(),
          onChanged: (value) {
            if (value != null) {
              final selectedStation = _getStationsByCity(_selectedToCity)
                  .firstWhere(
                    (s) => s.stationCode == value,
                    orElse: () => _getStationsByCity(_selectedToCity).first,
                  );
              setState(() {
                _selectedToStationCode = value;
                _selectedToStationName = selectedStation.stationName;
              });

              // 追蹤抵達站選擇
              FeatureAnalytics.trackFeatureUse(
                featureName: 'select_tra_station',
                featureType: 'railway',
                parameters: {
                  'station_type': 'to',
                  'station_name': selectedStation.stationName,
                },
              );
            }
          },
        ),
        const SizedBox(height: AppSpacing.sm),

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
        const SizedBox(height: AppSpacing.sm),

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
                      primary: TransportColors.railway,
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

        if (_timeModeIndex == 1) const SizedBox(height: AppSpacing.sm),

        // 車種篩選
        StyledDropdown<TrainType>(
          value: _selectedTrainType,
          labelText: l10n.railwayTrainTypeFilter,
          prefixIcon: Icons.filter_list,
          items: TrainType.values
              .map((type) => DropdownMenuItem(
                    value: type,
                    child: Text(type.getDisplayName(l10n)),
                  ))
              .toList(),
          onChanged: (value) {
            if (value != null) {
              setState(() {
                _selectedTrainType = value;
                _applyTrainTypeFilter();
              });

              // 追蹤車種篩選
              FeatureAnalytics.trackFilter(
                filterType: 'train_type',
                filterValue: value.name,
              );
            }
          },
        ),
        const SizedBox(height: AppSpacing.md),

        // 查詢按鈕
        SizedBox(
          height: 48,
          child: ElevatedButton(
            onPressed: _searchTimetable,
            style: ElevatedButton.styleFrom(
              backgroundColor: TransportColors.railway,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppRadius.medium),
              ),
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.search, size: 20),
                const SizedBox(width: AppSpacing.sm),
                Text(
                  l10n.railwaySearchButton,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    height: 1.2,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    ),
  );
}

  Color _getTrainTypeColor(String trainType) {
    if (trainType.contains('太魯閣') || trainType.contains('普悠瑪')) {
      return Colors.red; // 自強號（太魯閣、普悠瑪）
    } else if (trainType.contains('自強')) {
      return Colors.orange; // 自強號
    } else if (trainType.contains('莒光')) {
      return Colors.blue; // 莒光號
    } else if (trainType.contains('區間')) {
      return Colors.green; // 區間車
    }
    return Colors.grey;
  }
}
