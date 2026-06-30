import '../../../navigation/app_router.dart';
import 'package:flutter/material.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Goblin Black Office')),
      body: ListView(
        children: [
          ListTile(
            title: const Text('Ledgergut (Receipt Goblin)'),
            subtitle: const Text('First planned module'),
            onTap: () => Navigator.pushNamed(context, AppRouter.ledgergut),
          ),
          ListTile(
            title: const Text('Settings'),
            onTap: () => Navigator.pushNamed(context, AppRouter.settings),
          ),
        ],
      ),
    );
  }
}
