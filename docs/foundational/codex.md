# The Codex of Goblin Black Office

> **Status:** Canonical — Active  
> **Document Owner:** Red Ironbeard (Engineering Custodian)  
> **Last Updated:** 2026-07-05  
> **Classification:** Descriptive (records truth, does not instruct)

---

## 1. World Overview

Goblin Black Office is a narrative-first operations system where specialized goblins handle business workflows for a founder/operator context. The current repository is documentation-first and defines product behavior before implementation code exists.

## 2. System Architecture

Current architecture is specification-driven:

- **Foundational Scrolls layer:** canonical governance documents.
- **Scroll layer:** workflow specifications (agent-specific behavior).
- **Implementation layer:** not yet present in this repository.

Primary interaction flow today:

1. Ledgergut defines receipt intelligence behavior.
2. Ledgergut hands billable candidates to Squarmish.
3. Squarmish defines invoice draft behavior for review.

## 3. Goblin Registry

| Goblin | Role | Current Canonical Source |
|---|---|---|
| Ledgergut | Receipt intelligence and routing | `/home/runner/work/GoblinBlackOffice/GoblinBlackOffice/docs/goblins/GBO-001-ledgergut-workflow.md` |
| Squarmish | Invoice draft creation and invoice review prep | `/home/runner/work/GoblinBlackOffice/GoblinBlackOffice/docs/goblins/GBO-002-squarmish-invoice-workflow.md` |

## 4. Workflow Registry

| Scroll ID | Workflow | Status |
|---|---|---|
| GBO-001 | Ledgergut Founder/Operator Receipt Intelligence Workflow | Draft — Planning / Spec Only |
| GBO-002 | Squarmish Invoice Workflow | Draft — Planning / Spec Only |

## 5. Collar Registry

Defined collars currently referenced by canonical specs:

- Black Collar
- Blue Collar
- White Collar
- Service Collar
- Tie-Dye Collar
- Green Collar
- Gold Collar
- Red Collar
- Grey Collar

Black Collar is the first active operating profile in current scrolls.

## 6. Data Model Overview

Current canonical data entities (spec-level):

- `receipt_record` (Ledgergut output)
- `invoice_candidate_queue_entry` (Ledgergut → Squarmish handoff)
- `invoice_draft` (Squarmish output)
- `collar_profile` (configuration + vocabulary profile)
- `review_decision` (human approval/rejection state)

## 7. API Registry

No implemented APIs are currently canonical in this repository.  
Only payload schemas and field definitions in scroll documentation are canonical.

## 8. Design Principles

- Canonical truth lives in the Foundational Scrolls plus workflow scrolls.
- Collar-driven behavior over hardcoded business assumptions.
- Human review remains part of critical financial decisions.
- Narrative flavor must not reduce operational clarity.
- Data portability and practical usefulness are preferred over lock-in mechanics.

## 9. Canonical Terminology

- **Foundational Scrolls:** Codex, Character Bible, Production Manual.
- **Chronicles:** historical narrative updates and story continuity records.
- **Scrolls:** specs that introduce new workflows and system reality.
- **Goblin:** role-specific agent concept in the product ecosystem.
- **Collar:** visual + functional operating profile.
- **Canonical:** currently approved project truth.

## 10. Chronicle Index

No chronicle files are currently published in this repository.

## 11. Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-05 | Established initial Codex structure and canonical registries. |
