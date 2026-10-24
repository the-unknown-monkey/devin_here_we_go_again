import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models.dart';
import '../vault/audio_player.dart';
import '../vault/media_card.dart';

const _kindLabels = {
  'WATER': 'Water',
  'FOOD_CLEAN': 'Clean meal',
  'STRETCH': 'Stretch',
  'POSTURE_RESET': 'Posture reset',
  'WALK': 'Walk',
};

const _kindIcons = {
  'WATER': Icons.water_drop_outlined,
  'FOOD_CLEAN': Icons.restaurant_outlined,
  'STRETCH': Icons.self_improvement_outlined,
  'POSTURE_RESET': Icons.accessibility_new_outlined,
  'WALK': Icons.directions_walk_outlined,
};

String modeLabel(String mode) => switch (mode) {
  'LOCKED_IN' => 'Locked in',
  'PURE_FUN_RECOVERY' => 'Rest & fun',
  _ => mode,
};

/// Private day timeline — renders server events and media verbatim. A quiet
/// day shows an honest "unknown" state, never a failure or streak message.
class TimelineView extends StatelessWidget {
  const TimelineView({
    super.key,
    required this.events,
    required this.loading,
    this.media = const [],
    this.apiClient,
    this.audioPlayer,
    this.onMediaChanged,
  });

  final List<EventItem> events;
  final List<MediaItem> media;
  final bool loading;

  /// Required to render interactive media cards; when null, media rows are
  /// rendered read-only (used by older tests).
  final ApiClient? apiClient;
  final VaultAudioPlayer? audioPlayer;
  final VoidCallback? onMediaChanged;

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Padding(
        padding: EdgeInsets.all(24),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    if (events.isEmpty && media.isEmpty) {
      return Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          'Nothing logged yet today.',
          style: Theme.of(context).textTheme.bodyMedium,
          textAlign: TextAlign.center,
        ),
      );
    }
    return Column(
      children: [
        for (final m in media)
          if (apiClient != null && audioPlayer != null)
            MediaCard(
              item: m,
              apiClient: apiClient!,
              player: audioPlayer!,
              onChanged: onMediaChanged ?? () {},
            )
          else
            ListTile(
              dense: true,
              leading: const Icon(Icons.perm_media_outlined),
              title: Text(switch (m.kind) {
                'IMAGE' => 'Photo',
                'AUDIO' => 'Ambient',
                _ => 'Voice scrap',
              }),
              subtitle: Text(
                TimeOfDay.fromDateTime(m.capturedAt.toLocal()).format(context),
              ),
            ),
        for (final e in events)
          ListTile(
            dense: true,
            leading: Icon(_iconFor(e)),
            title: Text(_labelFor(e)),
            subtitle: Text(
              TimeOfDay.fromDateTime(e.occurredAt.toLocal()).format(context),
            ),
          ),
      ],
    );
  }

  IconData _iconFor(EventItem e) => switch (e.type) {
    'CONFIRMATION' => _kindIcons[e.kind] ?? Icons.check_circle_outline,
    'QUIET_MOMENT' => Icons.spa_outlined,
    'MODE_TRANSITION' => Icons.swap_horiz,
    'MEDIA_CAPTURED' => Icons.perm_media_outlined,
    _ => Icons.circle_outlined,
  };

  String _labelFor(EventItem e) => switch (e.type) {
    'CONFIRMATION' => _kindLabels[e.kind] ?? 'Confirmation',
    'QUIET_MOMENT' => 'Quiet moment',
    'MODE_TRANSITION' => 'Now ${modeLabel(e.mode ?? '')}',
    'MEDIA_CAPTURED' => 'Moment captured',
    _ => e.type,
  };
}
