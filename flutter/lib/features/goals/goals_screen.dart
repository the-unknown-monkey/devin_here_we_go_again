import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models.dart';

/// Rule-of-3 goals. The 3-cap is enforced by the backend; this screen only
/// renders GoalItem.age_days (computed server-side) and surfaces the typed
/// GOAL_CAP_REACHED error without judging the user.
class GoalsScreen extends StatefulWidget {
  const GoalsScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<GoalsScreen> createState() => _GoalsScreenState();
}

class _GoalsScreenState extends State<GoalsScreen> {
  List<GoalItem> _goals = [];
  bool _loading = true;
  bool _busy = false;
  String? _error;
  final _titleController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final goals = await widget.apiClient.getGoals();
      if (mounted) setState(() => _goals = goals);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.displayMessage);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _run(Future<GoalItem> Function() action) async {
    setState(() => _busy = true);
    try {
      await action();
      await _load();
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              e.error?.code == 'GOAL_CAP_REACHED'
                  ? 'Three active goals is the limit — finish or retire one first.'
                  : e.displayMessage,
            ),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _add() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) return;
    await _run(() => widget.apiClient.addGoal(title));
    _titleController.clear();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final active = _goals.where((g) => g.isActive).toList();
    final resolved = _goals.where((g) => !g.isActive).toList();
    return Scaffold(
      appBar: AppBar(title: const Text('Goals — rule of 3')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            '${active.length} of 3 active',
            style: theme.textTheme.titleMedium,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _titleController,
                  decoration: const InputDecoration(
                    hintText: 'One thing that matters',
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (_) => _add(),
                ),
              ),
              const SizedBox(width: 8),
              FilledButton(
                onPressed: _busy ? null : _add,
                child: const Text('Add'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (_loading)
            const Center(child: CircularProgressIndicator())
          else if (_error != null)
            Column(
              children: [
                Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
                TextButton(onPressed: _load, child: const Text('Retry')),
              ],
            )
          else ...[
            for (final g in active)
              Card(
                child: ListTile(
                  title: Text(g.title),
                  subtitle: Text(
                    g.ageDays == 0 ? 'Started today' : '${g.ageDays}d old',
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        tooltip: 'Complete',
                        icon: const Icon(Icons.check_circle_outline),
                        onPressed: _busy
                            ? null
                            : () => _run(
                                () => widget.apiClient.completeGoal(g.id),
                              ),
                      ),
                      IconButton(
                        tooltip: 'Retire',
                        icon: const Icon(Icons.archive_outlined),
                        onPressed: _busy
                            ? null
                            : () =>
                                  _run(() => widget.apiClient.retireGoal(g.id)),
                      ),
                    ],
                  ),
                ),
              ),
            if (active.isEmpty)
              Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  'No active goals.',
                  style: theme.textTheme.bodyMedium,
                  textAlign: TextAlign.center,
                ),
              ),
            if (resolved.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text('Resolved', style: theme.textTheme.titleSmall),
              for (final g in resolved)
                ListTile(
                  dense: true,
                  leading: Icon(
                    g.status == 'COMPLETED'
                        ? Icons.check_circle_outline
                        : Icons.archive_outlined,
                  ),
                  title: Text(g.title),
                  subtitle: Text(g.status.toLowerCase()),
                ),
            ],
          ],
        ],
      ),
    );
  }
}
