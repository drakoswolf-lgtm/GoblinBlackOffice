# GBO-001: Ledgergut Founder/Operator Receipt Intelligence Workflow (v0.2)

> **Status:** Draft — Planning / Spec Only
> **Agent:** Ledgergut
> **Version:** 0.2
> **Last Updated:** 2026-07-03

---

## 1. Purpose

Ledgergut is the Goblin Black Office agent responsible for turning receipts into usable operating records. Its primary goal is to ingest submitted receipts, extract relevant financial data via OCR, assign operational context, determine whether the cost is reimbursable or billable, and route the record to the next goblin or reviewer.

Ledgergut v0.2 is designed first for the real Goblin Black Office founder/operator workflow. Generic employee reimbursement remains supported as a future collar profile, but it is not the default assumption for v0.2.

---

## 2. Founder/Operator Priority

The first supported operating mode for Ledgergut is the founder/operator workflow used by Goblin Black Office.

The primary questions Ledgergut should answer are:

1. **What job/project does this receipt belong to?**
2. **Who paid for it?**
3. **Does anyone owe the owner money for it?**
4. **Should Squarmish include it on an invoice?**

Black Collar mode prioritizes contractor receipts, project/job assignment, billable expense detection, reimbursement tracking, and invoice handoff over department-policy reimbursement rules.

---

## 3. Collar System

Goblin Black Office uses a **Collar System** to adapt the base app to different real-world workflows.

A Collar is both:

- A visual identity layer for goblin agents.
- A functional configuration profile.

Collars define vocabulary, required fields, workflow behavior, defaults, validation rules, tone, and handoff logic between goblins.

The first supported collar is the **Black Collar**, optimized for the founder/operator workflow. This mode prioritizes practical receipt capture, project assignment, reimbursement tracking, billable expense detection, and invoice handoff.

Future collars may include Blue Collar, White Collar, Service Collar, Tie-Dye Collar, Green Collar, Gold Collar, Red Collar, and Grey Collar.

The base app should avoid hardcoding one business model. It should expose neutral internal concepts that each Collar can interpret through its own vocabulary and rule set.

---

## 4. Initial Collar Concepts

| Collar | Primary Use |
|--------|-------------|
| **Black Collar** | Founder/operator mode. Steve-first defaults, Goblin Black Office command mode. |
| **Blue Collar** | Trades, contractors, construction, materials, reimbursements, client billing. |
| **White Collar** | Office/corporate reimbursement workflows, departments, approvals, policy compliance. |
| **Service Collar** | Hospitality, venue work, service-industry expenses, and shift/site-linked records. |
| **Tie-Dye Collar** | Artist/creative mode for music, art, studio costs, promo, merch, video shoots, and project budgets. |
| **Green Collar** | Landscaping/property-maintenance mode, recurring sites, dump runs, plants, tools, and materials. |
| **Gold Collar** | Premium/client-facing output, polished proposals, estimates, summaries, and presentation-ready documents. |
| **Red Collar** | Urgent money-recovery mode, overdue invoices, missing receipts, and deadline triage. |
| **Grey Collar** | Unknown/mixed sorting mode for unclear receipts and records requiring review. |

---

## 5. User Flow

1. **Founder/operator submits receipt** — uploads an image (JPG/PNG) or PDF through the GBO interface with any known project or payment notes.
2. **Ledgergut ingests submission** — receives the file and metadata (`submitted_by`, timestamp, collar, optional project context).
3. **OCR extraction** — Ledgergut extracts vendor, dates, amounts, taxes, and other receipt fields.
4. **Context assignment** — Ledgergut attempts to infer project/job, payer, reimbursement state, and billable state.
5. **Validation** — extracted and inferred fields are checked against collar-specific rules.
6. **Routing decision** — Ledgergut produces a structured receipt record and assigns queues or handoffs:
   - **Review Queue** if confidence is low or required context is missing.
   - **Reimbursement Tracking** if the payer should be paid back.
   - **Squarmish Invoice Candidate Queue** if the receipt may become a client invoice line item.
7. **Human reviewer (if needed)** — founder/operator or designated reviewer confirms or corrects the record.
8. **Downstream goblin handoff** — Squarmish receives billable candidates; other goblins may receive payment, policy, or audit tasks later.

---

## 6. Required Inputs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `submitted_by` | string | Yes | User or operator identifier |
| `receipt_file` | file upload | Yes | JPG, PNG, or PDF; max 10 MB |
| `description` | string | Yes | Short free-text note about the expense |
| `collar_id` | enum | Auto / Yes | Defaults to `black_collar` in Goblin Black Office |
| `project_name` | string | No | Known project/job/site name if the submitter has it |
| `paid_by` | enum | No | Optional at submission; can be inferred later |
| `expense_category` | string | No | Optional neutral category for reporting |
| `currency` | string | No | ISO 4217 code; defaults come from the active collar |
| `submitted_at` | datetime | Auto | Set by the system at submission time |

---

## 7. OCR / Extraction Fields

Ledgergut attempts to extract the following fields from the receipt image or PDF:

| Field | Description | Example |
|-------|-------------|---------|
| `vendor_name` | Name of the merchant or vendor | `Home Hardware` |
| `receipt_date` | Date of the transaction on the receipt | `2026-06-28` |
| `line_items` | List of individual items/services with prices | `[{name, quantity, unit_price}]` |
| `subtotal` | Pre-tax total | `42.00` |
| `tax_lines` | Detected tax labels and amounts | `[{label: "GST", amount: 2.10}]` |
| `tax_amount` | Total tax charged | `3.78` |
| `total_amount` | Final amount charged including tax and fees | `45.78` |
| `payment_method` | How the transaction was paid | `Visa ...1234` |
| `receipt_number` | Vendor-assigned receipt or transaction ID | `RCT-00421` |
| `currency_symbol` | Currency detected on receipt | `$` |

Each extracted field is accompanied by an internal **confidence score** (0.0–1.0). Fields with a confidence score below `0.75` are flagged for review.

---

## 8. Operating Context / Classification Fields

In addition to OCR fields, Ledgergut produces workflow fields for project assignment, reimbursement tracking, and invoice handoff.

```json
{
  "project_name": "Jackson Retail",
  "paid_by": "steve",
  "reimbursement_status": "not_reimbursed",
  "billable_status": "maybe_billable",
  "invoice_id": null,
  "payment_notes": "Paid personally; check whether client reimbursed",
  "assignment_confidence": 0.82,
  "needs_user_review": true
}
```

### Suggested enums

**`paid_by`**

- `steve`
- `company_card`
- `client_card`
- `rob_visa`
- `cash`
- `unknown`

**`reimbursement_status`**

- `not_reimbursed`
- `reimbursed`
- `maybe_reimbursed`
- `not_reimbursable`
- `unknown`

**`billable_status`**

- `billable`
- `not_billable`
- `maybe_billable`
- `already_invoiced`
- `tax_only`

---

## 9. Validation Rules

The following rules are applied after extraction and context assignment. Any failure can set `needs_user_review: true`, route the record to a human queue, or trigger a collar-specific rejection.

| Rule ID | Field(s) | Rule Description | Failure Action |
|---------|----------|------------------|----------------|
| V-01 | `receipt_date` | Receipt date must not be in the future. | Reject |
| V-02 | `receipt_date` | Receipt age is evaluated by the active collar. Black Collar flags stale receipts for review; White Collar may reject based on policy window. | Collar-specific |
| V-03 | `total_amount` | Total amount must be greater than `0`. | Reject |
| V-04 | `total_amount`, `subtotal`, `tax_amount` | Subtotal + tax must equal total within ±0.05 rounding tolerance. | Flag for review |
| V-05 | `project_name`, `assignment_confidence` | Black Collar records should have a project/job assignment or be flagged as uncertain. | Flag for review |
| V-06 | `paid_by` | Payer must resolve to a known enum value or `unknown`. | Flag for review |
| V-07 | `currency` | Detected currency should match the submitted currency or collar default when possible. | Flag for review |
| V-08 | `billable_status` | Receipts marked `already_invoiced` should retain an invoice reference when available. | Flag for review |
| V-09 | (any OCR field) | Any OCR confidence score below `0.75`. | Flag for review |
| V-10 | `vendor_name`, `receipt_date`, `total_amount`, `project_name`, `paid_by` | Potential duplicate receipt detected. | Flag for review |
| V-11 | collar-specific fields | White Collar and future collars may add directory, department, approval, or policy checks. | Collar-specific |

### Black Collar default assumptions

| Setting | Default |
|---------|---------|
| `default_currency` | `CAD` |
| `tax_labels` | `GST`, `PST`, `HST` |
| `project_assignment_required` | Yes, unless explicitly unknown |
| `stale_receipt_behavior` | Flag for review rather than auto-reject |
| `invoice_handoff_enabled` | Yes |

---

## 10. Squarmish Handoff Logic

Ledgergut should identify receipts that may become invoice line items.

**Initial rule:**

- If `paid_by = steve` and `billable_status = billable` or `maybe_billable`, add the receipt to the **Squarmish Invoice Candidate Queue**.

This handoff is central to Goblin Black Office:

- **Ledgergut** finds and structures the receipts.
- **Squarmish** turns billable ones into invoice candidates and eventual invoice line items.

---

## 11. Output Format

Ledgergut produces a structured receipt record in JSON format:

```json
{
  "record_id": "LG-20260703-0042",
  "collar_id": "black_collar",
  "submitted_by": "steve",
  "submitted_at": "2026-07-03T14:30:00Z",
  "description": "Materials for Jackson Retail patch job",
  "project_name": "Jackson Retail",
  "expense_category": "materials",
  "paid_by": "steve",
  "reimbursement_status": "not_reimbursed",
  "billable_status": "maybe_billable",
  "invoice_id": null,
  "payment_notes": "Paid personally; check whether client reimbursed",
  "assignment_confidence": 0.82,
  "receipt": {
    "vendor_name": "Home Hardware",
    "receipt_date": "2026-07-01",
    "receipt_number": "RCT-00421",
    "line_items": [
      { "name": "Fasteners", "quantity": 2, "unit_price": 12.50 }
    ],
    "subtotal": 25.00,
    "tax_lines": [
      { "label": "GST", "amount": 1.25 },
      { "label": "PST", "amount": 1.75 }
    ],
    "tax_amount": 3.00,
    "total_amount": 28.00,
    "payment_method": "Visa ...1234",
    "currency": "CAD"
  },
  "ocr_confidence": {
    "vendor_name": 0.95,
    "receipt_date": 0.98,
    "total_amount": 0.91,
    "overall": 0.94
  },
  "validation_results": [
    { "rule_id": "V-01", "passed": true },
    { "rule_id": "V-04", "passed": true },
    { "rule_id": "V-05", "passed": true },
    { "rule_id": "V-09", "passed": true }
  ],
  "handoffs": [
    {
      "target": "squarmish",
      "queue": "invoice_candidate",
      "reason": "paid_by=steve and billable_status=maybe_billable"
    }
  ],
  "status": "pending_review",
  "needs_user_review": true,
  "review_notes": null,
  "created_at": "2026-07-03T14:30:05Z"
}
```

**Status values:** `pending_review` | `approved` | `rejected` | `partial_approval`

---

## 12. Human Review Step

Records flagged for human review (`needs_user_review: true`) enter the **Ledgergut Review Queue**. A founder/operator or designated reviewer performs the following:

1. **View flagged fields** — the UI highlights low-confidence OCR fields, uncertain project assignments, and validation failures.
2. **Verify against the receipt image** — reviewer compares extracted data to the original uploaded receipt.
3. **Resolve operating context** — reviewer can:
   - Correct project/job assignment.
   - Confirm who paid.
   - Set reimbursement and billable status.
   - Attach or clear an invoice reference.
4. **Override or confirm** — reviewer can approve, reject, or partially approve the record with justification.
5. **Submit decision** — the record is updated and any downstream goblin queues are refreshed.

**SLA (v0.2 target):** Human review completed within 2 business days of flagging.

---

## 13. Currency and Tax Defaults

Currency and tax handling should be collar-driven rather than hardcoded into the base app.

| Layer | Behavior |
|-------|----------|
| **Base app** | Currency is configurable. Tax labels are configurable metadata. |
| **Black Collar** | `default_currency = CAD`; preferred tax labels include `GST`, `PST`, and `HST`. |
| **White Collar** | Currency and tax labels are determined by organization settings. |

---

## 14. White Collar / Future Employee Reimbursement

The existing employee reimbursement concepts remain valid, but they should be treated as a future **White Collar** profile rather than the default Ledgergut worldview.

White Collar examples may include:

- Employee directory validation
- Department and approver chains
- Policy-driven category limits
- Corporate-card vs personal-spend reimbursement rules
- Standardized HR/finance notifications

This keeps the current reimbursement structure available without making it the core v0.2 product assumption.

---

## 15. Known Failure Cases

| Case | Description | Current Handling |
|------|-------------|------------------|
| Blurry or dark receipt image | OCR produces low-confidence scores across most fields | Entire record flagged for review |
| Handwritten receipts | OCR accuracy degrades significantly on handwritten text | Flag; may require manual re-entry |
| Mixed personal and billable receipt | One receipt contains both owner expense and client-billable items | Flag for review; split decisions manually |
| Unclear project assignment | Vendor and notes do not make the job/project obvious | `assignment_confidence` drops; review required |
| Multi-receipt uploads | User uploads a single file containing multiple receipts | Only first receipt is processed in v0.2 |
| Foreign-currency receipt | Receipt currency differs from the collar default | Flag for review; preserve detected currency |
| Corrupted or unsupported file | File cannot be opened or parsed | Submission rejected with error message |
| Duplicate submission | Same vendor/date/total/payer/project appears more than once | Flagged as potential duplicate |
| Missing total on receipt | Receipt shows line items but no printed total | Ledgergut calculates sum; flagged for confirmation |
| Already invoiced expense | Receipt appears billable but may already be attached to an invoice | Flag for review before Squarmish handoff |

---

## 16. Monetization Scaffolding

Goblin Black Office may support paid upgrades, collar packs, cosmetic goblin accessories, template bundles, automation credits, or premium workflows in the future.

Monetization is **not** part of the v0.2 product goal. The v0.2 goal is to build a useful owner/operator app first, with clean architectural scaffolding for future monetization where required.

### Principles

1. Core records must never be locked behind payment.
2. Users must always be able to access and export their own data.
3. Monetization hooks should not affect the default v0.2 workflow.
4. Paid features should add specialization, automation, cosmetics, templates, or scale — not remove core usefulness.
5. The Collar System should support future entitlement checks, but collars should begin as ordinary configuration profiles.
6. No gambling mechanics, loot boxes, artificial urgency timers, or deliberately confusing upgrade paths.

### Dormant entitlement fields

```json
{
  "feature_key": "blue_collar_advanced_job_costing",
  "requires_entitlement": false,
  "entitlement_key": null,
  "is_cosmetic": false,
  "is_core_feature": true,
  "monetization_status": "inactive"
}
```

---

## 17. Future Automation Ideas

The following improvements are out of scope for v0.2 but are candidates for future iterations:

- **Project assignment enrichment** — use prior receipts, client lists, and note history to improve `project_name` prediction.
- **Invoice candidate confirmation loops** — let Squarmish return invoice outcomes back to Ledgergut for learning and deduplication.
- **Currency conversion** — convert foreign receipts to a collar reporting currency while preserving original values.
- **Multi-receipt batch upload** — allow one submission to contain multiple receipts processed independently.
- **Duplicate detection** — fuzzy matching on vendor name, date, amount, payer, and project.
- **Policy rule engine** — admin-editable collar rules replacing hardcoded thresholds.
- **Vendor database enrichment** — cross-reference extracted vendors against known merchants or client histories.
- **Line-item categorization** — detect materials, meals, travel, tax-only items, or reimbursable vs non-billable splits.
- **Straight-through processing** — auto-approve high-confidence, low-risk records with no unresolved routing questions.
- **ERP/accounting system integration** — push approved records into bookkeeping, payroll, or accounts receivable systems.
