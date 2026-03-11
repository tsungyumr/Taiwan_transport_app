import 'package:flutter/material.dart';
import '../main.dart';
import '../ui_theme.dart';
import '../widgets/animated_card.dart';
import '../widgets/loading_animations.dart';
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
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.onPrimary,
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
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 20),
            FadeInAnimation(
              child: Container(
                padding: const EdgeInsets.all(AppSpacing.lg),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      AppColors.primary.withOpacity(0.1),
                      AppColors.secondary.withOpacity(0.05),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(AppRadius.large),
                ),
                child: Column(
                  children: [
                    Icon(
                      Icons.emoji_transportation,
                      size: 48,
                      color: AppColors.primaryDark,
                    ),
                    const SizedBox(height: AppSpacing.md),
                    Text(
                      '選擇縣市公車',
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 30),
            FadeInAnimation(
              delay: const Duration(milliseconds: 100),
              child: TransportCard(
                title: '大台北公車',
                subtitle: '查詢台北市、新北市公車路線',
                icon: Icons.directions_bus,
                color: TransportColors.bus,
                onTap: () => Navigator.push(
                  context,
                  SlidePageRoute(builder: (_) => const BusScreen()),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
