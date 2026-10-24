import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/permissions/capture_permissions.dart';
import 'vault_device.dart';

/// Sensory Moment Vault capture sheet (HWGA05).
///
/// Three user-initiated captures: photo (camera or library), ambient audio
/// (5–10 s capsule, auto-stops at 10 s), and a voice scrap with an optional
/// manual-text fallback (MANUAL_TEXT per D19). Device access goes through
/// [VaultDevice] so permissions are requested only at point of use and
/// tests run without platform channels.
class CaptureSheet extends StatefulWidget {
  const CaptureSheet({
    super.key,
    required this.apiClient,
    required this.device,
  });

  final ApiClient apiClient;
  final VaultDevice device;

  /// Ambient capsules are prompted at 5–10 s (D18); the server cap is 60 s.
  static const ambientMaxSeconds = 10;
  static const ambientMinSeconds = 5;

  @override
  State<CaptureSheet> createState() => _CaptureSheetState();
}

class _CaptureSheetState extends State<CaptureSheet> {
  bool _busy = false;
  bool _recording = false;
  bool _ambient = false;
  int _elapsed = 0;
  StreamSubscription<Duration>? _ticker;
  String? _error;
  final _voiceText = TextEditingController();

  @override
  void dispose() {
    _ticker?.cancel();
    _voiceText.dispose();
    super.dispose();
  }

  void _fail(Object e) {
    if (!mounted) return;
    setState(() {
      _busy = false;
      _error = e is ApiException
          ? e.displayMessage
          : e is PermissionDeniedException
          ? e.message
          : 'Capture failed. Please try again.';
    });
  }

  Future<void> _upload(
    CapturedMedia? captured,
    String kind, {
    String? transcriptText,
  }) async {
    if (captured == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.apiClient.uploadMedia(
        bytes: captured.bytes,
        mimeType: captured.mimeType,
        kind: kind,
        durationSec: captured.durationSec,
        capturedAt: DateTime.now(),
        transcriptText: transcriptText,
      );
      if (mounted) Navigator.of(context).pop(true);
    } on Object catch (e) {
      _fail(e);
    }
  }

  Future<void> _photo({required bool camera}) async {
    setState(() => _error = null);
    try {
      final captured = camera
          ? await widget.device.capturePhoto()
          : await widget.device.pickPhoto();
      await _upload(captured, 'IMAGE');
    } on Object catch (e) {
      _fail(e);
    }
  }

  Future<void> _startRecording({required bool ambient}) async {
    setState(() => _error = null);
    try {
      final ticks = await widget.device.startRecording();
      setState(() {
        _recording = true;
        _ambient = ambient;
        _elapsed = 0;
      });
      _ticker = ticks.listen((d) {
        if (!mounted) return;
        setState(() => _elapsed = d.inSeconds);
        if (ambient && d.inSeconds >= CaptureSheet.ambientMaxSeconds) {
          _stopRecording();
        }
      });
    } on Object catch (e) {
      _fail(e);
    }
  }

  Future<void> _stopRecording() async {
    // Fire-and-forget: awaiting cancel() from inside the ticker callback can
    // stall; the stream is single-subscription so this is safe.
    unawaited(_ticker?.cancel());
    _ticker = null;
    final ambient = _ambient;
    CapturedMedia? captured;
    try {
      captured = await widget.device.stopRecording();
    } on Object catch (e) {
      setState(() => _recording = false);
      _fail(e);
      return;
    }
    setState(() => _recording = false);
    if (captured == null) return;
    if (ambient &&
        (captured.durationSec ?? 0) < CaptureSheet.ambientMinSeconds) {
      setState(
        () => _error =
            'Ambient capsules are ${CaptureSheet.ambientMinSeconds}–'
            '${CaptureSheet.ambientMaxSeconds} seconds — hold it a moment longer.',
      );
      return;
    }
    await _upload(
      captured,
      ambient ? 'AUDIO' : 'VOICE',
      transcriptText: ambient ? null : _voiceText.text,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Keep a moment', style: theme.textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              'Private to your server — never posted anywhere.',
              style: theme.textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(
                  _error!,
                  style: TextStyle(color: theme.colorScheme.error),
                ),
              ),
            if (_recording) ...[
              Row(
                children: [
                  Icon(
                    Icons.fiber_manual_record,
                    color: theme.colorScheme.error,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _ambient
                          ? 'Ambient capsule · ${_elapsed}s / '
                                '${CaptureSheet.ambientMaxSeconds}s'
                          : 'Voice scrap · ${_elapsed}s',
                    ),
                  ),
                  FilledButton(
                    onPressed: _busy ? null : _stopRecording,
                    child: const Text('Stop'),
                  ),
                ],
              ),
            ] else ...[
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  FilledButton.tonalIcon(
                    onPressed: _busy ? null : () => _photo(camera: true),
                    icon: const Icon(Icons.photo_camera_outlined),
                    label: const Text('Photo'),
                  ),
                  FilledButton.tonalIcon(
                    onPressed: _busy ? null : () => _photo(camera: false),
                    icon: const Icon(Icons.photo_library_outlined),
                    label: const Text('Library'),
                  ),
                  FilledButton.tonalIcon(
                    onPressed: _busy
                        ? null
                        : () => _startRecording(ambient: true),
                    icon: const Icon(Icons.graphic_eq),
                    label: const Text('Ambient 5–10s'),
                  ),
                  FilledButton.tonalIcon(
                    onPressed: _busy
                        ? null
                        : () => _startRecording(ambient: false),
                    icon: const Icon(Icons.mic_none),
                    label: const Text('Voice scrap'),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _voiceText,
                maxLines: 2,
                decoration: const InputDecoration(
                  labelText: 'Voice scrap note (optional)',
                  hintText: 'Type it instead if transcription is unavailable',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                CapturePermissions.microphoneRationale,
                style: theme.textTheme.bodySmall,
              ),
            ],
            if (_busy)
              const Padding(
                padding: EdgeInsets.only(top: 12),
                child: LinearProgressIndicator(),
              ),
          ],
        ),
      ),
    );
  }
}
