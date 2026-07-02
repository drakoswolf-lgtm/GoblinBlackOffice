class ReceiptDraft {
  ReceiptDraft({
    required this.vendor,
    required this.date,
    required this.totalPaid,
    required this.purchaseGroup,
    required this.claimantName,
    required this.receiptImagePath,
    required this.confidenceFlags,
  });

  String vendor;
  String date;
  String totalPaid;
  String purchaseGroup;
  String claimantName;
  String receiptImagePath;
  Map<String, double> confidenceFlags;
}
