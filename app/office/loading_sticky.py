"""Curated production joke pool for the load-bearing splash-screen sticky.

The progress ring is the real loading indicator. These lines are only comedy.
Each line is eligible inside exactly one progress band and has a conditional
selection weight within that band. Weights in every band sum to 100.

At 100% the UI should stop rotating notes and trigger the explosion.
"""

from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class StickyLine:
    key: str
    text: str
    min_progress: int
    max_progress: int
    weight: int


LOAD_BEARING_STICKY_LINES: tuple[StickyLine, ...] = (
    # 0-24%: the office is waking up.
    StickyLine("scratch-wall", "Please ignore the scratching in the wall.", 0, 24, 20),
    StickyLine("not-on-fire", "Nothing important appears to be on fire.", 0, 24, 20),
    StickyLine("tiny-boots", "Several tiny boots can be heard approaching.", 0, 24, 17),
    StickyLine("filing-cabinet", "The filing cabinet has been persuaded to cooperate.", 0, 24, 15),
    StickyLine("good-pencil", "Someone moved the good pencil.", 0, 24, 15),
    StickyLine("confidence", "A lot of this runs on confidence.", 0, 24, 13),

    # 25-49%: introduce the staff.
    StickyLine("ledgergut-folklore", "Ledgergut is separating receipts from folklore.", 25, 49, 18),
    StickyLine("signor-as-needed", "SigNor has opinions about the words 'as needed'.", 25, 49, 18),
    StickyLine("squarmish-counting", "Squarmish is counting with intent.", 25, 49, 17),
    StickyLine("packrat-knows", "Packrat insists he knows where it is.", 25, 49, 17),
    StickyLine("patch-problem", "Patch has located the problem. Probably.", 25, 49, 15),
    StickyLine("grimscratch-concerns", "Grimscratch has several concerns.", 25, 49, 15),

    # 50-79%: the office is fully involved now.
    StickyLine("ledgergut-haunted", "Ledgergut says the totals feel haunted.", 50, 79, 18),
    StickyLine("signor-assumption", "SigNor has quarantined a dangerous assumption.", 50, 79, 17),
    StickyLine("squarmish-overdue", "Squarmish smells overdue balances.", 50, 79, 17),
    StickyLine("packrat-safe-place", "Packrat says this was in a very safe place.", 50, 79, 16),
    StickyLine("patch-reality", "Patch is negotiating with reality at close range.", 50, 79, 16),
    StickyLine("grimscratch-optimism", "Grimscratch is inspecting the blast radius of optimism.", 50, 79, 16),

    # 80-99%: increasingly concerning bomb-adjacent commentary.
    StickyLine("structural-confidence", "Structural confidence is decreasing.", 80, 99, 20),
    StickyLine("wall-argument", "The wall is losing the argument.", 80, 99, 18),
    StickyLine("charge-enthusiastic", "The charge appears enthusiastic.", 80, 99, 17),
    StickyLine("hands-clear", "Please keep hands outside the blast radius.", 80, 99, 17),
    StickyLine("slate-theoretical", "The slate is about to become theoretical.", 80, 99, 15),
    StickyLine("tasteful-detonation", "Brace for a tasteful detonation.", 80, 99, 13),
)


def sticky_candidates(progress: int) -> tuple[StickyLine, ...]:
    """Return eligible jokes for an integer loading percentage from 0 through 99."""
    if not 0 <= progress < 100:
        return ()
    return tuple(
        line
        for line in LOAD_BEARING_STICKY_LINES
        if line.min_progress <= progress <= line.max_progress
    )


def choose_sticky_line(progress: int, *, rng: random.Random | None = None) -> StickyLine | None:
    """Choose one eligible line using the line weights for that progress band."""
    candidates = sticky_candidates(progress)
    if not candidates:
        return None
    picker = rng or random
    return picker.choices(candidates, weights=[line.weight for line in candidates], k=1)[0]
