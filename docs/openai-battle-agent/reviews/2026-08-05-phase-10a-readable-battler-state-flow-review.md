# Phase 10A Readable Battler State Flow Review

**Specification reviewed:** [Phase 10A specification](../specs/2026-08-05-phase-10a-readable-battler-state.md)

## Repository context

`BattleAgent_CopySnapshot` already exports numeric V4 battler fields; `battle_agent_service.py` owns JSON translation and is the only safe place to improve model-facing labels without changing ROM protocol offsets.

## Flows

1. The model calls a battler/party state tool; Python decodes only mailbox data into names and returns JSON.
2. A known status/type/stage is translated; the model uses it when selecting a ROM-listed action.
3. An unknown value becomes an explicit safe unknown value; the ROM still validates the eventual action.
4. The service is unavailable or late; the existing mailbox timeout selects vanilla AI.

## Gaps resolved

| Severity | Gap | Resolution |
|---|---|---|
| Important | The V4 mailbox does not contain all volatile effects, particularly disable-structure effects such as Taunt. | Publish only directly available `status2`/`status3` names; document the deliberate omission. |
| Important | A model could mistake numeric stat stages for literal stats. | Expose stage deltas -6 through +6 under named stat keys and do not expose raw stages. |
| Minor | A future ROM enum can be unknown to Python. | Use `UNKNOWN` rather than guessing a battle fact. |

No critical gaps remain. The existing ROM legality check and timeout fallback cover every terminal response path.
