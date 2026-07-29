# Phase 5B Flow Review: Manual Demo Guide and Recovery

**Specification reviewed:** [Phase 5B manual demo guide](../specs/2026-07-29-phase-5b-demo-guide.md)

## Codebase grounding

`tools/mgba-bridge/battle_agent_service.py` logs `connecting to mGBA` and
retries the Lua listener every 250 ms, then logs `mGBA bridge connected` after
one connection. `tools/mgba-bridge/mgba_bridge.lua` binds loopback port 57621,
logs `BAGB listener ready`, accepts one client, logs request forwarding and
response writes, and disables further listener use after an active client
disconnects. The existing README already documents the basic setup, but it
does not make startup order, session reset, symptom diagnosis, or the
thinking-status smoke checks sufficiently explicit.

## User flows

1. **Connected Calvin demo.** The developer builds/regenerates the mailbox
   address, confirms and warms the local model, starts the service, opens the
   ROM, loads Lua, and starts Calvin. Python's waiting connection and Lua's
   listener handshake become visible before the request/response sequence.
2. **Intentional fallback.** The developer runs without the service or stops
   it after `BAGB request forwarded`. The ROM shows the current thinking
   status, then completes its existing fallback; the guide identifies that as
   expected rather than a frozen game.
3. **Recovery.** The developer matches an Ollama, generated-address, Lua bind,
   bridge disconnect, rejected response, or fallback symptom to one scoped
   recovery action. A bridge reconnect requires a new mGBA/Lua session, not a
   second Python process or probe connection.

## Gaps found and resolved

### Critical

None. The documentation-only slice neither modifies a battle decision nor
creates a new process, protocol, or authority boundary.

### Important

1. **Service-first startup can look stalled.** `_connect` retries silently
   after its one `connecting to mGBA` log until Lua is loaded. The specification
   now calls this expected state out and gives the paired expected logs, so the
   guide will not tell users to restart a correctly waiting service.
2. **A fallback cannot prove a cold model caused it.** The existing service
   intentionally returns no response for model, parsing, timeout, and audit
   errors too. The specification now calls cold loading a likely latency cause
   only and directs the guide to use the actual logs for known bridge failure
   or rejection evidence.
3. **The Lua listener is not a safe health-check endpoint.** Its one accepted
   client is the real service session, and a disconnect leaves that session
   unusable. The specification explicitly prohibits probing it and requires
   mGBA/Lua restart before reconnecting.

### Minor

1. **Mailbox generation timing can be misunderstood.** The guide will place
   regeneration immediately after the fresh ROM/ELF build and before opening
   mGBA, avoiding manual edits to the ignored generated file.

## Resolved defaults

1. **Launch order:** Start the Python service before or after mGBA is allowed;
   the documented primary flow starts it first and treats its retrying
   `connecting to mGBA` line as expected until Lua is loaded.
2. **Diagnostic surface:** PowerShell and mGBA Scripting logs remain the only
   operator surface. No launcher, dashboard, health endpoint, or persisted
   telemetry is added.
3. **Fallback recovery:** Wait for the existing ROM fallback, then reset
   mGBA/Lua before beginning a fresh service session if the bridge disconnected.

## Recommended next steps

1. Rewrite the README around the grounded connected, fallback, and recovery
   flows, preserving actual command and log strings.
2. Add a documentation-source test only if an existing test pattern supports
   it without coupling to prose; otherwise use exact manual review plus the
   existing Python/ROM regression suites.
3. Record both live smoke outcomes and link the specification, this review,
   and implementation plan from the roadmap.
