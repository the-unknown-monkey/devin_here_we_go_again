import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import 'api_error.dart';

/// Thrown for every failure path so callers render one safe error state.
class ApiException implements Exception {
  const ApiException({
    this.statusCode,
    this.error,
    required this.message,
    this.isNetwork = false,
  });

  /// HTTP status for server answers; null for network/timeout failures.
  final int? statusCode;
  final ApiError? error;
  final String message;
  final bool isNetwork;

  bool get isUnauthorized => statusCode == 401;

  String get displayMessage => error?.message ?? message;
}

/// Typed client for the HWGA FastAPI backend.
///
/// - Bearer token per D07 on every route except `GET /health`.
/// - Timeout-bounded; safe retry policy: idempotent GETs retry once on
///   network/timeout failures only — never on HTTP error responses.
class ApiClient {
  ApiClient({http.Client? client, String? baseUrl, this.tokenProvider})
    : _client = client ?? http.Client(),
      baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  final http.Client _client;
  final String baseUrl;

  /// Supplies the bearer token (secure storage in the app, fake in tests).
  final Future<String?> Function()? tokenProvider;

  static const Duration _timeout = Duration(seconds: 10);
  static const int _maxAttempts = 2;

  /// Unauthenticated liveness probe (contracts §3).
  Future<Map<String, dynamic>> getHealth() =>
      _get('/health', authenticated: false);

  /// Authenticated profile endpoint — proves a valid bearer token.
  Future<Map<String, dynamic>> getMe() => _get('/me', authenticated: true);

  Future<Map<String, dynamic>> _get(
    String path, {
    required bool authenticated,
  }) async {
    ApiException? last;
    for (var attempt = 0; attempt < _maxAttempts; attempt++) {
      try {
        return await _getOnce(path, authenticated: authenticated);
      } on ApiException catch (e) {
        if (!e.isNetwork) rethrow;
        last = e;
      }
    }
    throw last!;
  }

  Future<Map<String, dynamic>> _getOnce(
    String path, {
    required bool authenticated,
  }) async {
    final headers = <String, String>{'Accept': 'application/json'};
    if (authenticated) {
      final token = await tokenProvider?.call();
      if (token == null || token.isEmpty) {
        throw const ApiException(
          message: 'No auth token configured on this device',
        );
      }
      headers['Authorization'] = 'Bearer $token';
    }
    final http.Response res;
    try {
      res = await _client
          .get(Uri.parse('$baseUrl$path'), headers: headers)
          .timeout(_timeout);
    } on TimeoutException {
      throw const ApiException(message: 'Request timed out', isNetwork: true);
    } on SocketException catch (e) {
      throw ApiException(
        message: 'Cannot reach server: ${e.message}',
        isNetwork: true,
      );
    } on http.ClientException catch (e) {
      throw ApiException(
        message: 'Cannot reach server: ${e.message}',
        isNetwork: true,
      );
    }
    return _decode(res);
  }

  Map<String, dynamic> _decode(http.Response res) {
    Object? body;
    try {
      body = res.body.isEmpty ? null : jsonDecode(res.body);
    } on FormatException {
      body = null;
    }
    if (res.statusCode >= 400) {
      final error = body is Map<String, dynamic> && body.containsKey('code')
          ? ApiError.fromJson(body)
          : null;
      throw ApiException(
        statusCode: res.statusCode,
        error: error,
        message: error?.message ?? 'HTTP ${res.statusCode}',
      );
    }
    if (body is Map<String, dynamic>) return body;
    throw ApiException(
      statusCode: res.statusCode,
      message: 'Unexpected response body',
    );
  }

  void close() => _client.close();
}
