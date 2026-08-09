# Toxic Debris Animation Migration Design

## Goal

Restore the archived visual feedback for a successful Toxic Debris activation on the Expansion 1.16.3 migration branch without changing Toxic Debris hazard-placement behavior.

## Scope

In scope:

- Run the existing Toxic Spikes move animation only after `settoxicspikes` succeeds.
- Preserve the battle script’s existing return path when Toxic Spikes cannot be placed.
- Save and restore the battle move value around the temporary animation move.

Out of scope:

- Changes to Toxic Debris trigger conditions, Toxic Spikes layer count, damage, messages, or targeting.
- New animation assets, battle-engine APIs, or move-data changes.
- Any other ability or hazard animation.

## Design

`BattleScript_ToxicDebrisActivates` currently calls `settoxicspikes BattleScript_ToxicDebrisRet`, then immediately prints the scattered-hazards message. The archived behavior inserts a visual sequence only on the success path: copy `gCurrentMove` to `gChosenMove`, set `gCurrentMove` to `MOVE_TOXIC_SPIKES`, run `attackanimation` and `waitanimation`, then restore `gCurrentMove` from `gChosenMove` before the existing message.

This uses the current 1.16.3 Toxic Spikes animation rather than a legacy animation implementation. Because `settoxicspikes` branches to `BattleScript_ToxicDebrisRet` on failure, failed placement bypasses the animation and retains the exact current return behavior.

## Failure and Compatibility

The change uses battle-script commands and globals already used by the archived implementation. It adds no persistent state. If the battle-script assembler rejects the sequence or the build fails, do not integrate it; current 1.16.3 behavior remains the fallback.

## Validation and Exit Criteria

1. Static source inspection proves the animation commands occur after successful `settoxicspikes` and before the existing message.
2. A battle with a successful Toxic Debris trigger visibly runs the current Toxic Spikes animation, then reports scattered spikes.
3. A blocked/full Toxic Spikes side takes `BattleScript_ToxicDebrisRet` without animation or altered battle state.
4. The supported build succeeds and relevant battle tests, if available, pass.

## Evidence

- Archived behavior: `git show 01f34f7b03 -- data/battle_scripts_1.s`.
- Current target: `data/battle_scripts_1.s:BattleScript_ToxicDebrisActivates`.
- User policy: use the current 1.16.3 animation when one exists; this adaptation invokes the current Toxic Spikes animation because no dedicated Toxic Debris animation exists.
- Parent migration design: `2026-08-09-original-hack-1.16.3-migration-design.md`.
