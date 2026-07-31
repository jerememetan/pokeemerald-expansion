# Phase 6A Voluntary Switching Verification Evidence

**Date:** 2026-07-29

**Specification:** [Phase 6A specification](../specs/2026-07-29-phase-6a-voluntary-switching.md)

**Flow review:** [Phase 6A flow review](2026-07-29-phase-6a-voluntary-switching-flow-review.md)

**Implementation plan:** [Phase 6A implementation plan](../plans/2026-07-29-phase-6a-voluntary-switching.md)

## Automated results

| Check | Result |
| --- | --- |
| `py -3 -m unittest discover -s tools\\mgba-bridge\\tests -v` | Pass: 69 tests |
| `make -j16 check TESTS='External AI V3'` | Pass: 3 tests |
| `make -j16 check TESTS='External AI'` | Pass: 28 tests |
| `make -j16` | Pass: `pokeemerald.gba` produced |
| `python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf` | Pass: mailbox `0x0201C004` |
| `git diff --check` | Pass |

The V3 ROM tests cover publishing six opponent-party records, accepting a legal
voluntary switch through the standard controller path, blocking an external
request while locked, and rejecting a selected reserve that faints before the
response is consumed. The broader external-AI suite also confirms the existing
move, timeout, malformed-response, stale-response, and fallback behavior.

The normal ROM build used 248266 B of EWRAM (94.71%), 30396 B of IWRAM
(92.76%), and 23958224 B of ROM (71.40%).

## Manual connected-switch evidence

A connected mGBA session produced this service audit on request 5:

```text
legal actions: 0=LEER->battler 0; 1=TACKLE->battler 0; 2=ODOR_SLEUTH->battler 0;
3=SWITCH->party 1; 4=SWITCH->party 2
selected: 3=SWITCH->party 1
selected ROM facts: switch_to_party_slot=1
```

The game performed the requested switch. The following request exposed the
replacement Pokémon's legal moves (`BITE`, `HOWL`, and `PURSUIT`), confirming
that the ROM, Lua bridge, service, and normal switch controller stayed aligned
after the action.

## Remaining manual check

The connected-switch half of the manual smoke test is complete. Close only the
Python service while keeping mGBA and its Lua bridge open, then start a new
trainer turn. The normal `AI is thinking` status must clear and vanilla AI must
finish the turn without a permanent freeze. This verifies the V3 absent-service
fallback in the playable ROM.

## Conclusion

Phase 6A's code, protocol, service tools, normal ROM artifact, and live
connected voluntary switch are verified. The phase remains pending only the
absent-service manual smoke test above.
