import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models.dart';

/// Morning directive card (HWGA07): one small, concrete suggestion from
/// the backend's stored MorningDirective. The backend owns generation and
/// display dedupe (`shown_at`) — this widget only renders. FALLBACK
/// directives are labeled honestly, and failure states stay gentle.
class DirectiveCard extends StatefulWidget {
  const DirectiveCard({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<DirectiveCard> createState() => _DirectiveCardState();
}

class _DirectiveCardState extends State<DirectiveCard> {
  DirectiveItem? _directive;
  bool _loading = true;
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
    });
    try {
      final directive = await widget.apiClient.getDirectiveToday();
      if (mounted) setState(() => _directive = directive);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.displayMessage);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 250),
          child: _content(theme),
        ),
      ),
    );
  }

  Widget _content(ThemeData theme) {
    if (_loading) {
      return const Row(
        key: ValueKey('loading'),
        children: [
          SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          SizedBox(width: 12),
          Text('Waking up your day…'),
        ],
      );
    }
    if (_error != null) {
      return Row(
        key: const ValueKey('error'),
        children: [
          const Icon(Icons.wb_twilight_outlined),
          const SizedBox(width: 12),
          Expanded(child: Text(_error!)),
          TextButton(onPressed: _load, child: const Text('Retry')),
        ],
      );
    }
    final directive = _directive;
    if (directive == null || directive.content.isEmpty) {
      return const Row(
        key: ValueKey('empty'),
        children: [
          Icon(Icons.wb_sunny_outlined),
          SizedBox(width: 12),
          Expanded(child: Text('A fresh page — the day is yours.')),
        ],
      );
    }
    return Row(
      key: const ValueKey('directive'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Icon(Icons.wb_sunny_outlined),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                directive.isFallback ? 'A simple nudge' : 'Today',
                style: theme.textTheme.labelMedium,
              ),
              const SizedBox(height: 2),
              Text(directive.content),
            ],
          ),
        ),
      ],
    );
  }
}
