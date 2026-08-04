# Phase 9 Specification: Local Ollama Model Selection

**Status:** Flow-reviewed; implementation planned
**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)
**Flow review:** [Phase 9 flow review](../reviews/2026-08-04-phase-9-local-model-selection-flow-review.md)
**Implementation plan:** [Phase 9 implementation plan](../plans/2026-08-04-phase-9-local-model-selection.md)

## Goal

Let a local player choose an already-installed Ollama model when starting
`tools/mgba-bridge/battle_agent_service.py`, using an arrow-key selection menu
with `qwen2.5-coder:7b` highlighted when it is installed.

## In scope

- Discover locally installed models through the installed `ollama` command
  before opening the mGBA bridge socket.
- In Windows PowerShell, show a compact selector navigated by Up, Down, Enter,
  and Ctrl+C. Other interactive systems may use a numbered line prompt with
  the same available-model/default contract.
- Use the selected model for every local `/api/chat` request during that
  service run.
- Use a 20-second service request deadline to better accommodate local model
  variance; preserve the ROM's independent timeout and vanilla fallback.
- Keep `--model MODEL` as a non-interactive explicit override.
- Preserve the current `qwen2.5-coder:7b` default for non-interactive runs
  when it is installed.
- Add pure parsing/selection tests without requiring Ollama, mGBA, or a ROM.
- Document the normal interactive and explicit-model launch commands.
- In an interactive ANSI-capable terminal, render accepted audit `selected:`
  lines and their selected ROM-facts lines in bright green and bold; preserve
  plain text in redirected output.

## Out of scope

- Downloading, installing, updating, or managing models.
- Persisting a preferred model between service runs.
- ChatGPT, Claude, cloud API keys, subscriptions, launchers, or packaging a
  model with the GBA.
- Changes to audit content, action choice, fallback semantics, or error text.
- ROM mailbox, Lua bridge, battle logic, legal-action validation, ROM timeout, or
  fallback changes.

## Boundaries

| Component | Responsibility | Unchanged behavior |
| --- | --- | --- |
| Python service | Chooses one local model before opening the bridge socket. | Tool loop and strict action validation remain unchanged. |
| Ollama CLI | Lists installed local models only. | The service continues to call the existing local chat endpoint. |
| mGBA / ROM / Lua | None. | Missing or stopped service still reaches bounded vanilla fallback. |

## Required behavior

1. `py -3 tools\\mgba-bridge\\battle_agent_service.py` lists installed model
   names and provides an arrow-key selector before it connects to mGBA.
2. The preferred default is `qwen2.5-coder:7b`; it is highlighted when listed.
   If absent, the first installed model is highlighted.
3. Up/Down wrap through the list. Enter starts the service with the highlighted
   model. Ctrl+C exits cleanly before it connects to mGBA.
4. `--model NAME` skips discovery and the selector, then uses `NAME` exactly as
   provided. This supports scripts and a model name not presently discoverable.
5. If no models can be listed for an interactive start, print an actionable
   local-Ollama message and exit nonzero without opening a bridge connection.
6. If stdin/stdout are not interactive, do not wait for keyboard input: use
   the preferred default if it is listed, otherwise the first listed model; if
   no model is listed, fail nonzero with the same actionable message.
7. A selection failure never changes ROM behavior. With no service connected,
   the ROM’s existing timeout preserves vanilla trainer AI.

## Tests and exit criteria

- Unit tests prove parsing of normal `ollama list` output, headers/blank lines,
  empty output, default selection, wraparound navigation, `--model` bypass,
  and non-interactive selection.
- Existing Python bridge tests pass unchanged.
- `make -j16 check TESTS='External AI'` and a normal `make -j16` pass, proving
  no battle or ROM change.
- Manual Windows PowerShell smoke test confirms the menu, both arrow keys,
  Enter, `--model`, and Ctrl+C behavior; a selected model completes one trainer
  battle while an absent service still falls back normally.
