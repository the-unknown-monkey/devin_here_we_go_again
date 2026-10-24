import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';

/// Playback surface for vault audio cards. Abstract so widget tests never
/// touch platform channels.
abstract class VaultAudioPlayer {
  Future<void> play(Uint8List bytes, String mimeType);
  Future<void> stop();
  void dispose();
}

class AudioPlayersVaultPlayer implements VaultAudioPlayer {
  AudioPlayersVaultPlayer() : _player = AudioPlayer();

  final AudioPlayer _player;

  @override
  Future<void> play(Uint8List bytes, String mimeType) =>
      _player.play(BytesSource(bytes));

  @override
  Future<void> stop() => _player.stop();

  @override
  void dispose() => _player.dispose();
}
