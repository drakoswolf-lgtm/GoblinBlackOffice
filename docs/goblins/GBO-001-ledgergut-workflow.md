# GBO-001: Ledgergut Receipt Reimbursement Workflow (v0.1)

> **Status:** Draft — Planning / Spec Only  
> **Agent:** Ledgergut  
> **Version:** 0.1  
> **Last Updated:** 2026-07-02

---

## 1. Purpose

Ledgergut is the Goblin Black Office agent responsible for processing employee receipt reimbursement requests. Its primary goal is to ingest submitted receipts, extract relevant financial data via OCR, validate that data against company policy, and produce a structured reimbursement record ready for payment or human review.

This document defines Ledgergut's v0.1 workflow — the minimum viable process for receipt reimbursement from submission through approval or rejection.

---

## 2. User Flow

1. **Employee submits receipt** — uploads an image (JPG/PNG) or PDF of a receipt through the GBO interface, along with a brief description of the expense.
2. **Ledgergut ingests submission** — receives the file and metadata (submitter ID, submission timestamp, expense category).
3. **OCR extraction** — Ledgergut runs optical character recognition on the receipt to extract key fields.
4. **Validation** — extracted fields are checked against reimbursement policy rules.
5. **Output generated** — a structured reimbursement record is produced.
6. **Routing decision:**
   - If all validations pass → record is queued for automated approval.
   - If any validation fails or confidence is low → record is flagged for human review.
7. **Human reviewer (if needed)** — reviews flagged records, overrides or confirms Ledgergut's output, and resolves the request.
8. **Employee notified** — submitter receives approval, partial approval, or rejection with reason.

---

## 3. Required Inputs

| Field               | Type        | Required | Notes                                         |
|---------------------|-------------|----------|-----------------------------------------------|
| `submitter_id`      | string      | Yes      | Employee identifier                           |
| `receipt_file`      | file upload | Yes      | JPG, PNG, or PDF; max 10 MB                   |
| `expense_category`  | enum        | Yes      | e.g. `travel`, `meals`, `supplies`, `other`   |
| `description`       | string      | Yes      | Short free-text reason for expense (max 500 chars) |
| `currency`          | string      | No       | ISO 4217 code; defaults to `USD` if omitted   |
| `submitted_at`      | datetime    | Auto     | Set by the system at time of submission       |

---

## 4. OCR / Extraction Fields

Ledgergut attempts to extract the following fields from the receipt image or PDF:

| Field              | Description                                          | Example               |
|--------------------|------------------------------------------------------|-----------------------|
| `vendor_name`      | Name of the merchant or vendor                       | `Goblin Grub Co.`     |
| `receipt_date`     | Date of the transaction on the receipt               | `2026-06-28`          |
| `line_items`       | List of individual items/services with prices        | `[{name, quantity, unit_price}]` |
| `subtotal`         | Pre-tax total                                        | `42.00`               |
| `tax_amount`       | Tax charged                                          | `3.78`                |
| `total_amount`     | Final amount charged (including tax and any fees)    | `45.78`               |
| `payment_method`   | How the transaction was paid (card, cash, etc.)      | `Visa ...1234`        |
| `receipt_number`   | Vendor-assigned receipt or transaction ID (if present) | `RCT-00421`         |
| `currency_symbol`  | Currency detected on receipt                         | `$`                   |

Each extracted field is accompanied by an internal **confidence score** (0.0–1.0). Fields with a confidence score below `0.75` are flagged for human review.

---

## 5. Validation Rules

The following rules are applied after extraction. Any failure routes the record to human review and may result in rejection.

| Rule ID | Field(s)          | Rule Description                                                    | Failure Action         |
|---------|-------------------|---------------------------------------------------------------------|------------------------|
| V-01    | `receipt_date`    | Receipt date must not be in the future.                             | Reject                 |
| V-02    | `receipt_date`    | Receipt must be submitted within 90 days of the transaction date.   | Reject                 |
| V-03    | `total_amount`    | Total amount must be greater than `0`.                              | Reject                 |
| V-04    | `total_amount`    | Total amount must not exceed the per-category limit (see policy).   | Flag for human review  |
| V-05    | `total_amount`    | Subtotal + tax must equal total (within ±$0.05 rounding tolerance). | Flag for human review  |
| V-06    | `expense_category`| Category must match one of the approved enum values.                | Reject                 |
| V-07    | `vendor_name`     | Vendor name must be present and non-empty after OCR.                | Flag for human review  |
| V-08    | `currency`        | Detected currency must match submitted currency (if provided).      | Flag for human review  |
| V-09    | (any field)       | Any OCR confidence score below `0.75`.                              | Flag for human review  |
| V-10    | `submitter_id`    | Submitter must exist in the employee directory.                     | Reject                 |

**Per-category limits (v0.1 defaults):**

| Category   | Limit (USD) |
|------------|-------------|
| `travel`   | $500.00     |
| `meals`    | $75.00      |
| `supplies` | $150.00     |
| `other`    | $100.00     |

---

## 6. Output Format

Ledgergut produces a structured reimbursement record in JSON format:

```json
{
  "record_id": "LG-20260702-0042",
  "submitter_id": "emp-1138",
  "submitted_at": "2026-07-02T14:30:00Z",
  "expense_category": "meals",
  "description": "Team lunch with client",
  "receipt": {
    "vendor_name": "Goblin Grub Co.",
    "receipt_date": "2026-07-01",
    "receipt_number": "RCT-00421",
    "line_items": [
      { "name": "Lunch special x4", "quantity": 4, "unit_price": 12.50 }
    ],
    "subtotal": 50.00,
    "tax_amount": 4.50,
    "total_amount": 54.50,
    "payment_method": "Visa ...1234",
    "currency": "USD"
  },
  "ocr_confidence": {
    "vendor_name": 0.95,
    "receipt_date": 0.98,
    "total_amount": 0.91,
    "overall": 0.94
  },
  "validation_results": [
    { "rule_id": "V-01", "passed": true },
    { "rule_id": "V-02", "passed": true },
    { "rule_id": "V-03", "passed": true },
    { "rule_id": "V-04", "passed": true },
    { "rule_id": "V-05", "passed": true }
  ],
  "status": "approved",
  "flagged_for_review": false,
  "review_notes": null,
  "created_at": "2026-07-02T14:30:05Z"
}
```

**Status values:** `pending_review` | `approved` | `rejected` | `partial_approval`

---

## 7. Human Review Step

Records flagged for human review (`flagged_for_review: true`) enter the **Ledgergut Review Queue**. A human reviewer (Finance team or designated approver) performs the following:

1. **View flagged fields** — the UI highlights fields with low OCR confidence or validation failures.
2. **Verify against receipt image** — reviewer compares extracted data to the original uploaded receipt.
3. **Override or confirm** — reviewer can:
   - Correct any extracted field value.
   - Override a validation failure with a written justification.
   - Mark the record as `approved`, `rejected`, or `partial_approval`.
4. **Add review notes** — required when overriding a rejection or approving over a category limit.
5. **Submit decision** — the record is updated and the submitter is notified.

**SLA (v0.1 target):** Human review completed within 2 business days of flagging.

---

## 8. Known Failure Cases

| Case                          | Description                                                                                   | Current Handling                        |
|-------------------------------|-----------------------------------------------------------------------------------------------|-----------------------------------------|
| Blurry or dark receipt image  | OCR produces low-confidence scores across most fields                                         | Entire record flagged for human review  |
| Handwritten receipts          | OCR accuracy degrades significantly on handwritten text                                       | Flag; may require manual re-entry       |
| Multi-receipt uploads         | User uploads a single file containing multiple receipts                                       | Only first receipt is processed; rest ignored in v0.1 |
| Non-USD foreign receipts      | Currency conversion not yet implemented                                                        | Flagged for human review; reviewer sets USD equivalent manually |
| Corrupted or unsupported file | File cannot be opened or parsed (e.g., encrypted PDF, unsupported image format)               | Submission rejected with error message  |
| Duplicate submission          | Same receipt (same vendor, date, and total) submitted more than once by the same employee     | Flagged as potential duplicate; human review required |
| Missing total on receipt      | Receipt shows only line items; no printed total                                               | Ledgergut calculates sum; flagged for confirmation |
| Vendor name not extracted     | OCR fails to identify a vendor name (blank or garbled)                                        | Rule V-07 triggers; flagged for review  |

---

## 9. Future Automation Ideas

The following improvements are out of scope for v0.1 but are candidates for future iterations:

- **Currency conversion** — automatically convert foreign-currency receipts to USD using a live exchange rate API at time of submission.
- **Multi-receipt batch upload** — allow a single submission to contain multiple receipts, each extracted and validated independently.
- **Duplicate detection** — fuzzy matching on vendor name, date, and amount to automatically detect and surface duplicate submissions before human review.
- **Policy rule engine** — configurable, admin-editable rules replacing hardcoded per-category limits and validation thresholds.
- **Vendor database enrichment** — cross-reference extracted vendor names against a known-vendor registry to improve accuracy and flag unusual merchants.
- **Line-item categorization** — automatically map individual line items to expense subcategories (e.g., alcohol detection on meal receipts).
- **Employee spending dashboards** — aggregate reimbursement history per employee for budget tracking and anomaly detection.
- **Straight-through processing (STP)** — for high-confidence, low-value, repeat-vendor receipts, skip human review entirely and auto-approve.
- **Mobile receipt capture** — guided mobile upload flow with real-time image quality feedback before submission.
- **ERP/accounting system integration** — push approved reimbursement records directly into payroll or accounts payable systems.
