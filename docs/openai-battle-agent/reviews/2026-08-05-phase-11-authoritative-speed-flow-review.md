# Phase 11 Authoritative Speed Flow Review

`BattleAgent_CopySnapshot` currently exports `gBattleMons[battler].speed`, while the battle engine's `GetBattlerTotalSpeedStat` applies current battle modifiers. Python currently sorts that snapshot field and warns about priority. The active snapshot already has a `u16 speed` word, so replacing its value avoids protocol/version/offset changes. `compare_speed` must reverse only the effective-speed order under the published Trick Room bit; it cannot predict priority, switching, or equal-speed RNG.

## Flows

1. ROM snapshots each active battler with its authoritative total speed.
2. The Python tool reads those values, checks the field bit, and returns the ordinary effective-speed order or its Trick Room reversal.
3. The model combines that advisory context with per-move priority and selects an already ROM-listed legal action.
4. On missing/late/malformed service input, ROM keeps its existing vanilla fallback.

## Gaps resolved

| Severity | Gap | Resolution |
|---|---|---|
| Important | Replacing raw active speed can look like a protocol change. | Reuse the existing `u16 speed` word; parser offsets and protocol version remain unchanged. |
| Important | Trick Room changes ordering but not `GetBattlerTotalSpeedStat`. | Python reads the existing field bit and reverses only the reported effective-speed order. |
| Minor | Equal speeds and priority are not a deterministic speed list. | Tool explicitly states those limits rather than claiming a guaranteed turn sequence. |

No critical or unresolved important gaps remain.
