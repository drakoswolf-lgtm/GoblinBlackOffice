import 'package:flutter/material.dart';

class AppTheme {
  static const Color _greenAccent = Color(0xFF4CAF50);

  static final ThemeData light = ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: _greenAccent),
    useMaterial3: true,
  );

  static final ThemeData dark = ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: _greenAccent,
      brightness: Brightness.dark,
    ),
    useMaterial3: true,
  );
}
