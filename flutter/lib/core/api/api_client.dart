import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart' as http_parser;

import '../config/app_config.dart';
import 'api_error.dart';
import 'models.dart';

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

/// Bytes fetched from GET /media/{id} plus the server-asserted content type.
class MediaDownload {
  const MediaDownload({required this.bytes, required this.mimeType});

  final List<int> bytes;
  final String mimeType;
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

  // ---- HWGA04 routes (contracts.md §3) ----

  /// POST /events — idempotent on [idempotencyKey]; a network retry reuses
  /// the same key so duplicate taps can't create duplicate rows.
  Future<Map<String, dynamic>> postEvent({
    required String type,
    String? kind,
    String? mode,
    DateTime? occurredAt,
    required String idempotencyKey,
  }) => _post('/events', {
    'type': type,
    'kind': ?kind,
    'mode': ?mode,
    if (occurredAt != null) 'occurred_at': occurredAt.toUtc().toIso8601String(),
    'idempotency_key': idempotencyKey,
  });

  /// GET /timeline — today's events + media refs (server default window)
  /// or an explicit range.
  Future<TimelineBundle> getTimeline({DateTime? from, DateTime? to}) async {
    final query = <String, String>{
      if (from != null) 'from': from.toUtc().toIso8601String(),
      if (to != null) 'to': to.toUtc().toIso8601String(),
    };
    final path = query.isEmpty
        ? '/timeline'
        : '/timeline?${Uri(queryParameters: query).query}';
    final body = await _get(path, authenticated: true);
    return TimelineBundle(
      events: (body['events'] as List? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(EventItem.fromJson)
          .toList(),
      media: (body['media'] as List? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(MediaItem.fromJson)
          .toList(),
    );
  }

  // ---- HWGA05 media routes (contracts.md §3) ----

  /// POST /media — multipart upload → `MediaAssetMeta`. Not retried: the
  /// request body is one-shot and uploads carry no idempotency key.
  Future<MediaItem> uploadMedia({
    required List<int> bytes,
    required String mimeType,
    required String kind,
    double? durationSec,
    DateTime? capturedAt,
    String? transcriptText,
  }) async {
    final token = await tokenProvider?.call();
    if (token == null || token.isEmpty) {
      throw const ApiException(
        message: 'No auth token configured on this device',
      );
    }
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/media'));
    request.headers['Authorization'] = 'Bearer $token';
    request.fields['kind'] = kind;
    if (durationSec != null) {
      request.fields['duration_sec'] = durationSec.toString();
    }
    if (capturedAt != null) {
      request.fields['captured_at'] = capturedAt.toUtc().toIso8601String();
    }
    if (transcriptText != null && transcriptText.trim().isNotEmpty) {
      request.fields['transcript_text'] = transcriptText.trim();
    }
    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: 'capture',
        contentType: http_parser.MediaType.parse(mimeType),
      ),
    );
    http.StreamedResponse streamed;
    try {
      streamed = await _client.send(request).timeout(_timeout);
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
    final res = await http.Response.fromStream(streamed);
    final decoded = _decode(res);
    if (decoded is Map<String, dynamic>) return MediaItem.fromJson(decoded);
    throw const ApiException(message: 'Unexpected response body');
  }

  /// GET /media/{id} — authenticated bytes. Returns the body + server
  /// content type; no filesystem path is ever involved.
  Future<MediaDownload> getMediaBytes(String id) async {
    final headers = await _headers(true);
    final http.Response res;
    try {
      res = await _client
          .get(Uri.parse('$baseUrl/media/$id'), headers: headers)
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
    if (res.statusCode >= 400) {
      _decode(res); // throws the typed ApiException
    }
    return MediaDownload(
      bytes: res.bodyBytes,
      mimeType: (res.headers['content-type'] ?? 'application/octet-stream')
          .split(';')
          .first,
    );
  }

  /// DELETE /media/{id} — owner-only server delete.
  Future<void> deleteMedia(String id) async {
    final headers = await _headers(true);
    final http.Response res;
    try {
      res = await _client
          .delete(Uri.parse('$baseUrl/media/$id'), headers: headers)
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
    if (res.statusCode >= 400) {
      _decode(res); // throws
    }
  }

  /// GET /mode — `{current, intervals}`.
  Future<Map<String, dynamic>> getMode() => _get('/mode', authenticated: true);

  /// POST /mode — validated transition; server derives durations.
  Future<Map<String, dynamic>> postMode(
    String mode, {
    String? idempotencyKey,
    DateTime? occurredAt,
  }) => _post('/mode', {
    'mode': mode,
    if (occurredAt != null) 'occurred_at': occurredAt.toUtc().toIso8601String(),
    'idempotency_key': ?idempotencyKey,
  });

  Future<List<GoalItem>> getGoals() async {
    final body = await _getList('/goals', authenticated: true);
    return body
        .whereType<Map<String, dynamic>>()
        .map(GoalItem.fromJson)
        .toList();
  }

  Future<GoalItem> addGoal(String title) async =>
      GoalItem.fromJson(await _post('/goals', {'title': title}));

  Future<GoalItem> completeGoal(String id) async =>
      GoalItem.fromJson(await _post('/goals/$id/complete', const {}));

  Future<GoalItem> retireGoal(String id) async =>
      GoalItem.fromJson(await _post('/goals/$id/retire', const {}));

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

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> body,
  ) async {
    ApiException? last;
    // Safe to retry: every write carries a client idempotency key (or is
    // idempotent by route), so a retried POST can't duplicate server state.
    for (var attempt = 0; attempt < _maxAttempts; attempt++) {
      try {
        final decoded = await _requestOnce('POST', path, body: body);
        if (decoded is Map<String, dynamic>) return decoded;
        throw const ApiException(message: 'Unexpected response body');
      } on ApiException catch (e) {
        if (!e.isNetwork) rethrow;
        last = e;
      }
    }
    throw last!;
  }

  Future<List<dynamic>> _getList(
    String path, {
    required bool authenticated,
  }) async {
    ApiException? last;
    for (var attempt = 0; attempt < _maxAttempts; attempt++) {
      try {
        final decoded = await _requestOnce(
          'GET',
          path,
          authenticated: authenticated,
        );
        if (decoded is List) return decoded;
        throw const ApiException(message: 'Unexpected response body');
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
    final decoded = await _requestOnce(
      'GET',
      path,
      authenticated: authenticated,
    );
    if (decoded is Map<String, dynamic>) return decoded;
    throw const ApiException(message: 'Unexpected response body');
  }

  Future<Map<String, String>> _headers(bool authenticated) async {
    final headers = <String, String>{
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    if (authenticated) {
      final token = await tokenProvider?.call();
      if (token == null || token.isEmpty) {
        throw const ApiException(
          message: 'No auth token configured on this device',
        );
      }
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<Object?> _requestOnce(
    String method,
    String path, {
    bool authenticated = true,
    Map<String, dynamic>? body,
  }) async {
    final headers = await _headers(authenticated);
    final uri = Uri.parse('$baseUrl$path');
    final http.Response res;
    try {
      res = await switch (method) {
        'POST' =>
          _client
              .post(uri, headers: headers, body: jsonEncode(body ?? {}))
              .timeout(_timeout),
        _ => _client.get(uri, headers: headers).timeout(_timeout),
      };
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

  Object? _decode(http.Response res) {
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
    return body;
  }

  void close() => _client.close();
}
