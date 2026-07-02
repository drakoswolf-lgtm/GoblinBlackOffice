import 'package:flutter/material.dart';

import 'models/receipt_draft.dart';
import 'screens/capture_screen.dart';
import 'screens/home_screen.dart';
import 'screens/review_screen.dart';
import 'screens/success_screen.dart';

void main() {
  runApp(const LedgergutApp());
}

enum AppStep { home, capture, review, success }

class LedgergutApp extends StatefulWidget {
  const LedgergutApp({super.key});

  @override
  State<LedgergutApp> createState() => _LedgergutAppState();
}

class _LedgergutAppState extends State<LedgergutApp> {
  AppStep _step = AppStep.home;
  ReceiptDraft? _draft;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Goblin Black Office',
      theme: ThemeData(
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2ECC71),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: _buildCurrentScreen(),
    );
  }

  Widget _buildCurrentScreen() {
    switch (_step) {
      case AppStep.home:
        return HomeScreen(onOpenLedgergut: () => setState(() => _step = AppStep.capture));
      case AppStep.capture:
        return CaptureScreen(
          onBack: () => setState(() => _step = AppStep.home),
          onDraftReady: (draft) {
            setState(() {
              _draft = draft;
              _step = AppStep.review;
            });
          },
        );
      case AppStep.review:
        final draft = _draft;
        if (draft == null) {
          return HomeScreen(onOpenLedgergut: () => setState(() => _step = AppStep.capture));
        }
        return ReviewScreen(
          draft: draft,
          onBack: () => setState(() => _step = AppStep.capture),
          onGenerateSuccess: (updated) {
            setState(() {
              _draft = updated;
              _step = AppStep.success;
            });
          },
        );
      case AppStep.success:
        final draft = _draft;
        if (draft == null) {
          return HomeScreen(onOpenLedgergut: () => setState(() => _step = AppStep.capture));
        }
        return SuccessScreen(
          draft: draft,
          onDone: () {
            setState(() {
              _draft = null;
              _step = AppStep.home;
            });
          },
        );
    }
  }
}
