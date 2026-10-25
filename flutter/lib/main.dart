import 'package:flutter/material.dart';

import 'app/app.dart';
import 'core/api/api_client.dart';
import 'core/api/token_store.dart';
import 'core/widget_bridge.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final tokenStore = SecureTokenStore();
  final apiClient = ApiClient(tokenProvider: () => effectiveToken(tokenStore));
  // V2-D02/D03: app-side push of token mirror, base URL and widget state.
  WidgetBridge(apiClient: apiClient, tokenStore: tokenStore).attach();
  runApp(HwgaApp(apiClient: apiClient, tokenStore: tokenStore));
}
