# Phase 5A Specification: In-Battle Thinking Status

**Status:** Approved design; awaiting flow review and implementation plan

**Roadmap:** [mGBA AI Trainer Design](../2026-07-18-mgba-ai-trainer-design.md#phase-5a-in-battle-thinking-status)

**Prerequisite:** Phase 4A external-action response and Phase 4B decision audit remain unchanged.

**Flow review:** [Phase 5A thinking-status flow review](../reviews/2026-07-29-phase-5a-thinking-status-flow-review.md)

**Implementation plan:** [Phase 5A thinking-status plan](../plans/2026-07-29-phase-5a-thinking-status.md)

## Goal

Make the existing external-AI response wait visibly intentional in a playable
trainer-single battle. While the ROM is waiting for a legal external action, the
normal lower battle message window displays `AI is thinking` with an animated
ellipsis. The status disappears as soon as the response is accepted or the
saved vanilla trainer-AI fallback is used.

## Scope

### In scope

- Show the thinking status only after `BattleAgent_BeginExternalWait` has
  successfully published a request for an eligible opponent battler **and**
  the player-side action selection is confirmed. If the player is still using
  the Fight/Bag/Pokémon/Run UI, defer the status rather than replacing that UI.
- Use the standard lower battle message window, the same UI region used for
  trainer dialogue and battle text. It has no input prompt or red continue
  triangle.
- Animate the ellipsis at a fixed ROM-frame cadence while the external wait is
  active, without sending any new bridge or service messages.
- Stop the status before normal battle action processing resumes after either:
  - `BattleAgent_TryConsumeResponse` accepts the response; or
  - `BattleAgent_IsWaitExpired` causes `BattleAgent_UseVanillaFallback`.
- Preserve ordinary trainer, wild, unsupported, disconnected, malformed,
  stale, and late-response behavior. They retain the existing decision and
  fallback rules.

### Out of scope

- Changing the 900-frame response deadline, model, Ollama service, Lua bridge,
  mailbox layout, or V2 wire protocol.
- Running battle mechanics, accepting player input, or advancing turn execution
  while an opponent decision is pending.
- Adding a new sprite, HP-bar indicator, custom graphics, sound effect,
  model-written text, or a status for trainer switching/items/double battles.
- Showing a confirmation that the selected move later executed. That is a
  separate diagnostic feature if wanted.

## Behavior and boundaries

| Boundary | Responsibility |
| --- | --- |
| ROM battle state | Publishes the request, owns the wait state, displays and removes the status, validates an action, and retains the saved vanilla move/target fallback. |
| mGBA Lua bridge | Unchanged: forwards mailbox frames and writes only accepted response fields. |
| Python/Ollama service | Unchanged: selects an existing legal action or produces no response. Its PowerShell audit remains outside the ROM. |

The status is presentation only. It begins only after a request is truly pending,
not merely when a trainer is eligible. It must not expose request payload data,
tool calls, the selected move, model output, or fallback reason in the game.

## UI contract

During an active external wait, the lower message window is owned by the
battle-agent presentation helper and contains exactly one of these ROM text
strings:

```text
AI is thinking
AI is thinking.
AI is thinking..
AI is thinking...
```

The initial state is `AI is thinking...`. After 30 rendered frames it rotates
to no dot, then one dot, two dots, and back to three dots every 30 rendered
frames (about twice per second at 60 FPS). The status has no input cursor and
does not require a button press. When the wait ends, the helper clears only a
window it previously claimed. The normal battle controller/battle script may
then write the next standard message.

When the helper first claims this window, it must restore the normal battle
message viewport (`gBattle_BG0_X = 0` and `gBattle_BG0_Y = 0`) before writing
the text. Player move selection scrolls that same BG0 to a lower menu region;
without this reset the status text exists but is off-screen. Claiming remains
deferred until the player action is confirmed, so this reset cannot hide an
interactive player menu.

## Failure and fallback behavior

- If the external wait cannot begin, do not show the status; continue directly
  on the existing vanilla path.
- If the request begins while the player is choosing an action, defer the
  status until that player action is confirmed. If a response is accepted before
  then, never show a transient status.
- If the lower message window has an active text printer, do not overwrite it.
  On each later external-wait frame, make one non-blocking attempt to show the
  status after the printer becomes idle. The request may still be accepted or
  fall back before the status is ever shown.
- If a malformed, stale, duplicate, or illegal reply is rejected, the status
  continues only while the original ROM wait remains active. On timeout, it is
  removed and the saved vanilla choice is used.
- If battle state leaves the external wait for any reason, cleanup clears the
  status and resets its animation state. A later request starts a fresh status.
- The UI must never extend the deadline, prevent the fallback, alter move/target
  values, or freeze the frame loop.

## Tests

Add ROM-facing tests that prove:

1. A successful external request starts the status with the initial ellipsis.
2. A request made while the player menu is open does not replace that menu; the
   status starts only after the player action is confirmed.
3. The ellipsis changes only every 30 rendered frames while waiting.
4. A valid response clears the status before normal action selection continues.
5. Timeout fallback clears the status and preserves the saved vanilla action and
   target.
6. An ineligible trainer and a failed request publication never show the status.
7. A rejected response does not prematurely clear the status or alter fallback
   behavior.
8. Repeated requests do not retain dots, ownership, or text from the previous
   request.

Existing protocol, service, and battle tests remain required. No test may alter
move damage, targeting, turn order, or trainer AI choices solely to test UI.

## Measurable exit criteria

- A Calvin battle visibly displays `AI is thinking...` in the lower message
  window while a local service reply is pending.
- The ellipsis animates while mGBA remains responsive.
- The message clears without player input when a response is accepted and when
  the service is absent/late and the ROM uses vanilla fallback.
- Existing full relevant battle tests and bridge-service tests pass, and a fresh
  ROM build completes.
- A manual mGBA smoke test records both an accepted-response case and an
  absent-service fallback case with no stuck message or altered battle result.
