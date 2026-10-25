import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hwga/core/api/api_client.dart';
import 'package:hwga/core/api/token_store.dart';
import 'package:hwga/core/widget_bridge.dart';
import 'package:hwga/features/auth/token_screen.dart';
import 'package:hwga/features/connection/connection_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const channel = MethodChannel('ai.hwga.hwga/widget');

  void mockChannel(void Function(MethodCall) onCall) {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          onCall(call);
          return call.method == 'getLaunchUri' ? 'hwga://auth' : null;
        });
  }

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  group('WidgetBridge.syncToWidgets', () {
    test('pushes token, base URL and widget state JSON', () async {
      final calls = <MethodCall>[];
      mockChannel(calls.add);

      final store = MemoryTokenStore()..write('tok-abc');
      const stateBody = {
        'generated_at': '2026-10-25T10:00:00Z',
        'today_confirmations': {'WATER': 2},
        'quiet_moments_today': 1,
      };
      var stateRequested = false;
      final client = ApiClient(
        client: MockClient((req) async {
          if (req.url.path == '/widget/state') {
            stateRequested = true;
            expect(req.headers['Authorization'], 'Bearer tok-abc');
            return http.Response(jsonEncode(stateBody), 200);
          }
          return http.Response('{}', 404);
        }),
        baseUrl: 'http://127.0.0.1:8000',
        tokenProvider: store.read,
      );

      await WidgetBridge(
        apiClient: client,
        tokenStore: store,
        channel: channel,
      ).syncToWidgets();

      expect(stateRequested, isTrue);
      expect(calls.single.method, 'sync');
      expect(calls.single.arguments['token'], 'tok-abc');
      expect(calls.single.arguments['baseUrl'], 'http://127.0.0.1:8000');
      expect(
        jsonDecode(calls.single.arguments['stateJson'] as String),
        stateBody,
      );
    });

    test('still syncs honestly when there is no token', () async {
      final calls = <MethodCall>[];
      mockChannel(calls.add);

      var stateRequested = false;
      final store = MemoryTokenStore();
      final client = ApiClient(
        client: MockClient((req) async {
          stateRequested = true;
          return http.Response('{}', 401);
        }),
        baseUrl: 'http://127.0.0.1:8000',
        tokenProvider: store.read,
      );

      await WidgetBridge(
        apiClient: client,
        tokenStore: store,
        channel: channel,
      ).syncToWidgets();

      expect(stateRequested, isFalse);
      expect(calls.single.arguments['token'], isNull);
      expect(calls.single.arguments['stateJson'], isNull);
    });

    test('swallows backend errors and still pushes the mirror', () async {
      final calls = <MethodCall>[];
      mockChannel(calls.add);

      final store = MemoryTokenStore()..write('tok-abc');
      final client = ApiClient(
        client: MockClient((req) async => throw http.ClientException('down')),
        baseUrl: 'http://127.0.0.1:8000',
        tokenProvider: store.read,
      );

      await WidgetBridge(
        apiClient: client,
        tokenStore: store,
        channel: channel,
      ).syncToWidgets();

      expect(calls.single.arguments['token'], 'tok-abc');
      expect(calls.single.arguments['stateJson'], isNull);
    });
  });

  group('hwga://auth launch routing', () {
    testWidgets('no token + auth deep-link lands on TokenScreen', (
      tester,
    ) async {
      final store = MemoryTokenStore();
      final client = ApiClient(
        client: MockClient(
          (req) async => http.Response(jsonEncode({'status': 'ok'}), 200),
        ),
        baseUrl: 'http://127.0.0.1:8000',
        tokenProvider: store.read,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: ConnectionScreen(
            apiClient: client,
            tokenStore: store,
            launchUriProvider: () async => 'hwga://auth',
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(TokenScreen), findsOneWidget);
    });

    testWidgets('saved token ignores the auth deep-link', (tester) async {
      final store = MemoryTokenStore()..write('tok-abc');
      final client = ApiClient(
        client: MockClient(
          (req) async => http.Response(jsonEncode({'status': 'ok'}), 200),
        ),
        baseUrl: 'http://127.0.0.1:8000',
        tokenProvider: store.read,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: ConnectionScreen(
            apiClient: client,
            tokenStore: store,
            launchUriProvider: () async => 'hwga://auth',
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(TokenScreen), findsNothing);
    });
  });
}
