# Local AI Trainer Handoff

This is the first-run and verification guide for the completed local external AI trainer. It is a manual developer workflow: it does not install tools, download models, start processes, or automatically load mGBA Lua. For live runtime steps and recovery, see the [bridge runbook](../../tools/mgba-bridge/README.md).

## Validated target

The documented target is Windows with Ubuntu WSL and this repository checked out at `C:\Users\jerem\Documents\Github\pokeemerald-expansion`. If your clone is elsewhere, replace that path in the commands below with its own Windows and WSL paths.

| Requirement | Verification | Notes |
| --- | --- | --- |
| WSL build toolchain | `make --version` and `arm-none-eabi-gcc --version` in Ubuntu WSL | Follow [Windows/WSL setup](../../INSTALL.md#windows-1011-wsl1) if either is unavailable. |
| Python launcher | `py -3 --version` in PowerShell | Runs the bridge service and tests. |
| Ollama model | `ollama list` in PowerShell | Must list `qwen2.5-coder:7b`. |
| Windows mGBA | GUI title bar and `Get-FileHash` below | A different build is not automatically supported. |

### Pinned mGBA compatibility record

```text
Path:    C:\Program Files\mGBA\mGBA.exe
Version: 0.10.5 (Windows GUI title bar)
SHA-256: 5A3C98C2984DD04BD0D7C9378CDFAE937AE0D73A196C880BB2EECF3B254AF247
```

```powershell
Get-FileHash 'C:\Program Files\mGBA\mGBA.exe' -Algorithm SHA256
```

This mGBA build prints no textual version for `--version`; the GUI title bar is the version source. See [Phase 3A mGBA evidence](reviews/2026-07-29-phase-3a-mgba-loopback-bridge-evidence.md). The active ROM, Lua, and service contract is **BAGB/5**; do not mix an older script, generated address, or service with this ROM.

## Start the demo

### 1. Build in Ubuntu WSL

Close mGBA first: it can lock `pokeemerald.gba` and prevent rebuilding.

```bash
cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion
make -j16
python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf
git check-ignore tools/mgba-bridge/generated/mailbox_address.lua
```

Expected: the ROM and ELF are fresh, the generator writes the address from that ELF, and the final command prints the generated address path. Regenerate after every rebuilt ELF; never edit or reuse the generated address.

### 2. Verify Ollama and start one service

```powershell
ollama list
cd C:\Users\jerem\Documents\Github\pokeemerald-expansion
py -3 tools\mgba-bridge\battle_agent_service.py
```

`ollama list` must include `qwen2.5-coder:7b`. The service may wait at the following line until Lua is loaded; do not start a second service.

```text
BAGB service: connecting to mGBA at 127.0.0.1:57621
```

After an Ollama restart, optional manual warm-up can avoid a first-turn fallback caused by model loading:

```powershell
ollama run qwen2.5-coder:7b "Reply with exactly READY"
```

### 3. Open mGBA and load Lua once

1. Open the fresh `pokeemerald.gba` in Windows mGBA.
2. Choose **Tools > Scripting...** and load `tools\mgba-bridge\mgba_bridge.lua` exactly once.
3. Confirm mGBA prints `BAGB listener ready 127.0.0.1:57621` and `BAGB client connected`.
4. Confirm PowerShell prints `BAGB service: mGBA bridge connected`.

The Lua listener is loopback-only and accepts one service client. Do not probe the port, load the script twice, or run a second service.

## Verify the completed feature

Matching mGBA request and response sequence numbers show that the service response reached the ROM. The audit records selected ROM-authorized actions and tool calls; it is not hidden model reasoning.

Run all connected checks:

1. Normal trainer single: one audit chooses an action and the opponent uses it.
2. Intentional one-trainer double: one audit chooses actions for both opponents.
3. Two-trainer double (two trainers spot the player together): one audit contains selected actions for both opponent battlers. If party data is inspected, left and right reserve ownership stays distinct.

During a pending response, the lower message panel shows exactly `AI is thinking..`. It clears automatically before a valid action or fallback proceeds; no button press is required.

### Verify fallback deliberately

Stop or omit the PowerShell service during a voluntary opponent turn. After its bounded wait, the ROM clears `AI is thinking..` and uses saved vanilla trainer-AI actions. The battle must remain playable. After a service disconnect, restart mGBA and reload Lua before a new connected attempt; an existing Lua session is not reconnected in place.

## Choose a local Ollama model

Run the service normally to select from installed local models:

```powershell
py -3 tools\mgba-bridge\battle_agent_service.py
```

In Windows PowerShell, use Up/Down and Enter. `qwen2.5-coder:7b` is the
default when installed. To skip the menu for a specific model:

```powershell
py -3 tools\mgba-bridge\battle_agent_service.py --model hermes3:8b
```

Run `ollama list` to view names. Ctrl+C at the menu exits before mGBA connects;
Ctrl+C after connection still uses the existing ROM timeout and vanilla fallback.

## Automated verification

Run in PowerShell:

```powershell
py -3 -m unittest discover -s tools\mgba-bridge\tests -q
```

Run in Ubuntu WSL with mGBA closed:

```bash
make -j16 check TESTS='External AI'
make -j16
python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf
git check-ignore tools/mgba-bridge/generated/mailbox_address.lua
```

The commands must exit successfully, with no External AI test failure, a fresh ROM, and the generated address path printed by the ignore check.

## Recovery and limitations

| Situation | Safe action |
| --- | --- |
| ROM cannot be overwritten | Close mGBA or another Windows process holding it, then rebuild. |
| Generated address missing or stale | Regenerate from the fresh ELF; close and reopen mGBA before loading Lua. |
| Lua cannot listen on port `57621` | Close the previous mGBA/Lua session; reopen mGBA and load Lua once. |
| Model missing, cold, slow, malformed, or disconnected | Let the bounded wait use vanilla fallback; inspect logs before a new session. |
| Lua rejects a response or client disconnects | Let the current battle fall back; restart mGBA, reload Lua, then start one service. |

The model can inspect read-only battle tools and select only a current ROM-authorized move or voluntary switch. It cannot use battle items, write party slots directly, access mGBA, run commands, access files, or use the network. Trainer singles, intentional one-trainer doubles, and two-trainer doubles are supported; items are out of scope.

Do not commit `pokeemerald.gba`, `pokeemerald.elf`, map files, or `tools/mgba-bridge/generated/mailbox_address.lua`. They are generated machine-specific outputs, not shared source artifacts.

## Related artifacts

- [Phase 8 specification](specs/2026-08-04-phase-8-packaging-and-handoff.md)
- [Phase 8 flow review](reviews/2026-08-04-phase-8-packaging-and-handoff-flow-review.md)
- [Phase 8 implementation plan](plans/2026-08-04-phase-8-packaging-and-handoff.md)
- [Bridge runtime runbook](../../tools/mgba-bridge/README.md)
