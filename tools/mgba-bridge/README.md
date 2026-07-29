# mGBA local Ollama battle agent (Phase 4A)

This is the playable Calvin-only vertical slice. The ROM gives the local agent
read-only battle tools and accepts only one existing legal action index. It
keeps the normal trainer-AI decision as its fallback: if the bridge, service,
or Ollama response is absent or invalid, Calvin acts after at most 900 frames
(about 15 seconds).

## Scope and safety

- Only Youngster Calvin (`TRAINER_CALVIN_1`) in a standard trainer single
  battle is eligible. Moves only; no switches, items, benches, doubles, or
  other trainers.
- The Lua listener and Python service bind only to `127.0.0.1:57621`.
- The agent receives only read-only snapshot tools and can finish only with
  `choose_action(action_index)`. It cannot name a move or target, access mGBA,
  run commands, or use a network tool.
- `generated/mailbox_address.lua` is generated from the current ELF, ignored
  by Git, and must be regenerated after every ROM rebuild.
- One mGBA script accepts one service connection. Restart mGBA and reload the
  script before starting another service session.

## Build and launch

1. In WSL, build the ROM and generate the mailbox address:

   ```bash
   cd /mnt/c/Users/jerem/Documents/Github/pokeemerald-expansion
   make -j16
   python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf
   ```

2. In Windows PowerShell, confirm the local model exists, then start the
   service and leave the window open:

   ```powershell
   ollama list
   cd C:\Users\jerem\Documents\Github\pokeemerald-expansion
   py -3 tools\mgba-bridge\battle_agent_service.py
   ```

   The list must contain `qwen2.5-coder:7b`. Start `ollama serve` in a
   separate window only if its local API is not already available.

3. Open the newly built `pokeemerald.gba` in Windows mGBA. Select **Tools →
   Scripting…**, then load `tools\mgba-bridge\mgba_bridge.lua`.

4. Start a battle with Youngster Calvin. A successful agent turn has logs like:

   ```text
   BAGB service: request 1 received
   BAGB service: request 1 tool get_battler
   BAGB service: request 1 tool choose_action
   BAGB service: request 1 chose action 0
   BAGB request forwarded: 1
   BAGB response written: 1
   ```

   The `response written` sequence must match the service request sequence.
   Calvin then uses the corresponding legal move before the deadline.

## Fallback smoke test

Start Calvin's battle without the Python service, or close the service after
`BAGB request forwarded`. mGBA must remain responsive; Lua writes no later
response, and Calvin eventually performs the already-computed vanilla move.
To retry after a service disconnect, restart mGBA and reload the Lua script.

## Automated checks

```powershell
py -3 -m unittest discover -s tools\mgba-bridge\tests -v
```

```bash
make -j16 check TESTS='External AI'
make -j16
```

The protocol and acceptance criteria are defined in the [Phase 4A
specification](../../docs/openai-battle-agent/specs/2026-07-29-phase-4a-local-ollama-tool-agent.md).
