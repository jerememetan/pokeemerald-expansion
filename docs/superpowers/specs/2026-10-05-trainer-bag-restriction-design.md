# Trainer-only battle bag restriction

## Approved outcome

The user requested bag restrictions first and selected: disable bag use
against trainers only. Wild battles, including throwing Poke Balls, stay
available under the existing unrelated capture/battle rules. Better Bag,
capacity, save layout, UI and deferred Pokemon data are outside this unit.

## Native implementation

Keep `IsAllowedToUseBag`, its callers and the complete event-variable API
unchanged. Set only `B_VAR_NO_BAG_USE` in `include/config/battle.h` to
`NO_BAG_AGAINST_TRAINER` (1). Clarify the configuration comment: the option
accepts either a literal mode 0/1/2 or a real variable ID containing that mode.

`GetVarPointer` returns NULL for IDs below VARS_START; `VarGet` then returns
the input literal. Thus `VarGet(1)` selects the existing trainer-only branch
without occupying a save variable. `VarSet(1, 0)` during initialization fails
without modifying save memory. This works for fresh and existing saves;
no save conversion or new-game initialization is required. The native debug
toggle expects a real variable ID and will still report that it cannot toggle
this constant configuration. Debug menus remain disabled as already configured.

The earlier explanation that this setting necessarily needs a real variable
was too restrictive. Do not replace this native literal behavior with a new
default-setting mechanism or hardcode a different bag permission helper.

## Verification

Compile the actual header, `GetVarPointer`, `VarGet`, `VarSet` and
`IsAllowedToUseBag` using native WSL cc and narrow external storage globals.
Demonstrate RED before the one setting changes, then GREEN. Cover default
trainer/wild behavior, literal modes 0/1/2 and invalid-value fallback, an
actual variable-ID variant with dynamic 0/1/2 values, and no saved-variable
mutation when the literal is queried or initialization tries to reset it.
Exercise double-battle flags alongside trainer/wild flags. Existing special
battle/capture rules and caller-side player restrictions stay unchanged.

Extend only the existing native-configuration regression's explicit macro
allowlist with `B_VAR_NO_BAG_USE`; do not add it to the list whose values are
expected to match the archive. The old archive used a flag, not this native
mode, and the selected trainer-only policy is the user's current choice.

Run all focused migration checks, the map importer suite, native generated
sources and the ROM build. Keep generation/ROM/save outputs out of the
workspace. Specification and quality review precede completion. Record exact
results and manual trainer/wild acceptance still needed. No automatic push.

## Scope and branch boundary

Pre-unit checkpoint: `6c4fde611f` on `codex/rom-hack-1.16.3-migration`.
Runtime allowlist: `include/config/battle.h` only. No changes to master or
AI Trainer, bag capacity, item data, flags, variables, map data, event scripts,
Pokemon stats/abilities/evolutions or the two already restored balance tunings.
