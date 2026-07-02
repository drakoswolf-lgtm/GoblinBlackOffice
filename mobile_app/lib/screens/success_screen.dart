import 'package:flutter/material.dart';

import '../models/receipt_draft.dart';

class SuccessScreen extends StatelessWidget {
  const SuccessScreen({
    super.key,
    required this.draft,
    required this.onDone,
  });

  final ReceiptDraft draft;
  final VoidCallback onDone;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reimbursement Ready')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text('Receipt for ${draft.vendor} is ready to save, share, or export.'),
              ),
            ),
            const SizedBox(height: 16),
            _actionButton(context, 'Save'),
            const SizedBox(height: 12),
            _actionButton(context, 'Share'),
            const SizedBox(height: 12),
            _actionButton(context, 'Export'),
            const Spacer(),
            OutlinedButton(onPressed: onDone, child: const Text('Back to Home')),
          ],
        ),
      ),
    );
  }

  Widget _actionButton(BuildContext context, String label) {
    return FilledButton(
      onPressed: () {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$label action is ready for integration.')),
        );
      },
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14),
        child: Text(label),
      ),
    );
  }
}
