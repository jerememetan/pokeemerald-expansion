# Phase 8 Packaging and Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use task-by-task inline execution for this documentation-only plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give a new Windows-with-Ubuntu-WSL developer a reproducible, manual local handoff for the BAGB/5 AI trainer, including all supported battle modes and safe vanilla fallback recovery.

**Architecture:** Add one high-level project handoff guide for prerequisites, compatibility, build verification, and the full demo. Keep `tools/mgba-bridge/README.md` as the operational runbook; correct its stale presentation text and unsafe character rendering, then cross-link both guides. No launch script, ROM, Lua, protocol, Python-service, model, or battle-mechanics code changes are permitted.

**Tech Stack:** Markdown, Windows PowerShell, Ubuntu WSL, GNU Make, Python 3, Ollama, mGBA 0.10.5, BAGB/5.

---

## File structure

| File | Responsibility |
| --- | --- |
| Create `docs/openai-battle-agent/phase-8-handoff.md` | High-level first-run prerequisites, compatibility fingerprint, command sequence, three-mode verification, fallback demo, limitations, and artifact policy. |
| Modify `tools/mgba-bridge/README.md` | Runtime runbook: link the handoff guide, preserve exact launch/recovery commands, replace stale thinking text, and use ASCII-safe labels. |
| Modify `docs/openai-battle-agent/integration-plan.md` | Link the Phase 8 plan and later its evidence from the active roadmap. |
| Create `docs/openai-battle-agent/reviews/2026-08-04-phase-8-packaging-and-handoff-evidence.md` | Record fresh automated and manual verification only after it is actually observed. |
| Existing verification only: `tools/mgba-bridge/tests/*.py`, `test/battle/ai.c` | Prove the documentation-only change has not changed bridge/service or ROM behavior. No new test file is needed because this phase has no executable implementation. |

### Task 1: Capture the unmodified runtime verification baseline

**Files:**
- Test: `tools/mgba-bridge/tests/test_battle_agent_service.py`
- Test: `tools/mgba-bridge/tests/test_bridge_protocol.py`
- Test: `test/battle/ai.c`
- Verify: `.gitignore`

- [ ] **Step 1: Run the Python bridge/service suite before documentation edits**

Run in Windows PowerShell:

```powershell
py -3 -m unittest discover -s tools\mgba-bridge\tests -q
```

Expected: the command exits `0` and reports no failures or errors.

- [ ] **Step 2: Run the focused ROM External AI tests before documentation edits**

Run in Ubuntu WSL:

```bash
make -j16 check TESTS='External AI'
```

Expected: the command exits `0`; every External AI test passes. Established
unrelated `ASSUME` diagnostics, if any, are not an External AI failure.

- [ ] **Step 3: Verify the generated mailbox file remains ignored**

Run in Ubuntu WSL:

```bash
git check-ignore tools/mgba-bridge/generated/mailbox_address.lua
```

Expected: stdout is exactly `tools/mgba-bridge/generated/mailbox_address.lua`.

### Task 2: Write the high-level reproducible handoff guide

**Files:**
- Create: `docs/openai-battle-agent/phase-8-handoff.md`
- Reference: `docs/openai-battle-agent/reviews/2026-07-29-phase-3a-mgba-loopback-bridge-evidence.md`
- Reference: `tools/mgba-bridge/README.md`

- [ ] **Step 1: Create the guide with the validated target and boundaries**

State Windows with Ubuntu WSL as the validated target. List the required
existing tools: the project build toolchain, Python 3/`py -3`, Ollama with
`qwen2.5-coder:7b`, and Windows mGBA. State that it is manual only: it does
not install tools, download models, launch processes, or make cloud calls.

- [ ] **Step 2: Record the compatibility fingerprint without duplicating an unverifiable version command**

Include the path `C:\\Program Files\\mGBA\\mGBA.exe`, title-bar version
`0.10.5`, SHA-256
`5A3C98C2984DD04BD0D7C9378CDFAE937AE0D73A196C880BB2EECF3B254AF247`, and a
link to the Phase 3A evidence explaining that `--version` has no stdout on
this executable. State BAGB/5 is the active runtime contract.

- [ ] **Step 3: Add exact manual command blocks and expected observations**

Include these commands in the guide:

```bash
cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion
make -j16
python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf
git check-ignore tools/mgba-bridge/generated/mailbox_address.lua
```

```powershell
ollama list
cd C:\Users\jerem\Documents\Github\pokeemerald-expansion
py -3 tools\mgba-bridge\battle_agent_service.py
```

State that mGBA must be closed for the build, that the generator must run after
every rebuilt ELF, and that the service may wait at `connecting to mGBA` until
Lua is loaded. Use `Tools > Scripting...` and load
`tools\mgba-bridge\mgba_bridge.lua` once. Require connected logs from both
ends and matching request/response sequence numbers.

- [ ] **Step 4: Add manual verification and recovery checklists**

Require a connected trainer single, intentional one-trainer double, and
two-trainer double. For a two-trainer double, require one audit containing
both opponent battlers. Require one absent/disconnected-service demo that
shows `AI is thinking..` then continues with saved vanilla AI. Include exact
safe recovery for file locks, stale generated configuration, listener
conflicts, missing/cold model, malformed response, and service disconnect.

- [ ] **Step 5: Add limitations and artifact policy**

State the agent can choose only ROM-authorized moves or voluntary switches,
cannot use items, and cannot directly control mGBA/network/files. State that
ROM/ELF/map and `generated/mailbox_address.lua` are not committed, are
machine-specific build outputs, and must never be manually edited.

### Task 3: Align the operational runtime README

**Files:**
- Modify: `tools/mgba-bridge/README.md`
- Reference: `docs/openai-battle-agent/phase-8-handoff.md`

- [ ] **Step 1: Add a short cross-link at the start of the runtime README**

Point new developers to `../../docs/openai-battle-agent/phase-8-handoff.md`
for validated-machine prerequisites and the full handoff verification. Preserve
the README as the source of truth for running and recovering the bridge.

- [ ] **Step 2: Correct fixed-status and action terminology**

Replace every `AI is thinking...` checklist occurrence with exactly
`AI is thinking..`. Keep `choose_actions` plural where the current service
logs the terminal tool. Do not claim this audit is hidden model reasoning.

- [ ] **Step 3: Replace non-ASCII operational labels with ASCII-safe text**

Replace the garbled menu label with `Tools > Scripting...` and any garbled
`Pokemon` text with `Pokemon`. Preserve the semantic instructions, command
paths, endpoint `127.0.0.1:57621`, model name, fallback bound, and recovery
sequence.

### Task 4: Link planning artifacts and record verification evidence

**Files:**
- Modify: `docs/openai-battle-agent/integration-plan.md`
- Modify: `docs/openai-battle-agent/specs/2026-08-04-phase-8-packaging-and-handoff.md`
- Modify: `docs/openai-battle-agent/reviews/2026-08-04-phase-8-packaging-and-handoff-flow-review.md`
- Create: `docs/openai-battle-agent/reviews/2026-08-04-phase-8-packaging-and-handoff-evidence.md`

- [ ] **Step 1: Link the plan from the specification, flow review, and roadmap**

Use the exact plan path
`plans/2026-08-04-phase-8-packaging-and-handoff.md`. Keep the active roadmap
name as Phase 8 and describe the original parent-design Phase 9 heading only
as historical numbering.

- [ ] **Step 2: Run post-edit documentation and regression checks**

Run:

```powershell
git diff --check
py -3 -m unittest discover -s tools\mgba-bridge\tests -q
```

Run in Ubuntu WSL:

```bash
make -j16 check TESTS='External AI'
```

Expected: each command exits `0`; Python tests report no failures or errors,
and the focused ROM test has no External AI failures.

- [ ] **Step 3: Perform and record the fresh manual evidence**

With mGBA closed, run `make -j16`, generate the mailbox configuration, and
perform the connected three-mode demo plus the disconnected fallback demo from
the guide. Record only observed output and behavior, the mGBA fingerprint,
command results, generated-file ignore check, and any limitation. Do not claim
the phase is complete until this evidence exists.

## Compatibility and fallback checks

- Build addresses are generated from the current ELF and mGBA is restarted
  after regeneration.
- Only one mGBA Lua listener and one Python service use the loopback port.
- BAGB/5 is the documented active protocol; legacy helper names are not
  launch instructions.
- Every model/transport failure preserves the saved vanilla trainer action;
  no guide action instructs a user to forge a mailbox reply.
- All three supported scopes remain trainer singles, intentional one-trainer
  doubles, and two-trainer doubles. Items remain out of scope.

## Documentation updates

- Cross-link the Phase 8 specification, flow review, implementation plan,
  high-level handoff guide, runtime README, roadmap, and final evidence.
- Preserve Phase 3A as the source of the verified mGBA fingerprint.

## Phase exit criteria

1. The two guides are consistent with BAGB/5, `choose_actions`, the fixed
   `AI is thinking..` message, all three battle modes, recovery behavior, and
   artifact policy.
2. The Python bridge tests, focused External AI ROM tests, normal ROM build,
   and generated-file ignore check have fresh recorded evidence.
3. A manual connected decision and a manual absent/disconnected fallback are
   recorded, including a two-trainer-double audit with both opponent battlers.
4. No launcher, installer, runtime code, protocol, ROM behavior, model setup,
   or generated artifact is added or changed.

## Self-review

- **Specification coverage:** Tasks 1–4 cover every in-scope behavior,
  boundary, failure path, test, and exit criterion. Out-of-scope automation
  and runtime changes are explicitly excluded.
- **Terminology consistency:** The plan uses active `BAGB/5`, `choose_actions`,
  and `AI is thinking..`; the current roadmap's Phase 8 title is authoritative.
- **Placeholder scan:** No task contains a placeholder, undefined helper, or
  unspecified test command. This phase has no executable code, so it uses
  existing regression suites rather than an artificial documentation test.
- **Battle-mechanics and scope check:** All tasks modify documentation only and
  preserve the ROM-side legal-action validation and vanilla fallback invariant.
