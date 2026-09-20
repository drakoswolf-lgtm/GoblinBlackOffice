# Wave 2 grunt workflows

Wave 2 adds three operational specialists after the launch trio. These are workflow rough-ins, not commitments to large subsystems.

The design rule is simple: each grunt must own a clear problem, expose a small number of durable states, and hand facts to another specialist rather than duplicating their job.

## Packrat McDuffel — logistics & materials

**Owns:** material and item requests, sourcing notes, receiving, staging, movement, and delivery confirmation.

**Does not own:** accounting, purchasing authority, work scheduling, or safety/compliance decisions.

Workflow:

1. **Request** — project, item/specification, quantity, destination, needed-by.
2. **Source** — candidate supplier/source, availability, lead time, expected price.
3. **Authorize** — explicit human approval before paid purchase/reservation.
4. **Acquire / receive** — actual quantity, actual cost evidence, receipt reference.
5. **Stage / move** — current location and next destination.
6. **Verify** — human confirms final handoff.

Key handoffs:
- actual purchase evidence → Ledgergut
- material ready / blocked → Patch
- hazardous, restricted, uncertain, or high-risk item → Grimscratch

First useful release: material requests + status + receipt linkage. No automated ordering.

## Patch — operations & work orders

**Owns:** turning loose work into explicit tasks/work orders, dependency status, execution notes, and completion verification.

**Does not own:** contract interpretation, procurement, expense accounting, or invoice issuance.

Workflow:

1. **Intake** — project, task/request/defect, needed-by, known context.
2. **Triage** — priority, owner, dependencies, clarification state.
3. **Plan** — smallest executable work order, access/material/prerequisite needs.
4. **Execute** — work notes, actual supplied hours, scope changes, blockers.
5. **Verify** — human confirms completion evidence and remaining items.
6. **Close / hand off** — confirmed billable facts become available to Squarmish.

Key handoffs:
- material dependency → Packrat
- expense evidence → Ledgergut
- confirmed completed work → Squarmish
- safety/permit/access concern → Grimscratch

First useful release: work orders + blocked/active/verification-ready states + billing handoff. No workforce scheduling engine.

## Grimscratch — risk & compliance

**Owns:** visible risk flags, evidence, advisory disposition, human decisions, and an audit trail.

**Does not own:** legal advice, regulatory sign-off, contract drafting, or automatic veto power.

Workflow:

1. **Trigger** — flagged record/action/document/material/task.
2. **Classify** — category + severity, explicitly advisory.
3. **Evidence** — supporting facts/sources and missing information.
4. **Disposition** — allow / clarify / hold / escalate recommendation.
5. **Human decision** — accept, reject, or override with a note.
6. **Audit trail** — preserve trigger, evidence, decision, unresolved follow-up.

Key handoffs:
- contract/scope concern → SigNor
- procurement/material caution → Packrat
- work-order safety/access/permit hold → Patch
- billing/compliance hold → Squarmish

First useful release: risk flags + evidence + human disposition. No automated legal conclusions.

## Shared handoff chain

The six-specialist office should increasingly behave like one system:

**SigNor defines the commitment → Patch turns it into executable work → Packrat clears material dependencies → Ledgergut records actual spend → Patch confirms completed work → Squarmish drafts billing → Grimscratch flags exceptions anywhere in the chain.**

Æterna remains the routing layer. The specialists exchange records and states; the human remains the authority for purchases, completion confirmation, contractual acceptance, invoice approval, and risk overrides.
