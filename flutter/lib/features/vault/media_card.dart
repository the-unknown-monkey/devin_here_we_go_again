import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models.dart';
import 'audio_player.dart';

/// Timeline card for a MediaItem (IMAGE / AUDIO / VOICE). Bytes are fetched
/// lazily through the authenticated API — the client never sees a server
/// path. Delete is owner-initiated and confirmed.
class MediaCard extends StatefulWidget {
  const MediaCard({
    super.key,
    required this.item,
    required this.apiClient,
    required this.player,
    required this.onChanged,
  });

  final MediaItem item;
  final ApiClient apiClient;
  final VaultAudioPlayer player;
  final VoidCallback onChanged;

  @override
  State<MediaCard> createState() => _MediaCardState();
}

class _MediaCardState extends State<MediaCard> {
  bool _busy = false;
  bool _playing = false;
  String? _error;

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  Future<Uint8List> _load() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final res = await widget.apiClient.getMediaBytes(widget.item.id);
      return Uint8List.fromList(res.bytes);
    } on ApiException catch (e) {
      setState(() => _error = e.displayMessage);
      rethrow;
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _viewImage() async {
    try {
      final bytes = await _load();
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (_) =>
            Dialog(child: InteractiveViewer(child: Image.memory(bytes))),
      );
    } on ApiException {
      // _error already set by _load
    }
  }

  Future<void> _play() async {
    try {
      final bytes = await _load();
      await widget.player.play(bytes, widget.item.mimeType);
      if (mounted) setState(() => _playing = true);
    } on ApiException {
      // _error already set
    }
  }

  Future<void> _stop() async {
    await widget.player.stop();
    if (mounted) setState(() => _playing = false);
  }

  Future<void> _delete() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete this moment?'),
        content: const Text('This removes the file from your server.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    setState(() => _busy = true);
    try {
      await widget.apiClient.deleteMedia(widget.item.id);
      widget.onChanged();
    } on ApiException catch (e) {
      _toast(e.displayMessage);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    final theme = Theme.of(context);
    final (icon, label) = switch (item.kind) {
      'IMAGE' => (Icons.photo_outlined, 'Photo'),
      'AUDIO' => (Icons.graphic_eq, 'Ambient'),
      _ => (Icons.mic_none, 'Voice scrap'),
    };
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: ListTile(
        leading: _busy
            ? const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : Icon(icon),
        title: Text(label),
        subtitle: Text(
          [
            TimeOfDay.fromDateTime(item.capturedAt.toLocal()).format(context),
            if (item.durationSec != null)
              '${item.durationSec!.toStringAsFixed(0)}s',
            if (item.transcriptText != null) item.transcriptText!,
            if (item.transcriptState == 'PENDING') 'transcript pending',
            ?_error,
          ].join(' · '),
          style: _error != null
              ? TextStyle(color: theme.colorScheme.error)
              : null,
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (item.isImage)
              IconButton(
                tooltip: 'View',
                icon: const Icon(Icons.open_in_new),
                onPressed: _busy ? null : _viewImage,
              ),
            if (item.isAudio)
              IconButton(
                tooltip: _playing ? 'Stop' : 'Play',
                icon: Icon(_playing ? Icons.stop : Icons.play_arrow),
                onPressed: _busy ? null : (_playing ? _stop : _play),
              ),
            IconButton(
              tooltip: 'Delete',
              icon: const Icon(Icons.delete_outline),
              onPressed: _busy ? null : _delete,
            ),
          ],
        ),
      ),
    );
  }
}
