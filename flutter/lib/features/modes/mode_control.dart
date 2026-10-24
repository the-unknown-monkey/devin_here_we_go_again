import 'package:flutter/material.dart';

import '../../core/api/models.dart';
import '../timeline/timeline_view.dart';

/// Current-mode display + switch control. Both modes are presented as valid,
/// positive states — rest is never framed as failure.
class ModeControl extends StatelessWidget {
  const ModeControl({
    super.key,
    required this.current,
    required this.busy,
    required this.onSwitch,
  });

  final ModeIntervalItem? current;
  final bool busy;
  final VoidCallback onSwitch;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final mode = current?.mode;
    final next = mode == 'LOCKED_IN' ? 'PURE_FUN_RECOVERY' : 'LOCKED_IN';
    final elapsed = current?.durationMin;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(
              mode == 'LOCKED_IN'
                  ? Icons.center_focus_strong
                  : Icons.weekend_outlined,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    mode == null ? 'No mode set' : modeLabel(mode),
                    style: theme.textTheme.titleMedium,
                  ),
                  Text(
                    mode == null
                        ? 'Pick a mode to start the day'
                        : elapsed != null && elapsed > 0
                        ? 'For ${elapsed}m'
                        : 'Just started',
                    style: theme.textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            FilledButton.tonalIcon(
              onPressed: busy ? null : onSwitch,
              icon: const Icon(Icons.swap_horiz, size: 18),
              label: Text(
                mode == null ? 'Start' : 'Switch to ${modeLabel(next)}',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
