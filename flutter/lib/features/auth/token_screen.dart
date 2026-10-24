import 'package:flutter/material.dart';

import '../../core/api/token_store.dart';
import '../../core/config/app_config.dart';

/// Enter or rotate the single-user bearer token (D07). The token is shown
/// once by the backend bootstrap CLI and typed/pasted here; it is stored in
/// platform secure storage only.
class TokenScreen extends StatefulWidget {
  const TokenScreen({super.key, required this.tokenStore});

  final TokenStore tokenStore;

  @override
  State<TokenScreen> createState() => _TokenScreenState();
}

class _TokenScreenState extends State<TokenScreen> {
  final _controller = TextEditingController();
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _controller.text = AppConfig.devToken;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final token = _controller.text.trim();
    if (token.isEmpty) return;
    setState(() => _saving = true);
    await widget.tokenStore.write(token);
    if (mounted) Navigator.of(context).pop(true);
  }

  Future<void> _clear() async {
    await widget.tokenStore.clear();
    _controller.clear();
    if (mounted) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Device token')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Text(
            'Paste the bearer token issued by the backend bootstrap CLI. '
            'It is stored in this device\'s secure storage only.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _controller,
            obscureText: true,
            autocorrect: false,
            enableSuggestions: false,
            decoration: const InputDecoration(
              labelText: 'Bearer token',
              hintText: 'Provisioned token',
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _saving ? null : _save,
            icon: const Icon(Icons.save_outlined),
            label: const Text('Save token'),
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: _clear,
            child: const Text('Remove token from this device'),
          ),
        ],
      ),
    );
  }
}
