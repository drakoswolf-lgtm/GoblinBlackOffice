import '../models/receipt_draft.dart';

class LedgergutService {
  static const List<String> statusMessages = [
    'Ledgergut is examining the tribute...',
    'Vendor identified.',
    'Total extracted.',
    'Receipt image secured.',
    'Reimbursement package prepared.',
  ];

  Future<ReceiptDraft> extractMock({
    required String source,
    required String claimantName,
  }) async {
    await Future<void>.delayed(const Duration(milliseconds: 600));
    return ReceiptDraft(
      vendor: 'Goblin Supply Co.',
      date: '2026-07-02',
      totalPaid: '42.50',
      purchaseGroup: 'Materials',
      claimantName: claimantName,
      receiptImagePath: source,
      confidenceFlags: {
        'vendor': 0.96,
        'date': 0.92,
        'totalPaid': 0.94,
      },
    );
  }

  Future<bool> generateReimbursement(ReceiptDraft draft) async {
    await Future<void>.delayed(const Duration(milliseconds: 500));
    return true;
  }
}
