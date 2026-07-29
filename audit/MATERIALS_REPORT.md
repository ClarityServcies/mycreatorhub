# Materials / lighting pass (v0.39)

**Generated:** 2026-07-29

## Scan

| Finding | Count |
|---------|------:|
| `*materials.json` loose | 54 |
| Already using `nits` key | 0 |
| Old-style `"emissive": true` + weak factor | 3 → 1 left (Moon gauges) |
| GT7 re-grade flags (glowMap / hot factors) | 2 |

## Applied (batch ≤25)

| File | Change |
|------|--------|
| `majora_moon/.../grinning_hollow/main.materials.json` | Drop `"emissive": true`; bump `emissiveFactor` 1→6 |
| `majora_moon/.../jack_skeleton/main.materials.json` | Same |
| **11** majora `main.materials.json` | Rewrite `vehicles/common/<veh>/` → `vehicles/<veh>/` (post P1 folder move) |

Stock docs still use `emissiveFactor` for light energy (bastion ~5). 0.39 “nits” = raise these factors / map energy, not a separate JSON key in your mods.

## Flagged (no bake)

| Asset | Why |
|-------|-----|
| `pit_trap_mk2/.../main.materials.json` | glowMap / GT7 re-grade — eyeball in-game |
| `spike_trap_mk8/.../main.materials.json` | same |
| `Moon/.../main.materials.json` (`atv_gauges_screen`) | stock-ish gauge emissive — leave until gauge QA |

## Next

- GT7 eyeball pit/spike traps  
- Then mesh pass (one asset)
