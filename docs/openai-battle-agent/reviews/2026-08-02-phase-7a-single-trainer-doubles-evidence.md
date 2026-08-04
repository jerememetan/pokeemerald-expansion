# Phase 7A Evidence: One-Trainer Double Battles

**Specification:** [Phase 7A specification](../specs/2026-08-02-phase-7a-single-trainer-doubles.md)
**Flow review:** [Phase 7A flow review](2026-08-02-phase-7a-single-trainer-doubles-flow-review.md)
**Implementation plan:** [Phase 7A plan](../plans/2026-08-02-phase-7a-single-trainer-doubles.md)
**Latency expiry review:** [Phase 7A latency-expiry review](2026-08-03-phase-7a-latency-expiry-flow-review.md)

## Automated evidence — 2026-08-03

- The focused ROM test `External AI V4 rejects a reserve that faints while it waits` passed after the timeout path was changed to return the mailbox to `IDLE` before vanilla fallback.
- `make -j16 check TESTS='External AI'` completed successfully after the test-runner expectation was updated to accept that documented `IDLE` terminal state.
- `py -3 -m unittest discover -s tools\\mgba-bridge\\tests -q` passed: **72 tests, OK**.
- `git diff --check` passed from PowerShell. The chained WSL verification reached that final check after the ROM and Python tests; the WSL process was then stopped because Windows-mounted filesystem I/O left the final Git check running indefinitely.
- The exclusion regression test covers `BATTLE_TYPE_TWO_OPPONENTS`, ensuring Phase 7A does not request an external decision for a two-trainer double.

## Normal-ROM manual smoke evidence — 2026-08-03

After closing mGBA to release the output file, the normal `pokeemerald.gba` was rebuilt and loaded with the mGBA bridge and local service. The user confirmed that both:

- an eligible trainer single battle, and
- an intentional one-trainer double battle

worked correctly in the normal ROM (not the temporary latency-test ROM).

## Latency and fallback evidence

The service prompt now requests the minimal normal decision sequence: battle state, legal actions (which includes ROM-published move facts), and a single atomic choice. The normal-ROM timeout is 1,800 frames; the test-ROM timeout remains 900 frames. On expiration, the ROM clears the thinking message, resets the request to `IDLE`, and uses the unchanged vanilla trainer AI. A delayed bridge response is therefore rejected rather than being mistaken for the next decision.

## Exit status

Phase 7A's implementation, automated checks, and primary normal-ROM smoke tests are complete. The feature remains deliberately limited to intentional one-trainer doubles. The two-trainer-double ownership work is reserved for Phase 7B.
