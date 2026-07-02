import 'package:flutter/material.dart';

import '../models/receipt_draft.dart';
import '../services/ledgergut_service.dart';

class ReviewScreen extends StatefulWidget {
  const ReviewScreen({
    super.key,
    required this.draft,
    required this.onGenerateSuccess,
    required this.onBack,
  });

  final ReceiptDraft draft;
  final ValueChanged<ReceiptDraft> onGenerateSuccess;
  final VoidCallback onBack;

  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  final _formKey = GlobalKey<FormState>();
  final LedgergutService _service = LedgergutService();
  bool _isGenerating = false;

  late final TextEditingController _vendorController;
  late final TextEditingController _dateController;
  late final TextEditingController _totalController;
  late final TextEditingController _purchaseGroupController;
  late final TextEditingController _claimantController;

  @override
  void initState() {
    super.initState();
    _vendorController = TextEditingController(text: widget.draft.vendor);
    _dateController = TextEditingController(text: widget.draft.date);
    _totalController = TextEditingController(text: widget.draft.totalPaid);
    _purchaseGroupController = TextEditingController(text: widget.draft.purchaseGroup);
    _claimantController = TextEditingController(text: widget.draft.claimantName);
  }

  @override
  void dispose() {
    _vendorController.dispose();
    _dateController.dispose();
    _totalController.dispose();
    _purchaseGroupController.dispose();
    _claimantController.dispose();
    super.dispose();
  }

  Future<void> _generate() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final updated = ReceiptDraft(
      vendor: _vendorController.text,
      date: _dateController.text,
      totalPaid: _totalController.text,
      purchaseGroup: _purchaseGroupController.text,
      claimantName: _claimantController.text,
      receiptImagePath: widget.draft.receiptImagePath,
      confidenceFlags: widget.draft.confidenceFlags,
    );

    setState(() => _isGenerating = true);
    final success = await _service.generateReimbursement(updated);
    if (!mounted) {
      return;
    }

    setState(() => _isGenerating = false);
    if (success) {
      widget.onGenerateSuccess(updated);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: widget.onBack,
          icon: const Icon(Icons.arrow_back),
        ),
        title: const Text('Review Receipt'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              _field('Vendor', _vendorController),
              _field('Date', _dateController),
              _field(
                'Total Paid',
                _totalController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
              _field('Purchase Group', _purchaseGroupController),
              _field('Claimant Name', _claimantController),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: _isGenerating ? null : _generate,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  child: Text(_isGenerating ? 'Generating...' : 'Generate Reimbursement'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _field(
    String label,
    TextEditingController controller, {
    TextInputType keyboardType = TextInputType.text,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
        validator: (value) {
          if (value == null || value.trim().isEmpty) {
            return 'Required';
          }
          return null;
        },
      ),
    );
  }
}
