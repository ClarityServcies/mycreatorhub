# Smoke — ExplosionLab + Bollard (0.39)

**Date:** 2026-07-29  
**Live MCP:** PASS (`smallgrid`, physics running)

## File / mount check — PASS

| Check | Result |
|-------|--------|
| ExplosionLab active | yes (`unpacked`) |
| BollardContoller active | yes (`unpacked`) |
| Colliding `input_actions.json` | **gone** |
| ExplosionLab actions file | `input_actions_explosionlab.json` (mounted) |
| Bollard actions file | `input_actions_bollard.json` (mounted) |
| UI apps | `ExplosionLab`, `BollardControl`, `HammerControl`, `SpikeControl` |

## Live MCP — PASS

| Check | Result |
|-------|--------|
| `getActiveActions` theater hits | **21** (all ExplosionLab + Bollard GE actions) |
| `explosionLabUI` | `trigger_action` OK |
| `toggleBollardControl` | `trigger_action` OK (bollardControl.lua ran; spawned bollard_UD) |
| Missing-action spam | none for theater keys |

### Active theater actions (sample)
`explosionLabUI`, `explosionLabBoom`, `brainrot_run_show`, `brainrot_stop_show`, spawn hammer/slap/tph, `toggleBollardControl`, `bollardRaiseAll`, `bollardLowerAll`, `bollardSpawn`

### Note
`bollard_UD` vs `/vehicles/common/` duplicate part-name warnings in log — stock-ish noise, not a theater keybind fail. Skip unless you want a named parts cleanup.

## Alex optional QA (eyeballs)
1. Apps drawer → pin **ExplosionLab** + **Bollard Control**
2. Hit your binds once in freeroam
3. Done — audit closed
