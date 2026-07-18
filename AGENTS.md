# Agent Instructions

## mGBA AI Trainer: phase documentation gate

These rules apply to every implementation phase of the external AI trainer project. A phase is not ready for production-code changes until its specification, flow analysis, and implementation plan are present and reviewed.

1. Write a phase-specific specification in `docs/openai-battle-agent/specs/`. It must state the goal, in-scope and out-of-scope behavior, ROM/emulator/service boundaries, data contract changes, failure and fallback behavior, tests, and measurable exit criteria.
2. Use the `spec-flow-analyzer` skill on that specification before writing the implementation plan. Ground the analysis in the current repository, map the happy path and all relevant failure paths, identify critical/important/minor gaps, and record the resulting review in `docs/openai-battle-agent/reviews/`.
3. Resolve every critical and important gap in the specification. If a decision is intentionally deferred, record the explicit default behavior and why it is safe. Do not leave unresolved ambiguity for an implementer to guess.
4. Use the `writing-plans` skill only after the specification and flow review are complete. Save the task-by-task implementation plan in `docs/openai-battle-agent/plans/`.
5. Every implementation plan must include the feature goal, architecture, exact files to create or modify, test files, test-first steps, commands with expected outcomes, compatibility/fallback checks, documentation updates, and phase exit criteria. It must contain no placeholders or vague instructions.
6. Self-review the plan for specification coverage, terminology/type consistency, protocol compatibility, unintended battle-mechanics changes, and scope creep. Revise the specification or plan before implementation if the review finds a discrepancy.
7. Link the specification, flow review, and implementation plan to one another. Update the project roadmap when a phase's scope, protocol, or acceptance criteria changes.
8. Do not begin the next phase until the current phase has fresh build/test evidence and its documented exit criteria are met. Preserve the existing trainer AI as the fallback unless a later, explicitly approved specification changes that rule.

If a proposed phase contains independent subsystems, split it into separately specified and planned sub-phases. Prefer the smallest safe vertical slice: one configured trainer, singles, moves, and legal-action validation before switching, items, broad trainer coverage, or double battles.
