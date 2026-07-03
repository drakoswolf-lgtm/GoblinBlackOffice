# Ledgergut v0.1 — Black Collar Foundation Spec

## Purpose

Ledgergut v0.1 is designed first for Goblin Black Office’s real founder/operator workflow, and second for generalized reimbursement workflows.

Primary questions Ledgergut must answer in v0.1:
1. What job/project does this receipt belong to?
2. Who paid for it?
3. Does anyone owe the owner money for it?
4. Should Squarmish include it on an invoice?

Generic employee reimbursement remains supported as a future collar profile, but it is not the default assumption for v0.1.

## Product Framing

From: generic employee reimbursement app  
To: Goblin Black Office receipt intelligence system with Collar-based workflows

Core operating direction:
- Goblins do the work.
- Collars tell them what world they are working in.
- Ledgergut finds the receipts.
- Squarmish turns billable ones into invoices.
- SigNor protects the terms before anyone gets clever.

## Base Workflow (Black Collar Default)

1. Capture receipt (upload, photo, forward, or import)
2. Extract OCR fields and normalize data
3. Assign/confirm project and payer context
4. Evaluate reimbursement and billable status
5. Route uncertain records to human review
6. Queue invoice candidates for Squarmish handoff
7. Track reimbursement and invoice linkage over time

## OCR and Extraction Fields (v0.1)

### Core receipt fields
- merchant_name
- receipt_date
- total_amount
- currency
- tax_amount
- payment_method_text
- line_items (optional in v0.1 where available)
- raw_ocr_text

### Goblin Black Office context fields

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

`paid_by`
- steve
- company_card
- client_card
- rob_visa
- cash
- unknown

`reimbursement_status`
- not_reimbursed
- reimbursed
- maybe_reimbursed
- not_reimbursable
- unknown

`billable_status`
- billable
- not_billable
- maybe_billable
- already_invoiced
- tax_only

## Validation Rules (v0.1)

The base app should keep neutral validation primitives while Black Collar applies founder/operator defaults:
- Required: receipt_date, total_amount, merchant_name (if extractable), paid_by, billable_status
- Require review when assignment_confidence is below threshold
- Require review when project assignment is missing or ambiguous
- Block duplicate receipts by hash + amount/date heuristics
- Flag incompatible states (example: already_invoiced with null invoice_id)
- Track state changes with audit entries for reimbursement and invoice linkage

## Human Review Path

Human review remains a first-class part of v0.1:
- Low-confidence project assignment
- Unknown payer
- Unclear billable status
- Potential duplicate conflicts
- Tax or total mismatch from OCR ambiguity

Review outcomes:
- Confirm extracted values
- Correct project/payer/billable labels
- Mark reimbursed/not reimbursable
- Approve or reject Squarmish candidate routing

## Squarmish Handoff Logic

Ledgergut identifies receipts that may become invoice line items.

Initial rule:
- If `paid_by = steve`
- And `billable_status` is `billable` or `maybe_billable`
- Then add receipt to Squarmish invoice candidate queue

This is central to Goblin Black Office: Ledgergut finds receipts, Squarmish converts valid billable items into invoices.

## Output Schema (v0.1)

Output should include:
- Normalized receipt record
- Project and payer assignment
- Reimbursement status
- Billable status
- Invoice candidate flag
- Invoice linkage (when known)
- Review confidence metadata and review flags
- Audit trail references

## Collar System

Goblin Black Office uses a Collar System to adapt the base app to different real-world workflows.

A Collar is both a visual identity layer for goblin agents and a functional configuration profile. Collars define vocabulary, required fields, workflow behavior, defaults, validation rules, and handoff logic between goblins.

The first supported collar is the Black Collar, optimized for the founder/operator workflow. This mode prioritizes practical receipt capture, project assignment, reimbursement tracking, billable expense detection, and invoice handoff.

Future collars may include Blue Collar for trades and contractors, White Collar for office reimbursement workflows, Service Collar for hospitality operations, Tie-Dye Collar for artists and creative businesses, Green Collar for landscaping or property maintenance, and Gold Collar for premium/client-facing output.

The base app should avoid hardcoding one business model. Instead, it should expose neutral internal concepts that each Collar can interpret through its own vocabulary and rule set.

## Initial Collar Concepts (Planned)

- **Black Collar**: Founder/operator mode. Steve-first defaults, Goblin Black Office command mode.
- **Blue Collar**: Trades, contractors, construction, materials, reimbursements, client billing.
- **White Collar**: Office/corporate reimbursement workflows, departments, approvals, policy compliance.
- **Service Collar**: Hospitality, venue work, service industry expenses, shift/site-linked records.
- **Tie-Dye Collar**: Artist/creative mode for music, art, studio costs, promo, merch, video shoots, and project budgets.
- **Green Collar**: Landscaping/property maintenance mode, recurring sites, dump runs, plants, tools, materials.
- **Gold Collar**: Premium/client-facing output, polished proposals, estimates, summaries, and presentation-ready documents.
- **Red Collar**: Urgent money recovery mode, overdue invoices, missing receipts, deadline triage.
- **Grey Collar**: Unknown/mixed sorting mode for unclear receipts and records requiring review.

## Currency and Tax Assumptions

Base app:
- currency is configurable

Black Collar defaults:
- default_currency = CAD
- tax_labels = GST, PST, HST

White Collar:
- currency and tax labels are organization-configured

## White Collar (Future Profile): Employee Reimbursement

Employee reimbursement remains valuable, but is treated as a future White Collar workflow rather than v0.1 default.

Potential White Collar behaviors:
- Employee directory validation
- Department coding
- Corporate policy limits
- Multi-step approvals
- Organization-level compliance reporting

## Known Failure Cases

- OCR misses merchant, taxes, or total due to low image quality
- Incorrect project assignment from weak context
- Confusion between reimbursable and billable states
- Receipts already reimbursed but not recorded as such
- Receipts already invoiced but missing invoice linkage
- Mixed-tax receipts requiring manual review

## Future Automation Opportunities

- Better project inference from historical patterns
- Auto-linking to existing invoice drafts in Squarmish
- Smart duplicate detection across sources/channels
- Billable confidence scoring with explainability
- Automated reimbursement reminders for owner-paid items
- SigNor-assisted term checks before invoice finalization

## Monetization Scaffolding (Dormant in v0.1)

Goblin Black Office may support paid upgrades, collar packs, cosmetic goblin accessories, template bundles, automation credits, or premium workflows in the future.

Monetization is not part of the v0.1 product goal.

The v0.1 goal is to build a useful owner/operator app first, with clean architectural scaffolding for future monetization where required.

### Principles

1. Core records must never be locked behind payment.
2. Users must always be able to access and export their own data.
3. Monetization hooks should not affect the default v0.1 workflow.
4. Paid features should add specialization, automation, cosmetics, templates, or scale — not remove basic usefulness from the free/core app.
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
