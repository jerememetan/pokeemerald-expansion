# Badge and Received-HM Unlocks

Continuation of the approved original-hack restoration design. The user
explicitly clarified that badge plus HM-received flag is sufficient: no
Pokemon needs to learn the HM. This clarification supersedes the older
inventory's known-move requirement. Starting checkpoint: e6cd947d6f.

## Required behaviour

| HM | Emerald badge | Received flag |
| --- | --- | --- |
| Cut | 1 | FLAG_RECEIVED_HM_CUT |
| Flash | 2 | FLAG_RECEIVED_HM_FLASH |
| Rock Smash | 3 | FLAG_RECEIVED_HM_ROCK_SMASH |
| Strength | 4 | FLAG_RECEIVED_HM_STRENGTH |
| Surf | 5 | FLAG_RECEIVED_HM_SURF |
| Fly | 6 | FLAG_RECEIVED_HM_FLY |
| Dive, including surfacing | 7 | FLAG_RECEIVED_HM_DIVE |
| Waterfall | 8 | FLAG_RECEIVED_HM_WATERFALL |

Both flags must be set for all entry points. Preserve the current alternate
FRLG badge mapping when compiled for FRLG. Preserve terrain/warp/direction,
already-surfing, follower, link-room and other current environment checks.
Already-activated Strength retains its existing session state behaviour.

Use current field animations and a valid non-egg party member as the animation
actor, without requiring that actor to know the HM. Empty/all-egg parties
must fail safely without indexing PARTY_SIZE. Non-HM moves retain their
known-move and optional unlock requirements; no universal field-move cheat.

## Smallest practical implementation

- Add received-flag conjunctions to the existing eight unlock callbacks in
  src/field_move.c, preserving current badge choices.
- Add one shared party-selector function there, declared in include/field_move.h.
  HMs always require unlock; select the first non-egg member. Non-HMs use
  their current known-move policy and the caller's optional unlock check.
- ScrCmd_checkfieldmove delegates selection to that helper and preserves
  PARTY_SIZE failure and successful species/party-index outputs.
- PartyHasMonWithSurf uses the same selector instead of requiring learned
  Surf, while retaining its already-surfing check. No terrain logic changes.
- Add an HMs submenu to the existing party action menu, showing only unlocked
  HMs plus Cancel and invoking current CursorCb_FieldMove. This gives Fly
  and Flash an access point without teaching or restoring the full-screen
  start menu. Preserve existing known-move actions and all other menus.
- Expand the action buffer from eight to nine entries: root maximum is four
  known moves + Summary/Switch/Item/Cancel + HMs, and submenu maximum is
  eight HMs + Cancel. Nine entries occupy 18 tiles at top row 1, fitting the
  existing window formula. Never append all eight HMs to the root list.

No new configuration registry, full-screen menu, Better Bag, map geometry,
encounters, trainer teams or battle changes. Existing Cut/Rock Smash scripts
already satisfy no-teaching interaction and are not replaced.

## Verification

Focused tests compile actual field_move.c, actual script-command and Surf
selector bodies, and actual party root/submenu construction under narrow
native C stubs. Independently specify all eight badge/flag pairs; test every
combination with no learned HMs, learned-but-locked, valid/empty/egg parties,
non-HM known-move preservation, Emerald/FRLG mappings, script outputs and
safe failure. Exercise all-unlocked submenu, worst-case nine-action root,
Cancel placement and capacity/window bounds. Tests must fail before source
changes and pass after; independent spec then quality review, ROM build.

Actual animation, menu appearance/cancellation, Fly return flow, Flash effect,
Strength persistence and Dive/surfacing require disposable-save playtests.
