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

/// One insight line inside a Recap — always cites backend evidence ids.
class RecapInsight {
  const RecapInsight({required this.text, required this.evidenceEventIds});

  factory RecapInsight.fromJson(Map<String, dynamic> json) => RecapInsight(
    text: json['text'] as String? ?? '',
    evidenceEventIds: (json['evidence_event_ids'] as List? ?? const [])
        .whereType<String>()
        .toList(),
  );

  final String text;
  final List<String> evidenceEventIds;
}

/// `Recap` (contracts §2). `status` is GenerationStatus — GENERATED means
/// the model output passed the deterministic fact guard; FALLBACK means
/// the receipt was assembled purely from computed facts.
class RecapItem {
  const RecapItem({
    required this.id,
    required this.periodType,
    required this.periodStart,
    required this.periodEnd,
    required this.narrative,
    required this.insights,
    required this.highlightMediaIds,
    this.directiveForNextCycle,
    this.sourceRecapIds = const [],
    required this.status,
    required this.createdAt,
  });

  factory RecapItem.fromJson(Map<String, dynamic> json) => RecapItem(
    id: json['id'] as String,
    periodType: json['period_type'] as String,
    periodStart: DateTime.parse(json['period_start'] as String),
    periodEnd: DateTime.parse(json['period_end'] as String),
    narrative: json['narrative'] as String? ?? '',
    insights: (json['insights'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(RecapInsight.fromJson)
        .toList(),
    highlightMediaIds: (json['highlight_media_ids'] as List? ?? const [])
        .whereType<String>()
        .toList(),
    directiveForNextCycle: json['directive_for_next_cycle'] as String?,
    sourceRecapIds: (json['source_recap_ids'] as List? ?? const [])
        .whereType<String>()
        .toList(),
    status: json['status'] as String? ?? 'PENDING',
    createdAt: DateTime.parse(json['created_at'] as String),
  );

  final String id;
  final String periodType;
  final DateTime periodStart;
  final DateTime periodEnd;
  final String narrative;
  final List<RecapInsight> insights;
  final List<String> highlightMediaIds;
  final String? directiveForNextCycle;
  final List<String> sourceRecapIds;
  final String status;
  final DateTime createdAt;

  bool get isFallback => status == 'FALLBACK';
}

/// `MorningDirective` (contracts §2). `shown_at` is set by the backend on
/// first display — fetching again never regenerates.
class DirectiveItem {
  const DirectiveItem({
    required this.id,
    required this.forDate,
    required this.content,
    this.sourceRecapId,
    required this.status,
    this.shownAt,
  });

  factory DirectiveItem.fromJson(Map<String, dynamic> json) => DirectiveItem(
    id: json['id'] as String,
    forDate: DateTime.parse(json['for_date'] as String),
    content: json['content'] as String? ?? '',
    sourceRecapId: json['source_recap_id'] as String?,
    status: json['status'] as String? ?? 'PENDING',
    shownAt: json['shown_at'] == null
        ? null
        : DateTime.parse(json['shown_at'] as String),
  );

  final String id;
  final DateTime forDate;
  final String content;
  final String? sourceRecapId;
  final String status;
  final DateTime? shownAt;

  bool get isFallback => status == 'FALLBACK';
}
