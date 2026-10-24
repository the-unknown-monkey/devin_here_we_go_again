import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hwga/core/api/api_client.dart';
import 'package:hwga/features/goals/goals_screen.dart';

Widget screenWith(MockClient mock) => MaterialApp(
  home: GoalsScreen(
    apiClient: ApiClient(
      client: mock,
      baseUrl: 'http://127.0.0.1:8000',
      tokenProvider: () async => 'tok',
    ),
  ),
);

Map<String, dynamic> goalJson(String id, String title, {int age = 0}) => {
  'id': id,
  'title': title,
  'status': 'ACTIVE',
  'created_at': DateTime.now().toUtc().toIso8601String(),
  'resolved_at': null,
  'age_days': age,
};

void main() {
  testWidgets('renders active goals with server-computed age', (tester) async {
    final mock = MockClient((req) async {
      if (req.url.path == '/goals') {
        return http.Response(
          jsonEncode([
            goalJson('g-1', 'Ship the thing', age: 0),
            goalJson('g-2', 'Stretch daily', age: 4),
          ]),
          200,
        );
      }
      return http.Response('{}', 404);
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    expect(find.text('2 of 3 active'), findsOneWidget);
    expect(find.text('Ship the thing'), findsOneWidget);
    expect(find.text('Started today'), findsOneWidget);
    expect(find.text('4d old'), findsOneWidget);
  });

  testWidgets('GOAL_CAP_REACHED shows clear typed message', (tester) async {
    final mock = MockClient((req) async {
      if (req.method == 'POST' && req.url.path == '/goals') {
        return http.Response(
          jsonEncode({
            'code': 'GOAL_CAP_REACHED',
            'message': 'cap',
            'details': {'active_goals': 3},
          }),
          409,
        );
      }
      if (req.url.path == '/goals') {
        return http.Response(
          jsonEncode([for (var i = 0; i < 3; i++) goalJson('g-$i', 'g$i')]),
          200,
        );
      }
      return http.Response('{}', 404);
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'one more');
    await tester.tap(find.text('Add'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));
    expect(find.textContaining('Three active goals'), findsOneWidget);
  });

  testWidgets('completing a goal calls the complete route', (tester) async {
    var completed = false;
    final mock = MockClient((req) async {
      if (req.method == 'POST' && req.url.path == '/goals/g-1/complete') {
        completed = true;
        return http.Response(
          jsonEncode(goalJson('g-1', 'done')..['status'] = 'COMPLETED'),
          200,
        );
      }
      if (req.url.path == '/goals') {
        return http.Response(jsonEncode([goalJson('g-1', 'done')]), 200);
      }
      return http.Response('{}', 404);
    });
    await tester.pumpWidget(screenWith(mock));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Complete'));
    await tester.pumpAndSettle();
    expect(completed, isTrue);
  });
}
