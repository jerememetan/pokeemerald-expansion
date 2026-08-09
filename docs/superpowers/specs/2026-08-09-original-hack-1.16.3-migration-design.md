# Original Hack Migration to Expansion 1.16.3

## Goal

Recreate every custom, player-visible and developer-configured change present on `archive/master-pre-1.16.3` on top of the clean Expansion 1.16.3 release, while retaining the current release's upstream systems and fixes.

## Baselines

- **Target baseline:** `master`, at Expansion 1.16.3 (`c828d12721`).
- **Legacy reference:** `archive/master-pre-1.16.3` (`f5e81e85df`).
- **Out of scope for this migration:** The separate `hackathon-ai-trainer` branch and its external AI trainer feature. It remains an independent future migration.

## Migration Principles

1. Preserve intended legacy behavior, not obsolete legacy implementation details.
2. Never merge the legacy archive wholesale into the 1.16.3 baseline.
3. Retain all upstream 1.16.3 functionality unless a legacy custom behavior intentionally replaces it.
4. Port each independent feature in a dedicated, testable phase. A phase may depend only on previously completed phases.
5. Keep `master` releasable. Migration work happens on dedicated branches and reaches `master` only after verification.
6. Treat legacy imported features as required functionality when they are present in the archived game, but first determine whether 1.16.3 already supplies an equivalent implementation.

## Current Evidence

The archived and target trees differ in 2,124 paths: 1,411 modifications, 540 additions, 154 deletions, and renamed paths. The legacy history includes custom content, full-screen start-menu work, bag/pocket changes, nature-mint work, experience configuration, map/script edits, trainer changes, move and animation changes, and Battle Frontier changes. It also contains historical Expansion code and third-party merges that must not overwrite 1.16.3 blindly.

## Architecture

```text
archive/master-pre-1.16.3 (behavior reference)
              |
              v
  feature inventory and acceptance checklist
              |
              v
  focused migration branches based on master (1.16.3)
              |
              v
  build, automated checks, and in-game verification per phase
              |
              v
          master (updated custom hack)
```

## Phases

### 1. Migration inventory

Produce a feature-level manifest that maps every legacy difference to one of: direct transfer, current upstream equivalent, modern adaptation, or deliberate custom replacement. Each feature entry must list legacy source paths, target paths, behavior, dependencies, validation, and completion status.

### 2. Data, assets, and content

Port custom maps, map scripts, events, trainer data, encounters, text, graphics, audio, Pokémon, moves, items, and configuration data. Use modern source formats and generators. Regenerate derived assets instead of carrying legacy build output.

### 3. Interface and quality-of-life features

Port the full-screen start menu, bag/pocket behavior, and other player-facing UX changes against the 1.16.3 UI and configuration APIs.

### 4. Gameplay and battle features

Port custom mechanics, move changes, battle animations, team changes, and Battle Frontier behavior against current battle engine interfaces. Do not copy legacy battle-engine or test-suite deletions.

### 5. Imported-feature reconciliation

For each old third-party feature, identify the 1.16.3 equivalent or reimplement the missing behavior. Preserve the archived game's player-facing result, including intended configuration choices.

### 6. End-to-end parity verification

Build the game, run the applicable automated suites, inspect a clean new-game path, verify custom maps/events/UI/gameplay features, and compare every inventory entry against the legacy reference. Integrate only when every entry is verified or has a documented upstream-equivalent proof.

## Failure and Fallback Behavior

- A conflict, failed build, failed test, or uncertain legacy behavior stops only the affected phase; it does not block independent phases.
- The archived branch is the authoritative behavior reference when documentation and code differ.
- The current 1.16.3 behavior remains in place until a replacement feature is verified.
- If legacy data needs format conversion, retain the original source in the archive and generate current-format outputs reproducibly.

## Verification and Exit Criteria

The migration is complete only when:

1. Every custom legacy feature has an inventory record and a verified 1.16.3 implementation or upstream-equivalence finding.
2. No legacy upstream code or stale generated outputs overwrite current Expansion infrastructure.
3. The final branch builds successfully with the repository's supported build command.
4. Automated tests relevant to changed mechanics pass.
5. Manual in-game checks prove all custom maps, events, UI, content, and gameplay changes function as intended.
6. The `hackathon-ai-trainer` branch remains unmodified by this migration.
