import 'dart:math';

import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models.dart';
import '../baselines/confirmation_bar.dart';
import '../goals/goals_screen.dart';
import '../modes/mode_control.dart';
import '../timeline/timeline_view.dart';

final _rng = Random();

/// One unique key per user intent. If a save fails at the network layer and
/// the user retries, the same key is reused so the backend dedupes it.
String _newKey(String prefix) =>
    '$prefix-${DateTime.now().microsecondsSinceEpoch}-${_rng.nextInt(1 << 32)}';

/// Private day view: mode, one-tap confirmations, goal count, and today's
/// timeline. Server state is the source of truth — the UI refreshes from
/// the backend after every write and never claims a save before the server
/// confirms it.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  ModeIntervalItem? _currentMode;
  List<EventItem> _events = [];
  int _activeGoals = 0;
  bool _loading = true;
  bool _busy = false;
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
      final mode = await widget.apiClient.getMode();
      final events = await widget.apiClient.getTimeline();
      final goals = await widget.apiClient.getGoals();
      if (!mounted) return;
      setState(() {
        final cur = mode['current'];
        _currentMode = cur is Map<String, dynamic>
            ? ModeIntervalItem.fromJson(cur)
            : null;
        _events = events;
        _activeGoals = goals.where((g) => g.isActive).length;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.displayMessage);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _toast(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _write(Future<void> Function() action) async {
    setState(() => _busy = true);
    try {
      await action();
      await _load();
    } on ApiException catch (e) {
      if (mounted) _toast(e.displayMessage);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _confirm(String kind) => _write(() async {
    await widget.apiClient.postEvent(
      type: 'CONFIRMATION',
      kind: kind,
      idempotencyKey: _newKey('confirm'),
    );
  });

  Future<void> _quietMoment() => _write(() async {
    await widget.apiClient.postEvent(
      type: 'QUIET_MOMENT',
      idempotencyKey: _newKey('quiet'),
    );
  });

  Future<void> _switchMode() async {
    final next = _currentMode?.mode == 'LOCKED_IN'
        ? 'PURE_FUN_RECOVERY'
        : 'LOCKED_IN';
    await _write(() async {
      await widget.apiClient.postMode(next, idempotencyKey: _newKey('mode'));
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Today'),
        actions: [
          IconButton(
            tooltip: 'Goals',
            icon: Badge(
              isLabelVisible: _activeGoals > 0,
              label: Text('$_activeGoals'),
              child: const Icon(Icons.flag_outlined),
            ),
            onPressed: () async {
              await Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => GoalsScreen(apiClient: widget.apiClient),
                ),
              );
              _load();
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            ModeControl(
              current: _currentMode,
              busy: _busy,
              onSwitch: _switchMode,
            ),
            const SizedBox(height: 16),
            Text('Baselines', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ConfirmationBar(
              busy: _busy,
              onConfirm: _confirm,
              onQuietMoment: _quietMoment,
            ),
            const SizedBox(height: 16),
            Text('Timeline', style: Theme.of(context).textTheme.titleMedium),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    Text(
                      _error!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                    TextButton(onPressed: _load, child: const Text('Retry')),
                  ],
                ),
              )
            else
              TimelineView(events: _events, loading: _loading),
          ],
        ),
      ),
    );
  }
}
