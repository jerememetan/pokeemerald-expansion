# Deferred Custom Encounters Migration Design

## Goal

Restore the five archived custom encounters omitted from the bulk trainer-team import: early Steven in Granite Cave, Red in Altering Cave, Mom in Littleroot, Leaf's second New Mauville battle, and the Mt. Pyre Archie encounter. Preserve current Expansion 1.16.3 maps and progression as the base.

## Scope and Boundaries

Each encounter is an independently buildable vertical slice, but all five share one trainer-ID allocation change. The source of truth for each trainer's party, class, portrait, battle type, AI, dialogue, rewards, object location, and event flow is the archived commit named below. Current JSON map files and current Poryscript sources are the only authoring targets; generated `.inc` files are regenerated and never copied from the archive.

| Encounter | Archived evidence | Current behavior to preserve |
| --- | --- | --- |
| Steven | `c61b05602f` | Before Letter delivery, Steven challenges the player; a victory then continues the unchanged Letter, TM, PokeNav, and departure sequence. |
| Red | `c61b05602f` | Red stands at Altering Cave `(18,19)`, battles once, then is hidden only after a victory. |
| Mom | `c73e48076b`, `19b9449e16` | After the Amulet Coin, Mom offers an optional battle; accepting gives the three starter Mega Stones after victory, declining leaves a later retry, and a completed battle does not repeat. |
| Leaf 2 | `3b317f25c2`, `19b9449e16` | Leaf stands in New Mauville at `(27,34)`, has trainer sight range 6, battles once, and uses the archived Red-focused post-battle text. |
| Mt. Pyre Archie | `3b317f25c2` | Restore the archived Archie trainer and its intended Mt. Pyre story encounter; Route 122's separate blocker progression remains owned by its existing feature entry and is not broadened here. |

Out of scope: importing full archived maps/layouts, changing existing late-game Red/Steven battles, renumbering existing trainers, altering generic battle or save systems, and guessing a location, condition, or reward absent from archival evidence.

## Data Contract and Allocation

`src/data/trainers.party` remains the trainer authoring source and `src/data/trainers.h` remains generated output. Allocate the five new symbolic IDs consecutively after the current `TRAINER_MAY_PLACEHOLDER` ID: `TRAINER_STEVEN_GRANITE_CAVE`, `TRAINER_RED_ALTERING_CAVE`, `TRAINER_MOM`, `TRAINER_LEAF_2`, and `TRAINER_MT_PYRE_ARCHIE`.

Increase `TRAINERS_COUNT_EMERALD` from 855 to 860. This stays within `MAX_TRAINERS_COUNT_EMERALD` 864 and does not move any existing numeric ID. Preserve the archived team records exactly except where an archived species, move, item, ability, or AI spelling has a documented current 1.16.3 equivalent; such a substitution must be reported and validated in generated trainer output.

Use named progression flags rather than raw numeric values. The Mom flow uses the archived formerly-unused flags `0x1DA` (`FLAG_FOUGHT_MOM`) and `0x1DE` (`FLAG_DECLINED_MOM_BATTLE`) only after confirming they remain unused in current 1.16.3. Red gets a dedicated named hide flag selected from a currently unused flag after confirming no collision. Leaf uses the trainer-defeat state produced by its trainer battle; no second custom hide flag is added unless current map behavior requires one. Mt. Pyre Archie uses the archived battle-defeat state and any existing current story flag needed by its map script.

## Encounter Flows

### Steven

Add the archived battle invitation and no-intro trainer battle at the opening of the current Granite Cave Steven interaction. A loss must leave the Letter flow unconsumed. A victory shows the archived defeat text and resumes the untouched current Letter handover, TM reward, PokeNav registration, and departure actions exactly once.

### Red

Add Red to current `data/maps/AlteringCave/map.json` with the current object-event schema, archived `(18,19)` coordinates, `OBJ_EVENT_GFX_RED`, and a dedicated hide flag. His script starts the archived single battle. On victory only, show the archived completion text, fade/hide Red, set the hide flag, and release the player. On defeat, do not set the hide flag. The map-load script must respect the flag so Red remains absent after re-entry without modifying the existing landmark transition.

### Mom

Extend the current post-Amulet-Coin Mom interaction. If the Amulet Coin cannot enter the bag, use the existing bag-full fallback and do not offer the battle. Otherwise present the archived challenge prompt. Accepting starts the no-intro Mom battle; victory awards Sceptilite, Blazikenite, and Swampertite in order, with bag-full handling after every item, then sets `FLAG_FOUGHT_MOM`. Declining sets `FLAG_DECLINED_MOM_BATTLE` and leaves the later retry prompt available. Once fought, preserve Mom's normal healing behavior and never award the stones again.

### Leaf 2

Add the archived Leaf object to current New Mauville JSON at `(27,34)` using the current object schema and archived sight range. Use the current Poryscript source to start `TRAINER_LEAF_2`, show the archived intro/defeat text, then the archival Red-focused post-battle text from `data/text/trainers.inc`. A defeated Leaf follows normal trainer-defeat behavior and does not restart the battle.

### Mt. Pyre Archie

Use the existing current Mt. Pyre Summit Archie object at `(23,6)` and the existing `MtPyre_Summit_EventScript_TeamAquaExits` progression sequence. Insert the archived no-intro `TRAINER_MT_PYRE_ARCHIE` battle after Archie challenges the player and before the existing post-battle orb text, fade-out, object removals, hide flags, and `VAR_MT_PYRE_STATE` update. A loss must leave Archie and the Aqua grunts present and leave `VAR_MT_PYRE_STATE` unchanged. Route 122's optional blocker is not a substitute for this encounter.

## Failure, Fallback, and Validation

No slice may set a completion/hide flag before its trainer battle returns victory. A generator, script, or build failure leaves the current 1.16.3 behavior as the fallback; no generated file is edited manually.

Exit criteria:

1. Generated trainer output contains all five new IDs and their archived parties; total trainer count is 860 and no higher than 864.
2. Each map script compiles from its current source format and all map object identifiers resolve.
3. Steven, Red, Mom, and Leaf pass both victory and loss/decline behavior checks described above; Mt. Pyre Archie passes its archived prerequisite, victory, and loss paths once its source audit is complete.
4. A supported ROM build succeeds after all slices, and map reload checks confirm Red's one-time hide state and each defeated trainer's expected persistence.

## Links

- Existing Red/Steven design: [Early Story Red and Steven Battles Migration Design](2026-08-09-early-story-red-steven-battles-migration-design.md)
- Feature inventory: [Legacy Feature Review](../inventories/2026-08-09-legacy-feature-review.md)
- Parent design: [Original Hack 1.16.3 Migration Design](2026-08-09-original-hack-1.16.3-migration-design.md)
