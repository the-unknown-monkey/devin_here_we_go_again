import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:hwga/core/api/api_client.dart';
import 'package:hwga/features/vault/capture_sheet.dart';
import 'package:hwga/features/vault/vault_device.dart';

/// In-memory VaultDevice — no platform channels, scripted captures.
class FakeVaultDevice implements VaultDevice {
  CapturedMedia? nextPhoto;
  CapturedMedia? nextRecording;
  Object? error;
  final tickController = StreamController<Duration>();
  bool recordingStarted = false;

  @override
  Future<CapturedMedia?> capturePhoto() async {
    if (error != null) throw error!;
    return nextPhoto;
  }

  @override
  Future<CapturedMedia?> pickPhoto() async {
    if (error != null) throw error!;
    return nextPhoto;
  }

  @override
  Future<Stream<Duration>> startRecording() async {
    if (error != null) throw error!;
    recordingStarted = true;
    return tickController.stream;
  }

  @override
  Future<CapturedMedia?> stopRecording() async {
    if (error != null) throw error!;
    return nextRecording;
  }
}

Widget sheetWith({required MockClient mock, required FakeVaultDevice device}) =>
    MaterialApp(
      home: Scaffold(
        body: CaptureSheet(
          apiClient: ApiClient(
            client: mock,
            baseUrl: 'http://127.0.0.1:8000',
            tokenProvider: () async => 'tok',
          ),
          device: device,
        ),
      ),
    );

/// Captures the multipart upload body for assertions.
class UploadProbe {
  String? body;
  String? contentType;
  Uri? uri;
  String? authorization;

  MockClient get client => MockClient.streaming((req, bytes) async {
    authorization = req.headers['authorization'];
    contentType = req.headers['content-type'];
    uri = req.url;
    // Raw bytes — the file part is binary and won't survive a strict
    // UTF-8 decode.
    body = utf8.decode(await bytes.toBytes(), allowMalformed: true);
    return http.StreamedResponse(
      Stream.value(
        utf8.encode(
          jsonEncode({
            'id': 'm-1',
            'kind': 'IMAGE',
            'captured_at': DateTime.now().toUtc().toIso8601String(),
            'mime_type': 'image/jpeg',
            'byte_length': 10,
            'duration_sec': null,
            'transcript_state': 'NOT_APPLICABLE',
            'transcript_text': null,
          }),
        ),
      ),
      201,
      headers: {'content-type': 'application/json'},
    );
  });
}

void main() {
  testWidgets('photo capture uploads bytes with bearer auth', (tester) async {
    final device = FakeVaultDevice()
      ..nextPhoto = const CapturedMedia(
        bytes: [0xFF, 0xD8, 0xFF],
        mimeType: 'image/jpeg',
      );
    final probe = UploadProbe();
    await tester.pumpWidget(sheetWith(mock: probe.client, device: device));
    await tester.tap(find.text('Photo'));
    await tester.pumpAndSettle();

    expect(probe.authorization, 'Bearer tok');
    expect(probe.uri!.path, '/media');
    expect(probe.contentType, contains('multipart/form-data'));
    expect(probe.body, contains('name="kind"'));
    expect(probe.body, contains('IMAGE'));
    // Sheet pops with `true` on success.
    expect(find.byType(CaptureSheet), findsNothing);
  });

  testWidgets('ambient recording shows recording state and auto-stops at 10s', (
    tester,
  ) async {
    final device = FakeVaultDevice()
      ..nextRecording = const CapturedMedia(
        bytes: [1, 2, 3],
        mimeType: 'audio/mp4',
        durationSec: 9.9,
      );
    final probe = UploadProbe();
    await tester.pumpWidget(sheetWith(mock: probe.client, device: device));
    await tester.tap(find.text('Ambient 5–10s'));
    await tester.pumpAndSettle();

    expect(device.recordingStarted, isTrue);
    device.tickController.add(const Duration(seconds: 4));
    await tester.pump();
    await tester.pump();
    expect(find.textContaining('4s / 10s'), findsOneWidget);

    device.tickController.add(const Duration(seconds: 10));
    await tester.pumpAndSettle();
    expect(probe.body, contains('AUDIO'));
    expect(probe.body, contains('9.9'));
  });

  testWidgets('voice scrap sends manual transcript text', (tester) async {
    final device = FakeVaultDevice()
      ..nextRecording = const CapturedMedia(
        bytes: [1, 2, 3],
        mimeType: 'audio/mp4',
        durationSec: 3.0,
      );
    final probe = UploadProbe();
    await tester.pumpWidget(sheetWith(mock: probe.client, device: device));
    await tester.enterText(find.byType(TextField), 'idea: write it down');
    await tester.tap(find.text('Voice scrap'));
    await tester.pumpAndSettle();
    tester
        .widget<FilledButton>(find.widgetWithText(FilledButton, 'Stop'))
        .onPressed!();
    await tester.pumpAndSettle();

    expect(probe.body, contains('VOICE'));
    expect(probe.body, contains('idea: write it down'));
  });

  testWidgets('ambient clip under 5s shows a gentle message', (tester) async {
    final device = FakeVaultDevice()
      ..nextRecording = const CapturedMedia(
        bytes: [1, 2, 3],
        mimeType: 'audio/mp4',
        durationSec: 2.0,
      );
    var uploads = 0;
    final mock = MockClient.streaming((req, _) async {
      uploads++;
      return http.StreamedResponse(const Stream.empty(), 201);
    });
    await tester.pumpWidget(sheetWith(mock: mock, device: device));
    await tester.tap(find.text('Ambient 5–10s'));
    await tester.pumpAndSettle();
    tester
        .widget<FilledButton>(find.widgetWithText(FilledButton, 'Stop'))
        .onPressed!();
    await tester.pumpAndSettle();

    expect(uploads, 0);
    expect(find.textContaining('5–10 seconds'), findsOneWidget);
  });

  testWidgets('permission denial shows an understandable message', (
    tester,
  ) async {
    final device = FakeVaultDevice()
      ..error = const PermissionDeniedException(
        'Microphone permission is needed to record audio.',
      );
    await tester.pumpWidget(
      sheetWith(
        mock: MockClient((_) async => http.Response('{}', 500)),
        device: device,
      ),
    );
    await tester.tap(find.text('Voice scrap'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Microphone permission'), findsOneWidget);
  });

  testWidgets('server limit error is shown verbatim', (tester) async {
    final device = FakeVaultDevice()
      ..nextPhoto = const CapturedMedia(bytes: [1], mimeType: 'image/jpeg');
    final mock = MockClient.streaming(
      (req, _) async => http.StreamedResponse(
        Stream.value(
          utf8.encode(
            jsonEncode({
              'code': 'MEDIA_LIMIT_EXCEEDED',
              'message': 'IMAGE exceeds 10485760 bytes',
              'details': {},
            }),
          ),
        ),
        413,
      ),
    );
    await tester.pumpWidget(sheetWith(mock: mock, device: device));
    await tester.tap(find.text('Photo'));
    await tester.pumpAndSettle();
    expect(find.textContaining('IMAGE exceeds'), findsOneWidget);
    expect(find.byType(CaptureSheet), findsOneWidget);
  });
}
