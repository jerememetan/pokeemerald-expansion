# Lavaridge Random Egg Migration Design

## Goal

Restore the archived Lavaridge Egg Woman reward on the 1.16.3 migration branch: after a player accepts the gift and has a party slot, the Egg contains one uniformly selected species from Wynaut, Togepi, Chimchar, Piplup, or Turtwig.

## Scope

In scope:

- Replace only the hard-coded `SPECIES_WYNAUT` Egg result in the current Lavaridge script.
- Preserve the archived five equally likely outcomes.
- Preserve current one-time, decline, full-party, fanfare, message, and received-Egg behavior.

Out of scope:

- Any other Lavaridge events, dialogue, map objects, or rival progression.
- Egg moves, natures, IVs, or hatching behavior.
- New UI, configuration, flags, or save data.

## Design

The current `LavaridgeTown_EventScript_EggWoman` already validates acceptance and party capacity, sets `FLAG_RECEIVED_LAVARIDGE_EGG`, plays the received-item fanfare, and then calls `giveegg SPECIES_WYNAUT`. Replace only that final hard-coded command with a local script routine that calls `random 5` and dispatches values 0 through 4 to `giveegg` commands for Wynaut, Togepi, Chimchar, Piplup, and Turtwig respectively.

The routine returns to the existing caller. It creates no new persistent state, so declining or lacking party space continues not to consume the gift, and a completed gift continues to take the existing received-Egg path on later interactions.

## Compatibility and Failure Behavior

The implementation uses existing script commands and the existing generated Lavaridge source file, so it requires no engine change. Every random result has one valid `giveegg` branch. If script generation or compilation rejects the updated source, the change is not integrated and the current 1.16.3 script remains the fallback.

## Validation and Exit Criteria

1. A script/source inspection proves all five species are reachable from a `random 5` dispatch.
2. Declining leaves the gift available; a full party leaves it available; accepting with space sets the existing received-Egg flag exactly once.
3. Repeated eligible fresh-save trials can produce all five species.
4. The supported ROM build succeeds and no unrelated Lavaridge behavior changes.

## Evidence

- Archived implementation: `git show 01f34f7b03 -- data/maps/LavaridgeTown/scripts.pory`.
- Current target: `data/maps/LavaridgeTown/scripts.inc`, where the Egg Woman currently gives only Wynaut.
- Parent migration design: `2026-08-09-original-hack-1.16.3-migration-design.md`.
