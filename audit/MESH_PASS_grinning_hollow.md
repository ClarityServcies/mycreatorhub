# Mesh pass #1 — grinning_hollow

**Date:** 2026-07-29  
**Asset:** `mods/unpacked/majora_moon/vehicles/grinning_hollow`

## Inspect

| Check | Result |
|-------|--------|
| Submeshes | 1 (`grinning_hollow`) |
| Verts / tris | 33,108 / 60,000 |
| Bounds (m) | 1.68 × 1.85 × 1.90 |
| UV / normals | yes / yes |
| DAE material | `grinning_hollow_body` matches `main.materials.json` |
| Flexbody mesh name | `grinning_hollow` matches jbeam |
| Textures pow2 | all 2048×2048 |
| Decimate | **no** (silhouette OK; 60k acceptable for prop) |

Artifacts: `audit/mesh_grinning_hollow/` (`preview.png`, `tex_sheet.png`, `dae_report.json`)

## Fixed

Cooker suffixes were missing (raw `basecolor.png` etc. → no DDS cook).

| Old | New |
|-----|-----|
| `basecolor.png` | `grinning_hollow_body.color.png` |
| `normal.png` | `grinning_hollow_body.normal.png` |
| `metallic.png` | `grinning_hollow_body_m.data.png` |
| `roughness.png` | `grinning_hollow_body_r.data.png` |
| `emissive.png` | `grinning_hollow_body_e.data.png` |

`main.materials.json` updated to `/vehicles/grinning_hollow/...` cooker paths + emissiveFactor 6.  
Original PNGs copied to `_bak_textures_pre_cooker_2026-07-29/` (park, not delete).

## Next mesh candidates

Other majora vehicles still on bare `basecolor.png` / `vehicles/common` era names — same cooker rename pattern.  
Then pit_trap / spike_trap GT7 eyeball.
