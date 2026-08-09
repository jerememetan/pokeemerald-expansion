# Early Story Red and Steven Battles Migration Design

## Goal

Restore the archived v2.5.3 early-story battles with Steven in Granite Cave and Red in Altering Cave on the Expansion 1.16.3 migration branch, including their authored teams, text, map placement, and one-time progression behavior.

## Scope

In scope:

- Add two current-format trainer records and party pools using the archived teams and AI policy.
- Add `TRAINER_STEVEN_GRANITE_CAVE` and `TRAINER_RED_ALTERING_CAVE` after the current final trainer ID; increase `TRAINERS_COUNT_EMERALD` from 855 to 857 without exceeding the existing maximum of 864.
- Make Granite Cave Steven battle before accepting the Letter, then continue the existing Letter, TM, PokéNav, and departure flow.
- Add Red at archived Altering Cave coordinates `(18,19)` and remove/hide him permanently after defeat.

Out of scope:

- Existing late-game `TRAINER_STEVEN` and `TRAINER_RED` encounters.
- Other v2.5.3 trainer balance edits, configuration edits, trades, or map-visual changes.
- Changes to Letter rewards, Red/Steven graphics, generic trainer engine behavior, or save layout beyond the existing available trainer-ID range.

## Authored Battle Data

Steven uses five Pokémon with 11 IVs in each stat: Aron Lv.16 (Focus Sash; Stealth Rock, Dig, Rock Throw, Metal Claw), Anorith Lv.16 (Fury Cutter, Rock Throw, Metal Claw, Aqua Jet), Lileep Lv.16 (Mega Drain, Acid, Ingrain, Leech Seed), Metang Lv.18 (Leftovers; Iron Head, Confusion, Take Down, Iron Defense), and Gible Lv.16 (Berry Juice; Bulldoze, Bite, Rock Slide, Dragon Dance).

Red uses five Pokémon with 21 IVs in each stat: Pikachu Hoenn Cap Lv.22 (Light Ball; Volt Tackle, Iron Tail, Extreme Speed, Volt Switch), Snorlax Lv.21 (Body Slam, Crunch, Rest, Defense Curl), Charmeleon Lv.21 (Charcoal; Flame Charge, Dragon Breath, Metal Claw, Incinerate), Frogadier Lv.21 (Mystic Water; Water Pulse, U-turn, Mud Shot, Grass Knot), and Grotle Lv.21 (Eviolite; Substitute, Shell Smash, Earth Power, Mega Drain).

Both use the archived Rival class, portrait, male encounter music, singles format, and smart battle AI flags.

## Design

Use `src/data/trainers.party` as the authoring source and regenerate its derived `src/data/trainers.h` through the established trainer processor; do not edit the generated header by hand. Add the two trainer IDs within the current unused eight-slot headroom.

In `data/maps/GraniteCave_StevensRoom/scripts.inc`, update only Steven’s opening interaction: display the archived battle invitation, run a no-intro battle against the new early Steven trainer, show the archived defeat text, then resume the untouched current Letter handover sequence.

In Altering Cave, add the archived Red object at `(18,19)` with the current map JSON schema and a dedicated hide flag. Add map-load handling that removes/hides Red once defeated, and a Red interaction script that starts the new trainer battle, fades Red out, sets the hide flag, and releases control. Keep Altering Cave’s existing landmark transition behavior.

## Failure and Compatibility

The new IDs remain below `MAX_TRAINERS_COUNT_EMERALD` (864), preserving its current save allocation. No existing trainer ID changes. Red’s object hides only after a successful defeat; no failed battle or unrelated map load can consume the encounter. If trainer generation, script assembly, or the ROM build fails, the feature is not integrated and existing 1.16.3 behavior remains the fallback.

## Validation and Exit Criteria

1. Generated trainer output has both IDs and all ten exact party entries, levels, IVs, items, abilities where specified, and moves.
2. Steven battles before Letter delivery; after victory the normal Letter/TM/PokéNav/departure flow completes once.
3. Red appears at `(18,19)`, battles once, disappears after victory and a map reload, and remains present after a loss.
4. Trainer ID count is 857 and remains at or below the existing maximum of 864.
5. The supported build succeeds; targeted in-game checks cover both victory and failure paths.

## Evidence

- Archived source and teams: `git show c61b05602f -- data/maps/AlteringCave/scripts.pory data/maps/AlteringCave/map.json data/maps/GraniteCave_StevensRoom/scripts.pory src/data/trainer_parties.h src/data/trainers.h include/constants/opponents.h include/constants/flags.h`.
- Current targets: `src/data/trainers.party`, `include/constants/opponents.h`, `data/maps/AlteringCave/{map.json,scripts.inc}`, and `data/maps/GraniteCave_StevensRoom/scripts.inc`.
- Parent migration design: `2026-08-09-original-hack-1.16.3-migration-design.md`.
