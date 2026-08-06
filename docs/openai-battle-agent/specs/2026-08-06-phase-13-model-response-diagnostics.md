# Phase 13 Specification: Model-Response Diagnostics

**Roadmap:** [External AI Trainer Integration Plan](../integration-plan.md)
**Flow review:** [Phase 13 flow review](../reviews/2026-08-06-phase-13-model-response-diagnostics-flow-review.md)
**Implementation plan:** [Phase 13 implementation plan](../plans/2026-08-06-phase-13-model-response-diagnostics.md)

**Goal:** Make every Python-service fallback attributable to a specific malformed-response, invalid-action, per-call timeout, or whole-exchange deadline reason without changing game or model behavior.

**In scope:** When the existing tool-call parser cannot extract one valid call, log a deterministic failure category and a newline-normalized, at-most-240-character preview of the assistant response. Log the elapsed time when the 45-second tool-exchange deadline is reached. Log the name and argument-key mismatch for a syntactically parsed but unsupported tool call. Existing valid-action and invalid-`choose_actions` logs remain available.

**Out of scope:** Changing tool schemas, parser acceptance, prompts, Ollama parameters, retry count, time budgets, tool dispatch, action validation, mailbox protocol, mGBA Lua behavior, ROM behavior, or fallback selection.

**Boundaries and data contract:** Python service logging only. The diagnostic reads only Ollama's assistant response object, not the game request payload. Previews are bounded to 240 characters, replace newlines with spaces, and use `repr` so one model response produces one console line. No diagnostic data crosses the Python-to-Lua/ROM boundary.

**Failure and fallback behavior:** A malformed response receives the existing single correction retry. A second malformed response logs its category and returns no response. A parsed unsupported tool call logs its category and returns no response. Per-call HTTP failures continue to use the existing `rejected:` log. A 45-second exchange-expiry logs elapsed duration before returning no response. Every branch still gives the ROM no external action, preserving the existing vanilla trainer-AI fallback and never sending a partial plan.

**Tests and measurable exit criteria:** Unit tests must cover native multiple-call, invalid JSON content, unexpected JSON keys, and valid `choose_actions` list compatibility categories; preview must be single-line and bounded. A tool-loop test must assert a malformed response log names its category before its correction retry. A deadline test must assert the elapsed-duration diagnostic and existing `None` fallback. `py -3 -m unittest discover -s tools/mgba-bridge/tests -q` passes. Manual testing with a malformed response, invalid double action pair, and slow exchange shows one specific diagnostic before `produced no response`; normal single and double decisions remain unchanged.
