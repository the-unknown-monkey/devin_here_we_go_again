import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hwga/core/api/api_client.dart';

void main() {
  ApiClient clientWith(MockClient mock, {Future<String?> Function()? token}) =>
      ApiClient(
        client: mock,
        baseUrl: 'http://127.0.0.1:8000',
        tokenProvider: token,
      );

  test('health returns decoded body without auth header', () async {
    final mock = MockClient((req) async {
      expect(req.headers.containsKey('Authorization'), isFalse);
      return http.Response(jsonEncode({'status': 'ok'}), 200);
    });
    final res = await clientWith(mock).getHealth();
    expect(res['status'], 'ok');
  });

  test('me sends bearer token from provider', () async {
    final mock = MockClient((req) async {
      expect(req.headers['Authorization'], 'Bearer tok-123');
      return http.Response(
        jsonEncode({
          'user_id': 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
          'timezone': 'Asia/Kolkata',
        }),
        200,
      );
    });
    final res = await clientWith(mock, token: () async => 'tok-123').getMe();
    expect(res['timezone'], 'Asia/Kolkata');
  });

  test('401 maps to ApiException with ErrorResponse fields', () async {
    final mock = MockClient(
      (req) async => http.Response(
        jsonEncode({
          'code': 'UNAUTHORIZED',
          'message': 'Missing or invalid credentials',
          'details': {},
        }),
        401,
      ),
    );
    expect(
      () => clientWith(mock, token: () async => 'bad').getMe(),
      throwsA(
        isA<ApiException>()
            .having((e) => e.statusCode, 'statusCode', 401)
            .having((e) => e.error?.code, 'code', 'UNAUTHORIZED')
            .having((e) => e.isUnauthorized, 'isUnauthorized', isTrue),
      ),
    );
  });

  test('network error retries once then throws ApiException', () async {
    var calls = 0;
    final mock = MockClient((req) async {
      calls++;
      throw const SocketException('unreachable');
    });
    await expectLater(
      clientWith(mock).getHealth(),
      throwsA(isA<ApiException>()),
    );
    expect(calls, 2);
  });

  test('HTTP errors are not retried', () async {
    var calls = 0;
    final mock = MockClient((req) async {
      calls++;
      return http.Response(
        jsonEncode({'code': 'NOT_FOUND', 'message': 'nope', 'details': {}}),
        404,
      );
    });
    await expectLater(
      clientWith(mock).getHealth(),
      throwsA(isA<ApiException>()),
    );
    expect(calls, 1);
  });

  test('missing token throws before any request', () async {
    var calls = 0;
    final mock = MockClient((req) async {
      calls++;
      return http.Response('{}', 200);
    });
    await expectLater(
      clientWith(mock, token: () async => null).getMe(),
      throwsA(isA<ApiException>()),
    );
    expect(calls, 0);
  });
}
