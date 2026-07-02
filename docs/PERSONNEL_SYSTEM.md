# Personnel System

> **Classification: Internal Memorandum — Black Office Use Only**

The Goblin Black Office maintains two independent progression systems for every operative on file.
They are tracked separately, displayed together, and must never be conflated.

---

## Table of Contents

1. [Personnel Designation](#1-personnel-designation)
2. [Command Authority](#2-command-authority)
3. [Personnel Dossier — Display Specification](#3-personnel-dossier--display-specification)
4. [Progression Combinations](#4-progression-combinations)
5. [Design Notes](#5-design-notes)
6. [Copy & Terminology Guidelines](#6-copy--terminology-guidelines)

---

## 1. Personnel Designation

**What it measures:** The operative's support, loyalty, and contribution to the Black Office.

Personnel Designation is *not* determined solely by financial backing.
It accumulates through a range of recognised contributions, evaluated at the discretion of the Office.

### Recognised Contributions

| Contribution | Notes |
|---|---|
| Supporting development | Purchases, donations, or equivalent backing |
| Lifetime membership | Carries significant weight |
| Community contributions | Documentation, guides, translations, community management |
| Bug reports | Verified, reproducible, and submitted through proper channels |
| Feature suggestions | Adopted and shipped by the Office |
| Referrals | Verified new operatives brought into the Office |
| Long-term activity | Sustained engagement over time |

### Designation Progression

| Tier | Designation |
|---|---|
| 1 | Harmless Citizen |
| 2 | Suspicious Individual |
| 3 | Troublemaker |
| 4 | Mischief Coordinator |
| 5 | Agent of Chaos |
| 6 | Mastermind |
| 7 | Archvillain |
| 8 | Evil Overdirector |
| 9 | Supreme Menace |

### Character

Personnel Designation is **primarily cosmetic and thematic**.
It reflects how the Office views the operative — their reputation, their history, their notoriety.
It does not unlock features or expand operational capacity.

---

## 2. Command Authority

**What it measures:** The operative's organisational responsibility within the Black Office.

Command Authority increases as the operative hires, unlocks, and manages more Goblin employees.
It is a direct reflection of operational scope.

### Authority Progression

| Tier | Authority |
|---|---|
| 1 | Observer |
| 2 | Clerk |
| 3 | Case Officer |
| 4 | Field Agent |
| 5 | Section Chief |
| 6 | Operations Director |
| 7 | Regional Director |
| 8 | Deputy Overdirector |
| 9 | Overdirector |

### Function

Command Authority is **mechanically significant**.
Higher authority unlocks:

- Larger operative rosters
- Additional Goblin employee slots
- Advanced workflow orchestration features
- Expanded assignment pipelines

---

## 3. Personnel Dossier — Display Specification

Every operative's profile shall be presented as a **Personnel Dossier** — a classified internal file maintained by the Black Office.

Both ranks must appear on this file simultaneously, clearly labelled, and visually distinct from one another.

### Layout

```
────────────────────────

BLACK OFFICE
PERSONNEL DOSSIER

Name:
{operative_name}

Designation:
{personnel_designation}

Authority:
{command_authority}

Clearance:
{clearance_level}

Employees Managed:
{employee_count}

Assignments Completed:
{assignment_count}

Office Efficiency:
{efficiency_percent}%

Threat Assessment:
{threat_summary}

────────────────────────
```

### Field Definitions

| Field | Source | Notes |
|---|---|---|
| `Name` | Account display name | As provided by the operative |
| `Designation` | Personnel Designation tier | See §1 |
| `Authority` | Command Authority tier | See §2 |
| `Clearance` | Access level (e.g. BLACK, GREY, STANDARD) | Reflects subscription or access status |
| `Employees Managed` | Current active Goblin employee count | Live figure |
| `Assignments Completed` | Cumulative completed tasks | Lifetime total |
| `Office Efficiency` | Computed performance metric | Displayed as percentage |
| `Threat Assessment` | Generated summary line | Dry, deadpan, thematic |

### Example Dossier

```
────────────────────────

BLACK OFFICE
PERSONNEL DOSSIER

Name:
Steve Avery

Designation:
Archvillain

Authority:
Operations Director

Clearance:
BLACK

Employees Managed:
17

Assignments Completed:
1,284

Office Efficiency:
98.2%

Threat Assessment:
Concerning.

────────────────────────
```

### Clearance Levels

| Level | Label | Notes |
|---|---|---|
| 0 | STANDARD | Default access |
| 1 | GREY | Elevated access |
| 2 | BLACK | Full clearance |

Clearance level is **not** the same as Personnel Designation or Command Authority.
It reflects authorised access, not reputation or organisational rank.

When clearance changes, the UI shall read:

> *Clearance upgraded.*

Never: *"You've been upgraded to Premium."*

---

## 4. Progression Combinations

The two systems are independent. Any combination is valid and intentional.

| Scenario | Designation | Authority | Meaning |
|---|---|---|---|
| Long-term supporter, small operation | Archvillain | Clerk | Deep loyalty, limited operational footprint |
| New power user, heavy operator | Harmless Citizen | Operations Director | Organisational reach without established reputation |
| Veteran contributor and large operation | Supreme Menace | Overdirector | Full stature in both dimensions |
| Early operative, just getting started | Harmless Citizen | Observer | No history yet — the file is thin |

These combinations should feel natural and tell a story.
The Office does not penalise mismatched ranks — it simply notes them.

---

## 5. Design Notes

### Tone

All copy touching these systems must maintain the Black Office's dry, clandestine register.
The voice is bureaucratic, slightly ominous, and entirely deadpan.

No excitement. No gamification. No congratulations.

The Office issues memos. It does not celebrate.

### Rank Independence

The two ranks must **never replace one another**.

- Do not merge them into a single "level."
- Do not derive one from the other.
- Do not hide one when the other is high or low.
- Both are always visible in the Personnel Dossier.

### Subscription & Upgrade Language

Never refer to subscription tiers as "Premium."

Approved language:

| Avoid | Use instead |
|---|---|
| Premium | *(omit or use clearance level label)* |
| Upgrade to Premium | Clearance upgraded |
| Your plan has been upgraded | Personnel designation revised |
| You now have access to more features | Authority expanded |
| More agents unlocked | Additional operatives authorized |

### Progression Language

Avoid overt game terminology.

| Avoid | Use instead |
|---|---|
| XP / experience points | *(omit entirely)* |
| Level up | Promotion Review |
| Achievement unlocked | Commendation issued |
| Quest / mission | Assignment |
| Leaderboard | *(omit entirely)* |

### Record & History Language

| Avoid | Use instead |
|---|---|
| Profile | Personnel File |
| Stats / statistics | Office Record |
| Notifications about rank | Internal Memoranda |
| Progress bar label | Promotion Review |

---

## 6. Copy & Terminology Guidelines

### Designation-Related Copy

```
Your designation has been revised.
  → New designation: Mastermind.

The Office has noted your continued contributions.
A Promotion Review is pending.

Personnel File updated.
```

### Authority-Related Copy

```
Command Authority expanded.
  → Current authority: Section Chief.

Additional operatives have been authorized.
Your roster capacity has been increased.

Authority level: Field Agent.
```

### Clearance-Related Copy

```
Clearance upgraded.
  → Current clearance: BLACK.

Access to restricted workflows has been granted.
```

### Neutral / General Copy

```
Welcome back, {designation}.

The Office is watching.

Your file is on record.

Threat assessment: Manageable. For now.
```

---

*This document is maintained by the Black Office Records Division.*
*Unauthorised distribution will be noted in your file.*
