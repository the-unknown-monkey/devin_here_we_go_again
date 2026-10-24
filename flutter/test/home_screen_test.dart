import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hwga/core/api/api_client.dart';
import 'package:hwga/features/home/home_screen.dart';

Widget screenWith(MockClient mock) => MaterialApp(
  home: HomeScreen(
    apiClient: ApiClient(
      client: mock,
      baseUrl: 'http://127.0.0.1:8000',
      tokenProvider: () async => 'tok',
    ),
  ),
);

void main() {
  Future<http.Response> Function(http.Request) baseMock({
    Map<String, dynamic>? mode,
  }) => (req) async {
    switch ('${req.method} ${req.url.path}') {
      case 'GET /mode':
        return http.Response(
          jsonEncode(mode ?? {'current': null, 'intervals': []}),
          200,
        );
      case 'GET /timeline':
        return http.Response(jsonEncode({'events': [], 'media': []}), 200);
      case 'GET /goals':
        return http.Response(jsonEncode([]), 200);
      case 'POST /events':
        final body = jsonDecode(req.body) as Map<String, dynamic>;
        return http.Response(
          jsonEncode({
            'id': 'e-1',
            'type': body['type'],
            'kind': body['kind'],
            'mode': body['mode'],
            'occurred_at': DateTime.now().toUtc().toIso8601String(),
            'idempotency_key': body['idempotency_key'],
          }),
          201,
        );
      case 'POST /mode':
        final body = jsonDecode(req.body) as Map<String, dynamic>;
        return http.Response(
          jsonEncode({
            'event': {
              'id': 'e-2',
              'type': 'MODE_TRANSITION',
              'kind': null,
              'mode': body['mode'],
              'occurred_at': DateTime.now().toUtc().toIso8601String(),
              'idempotency_key': body['idempotency_key'],
            },
            'current': {
              'mode': body['mode'],
              'started_at': DateTime.now().toUtc().toIso8601String(),
              'ended_at': null,
              'duration_min': 0,
            },
          }),
          200,
        );
      default:
        return http.Response('{}', 404);
    }
  };

  testWidgets('renders sections and honest empty state', (tester) async {
    await tester.pumpWidget(screenWith(MockClient(baseMock())));
    await tester.pumpAndSettle();
    expect(find.text('Baselines'), findsOneWidget);
    expect(find.text('Timeline'), findsOneWidget);
    expect(find.text('No mode set'), findsOneWidget);
    expect(find.text('Nothing logged yet today.'), findsOneWidget);
  });

  testWidgets('confirmation tap posts event with kind and idempotency key', (
    tester,
  ) async {
    Map<String, dynamic>? sent;
    final mock = MockClient((req) async {
      if (req.method == 'POST' && req.url.path == '/events') {
        sent = jsonDecode(req.body) as Map<String, dynamic>;
      }
      return baseMock()(req);
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Water'));
    await tester.pumpAndSettle();
    expect(sent?['type'], 'CONFIRMATION');
    expect(sent?['kind'], 'WATER');
    expect((sent?['idempotency_key'] as String).isNotEmpty, isTrue);
  });

  testWidgets('mode switch posts the other mode', (tester) async {
    String? postedMode;
    final mock = MockClient((req) async {
      if (req.method == 'POST' && req.url.path == '/mode') {
        postedMode = (jsonDecode(req.body) as Map)['mode'] as String;
      }
      return baseMock(
        mode: {
          'current': {
            'mode': 'LOCKED_IN',
            'started_at': DateTime.now().toUtc().toIso8601String(),
            'ended_at': null,
            'duration_min': 25,
          },
          'intervals': [],
        },
      )(req);
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    expect(find.text('Locked in'), findsOneWidget);
    expect(find.text('For 25m'), findsOneWidget);
    await tester.tap(find.text('Switch to Rest & fun'));
    await tester.pumpAndSettle();
    expect(postedMode, 'PURE_FUN_RECOVERY');
  });

  testWidgets('failed save shows error and does not claim success', (
    tester,
  ) async {
    final mock = MockClient((req) async {
      if (req.method == 'POST' && req.url.path == '/events') {
        return http.Response(
          jsonEncode({
            'code': 'ERROR',
            'message': 'save failed',
            'details': {},
          }),
          500,
        );
      }
      return baseMock()(req);
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Walk'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));
    expect(find.text('save failed'), findsOneWidget);
    expect(find.text('Nothing logged yet today.'), findsOneWidget);
  });
}
