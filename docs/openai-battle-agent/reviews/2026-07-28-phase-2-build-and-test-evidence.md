# Phase 2 Build and Test Evidence: Legal-Action Snapshot

**Recorded:** 2026-07-28  
**Scope:** Version-1 mailbox publication and legal move-action snapshot for `TRAINER_CALVIN_1`

## Fresh WSL verification

The user ran the focused suite in Ubuntu WSL after the final Phase 2 corrections:

```bash
make -j16 check TESTS='External AI'
```

Result: **17 passed, 0 failed**. The group covers the existing Phase 1 mock/fallback cases plus publication, visible snapshot contents, normalized self/selected targets, empty and zero-PP slots, empty legal lists, stale-response replacement, excluded battles, non-move fallback preservation, and a fainted-target rejection helper.

The user then ran:

```bash
make -j16
```

Result: **passed** and produced the normal ROM.

## Smoke test

The user launched the rebuilt ROM in mGBA without Lua or a local service and fought Youngster Calvin on Route 102. The battle completed normally with no pause, crash, UI change, or external-process requirement.

## Fallback and scope result

Phase 2 publishes an EWRAM mailbox request only after the vanilla AI has selected a legal move fallback. It does not read, wait for, or apply a mailbox response. Consequently, the original trainer AI remains authoritative in the normal ROM, including when no bridge or service is present.

## Known baseline noise

The battle-test runner still prints existing `ASSUME failed` diagnostics from unrelated ability and move-effect tests while running the focused group. They do not belong to `External AI`; the focused group itself completed with 17 passes and no failures. The earlier full-suite baseline classification (44 accepted unrelated failures) remains documented in the Phase 1 evidence review and was not reclassified by this phase.

## Exit criteria

- Fixed-layout, pointer-free EWRAM mailbox: met.
- Publication restricted to an opted-in opponent trainer single battle: met.
- Every emitted move action uses an unmasked non-empty slot and a live normalized target: met by focused tests.
- Focused Phase 1 and Phase 2 tests: met, 17/17.
- Normal no-bridge Calvin battle remains playable: met by mGBA smoke test.

## Links

- [Phase 2 specification](../specs/2026-07-26-phase-2-legal-action-snapshot.md)
- [Phase 2 flow review](2026-07-26-phase-2-legal-action-snapshot-flow-review.md)
- [Phase 2 implementation plan](../plans/2026-07-26-phase-2-legal-action-snapshot.md)
- [Parent roadmap](../2026-07-18-mgba-ai-trainer-design.md)
