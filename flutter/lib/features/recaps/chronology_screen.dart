import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models.dart';
import 'highlight_tile.dart';
import 'receipt_screen.dart';

/// Private chronology view (HWGA07): the stored WEEKLY recap — generated
/// from daily receipt objects, not raw logs — plus a day strip linking to
/// each day's receipt. Media renders only via authenticated ids. No
/// sharing, streaks, or comparison affordances.
class ChronologyScreen extends StatefulWidget {
  const ChronologyScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<ChronologyScreen> createState() => _ChronologyScreenState();
}

class _ChronologyScreenState extends State<ChronologyScreen> {
  RecapItem? _weekly;
  bool _loading = true;
  bool _noRecap = false;
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
      _noRecap = false;
    });
    try {
      final recap = await widget.apiClient.getRecap(period: 'WEEKLY');
      if (!mounted) return;
      setState(() {
        _weekly = recap;
        _noRecap = recap == null;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.displayMessage);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _dayLabel(DateTime d) =>
      '${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Your week')),
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
    if (_noRecap || _weekly == null) {
      return ListView(
        children: const [
          Padding(
            padding: EdgeInsets.all(32),
            child: Column(
              children: [
                Icon(Icons.calendar_month_outlined, size: 48),
                SizedBox(height: 12),
                Text(
                  'No weekly recap yet — it appears once receipts are saved.',
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ],
      );
    }

    final weekly = _weekly!;
    final theme = Theme.of(context);
    final days = List.generate(
      weekly.periodEnd.difference(weekly.periodStart).inDays + 1,
      (i) => weekly.periodStart.add(Duration(days: i)),
    );
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Chip(
              avatar: Icon(
                weekly.isFallback
                    ? Icons.format_list_bulleted
                    : Icons.auto_awesome,
                size: 18,
              ),
              label: Text(weekly.isFallback ? 'Fact recap' : 'Weekly recap'),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '${_dayLabel(weekly.periodStart)} – ${_dayLabel(weekly.periodEnd)} · '
                '${weekly.sourceRecapIds.length} receipt'
                '${weekly.sourceRecapIds.length == 1 ? '' : 's'}',
                style: theme.textTheme.bodySmall,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Text(weekly.narrative, style: theme.textTheme.bodyLarge),
        if (weekly.insights.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('From your receipts', style: theme.textTheme.titleMedium),
          for (final insight in weekly.insights)
            ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.brightness_1, size: 8),
              title: Text(insight.text),
            ),
        ],
        if (weekly.highlightMediaIds.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('Moments', style: theme.textTheme.titleMedium),
          for (final id in weekly.highlightMediaIds)
            HighlightMediaTile(apiClient: widget.apiClient, mediaId: id),
        ],
        const SizedBox(height: 16),
        Text('Days', style: theme.textTheme.titleMedium),
        const SizedBox(height: 4),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final day in days)
              ActionChip(
                label: Text(_dayLabel(day)),
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) =>
                          ReceiptScreen(apiClient: widget.apiClient, date: day),
                    ),
                  );
                },
              ),
          ],
        ),
        if (weekly.directiveForNextCycle != null) ...[
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.wb_sunny_outlined),
                  const SizedBox(width: 12),
                  Expanded(child: Text(weekly.directiveForNextCycle!)),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}
