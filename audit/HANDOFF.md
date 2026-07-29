# HANDOFF — BeamNG 0.39 update session

**Date:** 2026-07-29  
**Game:** v0.39 · D3D12 · MCP `http://127.0.0.1:29292/mcp`  
**Status:** AUDIT CLOSED (live UI smoke PASS)

## Done
- P1 theater: keybinds, bak park, majora paths, mock_crab spawn
- Discovery + BREAKING scan + materials + mesh #1 (grinning_hollow)
- P2/P3 leftovers: hammer dedupe, FIXED info_2d strip, Special K park, Zeit off
- mock_crab physics: controller settle/ramp (stable ~830 dmg); walkers skipped
- Live smoke: ExplosionLab + Bollard actions active + `trigger_action` OK
- Parked walker zips → `mods\_parked\walkers_skipped_2026-07-29\`
- Tomas stripped zip applied over `mods\Tomas.zip` (backup `_parked\Tomas.zip_before_force_swap`)

## Repos
| Repo | Tip / note |
|------|------------|
| `~BEAM UPDATE CURSOR REPO~` | audit docs only (no remote) |
| `beamng-studio` | mock_crab commits through walk-park |

## Skip (Alex)
- All walker / attach-walk weirdos — inactive + most zips parked
- Blanket vehicle/prop work unless a **named** break

## Restore paths
- Special K: `beamng-studio\_parked\injectors_specialk_pre_d3d12_2026-07-29\`
- Zeit: `mods\repo\renderer_components_loadsave_zeit.zip` (db active=false)
- hammer.zip: `mods\_parked\hammer.zip_dup_of_SledgeHammer_*`
- Walkers: `mods\_parked\walkers_skipped_2026-07-29\`
