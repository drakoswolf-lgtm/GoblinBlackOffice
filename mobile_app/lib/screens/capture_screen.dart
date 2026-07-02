import 'package:flutter/material.dart';

import '../models/receipt_draft.dart';
import '../services/ledgergut_service.dart';

class CaptureScreen extends StatefulWidget {
  const CaptureScreen({
    super.key,
    required this.onDraftReady,
    required this.onBack,
  });

  final ValueChanged<ReceiptDraft> onDraftReady;
  final VoidCallback onBack;

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  final LedgergutService _service = LedgergutService();
  bool _isProcessing = false;
  String _status = '';

  Future<void> _process(String source) async {
    setState(() {
      _isProcessing = true;
      _status = LedgergutService.statusMessages.first;
    });

    for (final message in LedgergutService.statusMessages) {
      await Future<void>.delayed(const Duration(milliseconds: 300));
      if (!mounted) {
        return;
      }
      setState(() => _status = message);
    }

    final draft = await _service.extractMock(
      source: source,
      claimantName: 'Default Claimant',
    );

    if (!mounted) {
      return;
    }
    setState(() => _isProcessing = false);
    widget.onDraftReady(draft);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: widget.onBack,
          icon: const Icon(Icons.arrow_back),
        ),
        title: const Text('Ledgergut Capture'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            FilledButton.icon(
              onPressed: _isProcessing ? null : () => _process('camera://capture'),
              icon: const Icon(Icons.photo_camera),
              label: const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Text('Capture Receipt'),
              ),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _isProcessing ? null : () => _process('file://upload'),
              icon: const Icon(Icons.upload_file),
              label: const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Text('Upload Receipt'),
              ),
            ),
            const SizedBox(height: 24),
            if (_isProcessing)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(_status),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
