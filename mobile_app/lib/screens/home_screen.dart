import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key, required this.onOpenLedgergut});

  final VoidCallback onOpenLedgergut;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Goblin Black Office')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Card(
          child: InkWell(
            onTap: onOpenLedgergut,
            child: const Padding(
              padding: EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Ledgergut (GBO-001)',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  Text('Finance Division · Receipt Goblin'),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
