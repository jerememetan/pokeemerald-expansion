# Phase 5A Evidence: In-Battle Thinking Status

**Status:** Complete

**Specification:** [Phase 5A thinking status](../specs/2026-07-29-phase-5a-thinking-status.md)

**Flow review:** [Phase 5A thinking-status flow review](2026-07-29-phase-5a-thinking-status-flow-review.md)

**Implementation plan:** [Phase 5A thinking-status plan](../plans/2026-07-29-phase-5a-thinking-status.md)

## Automated verification

```powershell
wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI thinking status shows the normal message panel'"
```

Result: **1/1 test passed**. The regression begins with the BG0 position used
by player move selection (`X=24`, `Y=320`) and proves the thinking-status
renderer restores the normal battle-message viewport before displaying text.
The test was observed failing before the renderer correction and passing after
it.

```powershell
wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16 check TESTS='External AI'"
```

Result: **25/25 tests passed**. This includes thinking-status lifecycle,
current/stale/illegal V2 response, legal-action snapshot, and saved-vanilla
fallback coverage.

```powershell
wsl bash -lc "cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && make -j16"
```

Result: completed successfully and produced `pokeemerald.gba`. Final memory
usage was EWRAM 247,618 B (94.46%), IWRAM 30,396 B (92.76%), and ROM
23,957,320 B (71.40%). `git diff --check` produced no whitespace errors before
the evidence commit.

## Manual mGBA verification

The operator verified both Calvin scenarios with the existing mGBA Lua bridge
and local Python/Ollama service:

1. **Connected service:** after the player selected a move, the normal lower
   battle message panel visibly displayed `AI is thinking...` while the agent
   decided, then cleared automatically after an accepted response.
2. **Absent-service fallback:** after stopping the service, the thinking status
   displayed during the existing wait and cleared when the saved vanilla
   trainer-AI fallback continued the battle. No stuck status remained.

## Exit criteria

- [x] Calvin displays the animated waiting status in the normal lower message
  panel.
- [x] It clears on accepted response and on the existing absent-service
  fallback.
- [x] The 900-frame deadline, mailbox protocol, action validation, and saved
  vanilla fallback remain unchanged.
- [x] Focused and broader relevant ROM tests pass, and a fresh playable ROM
  build completed.

Phase 5A is complete. Broader Phase 5 diagnostics remain separate work.
