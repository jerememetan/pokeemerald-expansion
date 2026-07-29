# Phase 5B Evidence: Manual Demo Guide and Recovery

**Status:** Complete

**Specification:** [Phase 5B manual demo guide](../specs/2026-07-29-phase-5b-demo-guide.md)

**Flow review:** [Phase 5B demo-guide flow review](2026-07-29-phase-5b-demo-guide-flow-review.md)

**Implementation plan:** [Phase 5B demo-guide plan](../plans/2026-07-29-phase-5b-demo-guide.md)

## Documentation change

`tools/mgba-bridge/README.md` now documents the existing manual WSL build,
Ollama warm-up, Python-service, mGBA/Lua, successful-response, fallback, and
one-client recovery flows. No ROM, Lua, Python, protocol, model, port,
trainer, legal-action, timeout, or fallback code changed in Phase 5B.

## Fresh automated verification

```powershell
py -3 -m unittest discover -s tools\mgba-bridge\tests -v
```

Result: **61 tests passed**. This includes service action validation, audits,
format retry/fallback, V2 protocol parsing, mailbox generation, and Lua
source-contract checks.

```powershell
wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI'"
```

Result: **25/25 tests passed**. This includes thinking-status lifecycle,
mailbox V2, legal-action snapshot, valid response, rejected response, and
saved-vanilla fallback coverage.

`git diff --check` emitted no output before this evidence-only commit.

## Manual runtime evidence

The current manual setup was verified in the immediately preceding Phase 5A
smoke tests, which are the same connected and absent-service flows now written
into the guide:

1. **Connected service:** after the player selected a move in Calvin's battle,
   `AI is thinking...` appeared in the normal lower message panel, the local
   agent supplied a legal response, and the status cleared as the battle
   continued.
2. **Absent-service fallback:** after the service was stopped, the thinking
   status remained during the existing bounded wait, then cleared as the saved
   vanilla trainer AI continued the battle. No stuck message remained.

See [Phase 5A thinking-status evidence](2026-07-29-phase-5a-thinking-status-evidence.md)
for the original live smoke-test record. Phase 5B is documentation-only, so
the fresh regression runs above confirm that the documented workflow did not
change runtime behavior.

## Exit criteria

- [x] The README gives a complete manual launch sequence with exact expected
  service and Lua logs.
- [x] The README documents the one-client bridge-session rule and a safe
  recovery action for model, generated-address, bind, disconnect, rejection,
  and fallback symptoms.
- [x] Connected and fallback Calvin behavior is recorded without a stuck
  battle or a changed protocol/action result.
- [x] Fresh bridge-service and External AI regression suites pass.

Phase 5 demo hardening is complete. Phase 6 trainer coverage remains separate.
