# Play the local Ollama AI-trainer demo

Keep Ollama, the Python service, and mGBA in their own windows; this guide
does not start them for you.

For validated Windows/Ubuntu-WSL prerequisites, the mGBA fingerprint,
end-to-end verification, and limitations, read the
[Phase 8 handoff guide](../../docs/openai-battle-agent/phase-8-handoff.md).
This README remains the operational source of truth for starting, observing,
and recovering the bridge runtime.

## Scope and safety

- Every opted-in ordinary trainer battle can use the external agent: trainer
  singles, intentional one-trainer doubles, and two separate trainers that
  spot the player together. A two-trainer double produces one decision that
  selects both opponent actions.
- The agent reads battle data and may finish only by selecting current
  ROM-authorized move or voluntary-switch action indexes. It can inspect the
  six-slot opposing party with `get_party()`, including the owner of each
  record. It cannot name moves, targets, or party slots; access mGBA; run
  commands; use the network; or use battle items.
- The ordinary trainer AI is the fallback. If no valid response arrives, the
  opponents use their saved vanilla actions after at most 1,800 frames (about
  30 seconds).
- Lua listens only on `127.0.0.1:57621`; the Python service is its one client.
  Do not probe that port or start another service to test it.
- `generated/mailbox_address.lua` is ignored by Git. Regenerate it from a
  fresh ELF after every ROM rebuild; never edit it manually.

## Play the local AI-trainer demo

### 1. Build the ROM and mailbox address

In WSL:

```bash
cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion
make -j16
python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf
```

Expected: `make` produces `pokeemerald.gba` and the generator writes
`tools/mgba-bridge/generated/mailbox_address.lua`.

### 2. Confirm and warm Ollama

In Windows PowerShell:

```powershell
ollama list
```

The list must contain `qwen2.5-coder:7b`. Before a live demo after an Ollama
restart, warm it in a separate PowerShell window:

```powershell
ollama run qwen2.5-coder:7b "Reply with exactly READY"
```

Wait for `READY`. Warming is optional but recommended: a cold 7B-model load
can exceed the fallback deadline. A fallback alone does not prove cold loading
was the cause; use the service and Lua logs below to find known bridge errors.

### 3. Start the Python service

Leave this PowerShell process running:

```powershell
cd C:\Users\jerem\Documents\Github\pokeemerald-expansion
py -3 tools\mgba-bridge\battle_agent_service.py
```

It is normal for the service to print this once and wait silently until Lua is
loaded in mGBA:

```text
BAGB service: connecting to mGBA at 127.0.0.1:57621
```

Do not restart a service waiting at that line. It retries the Lua listener
until the next step completes.

### 4. Open mGBA, load Lua, and start a trainer battle

1. Open the freshly built `pokeemerald.gba` in Windows mGBA.
2. Choose **Tools > Scripting...** and load
   `tools\mgba-bridge\mgba_bridge.lua` exactly once.
3. Confirm the Scripting window says:

   ```text
   BAGB listener ready 127.0.0.1:57621
   BAGB client connected
   ```

4. Confirm PowerShell says:

   ```text
   BAGB service: mGBA bridge connected
   ```

5. Start a trainer battle and choose the player's move.

## What success looks like

Move/tool details vary by battle state, but every sequence number must match:

```text
mGBA Scripting:
BAGB request forwarded: 1
BAGB response written: 1

Python service:
BAGB service: request 1 received
BAGB service: request 1 tool list_legal_actions
BAGB service: request 1 tool choose_actions
BAGB service: request 1 chose actions ((1, 0),)
BAGB service: audit #1
  tools used: list_legal_actions, choose_actions
  legal actions: 0=TACKLE->battler 0; 1=LEER->battler 0
  selected: 0=TACKLE->battler 0
  selected ROM facts: STAB=yes, effectiveness=neutral, KO=no, priority=0
  speed context: battler_1_first
```

When a usable reserve exists, `list_legal_actions` can also show an entry such
as `2=SWITCH->party 1`. The model may call `get_party()` before selecting that
index. The ROM revalidates the reserve and performs the normal trainer switch;
the service never writes a party slot directly.

While a response is pending, the normal lower battle-message panel shows
`AI is thinking..`. It clears automatically when mGBA writes an accepted
response and the normal battle action continues. The audit reports dispatched
tools and ROM facts; it is not hidden model reasoning or model-written prose.

## Recovery

| Symptom | Meaning and safe recovery |
| --- | --- |
| `ollama list` lacks `qwen2.5-coder:7b` | Install/pull that configured model before starting the service. |
| Ollama is unavailable or a first turn falls back | Start Ollama normally, warm the model, then begin a new Calvin demo. Inspect logs: a fallback is not a conclusive diagnosis. |
| Lua cannot bind/listen on `127.0.0.1:57621` | Close the earlier mGBA/Lua session that owns the listener. Reopen mGBA and load Lua once. |
| Lua cannot load `generated/mailbox_address.lua`, or the ROM was rebuilt | Run the generator in step 1 against fresh `pokeemerald.elf`, then reopen mGBA. |
| `BAGB client disconnected`, malformed response, or `BAGB response rejected` | Let the current wait resolve through vanilla fallback. Then restart mGBA, reload Lua, and start one new service session. |
| `BAGB service: ... vanilla_fallback` or no response | The ROM intentionally keeps the saved trainer-AI action. Wait for the battle to proceed and inspect logs before resetting. |

Never edit generated files, send a mailbox reply manually, probe port 57621,
or run a second Python service. After a service disconnect, a new attempt
requires mGBA restart and Lua reload.

## Smoke-test checklists

### Connected service

1. Complete the launch steps and fight any ordinary trainer.
2. Choose the player's move and observe `AI is thinking..`.
3. Verify matching `BAGB request forwarded: N` and `BAGB response written: N`.
4. Verify the service logged `request N received`, `chose action`, and
   `audit #N`.
5. Verify the trainer acts and the thinking message clears without a button press.
6. If the trainer has another usable Pokemon, optionally verify an audit containing
   `SWITCH->party N` is followed by the same Pokemon entering the battle.

### Absent-service fallback

1. Omit the Python service, or stop it after `BAGB request forwarded`.
2. Choose the player's move in a trainer battle.
3. Observe `AI is thinking..` during the bounded wait.
4. Verify the message clears and the trainer uses saved vanilla AI without
   a stuck battle.
5. Before another connected demo after a disconnect, restart mGBA and reload
   Lua.

### Two-trainer double battle

1. Start a map battle where two independent trainers spot the player together.
2. Confirm one `BAGB request forwarded: N` and one service `audit #N` occur
   for each fully voluntary opponent turn, not one request per trainer.
3. Confirm the audit contains a selected action for both `battler 1` and
   `battler 3`.
4. If the agent calls `get_party`, confirm slots 0–2 say `opponent-left` and
   slots 3–5 say `opponent-right`. Only `list_legal_actions` determines
   selectable switches.
5. If a switch is selected, confirm the entering Pokemon belongs to the
   trainer whose action selected it. Stop the service on another voluntary
   turn to confirm both opponents fall back to vanilla AI and the battle
   remains playable.
6. After this check, smoke-test one normal trainer single and one intentional
   one-trainer double using the same Lua bridge and service.

## Automated checks

```powershell
py -3 -m unittest discover -s tools\mgba-bridge\tests -v
```

```bash
make -j16 check TESTS='External AI'
make -j16
```

## Phase artifacts

- [Phase 4A local Ollama agent specification](../../docs/openai-battle-agent/specs/2026-07-29-phase-4a-local-ollama-tool-agent.md)
- [Phase 4B decision-audit evidence](../../docs/openai-battle-agent/reviews/2026-07-29-phase-4b-powershell-decision-audit-evidence.md)
- [Phase 5A thinking-status evidence](../../docs/openai-battle-agent/reviews/2026-07-29-phase-5a-thinking-status-evidence.md)
- [Phase 5B specification](../../docs/openai-battle-agent/specs/2026-07-29-phase-5b-demo-guide.md)
- [Phase 5B flow review](../../docs/openai-battle-agent/reviews/2026-07-29-phase-5b-demo-guide-flow-review.md)
- [Phase 5B implementation plan](../../docs/openai-battle-agent/plans/2026-07-29-phase-5b-demo-guide.md)
- [Phase 6A voluntary-switching specification](../../docs/openai-battle-agent/specs/2026-07-29-phase-6a-voluntary-switching.md)
- [Phase 6A flow review](../../docs/openai-battle-agent/reviews/2026-07-29-phase-6a-voluntary-switching-flow-review.md)
- [Phase 6A implementation plan](../../docs/openai-battle-agent/plans/2026-07-29-phase-6a-voluntary-switching.md)
- [Phase 7A evidence](../../docs/openai-battle-agent/reviews/2026-08-02-phase-7a-single-trainer-doubles-evidence.md)
- [Phase 7B specification](../../docs/openai-battle-agent/specs/2026-08-03-phase-7b-two-trainer-doubles.md)
- [Phase 7B flow review](../../docs/openai-battle-agent/reviews/2026-08-03-phase-7b-two-trainer-doubles-flow-review.md)
- [Phase 7B implementation plan](../../docs/openai-battle-agent/plans/2026-08-04-phase-7b-two-trainer-doubles.md)
