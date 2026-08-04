# Phase 9 Local Ollama Model Selection Flow Review

**Specification reviewed:** [Phase 9 specification](../specs/2026-08-04-phase-9-local-model-selection.md)
**Implementation plan:** [Phase 9 implementation plan](../plans/2026-08-04-phase-9-local-model-selection.md)
**Grounding:** `tools/mgba-bridge/battle_agent_service.py` currently stores the model in the module constant `OLLAMA_MODEL`, posts it in `request_ollama`, and only accepts `--host` and `--port`; its tests use standard-library mocks and do not require a live Ollama installation.

## User flows

1. **Normal PowerShell start.** The service runs `ollama list`, parses the first name column, highlights `qwen2.5-coder:7b` when present, and starts the bridge only after Enter selects a model.
2. **Explicit startup.** `--model llama3.2:3b` bypasses discovery and input, connects to the bridge, and puts that exact value in the existing chat body.
3. **No usable local Ollama discovery.** A missing command, failed command, or empty model list prints one actionable message and exits before connecting. mGBA therefore sees no service and retains existing timeout/fallback.
4. **Noninteractive run.** Automated or redirected sessions never block for keys; they choose the preferred listed model, then first listed model, or exit with the same discovery error.
5. **Cancelled menu.** Ctrl+C exits cleanly before any bridge connection; a request that was already pending simply reaches the existing ROM timeout.

## Gaps and resolved defaults

| Severity | Finding | Resolution |
| --- | --- | --- |
| Important | Tests must not depend on a Windows terminal or live Ollama, but arrow-key behavior is central to the feature. | Separate parsing, defaulting, and key-navigation into pure functions. Wrap process execution and the Windows key reader behind small injectable functions. |
| Important | `ollama list` is formatted as a table and its version banner may vary; treating any whitespace line as a name could accidentally select a header. | Ignore blank lines and the `NAME` header; take only the first whitespace-separated field from remaining rows. A malformed/empty result is treated as no model. |
| Important | The service presently opens the mGBA socket inside `serve`, but model selection must not leave a half-started service. | Resolve the model in `main` before calling `serve`; pass the chosen model into request handling instead of mutating a global. |
| Important | A user may rely on scripted starts or name a model not in the current list. | `--model` is authoritative, skips discovery, and does no existence preflight. Ollama/network failures stay on the existing per-request fallback path. |
| Minor | Arrow-key terminals are platform-specific. | Phase 9 guarantees the arrow menu in Windows PowerShell via `msvcrt`; other interactive systems may use a numbered line prompt while preserving the same selected-model contract. |

No critical gaps remain. The specification’s failure behavior and scope are sufficient once it explicitly names the pre-bridge selection point and the Windows/non-Windows input default.

## Timeout amendment

The user requested a service-wide increase from 12 to 20 seconds after Qwen
occasionally timed out. The existing service uses this one constant for both
HTTP I/O and the bounded tool loop, so changing it keeps those layers aligned.
The ROM's 1,800-frame deadline remains authoritative: a slow or absent service
still yields no response and vanilla trainer AI.

## Audit highlighting amendment

The successful decision audit is already isolated in `format_decision_audit`.
Apply ANSI formatting only at the console-log boundary, based on the line
prefixes `selected:` and `battler ... ROM facts:`. This preserves audit strings,
tests, copied logs, malformed-response messages, and fallback behavior. When
stdout is redirected or does not support ANSI, emit the original plain text.
