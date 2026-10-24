import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hwga/app/app.dart';
import 'package:hwga/core/api/api_client.dart';
import 'package:hwga/core/api/token_store.dart';

HwgaApp appWith(MockClient mock, {TokenStore? store}) => HwgaApp(
  apiClient: ApiClient(
    client: mock,
    baseUrl: 'http://127.0.0.1:8000',
    tokenProvider: () => (store ?? MemoryTokenStore()).read(),
  ),
  tokenStore: store ?? MemoryTokenStore(),
);

void main() {
  testWidgets('shell renders both checks in idle state', (tester) async {
    await tester.pumpWidget(
      appWith(MockClient((r) async => http.Response('{}', 200))),
    );
    expect(find.text('Backend connection'), findsOneWidget);
    expect(find.text('Authenticated request'), findsOneWidget);
    expect(find.text('No token saved'), findsOneWidget);
  });

  testWidgets('health check shows success state', (tester) async {
    await tester.pumpWidget(
      appWith(
        MockClient(
          (r) async => http.Response(jsonEncode({'status': 'ok'}), 200),
        ),
      ),
    );
    await tester.tap(find.text('Check'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Server reachable'), findsOneWidget);
  });

  testWidgets('health check shows safe error state', (tester) async {
    await tester.pumpWidget(
      appWith(
        MockClient(
          (r) async => http.Response(
            jsonEncode({'code': 'ERROR', 'message': 'down', 'details': {}}),
            500,
          ),
        ),
      ),
    );
    await tester.tap(find.text('Check'));
    await tester.pumpAndSettle();
    expect(find.text('down'), findsOneWidget);
    expect(find.byIcon(Icons.error_outline), findsWidgets);
  });

  testWidgets('verify without token shows prompt state', (tester) async {
    await tester.pumpWidget(
      appWith(MockClient((r) async => http.Response('{}', 200))),
    );
    await tester.tap(find.text('Verify'));
    await tester.pumpAndSettle();
    expect(find.text('Add a device token first'), findsOneWidget);
  });

  testWidgets('verify with token shows authenticated identity', (tester) async {
    final store = MemoryTokenStore();
    await store.write('tok');
    final mock = MockClient((r) async {
      if (r.url.path == '/me') {
        expect(r.headers['Authorization'], 'Bearer tok');
        return http.Response(
          jsonEncode({'user_id': 'aaaaaaaa-1111', 'timezone': 'Asia/Kolkata'}),
          200,
        );
      }
      return http.Response(jsonEncode({'status': 'ok'}), 200);
    });
    await tester.pumpWidget(appWith(mock, store: store));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Verify'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Authenticated as aaaaaaaa'), findsOneWidget);
  });
}
