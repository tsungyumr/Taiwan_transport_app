import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class THSRScreen extends StatefulWidget {
  const THSRScreen({super.key});

  @override
  State<THSRScreen> createState() => _THSRScreenState();
}

class _THSRScreenState extends State<THSRScreen> {
  final ApiService _apiService = ApiService();
  
  List<TrainStation> _stations = [];
  List<THSRTrainEntry> _timetable = [];
  bool _isLoading = false;
  
  String? _selectedFromStation;
  String? _selectedToStation;
  DateTime? _selectedDate;

  @override
  void initState() {
    super.initState();
    _loadStations();
  }

  Future<void> _loadStations() async {
    setState(() => _isLoading = true);
    final stations = await _apiService.getTHSRStations();
    setState(() {
      _stations = stations;
      _isLoading = false;
    });
  }

  Future<void> _searchTimetable() async {
    if (_selectedFromStation == null || _selectedToStation == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('請選擇出發站與抵達站')),
      );
      return;
    }

    setState(() => _isLoading = true);
    
    final timetable = await _apiService.getTHSRTimetable(
      fromStation: _selectedFromStation!,
      toStation: _selectedToStation!,
      date: _selectedDate?.toIso8601String().split('T')[0],
    );
    
    setState(() {
      _timetable = timetable;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('台灣高鐵'),
        backgroundColor: Colors.red,
        foregroundColor: Colors.white,
      ),
      body: _isLoading && _stations.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  // 出發站選擇
                  DropdownButtonFormField<String>(
                    value: _selectedFromStation,
                    decoration: const InputDecoration(
                      labelText: '出發站',
                      prefixIcon: Icon(Icons.train),
                      border: OutlineInputBorder(),
                    ),
                    items: _stations.map((station) => DropdownMenuItem(
                      value: station.stationCode,
                      child: Text(station.stationName),
                    )).toList(),
                    onChanged: (value) => setState(() => _selectedFromStation = value),
                  ),
                  const SizedBox(height: 16),
                  
                  // 抵達站選擇
                  DropdownButtonFormField<String>(
                    value: _selectedToStation,
                    decoration: const InputDecoration(
                      labelText: '抵達站',
                      prefixIcon: Icon(Icons.location_on),
                      border: OutlineInputBorder(),
                    ),
                    items: _stations.map((station) => DropdownMenuItem(
                      value: station.stationCode,
                      child: Text(station.stationName),
                    )).toList(),
                    onChanged: (value) => setState(() => _selectedToStation = value),
                  ),
                  const SizedBox(height: 16),
                  
                  // 日期選擇
                  ElevatedButton.icon(
                    onPressed: () async {
                      final date = await showDatePicker(
                        context: context,
                        initialDate: DateTime.now(),
                        firstDate: DateTime.now(),
                        lastDate: DateTime.now().add(const Duration(days: 30)),
                      );
                      if (date != null) {
                        setState(() => _selectedDate = date);
                      }
                    },
                    icon: const Icon(Icons.calendar_today),
                    label: Text(_selectedDate == null
                        ? '選擇日期'
                        : '${_selectedDate!.year}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}'),
                  ),
                  const SizedBox(height: 16),
                  
                  // 查詢按鈕
                  ElevatedButton(
                    onPressed: _searchTimetable,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    child: const Text('查詢時刻表', style: TextStyle(fontSize: 16)),
                  ),
                  
                  const SizedBox(height: 20),
                  
                  Expanded(
                    child: _timetable.isEmpty
                        ? const Center(child: Text('請選擇站點並查詢時刻表'))
                        : ListView.builder(
                            itemCount: _timetable.length,
                            itemBuilder: (context, index) {
                              final entry = _timetable[index];
                              return Card(
                                margin: const EdgeInsets.symmetric(vertical: 4),
                                child: ListTile(
                                  leading: const CircleAvatar(
                                    backgroundColor: Colors.red,
                                    child: Icon(Icons.speed, color: Colors.white, size: 20),
                                  ),
                                  title: Text('車次 ${entry.trainNo}'),
                                  subtitle: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text('${entry.departureStation} → ${entry.arrivalStation}'),
                                      Text('時間: ${entry.departureTime} - ${entry.arrivalTime} (${entry.duration})'),
                                      Row(
                                        children: [
                                          Icon(Icons.business, size: 16, color: entry.businessSeatAvailable ? Colors.green : Colors.grey),
                                          const SizedBox(width: 8),
                                          Icon(Icons.event_seat, size: 16, color: entry.standardSeatAvailable ? Colors.green : Colors.grey),
                                          const SizedBox(width: 8),
                                          Icon(Icons.chair, size: 16, color: entry.freeSeatAvailable ? Colors.green : Colors.grey),
                                        ],
                                      ),
                                    ],
                                  ),
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
}
