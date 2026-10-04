# Native Configuration Restoration

Restore audited configuration choices using Expansion 1.16.3's existing
settings and numeric constants. No obsolete Pokemon/battle/bag engine import.
Continuation authorised by the user's request to do HMs and configurations.
Full-screen start menu and Better Bag remain out of this pass.

## Historical evidence

Pin archive f5e81e85df6fe40ae490bf7268d0186d7f0426ed. Compare it to effective
older upstream 1565171235 (expansion/1.7.4-5), incorporated as second parent
of 4860d1c854. Do not compare to merge-base 024848a9e9: the later 1.8.1 merge
was explicitly reverted by 517565131d, and withdrawn upstream features are
not custom tuning. There are 31 authored macro choices in four old config
headers; old pokemon.h and species_enabled.h have no custom macro changes.

## Required current settings

| Current header | Setting | Value |
| --- | --- | --- |
| config/battle.h | B_PROTEAN_LIBERO | GEN_8 |
| config/battle.h | B_INTREPID_SWORD | GEN_8 |
| config/battle.h | B_DAUNTLESS_SHIELD | GEN_8 |
| config/battle.h | B_WAIT_TIME_MULTIPLIER | 8 |
| config/battle.h | B_QUICK_MOVE_CURSOR_TO_RUN | TRUE |
| config/battle.h | B_AFFECTION_MECHANICS | FALSE |
| config/battle.h | B_USE_FROSTBITE | TRUE |
| config/wild_encounter.h | WE_DOUBLE_WILD_CHANCE | 20 |
| config/wild_encounter.h | WE_DOUBLE_WILD_REQUIRE_2_MONS | TRUE |
| config/item.h | I_SHINY_CHARM_ADDITIONAL_ROLLS | 5 |
| config/item.h | I_USE_EVO_HELD_ITEMS_FROM_BAG | TRUE |
| config/item.h | I_REUSABLE_TMS | TRUE |
| config/item.h | I_EXP_SHARE_FLAG | FLAG_TOGGLE_EXPALL |
| config/item.h | I_EXP_SHARE_ITEM | GEN_6 |
| config/overworld.h | OW_SYNCHRONIZE_NATURE | GEN_8 |
| config/debug.h | DEBUG_OVERWORLD_MENU | FALSE |
| config/debug.h | DEBUG_BATTLE_MENU | FALSE |
| config/debug.h | DEBUG_POKEMON_SPRITE_VISUALIZER | FALSE |
| config/pokedex_plus_hgss.h | POKEDEX_PLUS_HGSS | TRUE |
| constants/pokemon.h | SHINY_ODDS | 128 |
| constants/pokemon.h | LEGENDARY_PERFECT_IV_COUNT, enabled branch | 4 |

All header paths are under include/. Keep the disabled legendary-IV branch
at zero. These 21 choices use existing settings/constants, not replacement
implementations. The three debug menus must be off in ordinary developer
builds too: DISABLED_ON_RELEASE alone only matches the archive for RELEASE=1.
Retain all other current options, including latest Pokemon/species defaults.
HGSS Pokédex is a native toggle, separate from the excluded full-screen menu.

Rename unused Emerald FLAG_UNUSED_0x023 (0x23) to FLAG_TOGGLE_EXPALL in
include/constants/flags.h. It is permanent, above TEMP_FLAGS_END, unused by
the current game and matches the archive. Keep FLAG_RECEIVED_EXP_SHARE
separate: it tracks Mr. Stone's reward, not whether EXP All is enabled.
Receipt does not auto-enable it. Use the native Key Item toggle; fresh saves
start off until item use. Retain current native item data and EXP consumers.

## Already equivalent and unchanged

Current move-name length is already 16. Eleven archived overworld ability
settings already supply their old effects via current >=GEN_8 consumers or
unconditional implementations, so do not blanket-change every GEN_LATEST.
Nature mints are already native. Keep all current moves/animations/Psychic
Noise, berry/cap changes, HM implementation and custom data content.

## Explicitly outside this configuration unit

- Old B_FLAG_NO_BAG_USE=1 was a temporary FLAG ID, not a boolean. The current
  B_VAR_NO_BAG_USE expects a variable ID and mode value. Do not convert the
  literal 1 into a variable or activate accidental map-temporary restrictions.
  A deliberate restriction policy needs separate clarification/wiring.
- Friendship evolution threshold 120 is an old local code constant. Current
  generation setting offers 160/220, not 120. It remains an explicit numeric
  tuning adaptation, not solved by this settings pass.
- Species stats, abilities, learnsets and per-species evolutions are table
  edits, not settings. Toxic Boost's old 1.3x Speed is algorithmic, not a toggle.
- Battle Frontier data, full-screen start menu and Better Bag remain separate.

## Verification

Tests independently compare pinned old config choices and compile current
headers/constants to verify values and retained conditional branches. Also
compile the actual native EXP Share toggle and IsGen6ExpShareEnabled getter
with narrow engine stubs to verify off/on/off in bag and registered-key-item
paths, valid permanent flag ID and isolation from the receipt flag. Check
current Key Item pocket/toggle binding, reusable-TM and evolution-item wiring,
plus the absence of unrelated header changes. Red before settings edits,
green afterward, spec then quality review, full exact-source ROM build.

In-game item consumption, double encounters, abilities, Frostbite, Pokédex
and EXP All experience still require disposable-save acceptance checks.
