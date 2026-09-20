# Load-bearing sticky production copy

## Static header

**LOAD-BEARING STICKY**  
**DO NOT REMOVE**

The loading ring communicates real progress. The sticky exists only for comedy and worldbuilding.

At each text rotation, choose one eligible line from the current progress band using the listed probability. Every band totals 100%. At **100%**, stop rotating text and trigger the explosion immediately.

### 0–24%

| Chance | Line |
|---:|---|
| 20% | Please ignore the scratching in the wall. |
| 20% | Nothing important appears to be on fire. |
| 17% | Several tiny boots can be heard approaching. |
| 15% | The filing cabinet has been persuaded to cooperate. |
| 15% | Someone moved the good pencil. |
| 13% | A lot of this runs on confidence. |

### 25–49%

| Chance | Line |
|---:|---|
| 18% | Ledgergut is separating receipts from folklore. |
| 18% | SigNor has opinions about the words 'as needed'. |
| 17% | Squarmish is counting with intent. |
| 17% | Packrat insists he knows where it is. |
| 15% | Patch has located the problem. Probably. |
| 15% | Grimscratch has several concerns. |

### 50–79%

| Chance | Line |
|---:|---|
| 18% | Ledgergut says the totals feel haunted. |
| 17% | SigNor has quarantined a dangerous assumption. |
| 17% | Squarmish smells overdue balances. |
| 16% | Packrat says this was in a very safe place. |
| 16% | Patch is negotiating with reality at close range. |
| 16% | Grimscratch is inspecting the blast radius of optimism. |

### 80–99%

| Chance | Line |
|---:|---|
| 20% | Structural confidence is decreasing. |
| 18% | The wall is losing the argument. |
| 17% | The charge appears enthusiastic. |
| 17% | Please keep hands outside the blast radius. |
| 15% | The slate is about to become theoretical. |
| 13% | Brace for a tasteful detonation. |

## Display behavior

- Keep the sticky physically fixed to the bomb.
- The red warning header never changes.
- Only the black joke copy changes.
- Use a subtle crossfade rather than replacing the sticky itself.
- Do not show functional text such as “Loading…” or “Updating…” on the sticky.
- The ring is the only progress indicator.
- Suggested copy rotation interval: roughly 2.5–3.5 seconds when loading lasts long enough to justify another line.
- Do not delay the explosion to finish a joke. Reaching 100% wins immediately.

The production source of truth is `app/office/loading_sticky.py`.
