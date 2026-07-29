# Phase 5A Flow Review: In-Battle Thinking Status

**Specification reviewed:** [Phase 5A thinking status](../specs/2026-07-29-phase-5a-thinking-status.md)

**Repository grounding:** `HandleTurnActionSelectionState` in
`src/battle_main.c` puts an eligible opponent in
`STATE_WAIT_EXTERNAL_AI_RESPONSE` after `BattleAgent_BeginExternalWait`.
That wait already polls `BattleAgent_IsWaitExpired` and
`BattleAgent_TryConsumeResponse` once per frame. `BattlePutTextOnWindow` and
`IsTextPrinterActive(B_WIN_MSG)` are the existing message-window patterns.
The player controller also owns the lower window while it displays the action
or move menus. No mailbox, Lua, or Python change is needed.

## User flows

1. **Player confirms a move; agent responds while the turn is pending.**
   The ROM publishes an external request, reaches the external-wait state, and
   waits until the player action is confirmed and the lower text printer is
   idle. It claims the lower message window with `AI is thinking...`, rotates
   dots every 30 frames, accepts a legal response, clears its owned status, and
   continues normal action selection.

2. **Agent responds before the player has finished selecting.**
   The player keeps the normal action/move UI. The ROM accepts the legal reply
   and continues; it never flashes or overwrites the thinking status.

3. **Service is absent, late, malformed, stale, or returns an illegal action.**
   The status appears only when the player UI is no longer active and remains
   while the existing wait remains active. At the 900-frame deadline, the ROM
   clears the owned status, restores its saved vanilla action/target, and
   proceeds without player input.

4. **Normal or unsupported battle.**
   `BattleAgent_BeginExternalWait` is not active, so no presentation state is
   claimed and all existing UI remains unchanged.

5. **Back-to-back external turns.**
   Cleanup resets status ownership, dot state, and elapsed frame count. The
   next pending request starts from exactly `AI is thinking...` rather than a
   stale dot state or retained text.

## Gaps found and resolved

### Critical

None. The feature is presentation-only and does not create a new route to set
a move, target, mailbox field, or response deadline.

### Important

1. **The opponent request can begin while the player controls the same lower
   message window.** Replacing it would hide Fight/Bag/Pokémon/Run controls.
   The specification now defers status ownership until player action selection
   is confirmed; a fast reply may therefore finish without showing a status.

2. **An unspecified animation interval would make the behavior subjective and
   hard to test.** The specification now requires an initial three-dot state
   and a 30-rendered-frame cycle through zero, one, two, and three dots.

3. **Direct message-window writes can collide with an active text printer.**
   The specification now requires a single non-blocking attempt per external
   wait frame only after `IsTextPrinterActive(B_WIN_MSG)` is false. The
   response/fallback polling remains independent of UI availability.

4. **A general window clear could erase a subsequent battle message.** The
   specification now requires explicit ownership; cleanup clears only a window
   claimed by this status helper.

5. **The standard message window is off-screen after the player chooses a
   move.** `HandleChooseMoveAfterDma3` scrolls BG0 to the move-menu region.
   Writing `B_WIN_MSG` without resetting that viewport produces an apparently
   frozen blank screen even though the text was rendered. The specification
   now requires the helper to restore BG0 X/Y to zero immediately before its
   first status render, after player-action confirmation.

### Minor

1. **The existing battle tests are action-oriented rather than visual.** The
   implementation should expose a small test-visible presentation state rather
   than asserting pixel output. This is safe because it does not expose or
   alter battle mechanics.

## Questions and defaults

All important questions are resolved in the specification. The following minor
implementation default is safe:

1. **Where should test-visible state live?** Keep it private to the
   battle-agent presentation helper, with `#if TESTING` inspection/reset hooks
   only. This avoids changing the mailbox or public runtime behavior.

## Recommended next steps

1. Write a Phase 5A implementation plan with test-first steps for player-menu
   deferral, 30-frame animation, accepted-response cleanup, and timeout
   cleanup.
2. Keep protocol/service tests as regression coverage; do not modify Lua or
   Python for this UI-only slice.
3. Run the full relevant battle test suite, bridge-service tests, a fresh ROM
   build, then connected and absent-service Calvin smoke tests.
