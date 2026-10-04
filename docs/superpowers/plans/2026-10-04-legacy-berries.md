# Archived Berries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the eight archived starting-tree changes and higher berry yields.

**Architecture:** Change only current initialization operands and the existing yield kernel. A focused native-C regression test compares the real kernel against the pinned archive; no new ROM-wide test framework or replacement berry engine is needed.

**Tech Stack:** Current C/script sources, Python standard-library unittest, Git object reads, native WSL `cc`, Make.

---

Source specification: `docs/superpowers/specs/2026-10-04-legacy-berries-design.md`.
Archive: `f5e81e85df6fe40ae490bf7268d0186d7f0426ed`.
Starting HEAD: `bf8074499f` (the user's map/encounter cleanup is preserved).

### Task 1: Test and restore berry data and yield

**Files:**

- Modify `data/scripts/new_game.inc` — only eight `setberrytree` variety operands.
- Modify `src/berry.c` — only `CalcBerryYieldInternal` and its descriptive comment.
- Create `tools/migration/tests/test_legacy_berries.py` — independent actual-C and tree-data fixtures.

- [ ] Write the failing fixtures. Use this expected operand map:

```python
EXPECTED_VARIETIES = {
    'BERRY_TREE_ROUTE_116_PINAP_1': 'BERRY_ID_CHERI',
    'BERRY_TREE_ROUTE_115_BLUK_1': 'BERRY_ID_ORAN',
    'BERRY_TREE_ROUTE_115_BLUK_2': 'BERRY_ID_ORAN',
    'BERRY_TREE_ROUTE_110_NANAB_1': 'BERRY_ID_ORAN',
    'BERRY_TREE_ROUTE_110_NANAB_2': 'BERRY_ID_PERSIM',
    'BERRY_TREE_ROUTE_121_NANAB_2': 'BERRY_ID_SITRUS',
    'BERRY_TREE_ROUTE_123_PECHA': 'BERRY_ID_SITRUS',
    'BERRY_TREE_ROUTE_123_RAWST': 'BERRY_ID_SITRUS',
}
```

Parse the complete initial tree block, adapt archived `ITEM_TO_BERRY(ITEM_*_BERRY)`
names to `BERRY_ID_*`, and compare all commands against that pinned block;
this detects omitted or extra changes, not just the eight matching lines.

Extract actual C definitions with this complete definition matcher (not prototypes):

```python
def yield_definition(source):
    import re
    match = re.search(
        r'(?ms)^static u8 CalcBerryYieldInternal\([^;]*?\)\s*\n\{.*?^\}',
        source,
    )
    if match is None:
        raise AssertionError('yield definition missing')
    return match.group(0)
```

Compile the current and archived bodies into one temporary native C runner,
renaming only the archived function to `LegacyCalcBerryYieldInternal`. Supply
`u8/u16/u32` from `<stdint.h>`, `NUM_WATER_STAGES=4`, a deterministic `Random`
stub returning a chosen `u16`, and `OW_BERRY_MOISTURE=0` or `1`. The default
runner must compare both real functions on pairs `(max,min)` of `(5,2)`,
`(10,2)`, `(15,10)`, and `(1,1)`, watering counts 0–4, and random values
0–65535. Fail with the concrete inputs/results on any mismatch. The moisture
runner must require the current result to equal `min` for those inputs.
Use `cc -std=c11 -Wall -Wextra -Werror` and execute the resulting runner;
only use disposable temporary outputs. The test command must not silently
skip missing compiler coverage: run in WSL where `cc` is available.

- [ ] Run red before editing the production sources:

```powershell
wsl.exe -e bash -lc 'cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion && python3 -m unittest tools.migration.tests.test_legacy_berries -v'
```

Expected: assertions show missing tree substitutions and differing default yields;
the optional moisture behaviour already passes.

- [ ] Apply the operand map above and this complete yield kernel:

```c
static u8 CalcBerryYieldInternal(u16 max, u16 min, u8 water)
{
    u32 randMin;
    u32 randMax;
    u32 rand;
    u32 extraYield;

    if (OW_BERRY_MOISTURE)
    {
        return min;
    }
    else if (water == 0)
    {
        return Random() % 4 + min;
    }
    else
    {
        randMin = (max - min) * water;
        randMax = (max - min) * (water + 1);
        rand = randMin + Random() % (randMax - randMin + 1);

        if ((rand % NUM_WATER_STAGES) >= NUM_WATER_STAGES / 2)
            extraYield = rand / NUM_WATER_STAGES + 1;
        else
            extraYield = rand / NUM_WATER_STAGES;
        return extraYield + min;
    }
}
```

- [ ] Run the same tests green, `git diff --check`, and Python syntax checks.
- [ ] Obtain independent spec review, then quality review; fix and rereview any findings.
- [ ] Build the ROM using an exact native-filesystem source snapshot, or the normal workspace if fast enough.
- [ ] Stage only these three paths and commit `feat: restore archived berry varieties and yields` after verification.

### Task 2: Record acceptance and continue to caps

- [ ] Record automated results, exact source/build hashes, and explicitly pending fresh-save/harvest checks in the dated migration progress document.
- [ ] Preserve all user changes outside this allowlist; do not touch existing saves.
- [ ] Continue the separate level-cap unit without asking for another continuation approval.
