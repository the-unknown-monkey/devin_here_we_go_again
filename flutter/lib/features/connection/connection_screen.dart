import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/api/token_store.dart';
import '../../core/widget_bridge.dart';
import '../../app/app.dart';
import '../auth/token_screen.dart';
import '../home/home_screen.dart';

enum _Status { idle, loading, ok, error }

/// Minimal V1 shell: proves the phone reaches the backend (health) and that
/// the device bearer token is accepted (/me). All results are safe states —
/// never raw exceptions or tokens.
class ConnectionScreen extends StatefulWidget {
  const ConnectionScreen({
    super.key,
    required this.apiClient,
    required this.tokenStore,
    this.launchUriProvider,
  });

  final ApiClient apiClient;
  final TokenStore tokenStore;

  /// Source of the cold-start deep-link URI (widget contract §3); injectable
  /// for tests. Defaults to the native launch intent.
  final Future<String?> Function()? launchUriProvider;

  @override
  State<ConnectionScreen> createState() => _ConnectionScreenState();
}

class _ConnectionScreenState extends State<ConnectionScreen> {
  _Status _healthStatus = _Status.idle;
  _Status _meStatus = _Status.idle;
  String _healthDetail = 'Not checked yet';
  String _meDetail = 'Not checked yet';
  bool _hasToken = false;

  @override
  void initState() {
    super.initState();
    _refreshTokenState().then((_) {
      _checkAll();
      _routeLaunchUri();
    });
  }

  /// Widget auth-required state deep-links to `hwga://auth`; with no saved
  /// token it lands straight on the token screen (contracts_v2.md §3).
  Future<void> _routeLaunchUri() async {
    final uri = await (widget.launchUriProvider ?? WidgetBridge.launchUri)();
    if (uri == 'hwga://auth' && !_hasToken && mounted) {
      await _openTokenScreen();
    }
  }

  Future<void> _refreshTokenState() async {
    final token = await effectiveToken(widget.tokenStore);
    if (mounted) setState(() => _hasToken = token != null);
  }

  Future<void> _checkAll() async {
    await _checkHealth();
    await _checkMe();
  }

  Future<void> _checkHealth() async {
    setState(() {
      _healthStatus = _Status.loading;
      _healthDetail = 'Contacting server…';
    });
    try {
      final res = await widget.apiClient.getHealth();
      setState(() {
        _healthStatus = _Status.ok;
        _healthDetail = 'Server reachable (${res['status'] ?? 'ok'})';
        debugPrint('HWGA /health -> 200 ${res['status']}');
      });
    } on ApiException catch (e) {
      setState(() {
        _healthStatus = _Status.error;
        _healthDetail = e.displayMessage;
        debugPrint('HWGA /health -> FAIL ${e.displayMessage}');
      });
    }
  }

  Future<void> _checkMe() async {
    if (!_hasToken) {
      setState(() {
        _meStatus = _Status.error;
        _meDetail = 'Add a device token first';
      });
      return;
    }
    setState(() {
      _meStatus = _Status.loading;
      _meDetail = 'Checking token…';
    });
    try {
      final res = await widget.apiClient.getMe();
      final userId = (res['user_id'] as String?) ?? '?';
      final short = userId.length <= 8 ? userId : userId.substring(0, 8);
      setState(() {
        _meStatus = _Status.ok;
        _meDetail = 'Authenticated as $short… (${res['timezone'] ?? 'tz?'})';
        debugPrint('HWGA /me -> 200 user_id=$short tz=${res['timezone']}');
      });
    } on ApiException catch (e) {
      setState(() {
        _meStatus = _Status.error;
        _meDetail = e.isUnauthorized
            ? 'Token rejected (401)'
            : e.displayMessage;
      });
    }
  }

  Future<void> _openTokenScreen() async {
    await Navigator.of(context).push(
      MaterialPageRoute<bool>(
        builder: (_) => TokenScreen(tokenStore: widget.tokenStore),
      ),
    );
    await _refreshTokenState();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('HWGA'),
        actions: [
          IconButton(
            tooltip: 'Manage device token',
            icon: Icon(_hasToken ? Icons.key : Icons.key_off_outlined),
            onPressed: _openTokenScreen,
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _StatusCard(
            title: 'Backend connection',
            subtitle: widget.apiClient.baseUrl,
            status: _healthStatus,
            detail: _healthDetail,
            actionLabel: 'Check',
            onAction: _checkHealth,
          ),
          const SizedBox(height: 12),
          _StatusCard(
            title: 'Authenticated request',
            subtitle: _hasToken ? 'Device token saved' : 'No token saved',
            status: _meStatus,
            detail: _meDetail,
            actionLabel: 'Verify',
            onAction: _checkMe,
          ),
          const SizedBox(height: 24),
          if (_meStatus == _Status.ok)
            FilledButton.icon(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => HomeScreen(apiClient: widget.apiClient),
                ),
              ),
              icon: const Icon(Icons.today_outlined),
              label: const Text('Open today'),
            ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _openTokenScreen,
            icon: const Icon(Icons.badge_outlined),
            label: Text(_hasToken ? 'Update device token' : 'Set device token'),
          ),
        ],
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({
    required this.title,
    required this.subtitle,
    required this.status,
    required this.detail,
    required this.actionLabel,
    required this.onAction,
  });

  final String title;
  final String subtitle;
  final _Status status;
  final String detail;
  final String actionLabel;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final (icon, color) = switch (status) {
      _Status.idle => (Icons.circle_outlined, scheme.outline),
      _Status.loading => (Icons.sync, scheme.primary),
      _Status.ok => (Icons.check_circle_outline, scheme.primary),
      _Status.error => (Icons.error_outline, scheme.error),
    };
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 250),
              child: status == _Status.loading
                  ? SizedBox(
                      key: const ValueKey('loading'),
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: color,
                      ),
                    )
                  : Icon(icon, key: ValueKey(status), color: color),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleMedium),
                  Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
                  const SizedBox(height: 4),
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 250),
                    child: Text(
                      detail,
                      key: ValueKey(detail),
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            FilledButton.tonal(
              onPressed: status == _Status.loading ? null : onAction,
              child: Text(actionLabel),
            ),
          ],
        ),
      ),
    );
  }
}
