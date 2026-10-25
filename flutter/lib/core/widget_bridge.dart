import 'dart:async';
import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';

import '../app/app.dart' show effectiveToken;
import 'api/api_client.dart';
import 'api/token_store.dart';

/// App→widget bridge (V2-D02…V2-D05). On each app resume (and once at
/// startup) this pushes everything the native widgets cannot get on their
/// own into a private widget SharedPreferences file — token mirror, runtime
/// base URL, and the latest `/widget/state` JSON — then asks the native side
/// to re-render.
///
/// Best-effort by contract: every failure is swallowed because the widgets
/// have honest fallbacks (auth-required / no-data states) of their own.
class WidgetBridge with WidgetsBindingObserver {
  WidgetBridge({
    required ApiClient apiClient,
    required TokenStore tokenStore,
    MethodChannel? channel,
  }) : _apiClient = apiClient,
       _tokenStore = tokenStore,
       _channel = channel ?? _defaultChannel;

  static const _defaultChannel = MethodChannel('ai.hwga.hwga/widget');

  final ApiClient _apiClient;
  final TokenStore _tokenStore;
  final MethodChannel _channel;
  bool _attached = false;

  /// Register the lifecycle observer and push once. Idempotent.
  void attach() {
    if (_attached) return;
    _attached = true;
    WidgetsBinding.instance.addObserver(this);
    unawaited(syncToWidgets());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) unawaited(syncToWidgets());
  }

  /// Mirror token + base URL + freshest widget state into native prefs and
  /// trigger a widget refresh. Never throws.
  Future<void> syncToWidgets() async {
    String? token;
    String? stateJson;
    try {
      token = await effectiveToken(_tokenStore);
      if (token != null) {
        stateJson = jsonEncode(await _apiClient.getWidgetState());
      }
    } catch (_) {
      // No token / offline / backend down — widgets render their honest
      // fallback states; the mirror still updates what we do know.
    }
    try {
      await _channel.invokeMethod<void>('sync', {
        'token': token,
        'baseUrl': _apiClient.baseUrl,
        'stateJson': stateJson,
      });
    } on MissingPluginException {
      // Non-Android host or unit test without a mock — nothing to push to.
    }
  }

  /// The URI the app was cold-started with, if any (native forwards the
  /// launch intent's data string). Null off-Android or for normal launches.
  static Future<String?> launchUri({MethodChannel? channel}) async {
    try {
      return await (channel ?? _defaultChannel).invokeMethod<String>(
        'getLaunchUri',
      );
    } on MissingPluginException {
      return null;
    }
  }
}
