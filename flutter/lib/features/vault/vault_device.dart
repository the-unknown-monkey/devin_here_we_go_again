import 'dart:async';
import 'dart:io';

import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';

/// A finished on-device capture: bytes + the MIME the device produced.
/// Filenames/paths are device-local only — the server generates its own
/// opaque storage key and never trusts client names.
class CapturedMedia {
  const CapturedMedia({
    required this.bytes,
    required this.mimeType,
    this.durationSec,
  });

  final List<int> bytes;
  final String mimeType;
  final double? durationSec;
}

/// Thrown when the user denies a capture permission at point of use.
class PermissionDeniedException implements Exception {
  const PermissionDeniedException(this.message);
  final String message;

  @override
  String toString() => message;
}

/// Device-facing capture surface. Widgets depend only on this interface so
/// tests can inject a fake without platform channels.
abstract class VaultDevice {
  Future<CapturedMedia?> capturePhoto();
  Future<CapturedMedia?> pickPhoto();

  /// Starts audio capture; returns a stream of elapsed recording time.
  Future<Stream<Duration>> startRecording();

  /// Stops recording and returns the captured clip, or null if discarded.
  Future<CapturedMedia?> stopRecording();
}

/// Real implementation: image_picker for photos, record for audio,
/// permission_handler for point-of-use runtime requests (never at launch).
class PluginVaultDevice implements VaultDevice {
  PluginVaultDevice({ImagePicker? picker, AudioRecorder? recorder})
    : _picker = picker ?? ImagePicker(),
      _recorder = recorder ?? AudioRecorder();

  final ImagePicker _picker;
  final AudioRecorder _recorder;
  String? _recordingPath;
  DateTime? _recordStarted;

  static String _imageMime(String? name) {
    final lower = (name ?? '').toLowerCase();
    if (lower.endsWith('.png')) return 'image/png';
    if (lower.endsWith('.webp')) return 'image/webp';
    return 'image/jpeg';
  }

  Future<void> _require(Permission permission, String deniedMessage) async {
    final status = await permission.request();
    if (!status.isGranted) throw PermissionDeniedException(deniedMessage);
  }

  @override
  Future<CapturedMedia?> capturePhoto() async {
    await _require(
      Permission.camera,
      'Camera permission is needed to capture a photo.',
    );
    final x = await _picker.pickImage(source: ImageSource.camera);
    if (x == null) return null;
    return CapturedMedia(
      bytes: await x.readAsBytes(),
      mimeType: _imageMime(x.name),
    );
  }

  @override
  Future<CapturedMedia?> pickPhoto() async {
    final x = await _picker.pickImage(source: ImageSource.gallery);
    if (x == null) return null;
    return CapturedMedia(
      bytes: await x.readAsBytes(),
      mimeType: _imageMime(x.name),
    );
  }

  @override
  Future<Stream<Duration>> startRecording() async {
    await _require(
      Permission.microphone,
      'Microphone permission is needed to record audio.',
    );
    final dir = await getTemporaryDirectory();
    _recordingPath =
        '${dir.path}/hwga_capture_${DateTime.now().microsecondsSinceEpoch}.m4a';
    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.aacLc),
      path: _recordingPath!,
    );
    _recordStarted = DateTime.now();
    // Emit elapsed time once per second for the recording-state UI.
    return Stream.periodic(
      const Duration(seconds: 1),
      (i) => Duration(seconds: i + 1),
    );
  }

  @override
  Future<CapturedMedia?> stopRecording() async {
    final path = await _recorder.stop();
    final started = _recordStarted;
    _recordStarted = null;
    final effective = path ?? _recordingPath;
    if (effective == null) return null;
    final file = File(effective);
    if (!await file.exists()) return null;
    final bytes = await file.readAsBytes();
    await file.delete();
    final duration = started == null
        ? null
        : DateTime.now().difference(started).inMilliseconds / 1000.0;
    return CapturedMedia(
      bytes: bytes,
      mimeType: 'audio/mp4',
      durationSec: duration,
    );
  }
}
