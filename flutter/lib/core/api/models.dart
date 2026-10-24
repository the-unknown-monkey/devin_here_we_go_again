/// Typed mirrors of locked contract shapes (contracts.md §2) as returned by
/// the backend. The backend is the authority for values like `ageDays` and
/// `durationMin` — the client renders, it does not compute.
library;

class EventItem {
  const EventItem({
    required this.id,
    required this.type,
    this.kind,
    this.mode,
    required this.occurredAt,
    required this.idempotencyKey,
  });

  factory EventItem.fromJson(Map<String, dynamic> json) => EventItem(
    id: json['id'] as String,
    type: json['type'] as String,
    kind: json['kind'] as String?,
    mode: json['mode'] as String?,
    occurredAt: DateTime.parse(json['occurred_at'] as String),
    idempotencyKey: json['idempotency_key'] as String? ?? '',
  );

  final String id;
  final String type;
  final String? kind;
  final String? mode;
  final DateTime occurredAt;
  final String idempotencyKey;
}

class GoalItem {
  const GoalItem({
    required this.id,
    required this.title,
    required this.status,
    required this.createdAt,
    this.resolvedAt,
    required this.ageDays,
  });

  factory GoalItem.fromJson(Map<String, dynamic> json) => GoalItem(
    id: json['id'] as String,
    title: json['title'] as String,
    status: json['status'] as String,
    createdAt: DateTime.parse(json['created_at'] as String),
    resolvedAt: json['resolved_at'] == null
        ? null
        : DateTime.parse(json['resolved_at'] as String),
    ageDays: json['age_days'] as int? ?? 0,
  );

  final String id;
  final String title;
  final String status;
  final DateTime createdAt;
  final DateTime? resolvedAt;
  final int ageDays;

  bool get isActive => status == 'ACTIVE';
}

/// `MediaAssetMeta` (contracts §2). The backend never sends storage_key or
/// any filesystem path; bytes are fetched only via GET /media/{id}.
class MediaItem {
  const MediaItem({
    required this.id,
    required this.kind,
    required this.capturedAt,
    required this.mimeType,
    required this.byteLength,
    this.durationSec,
    required this.transcriptState,
    this.transcriptText,
  });

  factory MediaItem.fromJson(Map<String, dynamic> json) => MediaItem(
    id: json['id'] as String,
    kind: json['kind'] as String,
    capturedAt: DateTime.parse(json['captured_at'] as String),
    mimeType: json['mime_type'] as String,
    byteLength: json['byte_length'] as int? ?? 0,
    durationSec: (json['duration_sec'] as num?)?.toDouble(),
    transcriptState: json['transcript_state'] as String? ?? 'NOT_APPLICABLE',
    transcriptText: json['transcript_text'] as String?,
  );

  final String id;
  final String kind;
  final DateTime capturedAt;
  final String mimeType;
  final int byteLength;
  final double? durationSec;
  final String transcriptState;
  final String? transcriptText;

  bool get isImage => kind == 'IMAGE';
  bool get isAudio => kind == 'AUDIO' || kind == 'VOICE';
}

/// GET /timeline body: events + media refs for the private feed.
class TimelineBundle {
  const TimelineBundle({required this.events, required this.media});

  final List<EventItem> events;
  final List<MediaItem> media;
}

class ModeIntervalItem {
  const ModeIntervalItem({
    required this.mode,
    required this.startedAt,
    this.endedAt,
    this.durationMin,
  });

  factory ModeIntervalItem.fromJson(Map<String, dynamic> json) =>
      ModeIntervalItem(
        mode: json['mode'] as String,
        startedAt: DateTime.parse(json['started_at'] as String),
        endedAt: json['ended_at'] == null
            ? null
            : DateTime.parse(json['ended_at'] as String),
        durationMin: json['duration_min'] as int?,
      );

  final String mode;
  final DateTime startedAt;
  final DateTime? endedAt;
  final int? durationMin;
}
