import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:taiwan_transport_app/screens/home_screen.dart';
import 'providers/bus_provider.dart';
import 'screens/bus_list_screen.dart';

void main() {
  runApp(const TaiwanTransportApp());
}

class TaiwanTransportApp extends StatelessWidget {
  const TaiwanTransportApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '台灣交通時刻表',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
