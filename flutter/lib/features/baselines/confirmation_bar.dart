import 'package:flutter/material.dart';

/// One-tap baseline confirmations (contracts ConfirmationKind) plus a quiet
/// moment. Pure presentation: the parent owns the API call and idempotency
/// key; taps are disabled while a save is in flight so a double tap can't
/// fire two writes.
class ConfirmationBar extends StatelessWidget {
  const ConfirmationBar({
    super.key,
    required this.busy,
    required this.onConfirm,
    required this.onQuietMoment,
  });

  final bool busy;
  final void Function(String kind) onConfirm;
  final VoidCallback onQuietMoment;

  static const _kinds = <(String, IconData, String)>[
    ('WATER', Icons.water_drop_outlined, 'Water'),
    ('FOOD_CLEAN', Icons.restaurant_outlined, 'Clean meal'),
    ('STRETCH', Icons.self_improvement_outlined, 'Stretch'),
    ('POSTURE_RESET', Icons.accessibility_new_outlined, 'Posture'),
    ('WALK', Icons.directions_walk_outlined, 'Walk'),
  ];

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final (kind, icon, label) in _kinds)
          ActionChip(
            avatar: Icon(icon, size: 18),
            label: Text(label),
            onPressed: busy ? null : () => onConfirm(kind),
          ),
        ActionChip(
          avatar: const Icon(Icons.spa_outlined, size: 18),
          label: const Text('Quiet moment'),
          onPressed: busy ? null : onQuietMoment,
        ),
      ],
    );
  }
}
