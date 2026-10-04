# Trainer-only bag checkpoint - 2026-10-05

User-selected policy: no bag use against trainers; wild bag use, including
Poke Balls, stays available under unchanged capture/special-battle rules.
This follows `2026-10-04-friendship-toxic-boost-progress.md` and does not
complete the full custom-hack migration or its gameplay acceptance.

## Implementation

Runtime and regression checks committed as `2e9d85c4aa`.

Only runtime change: `B_VAR_NO_BAG_USE` in `include/config/battle.h` is now
`NO_BAG_AGAINST_TRAINER` (1), with a corrected explanatory comment.
The existing VarGet and bag permission helpers accept this literal mode.
No new variable, flag, engine path, initialization or save format was added.
Existing and fresh saves use the policy after rebuilding/loading the new ROM.
Debug variable-toggle UI requires a real variable ID and therefore remains
unavailable for this constant mode; existing disabled debug settings are intact.

Correction to the earlier explanation: B_VAR_NO_BAG_USE can be a literal
0/1/2 or a real variable ID. Native GetVarPointer returns NULL below VARS_START,
and VarGet returns that literal. VarSet on literal 1 returns FALSE, so the
existing initialization attempt does not change any save variables.

Bag slots, stack quantities, item tables and save storage are unchanged.
Better Bag remains a separate pending integration. Pokemon stats, abilities
and evolution edits are deferred per the user's latest instruction; already
restored friendship/Toxic Boost behavior remains intact. Master and AI Trainer
are untouched; work remains on `codex/rom-hack-1.16.3-migration`.

## Verification

- Independent specification and code-quality reviews approved the unit.
- Final combined integration review approved the scoped change, independently
  passing all 15 bag/configuration checks and verifying callers, protected
  map paths, branch boundaries and the recorded build hashes.
- Independent old-mode RED reproduction: seven tests, two expected assertion
  failures for normal/double trainer permission, zero errors.
- Seven new native-C checks compile the actual configuration, GetVarPointer,
  VarGet, VarSet and IsAllowedToUseBag using mandatory strict cc. Coverage:
  default trainer/wild singles/doubles, literal 0/1/2 and invalid fallback,
  real-variable overrides, null-save queries, unchanged save/special-variable
  storage after literal reset attempts, and unchanged relevant callers.
- Fresh combined native-C suite: 49 tests passed (4 berry, 14 cap, 11 HM,
  8 configuration, 5 balance, 7 bag). Existing configuration test gained
  only B_VAR_NO_BAG_USE in its explicit macro allowlist, not archive SETTINGS.
- Fresh map/event/reward importer suite: 154 tests passed. Total: 203.
- Native generated sources and full Emerald ROM build passed. All 21
  reviewed runtime/data overlays match the native build copy byte-for-byte.
- Runtime diff versus `6c4fde611f` contains only `include/config/battle.h`;
  the user's five `bf8074499f` map/encounter paths are unchanged.

Native build: `/home/jereme/pokeemerald-hm-config.08TZvd` in Ubuntu WSL.
Logs: `trainer-bag-generation.log`, `trainer-bag-rom-build.log`.
ROM: 33,554,432 bytes; SHA-256:
`e9f1cc2c43e1881d8a35252384d1c3d453659bd2cb7631bed17aa82500c7ad4d`.
Configuration SHA-256:
`55c3ce9141a5e0f0af7bcd85edf79d33d70cfb1daac3be28a56e73fcb7915cd1`.

No ROM, generated files or saves were copied into the workspace. Rebuild the
usual workspace ROM before playing, or use the native validation ROM directly.
No automatic push is included in this pass.

## Gameplay acceptance still needed

Use a disposable save: attempt an item against a trainer and verify the
native refusal message/no consumption, then use a healing item and throw a
Poke Ball in a normal wild battle. Check a double trainer battle and retain
ordinary special-battle/capture restrictions. No claim of emulator playtesting
or stock upstream battle-suite compatibility is made.

All prior map/HM/configuration/berry/cap/balance gameplay acceptance and the
other outstanding migration tasks remain pending.
