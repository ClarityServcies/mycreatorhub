# BeamNG v0.39 — Audit Summary

**Date:** 2026-07-29  
**Scope stop:** Alex — skip vehicles/props unless glaring; no more walker/attach-mesh work.

## Verdict

Theater blockers + discovery + BREAKING scan + non-vehicle polish **done enough to ship day-to-day on 0.39 D3D12**. Remaining vehicle/prop cosmetics deferred.

## Completed

| Area | Result |
|------|--------|
| MCP | In-engine `beamng-game` on `:29292`; Cursor `beamng` HTTP |
| P1 keybinds | Bollard / ExplosionLab unique `input_actions_*.json` |
| P1 bak | `pit_trap_mk2.bak_*` parked |
| P1 majora | Out of `/vehicles/common/`; cooker paths fixed |
| P1 mock_crab | Parse/spawn OK; settle controller; **walkers skipped/disabled** |
| Discovery | Inventories + `TRIAGE.md` |
| BREAKING | Clean (plates/Zeit/SK noted) |
| Materials | Majora emissive + path fix; GT7 traps flagged only |
| Mesh #1 | grinning_hollow cooker suffixes |
| P2 | hammer dedupe; FIXED info_2d strip |
| P3 | Filesystem MCP path; Special K parked; Zeit **off** |
| Graphics | Already **D3D12** High |
| Walkers | db `active=false` (crab/mechs/void_maw*/rooted*/etc.) |

## Cleared this pass

| Item | Note |
|------|------|
| Live UI smoke | PASS — 21 theater actions active; `explosionLabUI` + `toggleBollardControl` triggered |
| Walker zips | Parked to `mods\_parked\walkers_skipped_2026-07-29\` (locust/madcat/rooted/void_maw_klann) |
| Tomas.zip strip | Applied (backup `_parked\Tomas.zip_before_force_swap`) |
| Injectors | Special K removed from Bin64 (restorable) |

## Optional noise only

| Item | Note |
|------|------|
| bollard_UD part dupes | Log spam vs `/vehicles/common/` — ignore unless named cleanup |

## Do not do next (per Alex)

- Walker / attached walking mesh vehicles  
- Blanket vehicle/prop refactors  
- GT7 re-grade bake / mesh churn without a specific break  

## Suggested real next (non-vehicle)

1. Restart BeamNG once (SK gone, Zeit off, walkers inactive)  
2. Smoke-test **ExplosionLab** + **BollardControl** UI apps + keybinds  
3. Theater Director / Creator Hub if used on 0.39  
4. Only reopen vehicle work for a **named** broken spawn  

## Artifacts

All under `audit\` in this repo + live changes in BeamNG userfolder / `beamng-studio` (mock_crab source).
