import 'package:flutter/material.dart';

import '../core/api/api_client.dart';
import '../core/api/token_store.dart';
import '../core/config/app_config.dart';
import '../core/theme/app_theme.dart';
import '../features/connection/connection_screen.dart';

class HwgaApp extends StatelessWidget {
  const HwgaApp({super.key, ApiClient? apiClient, TokenStore? tokenStore})
    : _apiClient = apiClient,
      _tokenStore = tokenStore;

  final ApiClient? _apiClient;
  final TokenStore? _tokenStore;

  @override
  Widget build(BuildContext context) {
    final tokenStore = _tokenStore ?? SecureTokenStore();
    final apiClient =
        _apiClient ??
        ApiClient(tokenProvider: () => effectiveToken(tokenStore));
    return MaterialApp(
      title: 'HWGA',
      theme: buildAppTheme(Brightness.light),
      darkTheme: buildAppTheme(Brightness.dark),
      home: ConnectionScreen(apiClient: apiClient, tokenStore: tokenStore),
    );
  }
}

/// Stored token wins; the compile-time `HWGA_DEV_TOKEN` define is a dev-only
/// fallback so `flutter run` can prove auth without typing on the device.
Future<String?> effectiveToken(TokenStore store) async {
  final stored = await store.read();
  if (stored != null && stored.isNotEmpty) return stored;
  return AppConfig.devToken.isNotEmpty ? AppConfig.devToken : null;
}
