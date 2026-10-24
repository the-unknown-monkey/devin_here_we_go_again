import 'package:flutter/material.dart';

/// V1 visual baseline (D24): Material 3, calm seed color, material_icons,
/// standard transitions. Text scaling and semantics are left to the
/// framework/system settings; touch targets are kept >= 48dp.
ThemeData buildAppTheme(Brightness brightness) {
  final scheme = ColorScheme.fromSeed(
    seedColor: const Color(0xFF356859),
    brightness: brightness,
  );
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    visualDensity: VisualDensity.standard,
    snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
    inputDecorationTheme: const InputDecorationTheme(
      border: OutlineInputBorder(),
    ),
  );
}
