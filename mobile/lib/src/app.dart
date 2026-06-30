import 'navigation/app_router.dart';
import 'theme/app_theme.dart';
import 'package:flutter/material.dart';

class GoblinBlackOfficeApp extends StatelessWidget {
  const GoblinBlackOfficeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Goblin Black Office',
      themeMode: ThemeMode.dark,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      initialRoute: AppRouter.dashboard,
      onGenerateRoute: AppRouter.onGenerateRoute,
    );
  }
}
