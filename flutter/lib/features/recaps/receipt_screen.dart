import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models.dart';
import 'highlight_tile.dart';

/// Nightly receipt view (HWGA06): the Recap the backend persisted for a
/// local date. The UI renders what the server says — it never computes
/// facts, and it labels FALLBACK receipts honestly instead of pretending
/// the model succeeded.
class ReceiptScreen extends StatefulWidget {
  const ReceiptScreen({super.key, required this.apiClient, required this.date});

  final ApiClient apiClient;
  final DateTime date;

  @override
  State<ReceiptScreen> createState() => _ReceiptScreenState();
}

class _ReceiptScreenState extends State<ReceiptScreen> {
  RecapItem? _recap;
  bool _loading = true;
  bool _noReceipt = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
      _noReceipt = false;
    });
    try {
      final recap = await widget.apiClient.getRecap(
        period: 'DAILY',
        date: widget.date,
      );
      if (!mounted) return;
      setState(() {
        _recap = recap;
        _noReceipt = recap == null;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.displayMessage);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String get _dateLabel =>
      '${widget.date.year}-${widget.date.month.toString().padLeft(2, '0')}-'
      '${widget.date.day.toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Receipt · $_dateLabel')),
      body: RefreshIndicator(onRefresh: _load, child: _body(context)),
    );
  }

  Widget _body(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return ListView(
        children: [
          Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                Text(
                  _error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
                TextButton(onPressed: _load, child: const Text('Retry')),
              ],
            ),
          ),
        ],
      );
    }
    if (_noReceipt || _recap == null) {
      // Honest empty state — an uneventful day is not a failure.
      return ListView(
        children: const [
          Padding(
            padding: EdgeInsets.all(32),
            child: Column(
              children: [
                Icon(Icons.nightlight_outlined, size: 48),
                SizedBox(height: 12),
                Text(
                  'No receipt for this day — nothing was logged, '
                  'and that\u2019s okay.',
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ],
      );
    }
    final recap = _recap!;
    final theme = Theme.of(context);
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Chip(
              avatar: Icon(
                recap.isFallback
                    ? Icons.format_list_bulleted
                    : Icons.auto_awesome,
                size: 18,
              ),
              label: Text(recap.isFallback ? 'Fact receipt' : 'Receipt'),
            ),
            const SizedBox(width: 8),
            if (recap.isFallback)
              Text(
                'made from your logged facts',
                style: theme.textTheme.bodySmall,
              ),
          ],
        ),
        const SizedBox(height: 12),
        Text(recap.narrative, style: theme.textTheme.bodyLarge),
        if (recap.insights.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('Noticed', style: theme.textTheme.titleMedium),
          const SizedBox(height: 4),
          for (final insight in recap.insights)
            ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.brightness_1, size: 8),
              title: Text(insight.text),
            ),
        ],
        if (recap.highlightMediaIds.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('Moments', style: theme.textTheme.titleMedium),
          const SizedBox(height: 4),
          for (final id in recap.highlightMediaIds)
            HighlightMediaTile(apiClient: widget.apiClient, mediaId: id),
        ],
        if (recap.directiveForNextCycle != null) ...[
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.wb_sunny_outlined),
                  const SizedBox(width: 12),
                  Expanded(child: Text(recap.directiveForNextCycle!)),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}
