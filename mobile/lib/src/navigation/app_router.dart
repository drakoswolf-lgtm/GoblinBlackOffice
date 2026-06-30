import '../features/dashboard/presentation/dashboard_screen.dart';
import '../features/ledgergut/presentation/ledgergut_screen.dart';
import '../features/settings/presentation/settings_screen.dart';
import 'package:flutter/material.dart';

class AppRouter {
  static const String dashboard = '/';
  static const String ledgergut = '/ledgergut';
  static const String settings = '/settings';

  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case ledgergut:
        return MaterialPageRoute<void>(
          builder: (_) => const LedgergutScreen(),
          settings: settings,
        );
      case AppRouter.settings:
        return MaterialPageRoute<void>(
          builder: (_) => const SettingsScreen(),
          settings: settings,
        );
      case dashboard:
      default:
        return MaterialPageRoute<void>(
          builder: (_) => const DashboardScreen(),
          settings: settings,
        );
    }
  }
}
