import 'package:flutter/material.dart';
import 'core/app_theme.dart';
import 'screens/onboarding/insta_login.dart';

void main() {
  runApp(const SocialMediaDecisionApp());
}

class SocialMediaDecisionApp extends StatelessWidget {
  const SocialMediaDecisionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Decision Assistant',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const InstaLoginScreen(),
    );
  }
}
