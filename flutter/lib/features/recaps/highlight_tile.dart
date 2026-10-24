import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';

/// A private media reference — bytes fetched through the authenticated
/// /media/{id} route only; the client never sees a path. Shared by the
/// receipt and chronology views.
class HighlightMediaTile extends StatefulWidget {
  const HighlightMediaTile({
    super.key,
    required this.apiClient,
    required this.mediaId,
  });

  final ApiClient apiClient;
  final String mediaId;

  @override
  State<HighlightMediaTile> createState() => _HighlightMediaTileState();
}

class _HighlightMediaTileState extends State<HighlightMediaTile> {
  MediaDownload? _media;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final media = await widget.apiClient.getMediaBytes(widget.mediaId);
      if (mounted) setState(() => _media = media);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.displayMessage);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return ListTile(
        leading: const Icon(Icons.broken_image_outlined),
        title: Text(_error!),
      );
    }
    final media = _media;
    if (media == null) {
      return const ListTile(
        leading: SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
        title: Text('Loading moment…'),
      );
    }
    if (media.mimeType.startsWith('image/')) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: Image.memory(
            Uint8List.fromList(media.bytes),
            height: 160,
            width: double.infinity,
            fit: BoxFit.cover,
          ),
        ),
      );
    }
    return ListTile(
      leading: const Icon(Icons.graphic_eq),
      title: const Text('Audio moment'),
      subtitle: Text(media.mimeType),
    );
  }
}
