# Goblin Black Office Golden Job Lifecycle

**Status:** Product acceptance canon for the end-to-end contractor workflow.

## Why this exists

Goblin Black Office is not a set of disconnected specialist screens. The product succeeds when one real job can move through the Office from intake to payment without forcing the user to re-enter the same facts.

The primary acceptance scenario is:

**Splash -> Curriculum VitÆ -> Office Desk -> Agreement -> Estimate -> Materials plan -> Shopping list -> Receipts -> Work execution -> Labour capture -> Final materials -> Invoice -> Payment -> Ledger**

Each specialist works on the same Office-owned project record.

## Golden path

### 1. Startup and first entry

The user opens the app and receives the canonical startup sequence.

For first-run users:

`Startup -> Curriculum VitÆ -> Office Desk`

For returning users:

`Startup -> Office Desk`

Curriculum VitÆ captures shared business defaults once so specialist workflows do not repeatedly interrogate the user.

### 2. Start a job from the Office Desk

The Office Desk must make `New job` / `New project` obvious.

Minimum inputs:
- client
- project name / site
- job description or requested outcome
- known schedule constraints
- known pricing model

The Office creates or links the shared Client and Project records before handing the job to SigNor.

### 3. SigNor: agreement and scope

SigNor turns explicit human inputs into an Agreement draft.

The agreement should capture:
- scope
- assumptions
- exclusions
- pricing basis
- payment terms
- change-order terms

Nothing commercially consequential is silently invented.

The agreement remains Draft until human approval.

### 4. Estimate and material plan

The same project scope feeds an Estimate and a MaterialPlan.

The estimate may contain:
- estimated labour hours
- labour rate
- material quantities
- expected material cost
- equipment / subcontract allowances
- contingency
- tax assumptions when configured

The system may derive a suggested material list from the scope, but generated quantities, prices, and assumptions remain visible and editable before promotion.

The user must be able to distinguish:
- user-supplied facts
- system-derived suggestions
- unresolved assumptions

An estimate is never represented as an exact final cost until actual labour and expenses are known.

### 5. Packrat: shopping list and material state

Approved material requirements become a project ShoppingList.

Every item tracks at minimum:
- description / specification
- required quantity
- acquired quantity
- remaining quantity
- expected unit cost when known
- actual cost when known
- supplier / source note when known
- status

Suggested statuses:
- Needed
- Partially acquired
- Acquired
- Returned
- Substituted
- Cancelled

The ShoppingList is derived from the project material plan, not a disconnected checklist.

### 6. Ledgergut: receipt intake updates the job

The user can upload or photograph receipts during the job.

Ledgergut extracts receipt evidence into Expense records and attempts to match line items against the project's ShoppingList.

A successful match updates:
- acquired quantity
- remaining quantity
- actual material cost
- supplier
- receipt reference
- project expense totals

Ambiguous matches remain visible for human confirmation.

The system must not silently mark an item purchased merely because a vaguely similar receipt line exists.

The shopping list should visibly update as receipts are accepted so the user can see what still needs to be bought.

### 7. Patch: work execution

During the job, Patch tracks the operational state of the project.

The user should be able to record:
- work started / stopped
- task status
- blockers
- material dependencies
- scope changes
- notes
- actual labour hours

Labour hours are factual inputs. The Office never invents them.

Changed scope remains distinguishable from the original agreement and can be handed back to SigNor for a change order when required.

### 8. Job completion

When field work is complete, the user enters or confirms:
- actual labour hours
- final material receipts
- material returns / credits
- unresolved expenses
- completed scope
- remaining deficiencies if any

The Office compares estimate versus actual without overwriting either.

Useful completion views include:
- estimated labour vs actual labour
- estimated materials vs actual materials
- unbilled expenses
- change-order work
- gross project margin when enough facts exist

### 9. Squarmish: final invoice

Squarmish builds a Draft invoice from the shared project facts.

Possible invoice sources include:
- fixed agreement amount
- actual labour
- approved change orders
- confirmed billable material expenses
- configured markups
- configured tax treatment

The user reviews the invoice before issue.

The app must support a printable PDF.

Outbound email is a consequential action and requires explicit human approval before sending.

### 10. Payment

An issued invoice may expose a payment option when a payment provider is configured.

The first intended provider is Square unless the integration decision changes later.

Payment integration must remain optional. The Office should also support recording external/manual payment without a processor.

No merchant account is created and no paid service is activated without explicit human authorization.

Payment records should capture:
- invoice
- amount
- date
- method / processor
- processor reference when available
- partial vs full payment

### 11. Ledger update and closeout

A confirmed payment updates the shared running ledger.

Project closeout should expose:
- invoiced total
- paid total
- outstanding balance
- actual labour
- actual materials / expenses
- estimated vs actual variance
- project margin when calculable

The Office Desk should then stop treating the job as active work and surface any remaining follow-up, unpaid balance, warranty note, or unresolved record.

## Shared data spine

The target project record graph is:

`Business -> Client -> Project`

with linked records:

`Agreement`
`Estimate`
`MaterialPlan`
`ShoppingListItem`
`Expense`
`WorkLog`
`ChangeOrder`
`Invoice`
`Payment`

These are Office records. Specialists enrich and operate on them rather than creating private duplicates.

## Specialist ownership

- **Æterna**: command routing, context, approvals, status, unresolved ambiguity
- **SigNor**: agreements, scope, assumptions, exclusions, change orders
- **Packrat McDuffel**: material plan, shopping list, acquired/remaining state
- **Ledgergut**: receipt evidence, expenses, supplier/cost facts, shopping-list purchase evidence
- **Patch**: work execution, blockers, task completion, factual labour capture
- **Squarmish**: invoice construction, billable facts, issued / paid states
- **Grimscratch**: risk, compliance, hold / clarify recommendations

## Non-negotiable rules

1. The user should not have to enter the same fact into multiple goblin workflows.
2. Estimated values and actual values remain separate.
3. Derived materials and costs are suggestions until promoted or confirmed.
4. Actual labour hours are never invented.
5. Receipt matching may suggest, but ambiguous shopping-list updates require confirmation.
6. Contracts, invoice sending, purchases, paid reservations, and material financial commitments retain human approval gates.
7. Payment processing is optional and external/manual payments remain supported.
8. Every major project transition is visible on the Office Desk.

## End-to-end acceptance test

A release is not considered functionally convincing until a tester can:

1. open the startup sequence;
2. complete onboarding;
3. land on the Office Desk;
4. create a client and project;
5. draft and approve an agreement;
6. produce an editable estimate and materials list;
7. promote materials into a shopping list;
8. upload receipts and see acquired / remaining material state update;
9. record actual labour and final receipts;
10. generate a printable invoice;
11. issue or mark the invoice sent through a human-approved action;
12. record or collect payment;
13. see payment and project totals reflected in the running ledger.

That complete loop is the product's primary functional demonstration.
