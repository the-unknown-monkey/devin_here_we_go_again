import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hwga/core/api/api_client.dart';
import 'package:hwga/features/recaps/chronology_screen.dart';
import 'package:hwga/features/recaps/directive_card.dart';

ApiClient clientWith(MockClient mock) => ApiClient(
  client: mock,
  baseUrl: 'http://127.0.0.1:8000',
  tokenProvider: () async => 'tok',
);

Map<String, dynamic> directiveJson({String status = 'GENERATED'}) => {
  'id': 'd-1',
  'user_id': 'u-1',
  'for_date': '2026-10-25',
  'content': 'One small step on the demo — only if it feels right.',
  'source_recap_id': 'r-1',
  'status': status,
  'shown_at': '2026-10-25T01:30:00Z',
};

Map<String, dynamic> weeklyJson({
  String status = 'GENERATED',
  int sources = 2,
  List<String> media = const [],
}) => {
  'id': 'w-1',
  'user_id': 'u-1',
  'period_type': 'WEEKLY',
  'period_start': '2026-10-19',
  'period_end': '2026-10-25',
  'narrative': 'A week with 2 saved receipts.',
  'insights': [
    {
      'text': 'Receipts kept the week visible.',
      'evidence_event_ids': ['e-1'],
    },
  ],
  'highlight_media_ids': media,
  'directive_for_next_cycle': 'Next week, one small step.',
  'source_recap_ids': List.generate(sources, (i) => 'r-$i'),
  'status': status,
  'created_at': '2026-10-25T20:00:00Z',
};

void main() {
  group('DirectiveCard', () {
    testWidgets('shows generated directive content', (tester) async {
      final mock = MockClient((req) async {
        expect(req.headers['Authorization'], 'Bearer tok');
        return http.Response.bytes(
          utf8.encode(jsonEncode(directiveJson())),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });
      await tester.pumpWidget(
        MaterialApp(home: DirectiveCard(apiClient: clientWith(mock))),
      );
      await tester.pumpAndSettle();
      expect(
        find.text('One small step on the demo — only if it feels right.'),
        findsOneWidget,
      );
      expect(find.text('Today'), findsOneWidget);
    });

    testWidgets('labels fallback honestly', (tester) async {
      final mock = MockClient((req) async {
        return http.Response.bytes(
          utf8.encode(jsonEncode(directiveJson(status: 'FALLBACK'))),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });
      await tester.pumpWidget(
        MaterialApp(home: DirectiveCard(apiClient: clientWith(mock))),
      );
      await tester.pumpAndSettle();
      expect(find.text('A simple nudge'), findsOneWidget);
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
      await tester.pumpWidget(
        MaterialApp(home: DirectiveCard(apiClient: clientWith(mock))),
      );
      await tester.pumpAndSettle();
      expect(find.text('Retry'), findsOneWidget);
      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();
      expect(calls, greaterThan(1));
    });
  });

  group('ChronologyScreen', () {
    Widget screenWith(MockClient mock) =>
        MaterialApp(home: ChronologyScreen(apiClient: clientWith(mock)));

    testWidgets('shows weekly recap with day links', (tester) async {
      final mock = MockClient((req) async {
        if (req.url.path == '/recaps') {
          expect(req.url.queryParameters['period'], 'WEEKLY');
          return http.Response.bytes(
            utf8.encode(jsonEncode(weeklyJson())),
            200,
          );
        }
        return http.Response('{}', 404);
      });
      await tester.pumpWidget(screenWith(mock));
      await tester.pumpAndSettle();
      expect(find.text('Weekly recap'), findsOneWidget);
      expect(find.text('A week with 2 saved receipts.'), findsOneWidget);
      expect(find.textContaining('2 receipts'), findsOneWidget);
      expect(find.text('From your receipts'), findsOneWidget);
      expect(find.text('Days'), findsOneWidget);
      expect(find.text('10-19'), findsOneWidget); // Monday chip
      expect(find.text('10-25'), findsOneWidget); // Sunday chip
      expect(find.text('Next week, one small step.'), findsOneWidget);
    });

    testWidgets('labels fallback weekly honestly', (tester) async {
      final mock = MockClient((req) async {
        return http.Response.bytes(
          utf8.encode(jsonEncode(weeklyJson(status: 'FALLBACK'))),
          200,
        );
      });
      await tester.pumpWidget(screenWith(mock));
      await tester.pumpAndSettle();
      expect(find.text('Fact recap'), findsOneWidget);
    });

    testWidgets('empty weekly state is honest', (tester) async {
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
      expect(find.textContaining('No weekly recap yet'), findsOneWidget);
    });
  });
}
