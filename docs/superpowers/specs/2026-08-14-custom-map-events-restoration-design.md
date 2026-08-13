# Custom Map Events Restoration Design

## Goal

Restore the complete event layer that belongs to the archived map overhaul on top of the already migrated Expansion 1.16.3 layouts. This includes NPCs, trainers, item objects, warps, coordinate triggers, signs, hidden items, and the custom behavior they depend on. Preserve nonconflicting current-only 1.16.3 content and current schema improvements.

The migration must not copy shared archived `map.json` or script files wholesale. It must reproduce every archived custom delta through an explicit three-way decision and fail closed when an event cannot be matched or merged safely.

## Current Evidence

The restored layout report identifies 61 shared custom layout IDs. Those layouts are referenced by 75 shared maps in the audited baseline. Comparing the common base, archived hack, and current worktree shows event-layer changes on 69 of those maps:

- `object_events`: 68 maps changed; 35 changed the number of objects. The initial index-based diagnostic found 402 coordinate differences, but final ownership must use semantic matching rather than list index.
- `warp_events`: 6 maps changed.
- `coord_events`: 3 maps changed.
- `bg_events`: 16 maps changed.

The three restored custom maps—Littleroot Extension, Verdanturf Extension, and Petalburg Woodgrove—already use authoritative archived event data adapted to the current schema. They are validation inputs, not bulk-overwrite targets.

## Audited Sources

- Common base: `024848a9e9c0ae30cbb9a269779504561d5443d3`
- Archived hack: `f5e81e85df6fe40ae490bf7268d0186d7f0426ed`
- Current pre-event-migration baseline: `49c5f6dcaa57f0fc4dbc5bb114377ad49d6b9f5d`
- Layout scope: `docs/superpowers/inventories/2026-08-10-legacy-map-layout-report.json`

All tools must resolve these sources once, use immutable commit IDs for every Git read, and record source hashes in their evidence output.

## Chosen Approach

Use a candidate-first three-way semantic merge.

This is preferred over copying archived event arrays because wholesale copying would discard current-only objects, current schema changes, and upstream fixes. A coordinate-only migration is insufficient because the archive also added and removed NPCs, trainers, items, triggers, and warps.

## Scope Discovery

The event merger derives shared layout IDs from the committed layout report, resolves every current-baseline map that references those IDs, and requires the audited total of 75 shared maps. It then inventories all four event arrays for the common base, archive, and current baseline.

Every event receives one machine-readable disposition. Allowed outcomes are:

- Keep current unchanged
- Use archived custom change
- Keep current-only addition
- Restore archived-only addition
- Preserve converged change
- Merge nonconflicting fields
- Delete through archived custom removal
- Deliberate current equivalent
- Explicit conflict requiring a reviewed resolution

The candidate cannot be applied while any event is unmatched, ambiguously matched, multiply owned, or missing a disposition.

## Event Alignment

Events are never matched solely by array position. Alignment proceeds in deterministic stages and removes a matched event from further consideration at every stage:

1. Exact full-record match after ignoring current-only schema metadata.
2. Exact behavior match after ignoring placement fields `x`, `y`, and `elevation`.
3. Unique category-specific identity match:
   - Objects: script, flag, trainer type and trainer/berry value, graphics, and movement behavior.
   - Warps: destination map and destination warp ID.
   - Coordinate events: type plus script, weather, or variable behavior payload.
   - Background events: type plus script or hidden-item payload and facing behavior.
4. A reviewed explicit resolution for any remaining ambiguity.

An automatic match is accepted only when it is unique in both directions. Repeated or indistinguishable events must be resolved explicitly; the tool must not choose the nearest coordinate or first list entry as a guess.

## Three-Way Merge Rules

For a base-owned event:

- Archive changed, current unchanged: restore the complete archived change.
- Current changed, archive unchanged: keep current.
- Both made the same change: keep one converged event.
- Both changed disjoint fields: merge the fields. Archived placement wins, while compatible current schema-only fields remain.
- Both changed the same behavior field incompatibly: record a conflict and require an explicit resolution.
- Archive deleted, current unchanged: preserve the archived custom deletion.
- Current deleted, archive unchanged: preserve the current deletion.
- One side deleted while the other changed: require explicit resolution.

For additions:

- Preserve archive-only and current-only additions.
- Deduplicate semantically identical additions.
- Reject additions that collide on a unique script, flag, local ID, trainer identity, warp destination identity, or occupied event role without a reviewed resolution.

Output order keeps current events in their existing relative order where possible. Archived additions are inserted according to archived neighbor relationships. Ordering decisions must be deterministic and recorded.

## Behavior Dependencies

After creating candidate event arrays, audit every referenced script, flag, trainer, graphics ID, item, variable, map, and destination warp.

- Keep a current dependency when it already implements the custom behavior or is a compatible newer equivalent.
- Restore or adapt an archived-only dependency.
- Restore an archived semantic change when the archive changed it and current remained at the common base.
- Stop for review when archive and current changed the same behavior incompatibly.
- Never copy an entire shared archived script file merely because one label is needed.

Existing script labels also require three-way behavior auditing. A label being present in current is not sufficient proof that the archived custom behavior survived.

Every restored event must have a resolved dependency disposition before apply.

## Components and Outputs

Create a standard-library migration command that:

1. Audits and aligns events from the three pinned sources.
2. Reads a committed explicit-resolution manifest for ambiguous cases.
3. Writes candidate `map.json` files beneath an ignored build directory.
4. Writes a deterministic evidence report under `docs/superpowers/inventories/`.
5. Applies only exact reviewed candidates through an explicit `--apply` mode.

The evidence report records, per map and category:

- Source and candidate hashes.
- Every match and disposition.
- Added, removed, moved, retained, and field-merged events.
- Current-only content retained.
- Conflicts and explicit resolutions.
- Dependency ownership and validation results.

Any required script or constant adaptations are authored as small focused patches and referenced from the report rather than generated by copying whole legacy files.

## Apply Safety and Idempotence

Candidate mode never mutates authored source.

Before apply, the tool requires the complete destination set to be coherently in one of two states:

- Exact pinned pre-migration preimages.
- Exact recomputed post-migration candidates.

A mixed, stale, or third state is rejected before authoritative writes. Applying from the post-migration state is a true no-op.

Multi-file apply uses the repository's proven destination-side staging, preimage validation, atomic replacement, and recovery rules. A failed rollback must retain and name every recovery copy that contains the only preimage. Candidate, report, source, manifest, and internal transaction paths cannot collide.

## Validation

Automated acceptance requires:

- All source and candidate JSON parses.
- Exactly 75 shared maps are audited and all three custom maps validate without overwrite.
- Every archived custom event delta has exactly one disposition.
- Every current-only event is retained unless an explicit reviewed conflict says otherwise.
- Object coordinates and movement bounds fit the referenced layout.
- Local IDs, flags, and other unique identities do not collide.
- Every warp destination exists; reciprocal custom transitions remain valid.
- Every script and constant reference resolves.
- Map generation completes.
- A clean WSL-native full ROM build exits successfully and produces a nonempty ROM.
- Deterministic reruns reproduce candidate and evidence hashes from both exact pre- and post-migration states.

PoryMap inspection must cover the highest-change routes and dungeons plus all three custom maps. mGBA acceptance must exercise representative moved NPCs, trainers, items, coordinate triggers, signs, hidden items, and changed warps. Manual visual/runtime checks are reported separately and never claimed when not performed.

## Non-Goals

- Replacing current shared map scripts wholesale.
- Removing nonconflicting 1.16.3 event additions.
- Migrating maps outside the restored layout scope merely because their scripts share labels.
- Guessing through ambiguous repeated events.
- Editing map tiles, encounter tables, trainer parties, move animations, or unrelated gameplay behavior in this pass.

## Completion Criteria

The migration is complete when all scoped event and dependency records have exact dispositions, the candidate applies reproducibly, all automated validation and the full build pass, and remaining manual PoryMap/mGBA checks are handed off explicitly. No unresolved conflict may be hidden behind a category-level default.
