import 'package:flutter/material.dart';
import 'bus_screen.dart';
import 'railway_screen.dart';
import 'thsr_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('台灣交通時刻表'),
        centerTitle: true,
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 20),
            const Text(
              '選擇交通工具',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 30),
            _buildTransportCard(
              context,
              title: '大台北公車',
              subtitle: '查詢台北市、新北市公車路線',
              icon: Icons.directions_bus,
              color: Colors.green,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const BusScreen()),
              ),
            ),
            const SizedBox(height: 16),
            _buildTransportCard(
              context,
              title: '台鐵時刻表',
              subtitle: '查詢台灣鐵路各站時刻',
              icon: Icons.train,
              color: Colors.orange,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const RailwayScreen()),
              ),
            ),
            const SizedBox(height: 16),
            _buildTransportCard(
              context,
              title: '高鐵時刻表',
              subtitle: '查詢台灣高鐵時刻',
              icon: Icons.speed,
              color: Colors.red,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const THSRScreen()),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTransportCard(
    BuildContext context, {
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Row(
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, size: 32, color: color),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.arrow_forward_ios, color: Colors.grey[400]),
            ],
          ),
        ),
      ),
    );
  }
}
