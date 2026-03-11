import 'package:flutter/material.dart';
import '../main.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/animated_card.dart';
import '../widgets/expandable_search_panel.dart';
import '../widgets/loading_animations.dart';
import '../widgets/styled_inputs.dart';
import '../ui_theme.dart';

class THSRScreen extends StatefulWidget {
  final bool showAppBar;

  const THSRScreen({super.key, this.showAppBar = true});

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

  @override
  void initState() {
    super.initState();
    _loadStations();
    // 預設當天時間
    _startTime = TimeOfDay.now();
    _endTime = const TimeOfDay(hour: 23, minute: 59);
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
    final fromStation = _selectedFromStationName ?? '請選擇出發站';
    final toStation = _selectedToStationName ?? '請選擇抵達站';
    final date = _selectedDate != null
        ? '${_selectedDate!.year}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}'
        : '今天';
    final timeRange = _timeModeIndex == 1 && (_startTime != null || _endTime != null)
        ? '${_formatTime(_startTime)} - ${_formatTime(_endTime)}'
        : '全天';
    return '$fromStation → $toStation | $date | $timeRange';
  }

  Future<void> _loadStations() async {
    setState(() => _isLoading = true);
    final stations = await _apiService.getTHSRStations();
    if (!mounted) return;
    setState(() {
      _stations = stations;
      _isLoading = false;
    });
  }

  Future<void> _searchTimetable() async {
    if (_selectedFromStationName == null || _selectedToStationName == null) {
      _showErrorSnackBar('請選擇出發站與抵達站');
      return;
    }

    setState(() => _isLoading = true);

    // 準備時間參數
    final String? timeParam = _getTimeRangeForApi();
    final String? endTimeParam =
        (_timeModeIndex == 1 && _endTime != null) ? _formatTime(_endTime) : null;

    // TDX API 使用站名（如「台北」）查詢時刻表
    final timetable = await _apiService.getTHSRTimetable(
      fromStation: _selectedFromStationName!,
      toStation: _selectedToStationName!,
      date: _selectedDate?.toIso8601String().split('T')[0],
      time: timeParam,
      endTime: endTimeParam,
    );

    if (!mounted) return;
    setState(() {
      _timetable = timetable;
      _isLoading = false;
      // 搜尋後自動縮小搜尋條件區域
      _isSearchPanelExpanded = false;
    });
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
    return Scaffold(
      appBar: widget.showAppBar
          ? AppBar(
              title: const Text('台灣高鐵'),
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
                  title: '搜尋條件',
                  expandedContent: _buildSearchForm(),
                ),

                // 結果統計
                if (_timetable.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                    child: Row(
                      children: [
                        Icon(Icons.speed, size: 16, color: AppColors.onSurfaceLight),
                        const SizedBox(width: AppSpacing.xs),
                        Text(
                          '找到 ${_timetable.length} 班次',
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
                          : const EmptyStateCard(
                              icon: Icons.speed_outlined,
                              title: '請選擇站點並查詢時刻表',
                              subtitle: '選擇出發站與抵達站，查看高鐵班次資訊',
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
                              trainType: '高鐵 ',
                              extras: [
                                Row(
                                  children: [
                                    _buildSeatIndicator(
                                      icon: Icons.business,
                                      label: '商務',
                                      available: train.businessSeatAvailable,
                                    ),
                                    const SizedBox(width: AppSpacing.md),
                                    _buildSeatIndicator(
                                      icon: Icons.event_seat,
                                      label: '標準',
                                      available: train.standardSeatAvailable,
                                    ),
                                    const SizedBox(width: AppSpacing.md),
                                    _buildSeatIndicator(
                                      icon: Icons.chair,
                                      label: '自由',
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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // 出發站選擇
        StyledDropdown<String>(
          value: _stations.isEmpty ? null : _selectedFromStationCode,
          labelText: '出發站',
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
            }
          },
        ),
        const SizedBox(height: AppSpacing.md),

        // 抵達站選擇
        StyledDropdown<String>(
          value: _stations.isEmpty ? null : _selectedToStationCode,
          labelText: '抵達站',
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
            }
          },
        ),
        const SizedBox(height: AppSpacing.md),

        // 時間模式選擇 - 使用 SegmentedControl
        SegmentedControl(
          options: const ['當天', '自訂時間'],
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
          label: '出發日期',
          onTap: () async {
            final date = await showDatePicker(
              context: context,
              initialDate: _selectedDate ?? DateTime.now(),
              firstDate: DateTime.now(),
              lastDate: DateTime.now().add(const Duration(days: 30)),
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
                    Icon(Icons.access_time,
                        color: TransportColors.railway, size: 16),
                    const SizedBox(width: AppSpacing.xs),
                    Text(
                      '時間範圍',
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
                        label: '起始',
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
                        label: '結束',
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
            label: const Text(
              '查詢時刻表',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
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
