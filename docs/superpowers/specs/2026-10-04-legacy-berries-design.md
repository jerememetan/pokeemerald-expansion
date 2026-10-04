# Archived berry behaviour restoration

This is a small implementation unit of the approved original-hack migration.
Restore the behaviour in archive `f5e81e85df6fe40ae490bf7268d0186d7f0426ed`,
not its obsolete berry structures or the rest of its berry engine.

## Required changes

Restore exactly these initial-tree varieties using current `BERRY_ID_*` names:

| Tree | Variety |
| --- | --- |
| ROUTE_116_PINAP_1 | CHERI |
| ROUTE_115_BLUK_1 | ORAN |
| ROUTE_115_BLUK_2 | ORAN |
| ROUTE_110_NANAB_1 | ORAN |
| ROUTE_110_NANAB_2 | PERSIM |
| ROUTE_121_NANAB_2 | SITRUS |
| ROUTE_123_PECHA | SITRUS |
| ROUTE_123_RAWST | SITRUS |

Keep all other initial tree commands, tree IDs and growth stages unchanged.
This changes fresh-game initialization, not already-saved tree contents.

For the current default stage-based watering mode, transplant only the
archived calculation in `CalcBerryYieldInternal`: zero watering gives
`min + Random() % 4`; watered random bounds use `water` and `water + 1`,
with the existing rounding rule. Do not clamp this formula to the table's
maximum: the archived higher yields intentionally can exceed that value.
The archived comment claiming a 0–2 bonus is wrong; its code gives 0–3.

Retain the current optional moisture mode's `min` return and the modern
outer yield/mulch logic. Leave configuration, data structures, map geometry,
encounters, and the AI Trainer feature unchanged.

## Verification

Use a small standard-library test file that parses all starting-tree commands
and compiles the actual current and pinned archived C function bodies using
native `cc`. Compare the default-mode results for watering counts 0–4 and
all 16-bit random inputs on representative min/max pairs; separately verify
the retained moisture branch. Run the tests red before changing production
code, then green afterward, followed by a ROM build and two-stage review.
Do not claim an emulator harvest or fresh-save check unless performed.
