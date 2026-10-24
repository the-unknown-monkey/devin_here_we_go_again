import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hwga/core/api/api_client.dart';
import 'package:hwga/features/recaps/receipt_screen.dart';

Widget screenWith(MockClient mock) => MaterialApp(
  home: ReceiptScreen(
    apiClient: ApiClient(
      client: mock,
      baseUrl: 'http://127.0.0.1:8000',
      tokenProvider: () async => 'tok',
    ),
    date: DateTime(2026, 10, 20),
  ),
);

Map<String, dynamic> recapJson({
  String status = 'GENERATED',
  List<Map<String, dynamic>> insights = const [],
  List<String> media = const [],
  String? directive,
}) => {
  'id': 'r-1',
  'user_id': 'u-1',
  'period_type': 'DAILY',
  'period_start': '2026-10-20',
  'period_end': '2026-10-20',
  'narrative': 'A gentle day with water and rest.',
  'insights': insights,
  'highlight_media_ids': media,
  'directive_for_next_cycle': directive,
  'source_recap_ids': [],
  'status': status,
  'created_at': '2026-10-20T18:30:00Z',
};

void main() {
  testWidgets('shows generated receipt with insights and directive', (
    tester,
  ) async {
    final mock = MockClient((req) async {
      if (req.method == 'GET' && req.url.path == '/recaps') {
        return http.Response(
          jsonEncode(
            recapJson(
              insights: [
                {
                  'text': 'You paused once.',
                  'evidence_event_ids': ['e-1'],
                },
              ],
              directive: 'Tomorrow, one small step.',
            ),
          ),
          200,
        );
      }
      return http.Response('{}', 404);
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    expect(find.text('A gentle day with water and rest.'), findsOneWidget);
    expect(find.text('Receipt'), findsOneWidget);
    expect(find.text('You paused once.'), findsOneWidget);
    expect(find.text('Tomorrow, one small step.'), findsOneWidget);
  });

  testWidgets('labels fallback receipts honestly', (tester) async {
    final mock = MockClient((req) async {
      return http.Response(jsonEncode(recapJson(status: 'FALLBACK')), 200);
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    expect(find.text('Fact receipt'), findsOneWidget);
    expect(find.text('made from your logged facts'), findsOneWidget);
  });

  testWidgets('empty day state is honest, not shaming', (tester) async {
    final mock = MockClient((req) async {
      return http.Response(
        jsonEncode({
          'code': 'NOT_FOUND',
          'message': 'Not found',
          'details': {},
        }),
        404,
      );
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    expect(find.textContaining('No receipt for this day'), findsOneWidget);
    expect(find.textContaining('lazy'), findsNothing);
  });

  testWidgets('error state offers retry', (tester) async {
    var calls = 0;
    final mock = MockClient((req) async {
      calls++;
      return http.Response(
        '{"code":"ERROR","message":"boom","details":{}}',
        500,
      );
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    expect(find.text('Retry'), findsOneWidget);
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(calls, greaterThan(1));
  });

  testWidgets('highlight media fetched by authenticated id', (tester) async {
    // Minimal valid PNG header — only existence matters for the tile.
    final png = base64Decode(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
    );
    final mock = MockClient((req) async {
      if (req.url.path == '/recaps') {
        return http.Response(jsonEncode(recapJson(media: ['m-1'])), 200);
      }
      if (req.url.path == '/media/m-1') {
        expect(req.headers['Authorization'], 'Bearer tok');
        return http.Response.bytes(
          png,
          200,
          headers: {'content-type': 'image/png'},
        );
      }
      return http.Response('{}', 404);
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    expect(find.text('Moments'), findsOneWidget);
    expect(find.byType(Image), findsOneWidget);
  });
}
