# GBO-002: Squarmish Invoice Workflow (v0.1)

> **Status:** Draft — Planning / Spec Only
> **Agent:** Squarmish
> **Role:** Invoice Goblin
> **Version:** 0.1
> **Last Updated:** 2026-07-03

---

## 1. Purpose

Squarmish is the Goblin Black Office agent responsible for turning billable receipt records into invoice drafts. Its primary job is to receive candidates from Ledgergut's Invoice Candidate Queue, group them by client and project, add any applicable labour or additional line items, apply correct CAD tax treatment, and produce a draft invoice ready for human review before it goes out the door.

Squarmish does not send invoices autonomously. It prepares, organizes, and flags. A human always reviews before anything is issued.

---

## 2. Founder/Operator Priority

Squarmish v0.1 is designed first for the Black Collar founder/operator workflow.

The core questions Squarmish must answer are:

1. **Which client/project is this invoice for?**
2. **Which Ledgergut receipt records belong on it?**
3. **Which labour, materials, or fees should be added?**
4. **What has already been billed?**
5. **What still needs review before sending?**
6. **What total is owed?**

Black Collar mode prioritizes practical money recovery: get the right receipts on the right invoice, catch anything unbilled, and get it in front of the founder for sign-off before it is ever sent.

---

## 3. Relationship to Ledgergut

Squarmish does not ingest receipts or perform OCR. That is Ledgergut's job.

The hand-off works as follows:

- **Ledgergut** processes a receipt and determines `billable_status = billable` or `maybe_billable`.
- If `paid_by = steve` and the billable status qualifies, Ledgergut writes the receipt record to the **Squarmish Invoice Candidate Queue**.
- **Squarmish** picks up the queue, groups candidates by `project_name` and inferred client, and begins building or updating a draft invoice.

Squarmish should never pull a record that Ledgergut has flagged as `already_invoiced` unless a human explicitly asks for a review of that record.

---

## 4. Invoice Candidate Queue

The Invoice Candidate Queue is the shared hand-off surface between Ledgergut and Squarmish.

Each queue entry carries the full Ledgergut receipt record (see GBO-001, Section 11) plus the following Squarmish-facing summary fields:

| Field | Type | Notes |
|-------|------|-------|
| `record_id` | string | Ledgergut record ID, e.g. `LG-20260703-0042` |
| `project_name` | string | Assigned project from Ledgergut |
| `paid_by` | enum | Payer identifier from Ledgergut |
| `billable_status` | enum | `billable` or `maybe_billable` |
| `total_amount` | decimal | Receipt total including tax |
| `currency` | string | ISO 4217, e.g. `CAD` |
| `vendor_name` | string | Extracted vendor name |
| `receipt_date` | date | Receipt date |
| `queued_at` | datetime | When the record was added to the queue |
| `invoice_id` | string or null | Populated once Squarmish attaches it to a draft |

Records remain in the queue until:
- Squarmish attaches them to a draft invoice (`invoice_id` is set), or
- A human removes or dismisses the record from the queue.

---

## 5. Required Inputs

Before Squarmish can produce a draft invoice, the following information must be confirmed or resolvable:

| Field | Source | Notes |
|-------|--------|-------|
| `client_name` | Project mapping / human input | Derived from `project_name` or manually set |
| `project_name` | Ledgergut record | Must exist; ambiguous records require human resolution |
| `currency` | Collar default or human input | Default `CAD` in Black Collar mode |
| `tax_region` | Collar default or human input | e.g. `BC` — drives GST/PST vs HST logic |
| `invoice_date` | Human input or auto-set | Date of draft creation; adjustable before issue |
| `due_date` | Human input or template | Payment terms applied from collar or manually set |
| `line_items` | Receipt records + manual entries | Materials, labour, fees from Ledgergut or added by reviewer |

Squarmish should surface any missing required inputs to the human reviewer before marking a draft as ready to send.

---

## 6. Invoice Draft Fields

A Squarmish draft invoice contains the following top-level fields:

| Field | Type | Notes |
|-------|------|-------|
| `invoice_id` | string | System-generated, e.g. `SQ-20260703-0001` |
| `collar_id` | enum | Active collar; default `black_collar` |
| `client_name` | string | Billing target |
| `project_name` | string | Associated project or job |
| `invoice_date` | date | Date of draft |
| `due_date` | date | Payment due date |
| `currency` | string | ISO 4217 |
| `tax_region` | string | Province or jurisdiction code |
| `line_items` | array | See Section 9 |
| `linked_ledgergut_records` | array | `record_id` references from Ledgergut |
| `subtotal` | decimal | Sum of line item amounts before tax |
| `tax_lines` | array | `[{label, rate, amount}]` |
| `total` | decimal | `subtotal` + all tax amounts |
| `status` | enum | See Section 12 |
| `needs_user_review` | boolean | True if any field or line item is unresolved |
| `review_notes` | string or null | Squarmish's explanation of what needs attention |
| `created_at` | datetime | When the draft was created |
| `updated_at` | datetime | When the draft was last modified |

---

## 7. Client / Project Assignment

Squarmish derives `client_name` from `project_name` using a project-to-client mapping.

In v0.1:
- If a project-to-client mapping exists, it is applied automatically.
- If no mapping exists, `client_name` defaults to `null` and `needs_user_review` is set to `true`.
- The human reviewer sets or confirms the client before the draft can be marked ready to send.

Multiple projects may belong to the same client. Squarmish should support grouping multiple projects onto one invoice when the reviewer requests it, but the default behaviour in v0.1 is one invoice per project.

---

## 8. Billable Receipt Handling

Each Ledgergut receipt in the Invoice Candidate Queue becomes a candidate line item on the draft invoice.

Squarmish resolves `billable_status` for each record:

| Ledgergut Status | Squarmish Handling |
|------------------|-------------------|
| `billable` | Include as a confirmed line item |
| `maybe_billable` | Include as a flagged line item with `review_status = needs_review` |
| `already_invoiced` | Excluded by default; surfaced in review notes if detected |
| `not_billable` | Not included |

If a receipt is included as `maybe_billable`, the review note should explain which field made it uncertain (e.g. missing project assignment, low OCR confidence).

---

## 9. Labour Line Handling

Labour lines are not sourced from Ledgergut receipts. They are entered manually or templated by the reviewer.

A labour line item includes:

| Field | Type | Notes |
|-------|------|-------|
| `description` | string | e.g. `Site labour — Jackson Retail patch` |
| `quantity` | decimal | Hours or units |
| `unit` | string | e.g. `hr`, `day`, `flat` |
| `unit_price` | decimal | Rate per unit |
| `amount` | decimal | `quantity × unit_price` |
| `line_item_type` | enum | `labour` |
| `billable_status` | enum | Typically `billable` |
| `review_status` | enum | `confirmed` if entered by reviewer |

In v0.1, labour lines are added during the human review step. Future automation may pull from a time-tracking or scheduling goblin.

---

## 10. Materials Line Handling

Materials lines are sourced from Ledgergut receipt records where `expense_category = materials` or equivalent.

Squarmish groups materials by project. Each qualifying receipt produces one consolidated line item per vendor per date, or can be broken into individual items if the Ledgergut record contains `line_items` detail.

A materials line item includes:

| Field | Type | Notes |
|-------|------|-------|
| `description` | string | Vendor name + receipt summary |
| `quantity` | decimal | Usually `1` for a receipt total |
| `unit` | string | `receipt`, `item`, or explicit unit |
| `unit_price` | decimal | Receipt subtotal (pre-tax) |
| `amount` | decimal | Pre-tax amount to bill |
| `line_item_type` | enum | `materials` |
| `linked_record_id` | string | Ledgergut `record_id` |
| `billable_status` | enum | Carried from Ledgergut |
| `review_status` | enum | `needs_review` if `maybe_billable` |

Whether Squarmish bills tax as a pass-through or rolls it into the line item total is determined by collar config and reviewer preference. In v0.1, the reviewer decides.

---

## 11. Tax Handling — CAD / GST / PST / HST

Tax handling in Black Collar mode follows Canadian tax conventions.

### Tax regions

| Province | Tax Applied | Notes |
|----------|-------------|-------|
| `BC` | GST (5%) + PST (7%) | No HST in BC |
| `ON` | HST (13%) | Combined federal + provincial |
| `AB` | GST (5%) only | No provincial sales tax |
| `QC` | GST (5%) + QST (9.975%) | QST replaces PST in Quebec |
| Other | GST (5%) + provincial rate | Varies; configurable |

Squarmish applies tax lines based on `tax_region` from the draft invoice. Tax is calculated on the invoice `subtotal` (sum of pre-tax line item amounts).

### Tax line format

```json
{
  "label": "GST",
  "rate": 0.05,
  "amount": 2.50
}
```

Tax lines are advisory in v0.1. The human reviewer confirms correctness before issue, especially for mixed taxable/non-taxable line items.

Squarmish should never auto-apply HST to a province where it does not apply, or vice versa. Unrecognized `tax_region` values set `needs_user_review = true` for the tax section.

---

## 12. Draft Invoice Lifecycle

```
invoice_candidate_queue
        ↓
    [draft]
        ↓
[pending_review]
        ↓
   [approved]
        ↓
    [issued]
        ↓
   [paid] / [overdue] / [partially_paid]
```

A draft invoice may also be moved to `voided` at any stage before issue.

### Suggested enum: `invoice_status`

- `draft` — Squarmish is building or has built the draft; not yet reviewed
- `pending_review` — Squarmish has flagged it for human review
- `approved` — Human has confirmed all fields and line items
- `issued` — Invoice has been sent to the client
- `paid` — Payment received in full
- `partially_paid` — Partial payment received
- `overdue` — Past due date with no full payment
- `voided` — Cancelled before or after issue

---

## 13. Suggested Enums

### `line_item_type`

- `materials` — physical goods, supplies, job-site items
- `labour` — billable time, site work, consulting
- `subcontractor` — third-party labour passed through to client
- `fee` — permit fees, disposal fees, administrative fees
- `travel` — mileage, transportation, accommodation
- `tax_passthrough` — tax charged to the contractor and passed to the client
- `discount` — negative line item; client credit or reduction
- `other` — uncategorized; requires review

### `billable_status`

Inherited from Ledgergut; valid in Squarmish context:

- `billable` — confirmed billable to the client
- `maybe_billable` — requires human confirmation
- `not_billable` — excluded from invoicing
- `already_invoiced` — appears on a prior invoice; excluded unless overridden

### `client_payment_status`

- `unpaid` — invoice issued; no payment received
- `partially_paid` — partial payment received
- `paid` — payment received in full
- `overdue` — past due with no full payment
- `disputed` — client has raised a payment dispute
- `void` — invoice voided; payment not expected

### `review_status`

- `confirmed` — field or line item has been verified by a human reviewer
- `needs_review` — requires human attention before the invoice can be approved
- `auto_approved` — system-generated with high confidence; no review required
- `rejected` — reviewer excluded this item from the invoice

---

## 14. Human Review Step

All Squarmish draft invoices that contain unresolved fields or `maybe_billable` line items are placed in the **Squarmish Review Queue** with `needs_user_review = true`.

The reviewer performs the following:

1. **Confirm client and project** — verify the invoice is going to the right recipient.
2. **Review line items** — confirm, adjust, or remove each line item; resolve `needs_review` items.
3. **Add labour lines** — enter any billable hours or flat labour fees not sourced from receipts.
4. **Verify tax lines** — confirm tax region and applied rates match the job and client location.
5. **Set payment terms** — confirm `due_date` and any special payment notes.
6. **Approve or return** — mark the invoice `approved` (ready to issue) or return it to `draft` with notes.

Squarmish should present any items it is uncertain about in plain language via `review_notes`. No cryptic codes. Practical flags only.

---

## 15. Output JSON Example

The following is a sample Squarmish draft invoice in JSON format:

```json
{
  "invoice_id": "SQ-20260703-0001",
  "collar_id": "black_collar",
  "client_name": "Jackson Retail",
  "project_name": "Jackson Retail Patch Job",
  "invoice_date": "2026-07-03",
  "due_date": "2026-07-17",
  "currency": "CAD",
  "tax_region": "BC",
  "line_items": [
    {
      "description": "Home Hardware — Fasteners (RCT-00421)",
      "quantity": 1,
      "unit": "receipt",
      "unit_price": 25.00,
      "amount": 25.00,
      "line_item_type": "materials",
      "linked_record_id": "LG-20260703-0042",
      "billable_status": "maybe_billable",
      "review_status": "needs_review"
    },
    {
      "description": "Site labour — patch and repair",
      "quantity": 4.0,
      "unit": "hr",
      "unit_price": 85.00,
      "amount": 340.00,
      "line_item_type": "labour",
      "linked_record_id": null,
      "billable_status": "billable",
      "review_status": "confirmed"
    }
  ],
  "linked_ledgergut_records": [
    "LG-20260703-0042"
  ],
  "subtotal": 365.00,
  "tax_lines": [
    { "label": "GST", "rate": 0.05, "amount": 18.25 },
    { "label": "PST", "rate": 0.07, "amount": 25.55 }
  ],
  "total": 408.80,
  "status": "pending_review",
  "needs_user_review": true,
  "review_notes": "One materials line item sourced from a maybe_billable Ledgergut record (LG-20260703-0042). Confirm whether fasteners are billable to Jackson Retail before approving.",
  "created_at": "2026-07-03T15:00:00Z",
  "updated_at": "2026-07-03T15:00:00Z"
}
```

---

## 16. Future Collar Behaviour

Squarmish v0.1 supports Black Collar only. Future collar profiles may change invoice behaviour as follows:

| Collar | Expected Squarmish Behaviour |
|--------|------------------------------|
| **Blue Collar** | Job-costing focus; materials and labour split by phase; progress billing support. |
| **White Collar** | Department-level billing; internal chargebacks; policy-driven approval chains. |
| **Gold Collar** | Polished client-facing invoice output; branded templates; presentation-quality summaries. |
| **Red Collar** | Overdue invoice triage; automatic follow-up drafts; escalation flags. |
| **Tie-Dye Collar** | Project budgets, production costs, merch and studio line items; milestone billing. |
| **Green Collar** | Recurring site invoices; per-visit or per-season billing; dump-run and plant pass-through. |

Collar-specific invoice rules should be configuration-driven, not hardcoded. Squarmish should remain collar-agnostic at its core and delegate billing vocabulary, required fields, and output formatting to the active collar profile.

---

## 17. Known Limitations (v0.1)

| Limitation | Notes |
|------------|-------|
| No automatic invoice sending | Squarmish drafts only; human sends |
| No client contact management | `client_name` is a string; no address book in v0.1 |
| Labour lines are manual only | No time-tracking integration yet |
| One invoice per project (default) | Multi-project invoices require manual assembly |
| No partial billing / progress billing | Full invoice only in v0.1 |
| No PDF generation | Output is JSON; rendering is out of scope for this spec |
| Tax rates are static defaults | Rate changes require a config update |
| No payment reconciliation | Squarmish does not process payments in v0.1 |

---

## 18. Future Automation Ideas

- **Client address book** — map `client_name` to a full contact record with billing address and payment terms.
- **Labour time integration** — pull billable hours from a time-tracking goblin or calendar source.
- **Invoice template engine** — render approved invoices as branded PDF or HTML output.
- **Recurring invoice support** — auto-generate scheduled invoices for retainer or recurring clients.
- **Payment reconciliation** — match incoming payments to issued invoices and update `client_payment_status`.
- **Overdue escalation** — Red Collar integration to flag and follow up on overdue invoices.
- **Ledgergut feedback loop** — when Squarmish finalizes an invoice, update Ledgergut records to `already_invoiced`.
- **Partial billing / progress billing** — support milestone or phase billing for large projects.
- **Multi-currency** — convert receipt records to the invoice currency before billing.
- **Straight-through approval** — auto-approve high-confidence, fully confirmed draft invoices.
